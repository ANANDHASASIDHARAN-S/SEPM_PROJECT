from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

AlertLevelLiteral = Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]
ThreatStatusLiteral = Literal["OPEN", "INVESTIGATING", "RESOLVED", "FALSE_POSITIVE"]


class ThreatIn(BaseModel):
    alert_level: AlertLevelLiteral
    source: str = Field(min_length=2, max_length=255)
    event_type: str = Field(min_length=2, max_length=255)
    timestamp: datetime | None = None
    status: ThreatStatusLiteral = "OPEN"
    details: str | None = Field(default=None, max_length=5000)
    asset_id: int | None = None
    user_id: int | None = None


class ThreatBatchIn(BaseModel):
    events: list[ThreatIn] = Field(min_length=1, max_length=500)


class ThreatOut(BaseModel):
    id: int
    alert_level: AlertLevelLiteral
    source: str
    event_type: str
    timestamp: datetime
    status: ThreatStatusLiteral
    details: str | None


class DashboardResponse(BaseModel):
    total_open_alerts: int
    critical_open_alerts: int
    investigating_alerts: int
    latest_events: list[ThreatOut]
