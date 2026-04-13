from datetime import datetime

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.models.threat_event import AlertLevel, ThreatEvent, ThreatStatus
from app.models.user import RoleEnum, User
from app.schemas.threat import ThreatBatchIn, ThreatOut
from app.security.auth import get_current_user

router = APIRouter(prefix="/siem", tags=["siem"])


@router.post("/ingest")
def ingest_events(
    payload: ThreatBatchIn,
    db: Session = Depends(get_db),
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
) -> dict:
    if x_api_key != settings.siem_ingest_api_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid SIEM API key")

    events = []
    for item in payload.events:
        events.append(
            ThreatEvent(
                alert_level=AlertLevel(item.alert_level),
                source=item.source,
                event_type=item.event_type,
                timestamp=item.timestamp or datetime.utcnow(),
                status=ThreatStatus(item.status),
                details=item.details,
                asset_id=item.asset_id,
                user_id=item.user_id,
            )
        )

    db.bulk_save_objects(events)
    db.commit()

    return {"ingested": len(events)}


@router.get("/events", response_model=list[ThreatOut])
def list_events(
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[ThreatOut]:
    if current_user.role not in {RoleEnum.SOC_ANALYST, RoleEnum.ADMIN}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="SOC access required")

    rows = db.query(ThreatEvent).order_by(ThreatEvent.timestamp.desc()).limit(limit).all()
    return [
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
