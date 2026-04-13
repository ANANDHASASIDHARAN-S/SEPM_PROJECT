from datetime import datetime

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.db.session import SessionLocal
from app.models.device import Device
from app.models.user import User
from app.security.auth import decode_access_token


class ZeroTrustMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if not request.url.path.startswith("/soc"):
            return await call_next(request)

        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return JSONResponse(status_code=401, content={"detail": "Missing bearer token"})

        token = auth_header.removeprefix("Bearer ").strip()
        payload = decode_access_token(token)
        if not payload or "sub" not in payload:
            return JSONResponse(status_code=401, content={"detail": "Invalid token"})

        try:
            user_id = int(payload["sub"])
        except (TypeError, ValueError):
            return JSONResponse(status_code=401, content={"detail": "Invalid token subject"})

        device_id = request.headers.get("X-Device-Id")
        if not device_id:
            return JSONResponse(status_code=403, content={"detail": "Missing device identity header"})

        db = SessionLocal()
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user or not user.is_active:
                return JSONResponse(status_code=401, content={"detail": "Inactive user"})

            if not user.mfa_enabled:
                return JSONResponse(status_code=403, content={"detail": "MFA is required"})

            trusted_device = (
                db.query(Device)
                .filter(
                    Device.user_id == user.id,
                    Device.device_id == device_id,
                    Device.is_trusted.is_(True),
                )
                .first()
            )
            if not trusted_device:
                return JSONResponse(status_code=403, content={"detail": "Untrusted device"})

            trusted_device.last_seen = datetime.utcnow()
            db.commit()
        finally:
            db.close()

        return await call_next(request)
