import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import Column, String
from core.database.sqlalchamey.base import AbstractSQLModel
from core.database.sqlalchamey.fields import TZAwareDateTime
from core.database.sqlalchamey.mixins import TimestampsMixin


def generate_uuid():
    return str(uuid.uuid4())


def get_expiry_datetime():
    return datetime.now(timezone.utc) + timedelta(days=1)


class AdminAccessTokens(AbstractSQLModel, TimestampsMixin):
    __tablename__ = "admin_access_tokens"
    id = Column(
        String(36), primary_key=True, default=generate_uuid, unique=True, nullable=False
    )
    token = Column(String(500), nullable=False, unique=True, index=True)
    expiry = Column(
        TZAwareDateTime(timezone=True), nullable=False, default=get_expiry_datetime
    )
