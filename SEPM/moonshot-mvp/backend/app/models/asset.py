import enum
from datetime import datetime

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, String

from app.db.base import Base


class AssetType(str, enum.Enum):
    DEVICE = "DEVICE"
    SERVER = "SERVER"
    IP_RANGE = "IP_RANGE"


class AssetStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    QUARANTINED = "QUARANTINED"
    RETIRED = "RETIRED"


class Asset(Base):
    __tablename__ = "assets"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    asset_type = Column(Enum(AssetType, name="asset_type_enum"), nullable=False, index=True)
    ip_range = Column(String(64), nullable=True)
    owner_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    status = Column(Enum(AssetStatus, name="asset_status_enum"), default=AssetStatus.ACTIVE, nullable=False)
    criticality = Column(Integer, default=3, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
