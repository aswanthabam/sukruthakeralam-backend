from sqlalchemy import Column, String, Float, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base
import uuid
from datetime import datetime, timezone

from apps.payments.schema import PhonePePaymentStatus
from core.database.sqlalchamey.base import AbstractSQLModel
from core.database.sqlalchamey.fields import TZAwareDateTime
from core.database.sqlalchamey.mixins import TimestampsMixin, SoftDeleteMixin


def generate_uuid():
    return str(uuid.uuid4())


class PhonePePaymentLog(AbstractSQLModel, TimestampsMixin, SoftDeleteMixin):
    __tablename__ = "phonepe_payment_logs"

    id = Column(
        String(36), primary_key=True, default=generate_uuid, unique=True, nullable=False
    )
    merchant_order_id = Column(String(128), nullable=False, unique=True, index=True)
    phonepe_order_id = Column(String(128), nullable=False, index=True)
    redirect_url = Column(String(512), nullable=True)
    payment_status = Column(
        String(32),
        default=PhonePePaymentStatus.PENDING.value,
        nullable=False,
        index=True,
    )
    amount = Column(Float, nullable=False)
    currency = Column(String(8), nullable=False, default="INR")
    phonepe_payment_details = Column(JSON, nullable=True)
