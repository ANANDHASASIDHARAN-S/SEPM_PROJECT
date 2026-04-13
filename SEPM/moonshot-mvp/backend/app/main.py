from datetime import datetime, timedelta

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.base import Base
from app.db.session import SessionLocal, engine
from app.middleware import ZeroTrustMiddleware, log_api_action
from app.models.asset import Asset, AssetType
from app.models.device import Device
from app.models.threat_event import AlertLevel, ThreatEvent, ThreatStatus
from app.models.user import RoleEnum, User
from app.routers import auth_router, siem_router, soc_router
from app.security.auth import get_password_hash

app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(ZeroTrustMiddleware)


@app.middleware("http")
async def audit_middleware(request, call_next):
    response = await call_next(request)
    log_api_action(request, response)
    return response


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}


@app.on_event("startup")
def startup_event() -> None:
    Base.metadata.create_all(bind=engine)
    seed_defaults(SessionLocal())


app.include_router(auth_router)
app.include_router(siem_router)
app.include_router(soc_router)


def seed_defaults(db: Session) -> None:
    try:
        if db.query(User).count() == 0:
            soc_user = User(
                username="soc_analyst",
                email="soc.analyst@srm.edu",
                password_hash=get_password_hash("ChangeMe123!"),
                role=RoleEnum.SOC_ANALYST,
                mfa_enabled=True,
                is_active=True,
            )
            admin_user = User(
                username="admin",
                email="admin@srm.edu",
                password_hash=get_password_hash("ChangeMe123!"),
                role=RoleEnum.ADMIN,
                mfa_enabled=True,
                is_active=True,
            )
            student_user = User(
                username="student1",
                email="student1@srm.edu",
                password_hash=get_password_hash("ChangeMe123!"),
                role=RoleEnum.STUDENT,
                mfa_enabled=True,
                is_active=True,
            )
            faculty_user = User(
                username="faculty1",
                email="faculty1@srm.edu",
                password_hash=get_password_hash("ChangeMe123!"),
                role=RoleEnum.FACULTY,
                mfa_enabled=True,
                is_active=True,
            )

            db.add_all([soc_user, admin_user, student_user, faculty_user])
            db.flush()

            db.add(
                Device(
                    device_id="SOC-WS-001",
                    user_id=soc_user.id,
                    hostname="soc-workstation-1",
                    os="Linux",
                    ip_address="10.0.10.15",
                    is_trusted=True,
                )
            )

            db.add_all(
                [
                    Asset(
                        name="Core SOC Server",
                        asset_type=AssetType.SERVER,
                        ip_range="10.0.0.10/32",
                        owner_user_id=admin_user.id,
                        criticality=5,
                    ),
                    Asset(
                        name="Student Endpoint Pool",
                        asset_type=AssetType.DEVICE,
                        ip_range="10.10.0.0/16",
                        owner_user_id=student_user.id,
                        criticality=2,
                    ),
                    Asset(
                        name="Campus VPN Block",
                        asset_type=AssetType.IP_RANGE,
                        ip_range="172.16.0.0/20",
                        owner_user_id=admin_user.id,
                        criticality=4,
                    ),
                ]
            )

        if db.query(ThreatEvent).count() == 0:
            now = datetime.utcnow()
            db.add_all(
                [
                    ThreatEvent(
                        alert_level=AlertLevel.CRITICAL,
                        source="SIEM",
                        event_type="Suspicious Privilege Escalation",
                        timestamp=now,
                        status=ThreatStatus.OPEN,
                        details="Initial seeded event for SOC dashboard.",
                    ),
                    ThreatEvent(
                        alert_level=AlertLevel.HIGH,
                        source="EDR",
                        event_type="Malware Beaconing Pattern",
                        timestamp=now - timedelta(minutes=1),
                        status=ThreatStatus.INVESTIGATING,
                        details="Endpoint telemetry indicates command-and-control callbacks.",
                    ),
                    ThreatEvent(
                        alert_level=AlertLevel.MEDIUM,
                        source="Firewall",
                        event_type="Unusual East-West Traffic",
                        timestamp=now - timedelta(minutes=2),
                        status=ThreatStatus.OPEN,
                        details="Lateral traffic spike detected between segmented VLANs.",
                    ),
                ]
            )

        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
