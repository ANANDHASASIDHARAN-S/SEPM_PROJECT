// ─── ELMS Main JavaScript ────────────────────────────────────

// Auto-dismiss flash messages after 5 seconds
document.addEventListener('DOMContentLoaded', () => {
    const flashMessages = document.querySelectorAll('.flash-msg');
    flashMessages.forEach(msg => {
        setTimeout(() => {
            msg.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
            msg.style.opacity = '0';
            msg.style.transform = 'translateY(-8px)';
            setTimeout(() => msg.remove(), 300);
        }, 5000);
    });

    // Close sidebar on mobile when clicking outside
    document.addEventListener('click', (e) => {
        const sidebar = document.getElementById('sidebar');
        if (sidebar && window.innerWidth < 1024) {
            if (!sidebar.contains(e.target) && !e.target.closest('button[onclick*="sidebar"]')) {
                sidebar.classList.add('-translate-x-full');
            }
        }
    });

    initLeaveApplyAssistant();
    initAiAssistantPreview();
});


function debounce(fn, delayMs) {
    let timerId;
    return (...args) => {
        clearTimeout(timerId);
        timerId = setTimeout(() => fn(...args), delayMs);
    };
}


function setHelperStatus(statusElement, status, reasonScore, sourceLabel) {
    if (!statusElement) {
        return;
    }

    const classesByStatus = {
        ready: 'bg-green-100 text-green-800',
        warning: 'bg-yellow-100 text-yellow-800',
        blocked: 'bg-red-100 text-red-800'
    };

    statusElement.className = `text-xs px-2 py-1 rounded-full ${classesByStatus[status] || 'bg-gray-200 text-gray-700'}`;
    const scoreSuffix = typeof reasonScore === 'number' ? ` | Reason score ${reasonScore}/100` : '';
    const sourceSuffix = sourceLabel ? ` | ${sourceLabel}` : '';

    if (status === 'ready') {
        statusElement.textContent = `Ready${scoreSuffix}${sourceSuffix}`;
    } else if (status === 'warning') {
        statusElement.textContent = `Review${scoreSuffix}${sourceSuffix}`;
    } else if (status === 'blocked') {
        statusElement.textContent = `Fix Required${scoreSuffix}${sourceSuffix}`;
    } else {
        statusElement.textContent = `Waiting${scoreSuffix}${sourceSuffix}`;
    }
}


function populateMessageList(listElement, messages, emptyText, iconClass) {
    if (!listElement) {
        return;
    }

    listElement.innerHTML = '';
    if (!messages || messages.length === 0) {
        const item = document.createElement('li');
        item.className = 'text-gray-500';
        item.textContent = emptyText;
        listElement.appendChild(item);
        return;
    }

    messages.forEach((message) => {
        const item = document.createElement('li');
        item.className = 'flex items-start gap-2';

        const icon = document.createElement('i');
        icon.className = `${iconClass} mt-0.5 text-xs`;

        const text = document.createElement('span');
        text.textContent = message;

        item.appendChild(icon);
        item.appendChild(text);
        listElement.appendChild(item);
    });
}


function collectPrecheckPayload(formElement) {
    return {
        leave_type_id: formElement.querySelector('[name="leave_type_id"]')?.value || '',
        start_date: formElement.querySelector('[name="start_date"]')?.value || '',
        end_date: formElement.querySelector('[name="end_date"]')?.value || '',
        reason: formElement.querySelector('[name="reason"]')?.value || ''
    };
}


function initLeaveApplyAssistant() {
    const form = document.getElementById('leave-apply-form');
    const panel = document.getElementById('ai-helper-panel');
    if (!form || !panel) {
        return;
    }

    const helperEnabled = form.dataset.aiHelperEnabled === 'true';
    const precheckEnabled = form.dataset.aiPrecheckEnabled === 'true';
    const ollamaEnabled = form.dataset.aiOllamaEnabled === 'true';
    const runtimeStatusVisible = form.dataset.runtimeStatusVisible === 'true';
    const precheckUrl = form.dataset.precheckUrl;
    const ollamaStatusUrl = form.dataset.ollamaStatusUrl;

    if (!helperEnabled && !precheckEnabled) {
        return;
    }

    panel.classList.remove('hidden');

    const summaryEl = document.getElementById('ai-helper-summary');
    const sourceNoteEl = document.getElementById('ai-helper-source-note');
    const statusEl = document.getElementById('ai-helper-status');
    const issuesEl = document.getElementById('ai-helper-issues');
    const suggestionsEl = document.getElementById('ai-helper-suggestions');

    if (runtimeStatusVisible && ollamaEnabled && ollamaStatusUrl && sourceNoteEl) {
        fetch(ollamaStatusUrl)
            .then((response) => response.json())
            .then((data) => {
                const thinkingHint = data.thinking_model ? ' (thinking model mode)' : '';
                if (data.reachable && data.model_available) {
                    sourceNoteEl.textContent = `Guidance source: Rule engine + Ollama (${data.model})${thinkingHint}.`;
                } else if (data.reachable && !data.model_available) {
                    sourceNoteEl.textContent = 'Guidance source: Rule engine (Ollama model not found locally).';
                } else {
                    sourceNoteEl.textContent = 'Guidance source: Rule engine (Ollama offline fallback active).';
                }
            })
            .catch(() => {
                sourceNoteEl.textContent = 'Guidance source: Rule engine (Ollama status unavailable).';
            });
    }

    if (!precheckEnabled || !precheckUrl) {
        setHelperStatus(statusEl, 'warning');
        if (summaryEl) {
            summaryEl.textContent = 'Smart helper is enabled, but policy pre-check endpoint is unavailable.';
        }
        return;
    }

    const handlePrecheck = debounce(async () => {
        const payload = collectPrecheckPayload(form);
        const hasMinimumInput = payload.leave_type_id && payload.start_date && payload.end_date;

        if (!hasMinimumInput) {
            setHelperStatus(statusEl, 'warning');
            if (summaryEl) {
                summaryEl.textContent = 'Select leave type and dates to run policy pre-check.';
            }
            populateMessageList(issuesEl, [], 'No checks yet.', 'fa-solid fa-circle-info text-blue-500');
            populateMessageList(suggestionsEl, [], 'Suggestions will appear here.', 'fa-solid fa-lightbulb text-amber-500');
            return;
        }

        try {
            const response = await fetch(precheckUrl, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            const data = await response.json();
            const status = data.status || 'warning';
            const reasonScore = data.reason_analysis?.score;
            const modelSource = data.reason_analysis?.model_source || 'rule';
            let sourceLabel = 'Rule';
            if (modelSource.startsWith('rule+ollama:')) {
                sourceLabel = 'Rule + Ollama';
            } else if (modelSource.startsWith('ollama:')) {
                sourceLabel = 'Ollama';
            }

            if (sourceNoteEl) {
                sourceNoteEl.textContent = `Guidance source: ${sourceLabel}.`;
            }

            setHelperStatus(statusEl, status, reasonScore, sourceLabel);
            if (summaryEl) {
                summaryEl.textContent = data.summary || 'Live guidance is available.';
            }

            const issueMessages = (data.issues || []).map((item) => item.message || 'Check this field.');
            const suggestionMessages = [
                ...(data.suggestions || []),
                ...((data.reason_analysis?.tips || []))
            ];

            populateMessageList(issuesEl, issueMessages, 'No issues found.', 'fa-solid fa-shield-check text-green-500');
            populateMessageList(suggestionsEl, suggestionMessages, 'No extra suggestions right now.', 'fa-solid fa-lightbulb text-amber-500');
        } catch (error) {
            setHelperStatus(statusEl, 'warning');
            if (summaryEl) {
                summaryEl.textContent = 'Policy pre-check is temporarily unavailable. You can still submit your request.';
            }
            populateMessageList(issuesEl, ['Unable to fetch live checks right now.'], 'No issues found.', 'fa-solid fa-circle-info text-blue-500');
            populateMessageList(suggestionsEl, ['Try again in a moment or submit when ready.'], 'No extra suggestions right now.', 'fa-solid fa-lightbulb text-amber-500');
        }
    }, 450);

    ['leave_type_id', 'start_date', 'end_date', 'reason'].forEach((fieldName) => {
        const field = form.querySelector(`[name="${fieldName}"]`);
        if (!field) {
            return;
        }

        field.addEventListener('change', handlePrecheck);
        field.addEventListener('input', handlePrecheck);
    });

    handlePrecheck();
}


function initAiAssistantPreview() {
    const form = document.getElementById('ai-reason-preview-form');
    const resultBox = document.getElementById('ai-preview-result');
    if (!form || !resultBox) {
        return;
    }

    const previewUrl = form.dataset.previewUrl;
    if (!previewUrl) {
        return;
    }

    form.addEventListener('submit', async (event) => {
        event.preventDefault();

        const payload = {
            leave_type_id: form.querySelector('[name="leave_type_id"]')?.value || '',
            start_date: form.querySelector('[name="start_date"]')?.value || '',
            end_date: form.querySelector('[name="end_date"]')?.value || '',
            reason: form.querySelector('[name="reason"]')?.value || ''
        };

        resultBox.innerHTML = '<p class="text-sm text-gray-600">Generating AI preview...</p>';

        try {
            const response = await fetch(previewUrl, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            const data = await response.json();

            const analysis = data.reason_analysis || {};
            const tips = analysis.tips || [];
            const tipsMarkup = tips.length
                ? tips.map((tip) => `<li class="flex items-start gap-2"><i class="fa-solid fa-lightbulb text-amber-500 mt-1 text-xs"></i><span>${tip}</span></li>`).join('')
                : '<li class="text-gray-500">No suggestions generated.</li>';

            resultBox.innerHTML = `
                <div class="space-y-2 text-sm">
                    <p><span class="font-semibold text-gray-700">Status:</span> ${data.status || 'ok'}</p>
                    <p><span class="font-semibold text-gray-700">Label:</span> ${analysis.label || 'n/a'}</p>
                    <p><span class="font-semibold text-gray-700">Score:</span> ${analysis.score ?? 'n/a'}</p>
                    <p><span class="font-semibold text-gray-700">Source:</span> ${analysis.model_source || 'rule'}</p>
                    <p><span class="font-semibold text-gray-700">Summary:</span> ${analysis.summary || 'No summary returned.'}</p>
                    <div>
                        <p class="font-semibold text-gray-700 mb-1">Suggestions</p>
                        <ul class="space-y-1">${tipsMarkup}</ul>
                    </div>
                </div>
            `;
        } catch (error) {
            resultBox.innerHTML = '<p class="text-sm text-red-600">Unable to generate preview right now.</p>';
        }
    });
}
