from fastapi import Request, Response

from app.db.session import SessionLocal
from app.models.audit_log import AuditLog
from app.security.auth import decode_access_token


def _extract_actor_user_id(auth_header: str | None) -> int | None:
    if not auth_header or not auth_header.startswith("Bearer "):
        return None

    token = auth_header.removeprefix("Bearer ").strip()
    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        return None

    try:
        return int(payload["sub"])
    except (TypeError, ValueError):
        return None


def log_api_action(request: Request, response: Response) -> None:
    actor_user_id = _extract_actor_user_id(request.headers.get("Authorization"))
    db = SessionLocal()
    try:
        db.add(
            AuditLog(
                actor_user_id=actor_user_id,
                action="api.request",
                path=request.url.path,
                method=request.method,
                status_code=response.status_code,
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent"),
            )
        )
        db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()
