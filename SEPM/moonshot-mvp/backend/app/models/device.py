from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.db.base import Base


class Device(Base):
    __tablename__ = "devices"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(String(128), unique=True, nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    hostname = Column(String(255), nullable=True)
    os = Column(String(100), nullable=True)
    ip_address = Column(String(64), nullable=True)
    is_trusted = Column(Boolean, default=False, nullable=False)
    last_seen = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="devices")
