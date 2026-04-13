import os


def env_to_bool(name, default=False):
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {'1', 'true', 'yes', 'on'}

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'elms-secret-key-change-in-production'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///elms.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    AI_SMART_APPLY_HELPER_ENABLED = env_to_bool('AI_SMART_APPLY_HELPER_ENABLED', True)
    AI_POLICY_PRECHECK_ENABLED = env_to_bool('AI_POLICY_PRECHECK_ENABLED', True)
    AI_PRECHECK_AUDIT_LOG_ENABLED = env_to_bool('AI_PRECHECK_AUDIT_LOG_ENABLED', True)
    AI_OLLAMA_ENABLED = env_to_bool('AI_OLLAMA_ENABLED', True)
    AI_OLLAMA_BASE_URL = os.environ.get('AI_OLLAMA_BASE_URL', 'http://127.0.0.1:11434').rstrip('/')
    AI_OLLAMA_MODEL = os.environ.get('AI_OLLAMA_MODEL', 'qwen3.5:4b')
    AI_OLLAMA_TIMEOUT_SECONDS = int(os.environ.get('AI_OLLAMA_TIMEOUT_SECONDS', '20'))
    AI_OLLAMA_THINKING_MODEL = env_to_bool('AI_OLLAMA_THINKING_MODEL', True)
    AI_OLLAMA_REASON_MIN_CHARS = int(os.environ.get('AI_OLLAMA_REASON_MIN_CHARS', '20'))
    AI_OLLAMA_CACHE_TTL_SECONDS = int(os.environ.get('AI_OLLAMA_CACHE_TTL_SECONDS', '120'))
    AI_OLLAMA_CACHE_MAX_ENTRIES = int(os.environ.get('AI_OLLAMA_CACHE_MAX_ENTRIES', '256'))
    AI_LEAVE_PREDICTION_ENABLED = env_to_bool('AI_LEAVE_PREDICTION_ENABLED', True)
    AI_OLLAMA_LEAVE_PREDICTION_TIMEOUT_SECONDS = int(os.environ.get('AI_OLLAMA_LEAVE_PREDICTION_TIMEOUT_SECONDS', '25'))
    AI_OLLAMA_LEAVE_PREDICTION_CACHE_TTL_SECONDS = int(os.environ.get('AI_OLLAMA_LEAVE_PREDICTION_CACHE_TTL_SECONDS', '300'))
