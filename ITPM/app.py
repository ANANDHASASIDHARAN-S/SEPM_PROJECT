from flask import Flask, render_template, redirect, url_for, request, flash, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from functools import wraps
from datetime import datetime, date, timedelta
from collections import Counter
import hashlib
import json
import time
import urllib.error
import urllib.request
from threading import Lock
from config import Config
from models import db, User, LeaveType, LeaveBalance, LeaveRequest, LeavePolicy, AuditLog

# ─── App Setup ────────────────────────────────────────────────────────────────

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'warning'

# Small in-memory cache to avoid repeated local model calls during live form typing.
OLLAMA_REASON_CACHE = {}
OLLAMA_REASON_CACHE_LOCK = Lock()
OLLAMA_LEAVE_PRED_CACHE = {}
OLLAMA_LEAVE_PRED_CACHE_LOCK = Lock()


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# ─── Decorators ───────────────────────────────────────────────────────────────

def role_required(*roles):
    """Restrict access to specific roles."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if current_user.role not in roles:
                flash('You do not have permission to access this page.', 'danger')
                return redirect(url_for('dashboard'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def log_action(user_id, action, details=None):
    """Log an action to the audit log."""
    entry = AuditLog(user_id=user_id, action=action, details=details)
    db.session.add(entry)
    db.session.commit()


def count_business_days(start_date, end_date):
    """Count weekdays between two dates (inclusive)."""
    business_days = 0
    current = start_date
    while current <= end_date:
        if current.weekday() < 5:
            business_days += 1
        current += timedelta(days=1)
    return business_days


def next_business_day(candidate_date):
    """Move date forward to the next weekday if needed."""
    while candidate_date.weekday() >= 5:
        candidate_date += timedelta(days=1)
    return candidate_date


def add_business_days(start_date, business_days):
    """Add business days to a date and return the inclusive end date."""
    if business_days <= 0:
        return start_date

    current = start_date
    remaining = business_days
    while remaining > 0:
        if current.weekday() < 5:
            remaining -= 1
            if remaining == 0:
                break
        current += timedelta(days=1)
    return current


def analyze_leave_reason(reason):
    """Rule-based reason quality analysis for the Smart Apply Helper."""
    text = (reason or '').strip()
    lowered = text.lower()
    words = [w for w in text.replace('\n', ' ').split(' ') if w]

    urgent_keywords = {
        'urgent', 'emergency', 'hospital', 'surgery', 'accident',
        'bereavement', 'funeral', 'critical'
    }

    tips = []
    score = 100

    if not text:
        score = 20
        tips.append('Add a short reason so your manager can review quickly.')
    else:
        if len(words) < 5:
            score -= 35
            tips.append('Add a bit more detail (what and why) to avoid back-and-forth.')
        elif len(words) < 10:
            score -= 15
            tips.append('Consider adding one more detail for clarity.')

        if len(text) < 25:
            score -= 15
            tips.append('Very short reasons are often delayed during review.')

        if lowered in {'personal', 'medical', 'family', 'private', 'other'}:
            score -= 25
            tips.append('Try to be slightly more specific while keeping private details minimal.')

    is_urgent = any(keyword in lowered for keyword in urgent_keywords)
    if is_urgent:
        tips.append('This looks urgent. Inform your manager directly for faster response.')

    score = max(0, min(100, score))
    if is_urgent:
        label = 'urgent'
        summary = 'Urgent request detected. Submit now and notify your manager directly.'
    elif score < 60:
        label = 'needs_detail'
        summary = 'Reason may be too brief. Add more context to improve approval speed.'
    elif score < 80:
        label = 'improve'
        summary = 'Reason is acceptable, but a little more detail can help review faster.'
    else:
        label = 'good'
        summary = 'Reason looks clear and ready for manager review.'

    return {
        'label': label,
        'score': score,
        'is_urgent': is_urgent,
        'tips': tips,
        'summary': summary,
        'model_source': 'rule'
    }


def get_ollama_reason_analysis(reason, leave_type_name=None, start_date=None, end_date=None):
    """Fetch optional leave-reason guidance from a local Ollama model."""
    if not app.config.get('AI_OLLAMA_ENABLED', False):
        return None

    text = (reason or '').strip()
    if not text:
        return None

    prompt = (
        'You are assisting an employee leave form reviewer. '
        'Analyze the leave reason quality and return strict JSON only with keys: '
        'label, summary, tips, score. '
        'Allowed label values: good, improve, needs_detail, urgent. '
        'tips must be a JSON array with at most 3 short strings. '
        'score must be an integer from 0 to 100. '
        f'Leave type: {leave_type_name or "Unknown"}. '
        f'Start date: {start_date.isoformat() if start_date else "Unknown"}. '
        f'End date: {end_date.isoformat() if end_date else "Unknown"}. '
        f'Reason: "{text}"'
    )

    payload = {
        'model': app.config.get('AI_OLLAMA_MODEL', 'qwen3.5:4b'),
        'prompt': prompt,
        'stream': False,
        'format': 'json',
        'options': {
            'temperature': 0.2
        }
    }

    endpoint = f"{app.config.get('AI_OLLAMA_BASE_URL', 'http://127.0.0.1:11434').rstrip('/')}/api/generate"
    timeout = app.config.get('AI_OLLAMA_TIMEOUT_SECONDS', 20)

    try:
        req = urllib.request.Request(
            endpoint,
            data=json.dumps(payload).encode('utf-8'),
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
        with urllib.request.urlopen(req, timeout=timeout) as response:
            body = response.read().decode('utf-8')
    except (urllib.error.URLError, TimeoutError, OSError, ValueError):
        return None

    try:
        response_json = json.loads(body)
    except (json.JSONDecodeError, TypeError, AttributeError):
        return None

    # Some local models put structured output in `thinking` and leave `response` empty.
    model_text = (response_json.get('response') or '').strip()
    source_suffix = ':response'
    if not model_text:
        model_text = (response_json.get('thinking') or '').strip()
        source_suffix = ':thinking'
    if not model_text:
        return None

    try:
        parsed = json.loads(model_text)
    except json.JSONDecodeError:
        first_brace = model_text.find('{')
        last_brace = model_text.rfind('}')
        if first_brace == -1 or last_brace == -1 or last_brace <= first_brace:
            return None
        try:
            parsed = json.loads(model_text[first_brace:last_brace + 1])
        except json.JSONDecodeError:
            return None

    summary = str(parsed.get('summary', '')).strip()
    raw_tips = parsed.get('tips', [])
    tips = [str(item).strip() for item in raw_tips if str(item).strip()]
    tips = tips[:3]

    raw_score = parsed.get('score', 0)
    try:
        score = max(0, min(100, int(raw_score)))
    except (ValueError, TypeError):
        score = 0

    raw_label = str(parsed.get('label', '')).strip().lower().replace(' ', '_')
    label_alias = {
        'good': 'good',
        'clear': 'good',
        'strong': 'good',
        'improve': 'improve',
        'ok': 'improve',
        'okay': 'improve',
        'average': 'improve',
        'needs_detail': 'needs_detail',
        'needs_more_detail': 'needs_detail',
        'weak': 'needs_detail',
        'bad': 'needs_detail',
        'urgent': 'urgent',
        'emergency': 'urgent',
        'critical': 'urgent'
    }
    label = label_alias.get(raw_label)

    if not label:
        summary_lower = summary.lower()
        if any(token in summary_lower for token in {'urgent', 'emergency', 'critical'}):
            label = 'urgent'
        elif score >= 80:
            label = 'good'
        elif score >= 60:
            label = 'improve'
        else:
            label = 'needs_detail'

    return {
        'label': label,
        'summary': summary,
        'tips': tips,
        'score': score,
        'model_source': f"ollama:{app.config.get('AI_OLLAMA_MODEL', 'qwen3.5:4b')}{source_suffix}"
    }


def get_cached_ollama_reason_analysis(reason, leave_type_name=None, start_date=None, end_date=None):
    """Wrapper that stores successful Ollama responses in a small in-memory cache."""
    text = (reason or '').strip()
    if not text:
        return None

    cache_ttl = app.config.get('AI_OLLAMA_CACHE_TTL_SECONDS', 120)
    cache_max_entries = app.config.get('AI_OLLAMA_CACHE_MAX_ENTRIES', 256)
    cache_key_raw = '|'.join([
        app.config.get('AI_OLLAMA_MODEL', 'qwen3.5:4b'),
        leave_type_name or '',
        start_date.isoformat() if start_date else '',
        end_date.isoformat() if end_date else '',
        text
    ])
    cache_key = hashlib.sha256(cache_key_raw.encode('utf-8')).hexdigest()

    now_ts = time.time()
    with OLLAMA_REASON_CACHE_LOCK:
        expired_keys = [
            k for k, item in OLLAMA_REASON_CACHE.items()
            if (now_ts - item.get('ts', 0)) > cache_ttl
        ]
        for k in expired_keys:
            OLLAMA_REASON_CACHE.pop(k, None)

        cached = OLLAMA_REASON_CACHE.get(cache_key)
        if cached and (now_ts - cached.get('ts', 0)) <= cache_ttl:
            return dict(cached.get('value', {}))

    analysis = get_ollama_reason_analysis(
        reason=reason,
        leave_type_name=leave_type_name,
        start_date=start_date,
        end_date=end_date
    )
    if not analysis:
        return None

    with OLLAMA_REASON_CACHE_LOCK:
        if len(OLLAMA_REASON_CACHE) >= cache_max_entries:
            oldest_key = min(OLLAMA_REASON_CACHE, key=lambda k: OLLAMA_REASON_CACHE[k].get('ts', 0))
            OLLAMA_REASON_CACHE.pop(oldest_key, None)
        OLLAMA_REASON_CACHE[cache_key] = {
            'ts': time.time(),
            'ttl': cache_ttl,
            'value': dict(analysis)
        }

    return analysis


def merge_reason_analysis(rule_analysis, ollama_analysis):
    """Merge deterministic rules with optional Ollama insights."""
    if not ollama_analysis:
        return rule_analysis

    merged = dict(rule_analysis)

    merged_tips = []
    for tip in (rule_analysis.get('tips', []) + ollama_analysis.get('tips', [])):
        if tip and tip not in merged_tips:
            merged_tips.append(tip)

    # Keep deterministic rules dominant while still learning from local LLM nuance.
    merged_score = int(round((rule_analysis.get('score', 0) * 0.75) + (ollama_analysis.get('score', 0) * 0.25)))

    merged_label = rule_analysis.get('label', 'good')
    ollama_label = ollama_analysis.get('label', 'good')
    if rule_analysis.get('label') == 'urgent' or ollama_label == 'urgent':
        merged_label = 'urgent'
    elif merged_score >= 80:
        merged_label = 'good'
    elif merged_score >= 60:
        merged_label = 'improve'
    else:
        merged_label = 'needs_detail'

    merged.update({
        'label': merged_label,
        'score': max(0, min(100, merged_score)),
        'is_urgent': (merged_label == 'urgent') or bool(rule_analysis.get('is_urgent')),
        'tips': merged_tips[:6],
        'summary': ollama_analysis.get('summary') or rule_analysis.get('summary'),
        'model_source': f"rule+{ollama_analysis.get('model_source', 'ollama')}"
    })

    return merged


def build_reason_analysis(reason, leave_type_name=None, start_date=None, end_date=None):
    """Build leave reason analysis with rule baseline and optional Ollama enhancement."""
    rule_analysis = analyze_leave_reason(reason)
    text = (reason or '').strip()
    min_chars = app.config.get('AI_OLLAMA_REASON_MIN_CHARS', 20)

    # Skip expensive model calls for tiny inputs while still giving rule-based hints.
    if len(text) < min_chars:
        return rule_analysis

    if app.config.get('AI_OLLAMA_THINKING_MODEL', False) and text.count(' ') < 3:
        return rule_analysis

    ollama_analysis = get_cached_ollama_reason_analysis(
        reason=reason,
        leave_type_name=leave_type_name,
        start_date=start_date,
        end_date=end_date
    )
    return merge_reason_analysis(rule_analysis, ollama_analysis)


def get_ollama_runtime_status():
    """Return current Ollama runtime and model availability information."""
    enabled = app.config.get('AI_OLLAMA_ENABLED', False)
    model_name = app.config.get('AI_OLLAMA_MODEL', 'qwen3.5:4b')
    base_url = app.config.get('AI_OLLAMA_BASE_URL', 'http://127.0.0.1:11434').rstrip('/')
    timeout = app.config.get('AI_OLLAMA_TIMEOUT_SECONDS', 20)

    status = {
        'enabled': enabled,
        'base_url': base_url,
        'model': model_name,
        'thinking_model': app.config.get('AI_OLLAMA_THINKING_MODEL', False),
        'reason_min_chars': app.config.get('AI_OLLAMA_REASON_MIN_CHARS', 20),
        'timeout_seconds': timeout,
        'reachable': False,
        'model_available': False,
        'installed_models': []
    }

    if not enabled:
        return status

    endpoint = f'{base_url}/api/tags'
    try:
        req = urllib.request.Request(endpoint, method='GET')
        with urllib.request.urlopen(req, timeout=timeout) as response:
            body = response.read().decode('utf-8')
            parsed = json.loads(body)
    except (urllib.error.URLError, TimeoutError, OSError, ValueError, json.JSONDecodeError):
        return status

    models = parsed.get('models', []) if isinstance(parsed, dict) else []
    model_names = []
    for item in models:
        name = item.get('name') if isinstance(item, dict) else None
        if name:
            model_names.append(name)

    status['reachable'] = True
    status['installed_models'] = model_names
    status['model_available'] = model_name in model_names
    return status


def evaluate_leave_precheck(user, leave_type_id, start_date, end_date, reason):
    """Run non-destructive policy/balance checks and produce guidance before submit."""
    current_year = date.today().year
    issues = []
    suggestions = []

    reason_analysis = analyze_leave_reason(reason)

    if end_date < start_date:
        issues.append({'level': 'error', 'message': 'End date cannot be before start date.'})
        return {
            'status': 'blocked',
            'summary': 'Please fix the selected dates before submitting.',
            'business_days': 0,
            'issues': issues,
            'suggestions': suggestions,
            'reason_analysis': reason_analysis
        }

    business_days = count_business_days(start_date, end_date)
    if business_days <= 0:
        issues.append({'level': 'error', 'message': 'Selected dates fall entirely on weekends.'})
        next_start = next_business_day(start_date)
        next_end = add_business_days(next_start, 1)
        suggestions.append(f'Try {next_start.isoformat()} to {next_end.isoformat()} instead.')

    leave_type = LeaveType.query.get(leave_type_id)
    if not leave_type or not leave_type.is_active:
        issues.append({'level': 'error', 'message': 'Select a valid leave type.'})

    reason_analysis = build_reason_analysis(
        reason=reason,
        leave_type_name=leave_type.name if leave_type else None,
        start_date=start_date,
        end_date=end_date
    )

    balance = LeaveBalance.query.filter_by(
        user_id=user.id,
        leave_type_id=leave_type_id,
        year=current_year
    ).first()

    remaining_days = balance.remaining_days if balance else 0
    if business_days > 0 and remaining_days < business_days:
        issues.append({
            'level': 'error',
            'message': f'Insufficient leave balance. You have {remaining_days} day(s) remaining.'
        })

    overlap = LeaveRequest.query.filter(
        LeaveRequest.user_id == user.id,
        LeaveRequest.status.in_(['pending', 'approved']),
        LeaveRequest.start_date <= end_date,
        LeaveRequest.end_date >= start_date
    ).first()
    if overlap:
        issues.append({'level': 'error', 'message': 'You already have a leave request overlapping with these dates.'})
        suggested_start = next_business_day(overlap.end_date + timedelta(days=1))
        if business_days > 0:
            suggested_end = add_business_days(suggested_start, business_days)
            suggestions.append(f'Next non-overlapping option: {suggested_start.isoformat()} to {suggested_end.isoformat()}.')

    policy = LeavePolicy.query.filter_by(is_active=True).first()
    if policy:
        if business_days > policy.max_consecutive_days:
            issues.append({
                'level': 'error',
                'message': f'Exceeds maximum consecutive days ({policy.max_consecutive_days}).'
            })
            suggestions.append(f'Split into smaller requests of up to {policy.max_consecutive_days} business day(s).')

        days_notice = (start_date - date.today()).days
        if days_notice < policy.min_days_notice:
            issues.append({
                'level': 'error',
                'message': f'Minimum {policy.min_days_notice} day(s) notice required.'
            })
            earliest_start = next_business_day(date.today() + timedelta(days=policy.min_days_notice))
            if business_days > 0:
                earliest_end = add_business_days(earliest_start, business_days)
                suggestions.append(f'Earliest compliant dates: {earliest_start.isoformat()} to {earliest_end.isoformat()}.')

    if reason_analysis['label'] == 'needs_detail':
        issues.append({'level': 'warning', 'message': 'Reason is very short and may delay review.'})
    elif reason_analysis['label'] == 'improve':
        issues.append({'level': 'warning', 'message': 'A bit more detail could improve approval speed.'})
    elif reason_analysis['label'] == 'urgent':
        issues.append({'level': 'info', 'message': 'Urgent pattern detected. Notify your manager directly.'})

    has_error = any(item['level'] == 'error' for item in issues)
    has_warning = any(item['level'] == 'warning' for item in issues)
    status = 'blocked' if has_error else ('warning' if has_warning else 'ready')

    if status == 'ready':
        summary = 'Looks good. Your request appears policy-compliant and ready to submit.'
    elif status == 'warning':
        summary = 'Your request is likely valid, but improvements are recommended before submit.'
    else:
        summary = 'Your request is likely to be rejected unless the issues below are fixed.'

    return {
        'status': status,
        'summary': summary,
        'business_days': business_days,
        'remaining_days': remaining_days,
        'issues': issues,
        'suggestions': suggestions,
        'reason_analysis': reason_analysis
    }


def extract_first_json_object(text):
    """Extract and parse first JSON object from model output text."""
    if not text:
        return None

    candidate = text.strip()
    try:
        parsed = json.loads(candidate)
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        pass

    first = candidate.find('{')
    last = candidate.rfind('}')
    if first == -1 or last == -1 or last <= first:
        return None

    snippet = candidate[first:last + 1]
    try:
        parsed = json.loads(snippet)
        return parsed if isinstance(parsed, dict) else None
    except json.JSONDecodeError:
        return None


def get_cached_ollama_leave_prediction(feature_payload):
    """Get AI leave prediction with TTL cache to reduce repetitive inference calls."""
    cache_ttl = app.config.get('AI_OLLAMA_LEAVE_PREDICTION_CACHE_TTL_SECONDS', 300)
    key_raw = json.dumps(feature_payload, sort_keys=True)
    cache_key = hashlib.sha256(key_raw.encode('utf-8')).hexdigest()

    now_ts = time.time()
    with OLLAMA_LEAVE_PRED_CACHE_LOCK:
        expired_keys = [
            key for key, item in OLLAMA_LEAVE_PRED_CACHE.items()
            if (now_ts - item.get('ts', 0)) > cache_ttl
        ]
        for key in expired_keys:
            OLLAMA_LEAVE_PRED_CACHE.pop(key, None)

        cached = OLLAMA_LEAVE_PRED_CACHE.get(cache_key)
        if cached and (now_ts - cached.get('ts', 0)) <= cache_ttl:
            return dict(cached.get('value', {}))

    ai_result = get_ollama_leave_prediction(feature_payload)
    if not ai_result:
        return None

    with OLLAMA_LEAVE_PRED_CACHE_LOCK:
        OLLAMA_LEAVE_PRED_CACHE[cache_key] = {
            'ts': time.time(),
            'value': dict(ai_result)
        }

    return ai_result


def get_ollama_leave_prediction(feature_payload):
    """Use Ollama to predict near-term leave demand from historical leave features."""
    if not app.config.get('AI_OLLAMA_ENABLED', False):
        return None
    if not app.config.get('AI_LEAVE_PREDICTION_ENABLED', True):
        return None

    prompt = (
        'You are an HR leave-forecast assistant. '\
        'Given leave history features, predict leave demand. '\
        'Return STRICT JSON ONLY with keys: '\
        'predicted_next_30_days, predicted_next_90_days, risk_level, pattern_summary. '\
        'risk_level must be one of low, medium, high. '\
        'predicted values must be numbers >= 0. '\
        'Use conservative estimates when history is sparse. '\
        f'Features: {json.dumps(feature_payload, sort_keys=True)}'
    )

    payload = {
        'model': app.config.get('AI_OLLAMA_MODEL', 'qwen3.5:4b'),
        'prompt': prompt,
        'stream': False,
        'format': 'json',
        'options': {
            'temperature': 0.15
        }
    }

    endpoint = f"{app.config.get('AI_OLLAMA_BASE_URL', 'http://127.0.0.1:11434').rstrip('/')}/api/generate"
    timeout = app.config.get('AI_OLLAMA_LEAVE_PREDICTION_TIMEOUT_SECONDS', 25)

    try:
        req = urllib.request.Request(
            endpoint,
            data=json.dumps(payload).encode('utf-8'),
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
        with urllib.request.urlopen(req, timeout=timeout) as response:
            body = response.read().decode('utf-8')
    except (urllib.error.URLError, TimeoutError, OSError, ValueError):
        return None

    try:
        envelope = json.loads(body)
    except (json.JSONDecodeError, TypeError):
        return None

    source_suffix = ':response'
    model_text = (envelope.get('response') or '').strip()
    if not model_text:
        model_text = (envelope.get('thinking') or '').strip()
        source_suffix = ':thinking'

    parsed = extract_first_json_object(model_text)
    if not parsed:
        return None

    try:
        next_30 = max(0.0, float(parsed.get('predicted_next_30_days', 0)))
    except (TypeError, ValueError):
        next_30 = 0.0

    try:
        next_90 = max(0.0, float(parsed.get('predicted_next_90_days', next_30 * 3)))
    except (TypeError, ValueError):
        next_90 = next_30 * 3

    risk_value = str(parsed.get('risk_level', '')).strip().lower()
    if risk_value not in {'low', 'medium', 'high'}:
        if next_30 >= 6:
            risk_value = 'high'
        elif next_30 >= 3:
            risk_value = 'medium'
        else:
            risk_value = 'low'

    summary = str(parsed.get('pattern_summary', '')).strip()
    if not summary:
        summary = 'AI generated leave prediction based on historical leave usage patterns.'

    return {
        'predicted_next_30_days': round(next_30, 1),
        'predicted_next_90_days': round(next_90, 1),
        'risk_level': risk_value,
        'pattern_summary': summary,
        'prediction_source': f"ai:{app.config.get('AI_OLLAMA_MODEL', 'qwen3.5:4b')}{source_suffix}"
    }


def build_leave_pattern_prediction(user):
    """Build leave usage patterns and AI-backed short-term prediction per user."""
    approved_requests = LeaveRequest.query.filter_by(
        user_id=user.id,
        status='approved'
    ).order_by(LeaveRequest.start_date.asc()).all()

    total_days = 0.0
    notice_days = []
    month_counter = Counter()
    type_counter = Counter()

    for req in approved_requests:
        days = float(req.total_days or 0)
        total_days += days
        month_counter[req.start_date.month] += 1
        type_name = req.leave_type.name if req.leave_type else 'Unknown'
        type_counter[type_name] += 1

        if req.created_at:
            notice = (req.start_date - req.created_at.date()).days
            if notice >= 0:
                notice_days.append(notice)

    approved_count = len(approved_requests)
    avg_days_per_request = round(total_days / approved_count, 1) if approved_count else 0
    avg_notice = round(sum(notice_days) / len(notice_days), 1) if notice_days else 0

    peak_month_idx = month_counter.most_common(1)[0][0] if month_counter else None
    peak_month = datetime(2000, peak_month_idx, 1).strftime('%B') if peak_month_idx else 'N/A'
    top_leave_type = type_counter.most_common(1)[0][0] if type_counter else 'N/A'

    first_day = approved_requests[0].start_date if approved_requests else date.today() - timedelta(days=365)
    observed_days = max(1, (date.today() - first_day).days + 1)
    baseline_monthly = (total_days / observed_days) * 30

    recent_cutoff = date.today() - timedelta(days=90)
    recent_days = sum(float(req.total_days or 0) for req in approved_requests if req.start_date >= recent_cutoff)
    recent_monthly = recent_days / 3.0

    blended_next_30 = round((baseline_monthly * 0.6) + (recent_monthly * 0.4), 1)
    predicted_next_30 = max(0, blended_next_30)
    predicted_next_90 = round(predicted_next_30 * 3, 1)

    if predicted_next_30 >= 6:
        risk_level = 'high'
    elif predicted_next_30 >= 3:
        risk_level = 'medium'
    else:
        risk_level = 'low'

    baseline_summary = (
        f"Frequent leave type: {top_leave_type}. "
        f"Peak month: {peak_month}. "
        f"Expected leave in next 30 days: {predicted_next_30} day(s)."
    )

    feature_payload = {
        'user_role': user.role,
        'department': user.department or '-',
        'approved_requests': approved_count,
        'total_approved_days': round(total_days, 1),
        'avg_days_per_request': avg_days_per_request,
        'avg_notice_days': avg_notice,
        'top_leave_type': top_leave_type,
        'peak_month': peak_month,
        'recent_90d_approved_days': round(recent_days, 1),
        'baseline_next_30_days': round(predicted_next_30, 1),
        'baseline_next_90_days': round(predicted_next_90, 1)
    }

    prediction_source = 'rule-fallback'
    pattern_summary = baseline_summary

    ai_prediction = get_cached_ollama_leave_prediction(feature_payload)
    if ai_prediction:
        predicted_next_30 = ai_prediction['predicted_next_30_days']
        predicted_next_90 = ai_prediction['predicted_next_90_days']
        risk_level = ai_prediction['risk_level']
        pattern_summary = ai_prediction['pattern_summary']
        prediction_source = ai_prediction['prediction_source']
    elif approved_count == 0:
        pattern_summary = 'Not enough approved leave history yet; showing conservative baseline prediction.'

    return {
        'user_id': user.id,
        'full_name': user.full_name,
        'role': user.role,
        'department': user.department or '-',
        'manager_name': user.manager.full_name if user.manager else '-',
        'approved_requests': approved_count,
        'avg_days_per_request': avg_days_per_request,
        'avg_notice_days': avg_notice,
        'top_leave_type': top_leave_type,
        'peak_month': peak_month,
        'predicted_next_30_days': predicted_next_30,
        'predicted_next_90_days': predicted_next_90,
        'risk_level': risk_level,
        'pattern_summary': pattern_summary,
        'prediction_source': prediction_source
    }


# ─── Context Processor ────────────────────────────────────────────────────────

@app.context_processor
def inject_now():
    return {
        'now': datetime.utcnow(),
        'ai_smart_apply_helper_enabled': app.config.get('AI_SMART_APPLY_HELPER_ENABLED', False),
        'ai_policy_precheck_enabled': app.config.get('AI_POLICY_PRECHECK_ENABLED', False),
        'ai_ollama_enabled': app.config.get('AI_OLLAMA_ENABLED', False),
        'ai_ollama_model': app.config.get('AI_OLLAMA_MODEL', '')
    }


@app.route('/ai/ollama/status', methods=['GET'])
@login_required
def ollama_status():
    if current_user.role != 'admin':
        return jsonify({'message': 'Runtime status is available to admin only.'}), 403

    status = get_ollama_runtime_status()
    http_status = 200 if (not status['enabled'] or status['reachable']) else 503
    return jsonify(status), http_status


@app.route('/ai/assistant', methods=['GET'])
@login_required
def ai_assistant():
    leave_types = LeaveType.query.filter_by(is_active=True).order_by(LeaveType.name).all()
    return render_template(
        'ai/assistant.html',
        leave_types=leave_types,
        ollama_status=get_ollama_runtime_status()
    )


@app.route('/ai/reason-preview', methods=['POST'])
@login_required
def ai_reason_preview():
    payload = request.get_json(silent=True) or {}
    reason = (payload.get('reason') or '').strip()
    leave_type_id_raw = payload.get('leave_type_id')
    start_date_raw = payload.get('start_date')
    end_date_raw = payload.get('end_date')

    leave_type_name = None
    if leave_type_id_raw:
        try:
            leave_type_id = int(leave_type_id_raw)
            leave_type = LeaveType.query.get(leave_type_id)
            if leave_type:
                leave_type_name = leave_type.name
        except (ValueError, TypeError):
            leave_type_name = None

    start_date = None
    end_date = None
    try:
        if start_date_raw:
            start_date = datetime.strptime(start_date_raw, '%Y-%m-%d').date()
        if end_date_raw:
            end_date = datetime.strptime(end_date_raw, '%Y-%m-%d').date()
    except (TypeError, ValueError):
        return jsonify({
            'status': 'error',
            'message': 'Dates must use YYYY-MM-DD format.',
            'reason_analysis': analyze_leave_reason(reason)
        }), 400

    analysis = build_reason_analysis(
        reason=reason,
        leave_type_name=leave_type_name,
        start_date=start_date,
        end_date=end_date
    )

    return jsonify({
        'status': 'ok',
        'message': 'Preview generated successfully.',
        'reason_analysis': analysis,
        'ollama_status': get_ollama_runtime_status()
    })


@app.route('/ai/leave-predictions', methods=['GET'])
@login_required
@role_required('manager', 'admin')
def ai_leave_predictions():
    if current_user.role == 'manager':
        users = User.query.filter_by(
            role='employee',
            is_active=True,
            manager_id=current_user.id
        ).order_by(User.first_name, User.last_name).all()
        scope_label = 'Team view: showing employee leave patterns and predictions.'
    else:
        users = User.query.filter(
            User.role.in_(['manager', 'employee']),
            User.is_active.is_(True)
        ).order_by(User.role, User.first_name, User.last_name).all()
        scope_label = 'Admin view: showing manager and employee leave patterns and predictions.'

    predictions = [build_leave_pattern_prediction(user) for user in users]
    predictions.sort(key=lambda item: item['predicted_next_30_days'], reverse=True)

    return render_template(
        'ai/leave_predictions.html',
        predictions=predictions,
        scope_label=scope_label,
        is_admin=(current_user.role == 'admin')
    )


# ─── Auth Routes ──────────────────────────────────────────────────────────────

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password) and user.is_active:
            login_user(user)
            log_action(user.id, 'Login', f'{user.full_name} logged in')
            flash(f'Welcome back, {user.first_name}!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard'))
        else:
            flash('Invalid username or password.', 'danger')

    return render_template('auth/login.html')


@app.route('/logout')
@login_required
def logout():
    log_action(current_user.id, 'Logout', f'{current_user.full_name} logged out')
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))


# ─── Dashboard ────────────────────────────────────────────────────────────────

@app.route('/dashboard')
@login_required
def dashboard():
    role = current_user.role
    current_year = date.today().year

    if role == 'admin':
        total_employees = User.query.filter_by(role='employee', is_active=True).count()
        total_managers = User.query.filter_by(role='manager', is_active=True).count()
        pending_requests = LeaveRequest.query.filter_by(status='pending').count()
        approved_today = LeaveRequest.query.filter(
            LeaveRequest.status == 'approved',
            LeaveRequest.start_date <= date.today(),
            LeaveRequest.end_date >= date.today()
        ).count()
        recent_requests = LeaveRequest.query.order_by(LeaveRequest.created_at.desc()).limit(10).all()
        return render_template('dashboard.html',
                               total_employees=total_employees,
                               total_managers=total_managers,
                               pending_requests=pending_requests,
                               approved_today=approved_today,
                               recent_requests=recent_requests)

    elif role == 'manager':
        team_ids = [m.id for m in current_user.team_members]
        pending_requests = LeaveRequest.query.filter(
            LeaveRequest.user_id.in_(team_ids),
            LeaveRequest.status == 'pending'
        ).order_by(LeaveRequest.created_at.desc()).all()
        team_on_leave = LeaveRequest.query.filter(
            LeaveRequest.user_id.in_(team_ids),
            LeaveRequest.status == 'approved',
            LeaveRequest.start_date <= date.today(),
            LeaveRequest.end_date >= date.today()
        ).all()
        return render_template('dashboard.html',
                               pending_requests=pending_requests,
                               team_on_leave=team_on_leave,
                               team_count=len(team_ids))

    else:  # employee
        balances = LeaveBalance.query.filter_by(user_id=current_user.id, year=current_year).all()
        recent = LeaveRequest.query.filter_by(user_id=current_user.id)\
            .order_by(LeaveRequest.created_at.desc()).limit(5).all()
        return render_template('dashboard.html', balances=balances, recent_requests=recent)


# ─── Employee: Apply for Leave ────────────────────────────────────────────────

@app.route('/leave/apply', methods=['GET', 'POST'])
@login_required
@role_required('employee')
def apply_leave():
    leave_types = LeaveType.query.filter_by(is_active=True).all()
    current_year = date.today().year

    if request.method == 'POST':
        leave_type_id = int(request.form.get('leave_type_id'))
        start_date = datetime.strptime(request.form.get('start_date'), '%Y-%m-%d').date()
        end_date = datetime.strptime(request.form.get('end_date'), '%Y-%m-%d').date()
        reason = request.form.get('reason', '').strip()

        # Validation
        if end_date < start_date:
            flash('End date cannot be before start date.', 'danger')
            return render_template('leave/apply.html', leave_types=leave_types)

        total_days = count_business_days(start_date, end_date)

        if total_days <= 0:
            flash('Selected dates fall entirely on weekends.', 'danger')
            return render_template('leave/apply.html', leave_types=leave_types)

        # Check balance
        balance = LeaveBalance.query.filter_by(
            user_id=current_user.id, leave_type_id=leave_type_id, year=current_year
        ).first()

        if not balance or balance.remaining_days < total_days:
            flash(f'Insufficient leave balance. You have {balance.remaining_days if balance else 0} days remaining.', 'danger')
            return render_template('leave/apply.html', leave_types=leave_types)

        # Check overlapping requests
        overlap = LeaveRequest.query.filter(
            LeaveRequest.user_id == current_user.id,
            LeaveRequest.status.in_(['pending', 'approved']),
            LeaveRequest.start_date <= end_date,
            LeaveRequest.end_date >= start_date
        ).first()

        if overlap:
            flash('You already have a leave request overlapping with these dates.', 'danger')
            return render_template('leave/apply.html', leave_types=leave_types)

        # Check policy constraints
        policy = LeavePolicy.query.filter_by(is_active=True).first()
        if policy:
            if total_days > policy.max_consecutive_days:
                flash(f'Exceeds maximum consecutive days ({policy.max_consecutive_days}).', 'danger')
                return render_template('leave/apply.html', leave_types=leave_types)
            days_notice = (start_date - date.today()).days
            if days_notice < policy.min_days_notice:
                flash(f'Minimum {policy.min_days_notice} day(s) notice required.', 'danger')
                return render_template('leave/apply.html', leave_types=leave_types)

        if app.config.get('AI_SMART_APPLY_HELPER_ENABLED', False):
            reason_analysis = build_reason_analysis(
                reason=reason,
                start_date=start_date,
                end_date=end_date
            )
            if reason_analysis['label'] == 'needs_detail':
                flash('Smart Apply Helper: adding a little more detail can speed up manager review.', 'warning')
            elif reason_analysis['label'] == 'urgent':
                flash('Smart Apply Helper: this appears urgent. Notify your manager directly as well.', 'info')

        # Create request
        leave_request = LeaveRequest(
            user_id=current_user.id,
            leave_type_id=leave_type_id,
            start_date=start_date,
            end_date=end_date,
            total_days=total_days,
            reason=reason,
            status='pending'
        )
        db.session.add(leave_request)
        db.session.commit()

        log_action(current_user.id, 'Leave Applied',
                   f'Applied for {total_days} days from {start_date} to {end_date}')
        flash('Leave request submitted successfully! Waiting for manager approval.', 'success')
        return redirect(url_for('leave_history'))

    return render_template('leave/apply.html', leave_types=leave_types)


@app.route('/leave/precheck', methods=['POST'])
@login_required
@role_required('employee')
def leave_precheck():
    if not app.config.get('AI_POLICY_PRECHECK_ENABLED', False):
        return jsonify({'message': 'Pre-check is disabled.'}), 403

    payload = request.get_json(silent=True) or {}
    leave_type_id_raw = payload.get('leave_type_id')
    start_date_raw = payload.get('start_date')
    end_date_raw = payload.get('end_date')
    reason = payload.get('reason', '').strip()

    if not leave_type_id_raw or not start_date_raw or not end_date_raw:
        return jsonify({
            'status': 'warning',
            'summary': 'Select leave type, start date, and end date to run policy pre-check.',
            'business_days': 0,
            'issues': [{'level': 'info', 'message': 'Waiting for complete leave details.'}],
            'suggestions': [],
            'reason_analysis': build_reason_analysis(reason=reason)
        })

    try:
        leave_type_id = int(leave_type_id_raw)
        start_date = datetime.strptime(start_date_raw, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_raw, '%Y-%m-%d').date()
    except (TypeError, ValueError):
        return jsonify({
            'status': 'blocked',
            'summary': 'Invalid input format detected.',
            'business_days': 0,
            'issues': [{'level': 'error', 'message': 'Use a valid leave type and dates (YYYY-MM-DD).'}],
            'suggestions': [],
            'reason_analysis': build_reason_analysis(reason=reason)
        }), 400

    result = evaluate_leave_precheck(
        user=current_user,
        leave_type_id=leave_type_id,
        start_date=start_date,
        end_date=end_date,
        reason=reason
    )

    if app.config.get('AI_PRECHECK_AUDIT_LOG_ENABLED', True):
        log_action(
            current_user.id,
            'Leave Precheck',
            f"status={result['status']}, business_days={result['business_days']}"
        )

    return jsonify(result)


# ─── Employee: Leave History ──────────────────────────────────────────────────

@app.route('/leave/history')
@login_required
@role_required('employee')
def leave_history():
    requests = LeaveRequest.query.filter_by(user_id=current_user.id)\
        .order_by(LeaveRequest.created_at.desc()).all()
    current_year = date.today().year
    balances = LeaveBalance.query.filter_by(user_id=current_user.id, year=current_year).all()
    return render_template('leave/history.html', requests=requests, balances=balances)


# ─── Manager: View Leave Requests ────────────────────────────────────────────

@app.route('/leave/requests')
@login_required
@role_required('manager')
def leave_requests():
    team_ids = [m.id for m in current_user.team_members]
    status_filter = request.args.get('status', 'pending')

    query = LeaveRequest.query.filter(LeaveRequest.user_id.in_(team_ids))
    if status_filter != 'all':
        query = query.filter_by(status=status_filter)

    requests = query.order_by(LeaveRequest.created_at.desc()).all()
    return render_template('leave/requests.html', requests=requests, status_filter=status_filter)


# ─── Manager: Approve Leave ──────────────────────────────────────────────────

@app.route('/leave/approve/<int:request_id>', methods=['POST'])
@login_required
@role_required('manager')
def approve_leave(request_id):
    leave_req = LeaveRequest.query.get_or_404(request_id)
    comment = request.form.get('comment', '').strip()

    # Verify this request belongs to manager's team
    team_ids = [m.id for m in current_user.team_members]
    if leave_req.user_id not in team_ids:
        flash('You can only approve requests from your team.', 'danger')
        return redirect(url_for('leave_requests'))

    if leave_req.status != 'pending':
        flash('This request has already been processed.', 'warning')
        return redirect(url_for('leave_requests'))

    # Approve and deduct balance
    leave_req.status = 'approved'
    leave_req.reviewed_by = current_user.id
    leave_req.review_comment = comment
    leave_req.updated_at = datetime.utcnow()

    current_year = leave_req.start_date.year
    balance = LeaveBalance.query.filter_by(
        user_id=leave_req.user_id,
        leave_type_id=leave_req.leave_type_id,
        year=current_year
    ).first()

    if balance:
        balance.used_days += leave_req.total_days

    db.session.commit()

    log_action(current_user.id, 'Leave Approved',
               f'Approved leave request #{leave_req.id} for {leave_req.applicant.full_name}')
    flash(f'Leave request approved for {leave_req.applicant.full_name}.', 'success')
    return redirect(url_for('leave_requests'))


# ─── Manager: Reject Leave ───────────────────────────────────────────────────

@app.route('/leave/reject/<int:request_id>', methods=['POST'])
@login_required
@role_required('manager')
def reject_leave(request_id):
    leave_req = LeaveRequest.query.get_or_404(request_id)
    comment = request.form.get('comment', '').strip()

    team_ids = [m.id for m in current_user.team_members]
    if leave_req.user_id not in team_ids:
        flash('You can only reject requests from your team.', 'danger')
        return redirect(url_for('leave_requests'))

    if leave_req.status != 'pending':
        flash('This request has already been processed.', 'warning')
        return redirect(url_for('leave_requests'))

    leave_req.status = 'rejected'
    leave_req.reviewed_by = current_user.id
    leave_req.review_comment = comment
    leave_req.updated_at = datetime.utcnow()
    db.session.commit()

    log_action(current_user.id, 'Leave Rejected',
               f'Rejected leave request #{leave_req.id} for {leave_req.applicant.full_name}')
    flash(f'Leave request rejected for {leave_req.applicant.full_name}.', 'warning')
    return redirect(url_for('leave_requests'))


# ─── Admin: Manage Employees ─────────────────────────────────────────────────

@app.route('/admin/employees')
@login_required
@role_required('admin')
def admin_employees():
    employees = User.query.filter_by(role='employee').order_by(User.first_name).all()
    return render_template('admin/employees.html', employees=employees)


@app.route('/admin/managers')
@login_required
@role_required('admin')
def admin_managers():
    managers = User.query.filter_by(role='manager').order_by(User.first_name).all()
    return render_template('admin/managers.html', managers=managers)


@app.route('/admin/add-user', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def admin_add_user():
    managers = User.query.filter_by(role='manager', is_active=True).all()

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        role = request.form.get('role', 'employee')
        department = request.form.get('department', '').strip()
        manager_id = request.form.get('manager_id')

        # Validation
        if User.query.filter_by(username=username).first():
            flash('Username already exists.', 'danger')
            return render_template('admin/add_user.html', managers=managers)
        if User.query.filter_by(email=email).first():
            flash('Email already exists.', 'danger')
            return render_template('admin/add_user.html', managers=managers)

        user = User(
            username=username, email=email,
            first_name=first_name, last_name=last_name,
            role=role, department=department,
            manager_id=int(manager_id) if manager_id else None
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        # Create leave balances for the new user
        current_year = date.today().year
        leave_types = LeaveType.query.filter_by(is_active=True).all()
        for lt in leave_types:
            balance = LeaveBalance(
                user_id=user.id, leave_type_id=lt.id,
                year=current_year, total_days=lt.days_per_year, used_days=0
            )
            db.session.add(balance)
        db.session.commit()

        log_action(current_user.id, 'User Created',
                   f'Created {role} account for {first_name} {last_name}')
        flash(f'{role.capitalize()} "{first_name} {last_name}" added successfully!', 'success')
        return redirect(url_for('admin_employees') if role == 'employee' else url_for('admin_managers'))

    return render_template('admin/add_user.html', managers=managers)


@app.route('/admin/delete-user/<int:user_id>', methods=['POST'])
@login_required
@role_required('admin')
def admin_delete_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('You cannot delete yourself.', 'danger')
        return redirect(url_for('admin_employees'))

    name = user.full_name
    role = user.role

    # Delete related records
    LeaveBalance.query.filter_by(user_id=user.id).delete()
    LeaveRequest.query.filter_by(user_id=user.id).delete()
    AuditLog.query.filter_by(user_id=user.id).delete()

    # Unassign team members if deleting a manager
    if user.role == 'manager':
        for member in user.team_members:
            member.manager_id = None

    db.session.delete(user)
    db.session.commit()

    log_action(current_user.id, 'User Deleted', f'Deleted {role} "{name}"')
    flash(f'{role.capitalize()} "{name}" has been deleted.', 'success')
    return redirect(url_for('admin_employees') if role == 'employee' else url_for('admin_managers'))


@app.route('/admin/toggle-user/<int:user_id>', methods=['POST'])
@login_required
@role_required('admin')
def admin_toggle_user(user_id):
    user = User.query.get_or_404(user_id)
    user.is_active = not user.is_active
    db.session.commit()
    status = 'activated' if user.is_active else 'deactivated'
    log_action(current_user.id, f'User {status.capitalize()}', f'{status.capitalize()} {user.full_name}')
    flash(f'{user.full_name} has been {status}.', 'success')
    return redirect(request.referrer or url_for('admin_employees'))


# ─── Admin: Leave Types ──────────────────────────────────────────────────────

@app.route('/admin/leave-types', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def admin_leave_types():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        days_per_year = int(request.form.get('days_per_year', 0))
        description = request.form.get('description', '').strip()

        if LeaveType.query.filter_by(name=name).first():
            flash('Leave type already exists.', 'danger')
        else:
            lt = LeaveType(name=name, days_per_year=days_per_year, description=description)
            db.session.add(lt)
            db.session.commit()

            # Create balances for all employees/managers
            current_year = date.today().year
            users = User.query.filter(User.role.in_(['employee', 'manager'])).all()
            for u in users:
                bal = LeaveBalance(user_id=u.id, leave_type_id=lt.id,
                                   year=current_year, total_days=days_per_year, used_days=0)
                db.session.add(bal)
            db.session.commit()

            log_action(current_user.id, 'Leave Type Created', f'Created leave type "{name}"')
            flash(f'Leave type "{name}" created successfully!', 'success')

    leave_types = LeaveType.query.order_by(LeaveType.name).all()
    return render_template('admin/leave_types.html', leave_types=leave_types)


@app.route('/admin/delete-leave-type/<int:lt_id>', methods=['POST'])
@login_required
@role_required('admin')
def admin_delete_leave_type(lt_id):
    lt = LeaveType.query.get_or_404(lt_id)
    name = lt.name
    LeaveBalance.query.filter_by(leave_type_id=lt.id).delete()
    LeaveRequest.query.filter_by(leave_type_id=lt.id).delete()
    db.session.delete(lt)
    db.session.commit()
    log_action(current_user.id, 'Leave Type Deleted', f'Deleted leave type "{name}"')
    flash(f'Leave type "{name}" deleted.', 'success')
    return redirect(url_for('admin_leave_types'))


# ─── Admin: Leave Policies ───────────────────────────────────────────────────

@app.route('/admin/leave-policies', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def admin_leave_policies():
    if request.method == 'POST':
        policy_id = request.form.get('policy_id')
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        max_consecutive = int(request.form.get('max_consecutive_days', 30))
        min_notice = int(request.form.get('min_days_notice', 1))
        carry_forward = request.form.get('carry_forward_allowed') == 'on'
        carry_max = int(request.form.get('carry_forward_max_days', 0))

        if policy_id:
            policy = LeavePolicy.query.get(int(policy_id))
            if policy:
                policy.name = name
                policy.description = description
                policy.max_consecutive_days = max_consecutive
                policy.min_days_notice = min_notice
                policy.carry_forward_allowed = carry_forward
                policy.carry_forward_max_days = carry_max
                policy.updated_at = datetime.utcnow()
                flash(f'Policy "{name}" updated.', 'success')
        else:
            policy = LeavePolicy(
                name=name, description=description,
                max_consecutive_days=max_consecutive, min_days_notice=min_notice,
                carry_forward_allowed=carry_forward, carry_forward_max_days=carry_max
            )
            db.session.add(policy)
            flash(f'Policy "{name}" created.', 'success')

        db.session.commit()
        log_action(current_user.id, 'Leave Policy Updated', f'Updated/created policy "{name}"')

    policies = LeavePolicy.query.order_by(LeavePolicy.name).all()
    return render_template('admin/leave_policies.html', policies=policies)


@app.route('/admin/delete-policy/<int:policy_id>', methods=['POST'])
@login_required
@role_required('admin')
def admin_delete_policy(policy_id):
    policy = LeavePolicy.query.get_or_404(policy_id)
    name = policy.name
    db.session.delete(policy)
    db.session.commit()
    log_action(current_user.id, 'Leave Policy Deleted', f'Deleted policy "{name}"')
    flash(f'Policy "{name}" deleted.', 'success')
    return redirect(url_for('admin_leave_policies'))


# ─── Admin: View All Details ─────────────────────────────────────────────────

@app.route('/admin/details')
@login_required
@role_required('admin')
def admin_details():
    employees = User.query.filter_by(role='employee').order_by(User.first_name).all()
    managers = User.query.filter_by(role='manager').order_by(User.first_name).all()
    current_year = date.today().year
    return render_template('admin/details.html',
                           employees=employees, managers=managers, current_year=current_year)


# ─── Admin: Reports ──────────────────────────────────────────────────────────

@app.route('/admin/reports')
@login_required
@role_required('admin')
def admin_reports():
    current_year = date.today().year

    # Summary stats
    total_requests = LeaveRequest.query.filter(
        db.extract('year', LeaveRequest.created_at) == current_year
    ).count()
    approved_count = LeaveRequest.query.filter(
        db.extract('year', LeaveRequest.created_at) == current_year,
        LeaveRequest.status == 'approved'
    ).count()
    rejected_count = LeaveRequest.query.filter(
        db.extract('year', LeaveRequest.created_at) == current_year,
        LeaveRequest.status == 'rejected'
    ).count()
    pending_count = LeaveRequest.query.filter_by(status='pending').count()

    # Leave type breakdown
    leave_types = LeaveType.query.filter_by(is_active=True).all()
    type_stats = []
    for lt in leave_types:
        count = LeaveRequest.query.filter(
            LeaveRequest.leave_type_id == lt.id,
            db.extract('year', LeaveRequest.created_at) == current_year
        ).count()
        type_stats.append({'name': lt.name, 'count': count})

    # Department breakdown
    departments = db.session.query(User.department).filter(User.department.isnot(None)).distinct().all()
    dept_stats = []
    for (dept,) in departments:
        if dept:
            users_in_dept = User.query.filter_by(department=dept).all()
            user_ids = [u.id for u in users_in_dept]
            dept_count = LeaveRequest.query.filter(
                LeaveRequest.user_id.in_(user_ids),
                db.extract('year', LeaveRequest.created_at) == current_year
            ).count()
            dept_stats.append({'name': dept, 'count': dept_count})

    # Recent audit logs
    audit_logs = AuditLog.query.order_by(AuditLog.created_at.desc()).limit(20).all()

    return render_template('admin/reports.html',
                           total_requests=total_requests,
                           approved_count=approved_count,
                           rejected_count=rejected_count,
                           pending_count=pending_count,
                           type_stats=type_stats,
                           dept_stats=dept_stats,
                           audit_logs=audit_logs,
                           current_year=current_year)


# ─── Admin: Status of Leave  ─────────────────────────────────────────────────

@app.route('/admin/leave-status')
@login_required
@role_required('admin')
def admin_leave_status():
    status_filter = request.args.get('status', 'all')
    query = LeaveRequest.query
    if status_filter != 'all':
        query = query.filter_by(status=status_filter)
    requests = query.order_by(LeaveRequest.created_at.desc()).all()
    return render_template('admin/leave_status.html', requests=requests, status_filter=status_filter)


# ─── Profile ─────────────────────────────────────────────────────────────────

@app.route('/profile')
@login_required
def profile():
    current_year = date.today().year
    balances = LeaveBalance.query.filter_by(user_id=current_user.id, year=current_year).all()
    return render_template('profile.html', balances=balances)


# ─── Initialize Database ─────────────────────────────────────────────────────

with app.app_context():
    db.create_all()


# ─── Run ──────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    app.run(debug=True, port=5000)
