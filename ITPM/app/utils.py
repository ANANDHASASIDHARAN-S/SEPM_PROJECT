from flask import request
from app.models import db, AuditLog
from functools import wraps
from flask_login import current_user
import json
from datetime import datetime

def log_audit(action, entity_type, entity_id=None, changes=None):
    """Log audit trail for user actions"""
    try:
        audit_log = AuditLog(
            user_id=current_user.id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            changes=json.dumps(changes) if changes else None,
            ip_address=request.remote_addr
        )
        db.session.add(audit_log)
        db.session.commit()
    except Exception as e:
        print(f"Error logging audit: {str(e)}")

def require_role(*roles):
    """Decorator to require specific roles"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            from flask_login import current_user
            from flask import redirect, url_for, flash
            
            if not current_user.is_authenticated:
                flash('Please log in first.', 'danger')
                return redirect(url_for('auth.login'))
            
            from app.models import Role
            role_values = [r.value if isinstance(r, Role) else r for r in roles]
            
            if current_user.role.value not in role_values and current_user.role != Role.ADMIN:
                flash('You do not have permission to access this page.', 'danger')
                return redirect(url_for('main.dashboard'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def get_client_ip():
    """Get client IP address"""
    if request.environ.get('HTTP_CF_CONNECTING_IP'):
        return request.environ['HTTP_CF_CONNECTING_IP']
    return request.environ.get('REMOTE_ADDR')

def calculate_skill_match(employee_skills, required_skills):
    """Calculate skill match percentage"""
    if not required_skills:
        return 100
    
    employee_skill_ids = {skill.id for skill in employee_skills}
    required_skill_ids = {skill.id for skill in required_skills}
    
    if not required_skill_ids:
        return 100
    
    matching = len(employee_skill_ids & required_skill_ids)
    return (matching / len(required_skill_ids)) * 100

def format_date(date):
    """Format date for display"""
    if date:
        return date.strftime('%Y-%m-%d')
    return 'N/A'

def get_role_color(role):
    """Get bootstrap color for role"""
    role_colors = {
        'Admin': 'danger',
        'Top Management': 'dark',
        'HR Manager': 'info',
        'Project Manager': 'warning',
        'Employee': 'success'
    }
    return role_colors.get(role, 'secondary')

def get_status_color(status):
    """Get bootstrap color for status"""
    status_colors = {
        'Planning': 'secondary',
        'In Progress': 'info',
        'On Hold': 'warning',
        'Completed': 'success',
        'Cancelled': 'danger'
    }
    return status_colors.get(status, 'secondary')

def export_to_csv(rows, filename):
    """Helper to export data to CSV format"""
    import csv
    from io import StringIO
    
    output = StringIO()
    if rows:
        writer = csv.DictWriter(output, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    
    return output.getvalue()
