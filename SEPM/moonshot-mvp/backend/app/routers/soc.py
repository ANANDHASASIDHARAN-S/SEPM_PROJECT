from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.threat_event import AlertLevel, ThreatEvent, ThreatStatus
from app.models.user import RoleEnum, User
from app.schemas.threat import DashboardResponse, ThreatOut
from app.security.auth import get_current_user

router = APIRouter(prefix="/soc", tags=["soc"])


@router.get("/dashboard", response_model=DashboardResponse)
def get_dashboard(
    limit: int = Query(default=200, ge=10, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DashboardResponse:
    if current_user.role not in {RoleEnum.SOC_ANALYST, RoleEnum.ADMIN}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="SOC access required")

    total_open_alerts = db.query(func.count(ThreatEvent.id)).filter(ThreatEvent.status == ThreatStatus.OPEN).scalar() or 0
    critical_open_alerts = (
        db.query(func.count(ThreatEvent.id))
        .filter(ThreatEvent.status == ThreatStatus.OPEN, ThreatEvent.alert_level == AlertLevel.CRITICAL)
        .scalar()
        or 0
    )
    investigating_alerts = (
        db.query(func.count(ThreatEvent.id))
        .filter(ThreatEvent.status == ThreatStatus.INVESTIGATING)
        .scalar()
        or 0
    )

    rows = db.query(ThreatEvent).order_by(ThreatEvent.timestamp.desc()).limit(limit).all()
    latest_events = [
        ThreatOut(
            id=row.id,
            alert_level=row.alert_level.value,
            source=row.source,
            event_type=row.event_type,
            timestamp=row.timestamp,
            status=row.status.value,
            details=row.details,
        )
        for row in rows
    ]

    return DashboardResponse(
        total_open_alerts=total_open_alerts,
        critical_open_alerts=critical_open_alerts,
        investigating_alerts=investigating_alerts,
        latest_events=latest_events,
    )
