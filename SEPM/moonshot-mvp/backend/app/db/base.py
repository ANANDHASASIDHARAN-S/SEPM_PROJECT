from sqlalchemy.orm import declarative_base

Base = declarative_base()

# Import models so SQLAlchemy registers table metadata before create_all.
from app.models import asset, audit_log, device, threat_event, user  # noqa: E402,F401
