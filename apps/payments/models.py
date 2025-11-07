from sqlalchemy import Column, String, Float, JSON, Text
import uuid

from apps.payments.schema import PhonePePaymentStatus, SbiePayPaymentStatus
from core.database.sqlalchamey.base import AbstractSQLModel
from core.database.sqlalchamey.mixins import TimestampsMixin, SoftDeleteMixin


def generate_uuid():
    return str(uuid.uuid4())


class SbiePayPaymentLog(AbstractSQLModel, TimestampsMixin, SoftDeleteMixin):
    """Database model to track SBIePay payment transactions"""

    __tablename__ = "sbiepay_payment_logs"

    id = Column(
        String(36), primary_key=True, default=generate_uuid, unique=True, nullable=False
    )
    merchant_order_id = Column(String(128), nullable=False, unique=True, index=True)
    sbiepay_ref_id = Column(String(128), nullable=True, index=True)  # ATRN from SBIePay
    encrypted_trans = Column(Text, nullable=False)
    payment_status = Column(
        String(32),
        default=SbiePayPaymentStatus.PENDING.value,
        nullable=False,
        index=True,
    )
    customer_id = Column(String(100), nullable=True)
    amount = Column(Float, nullable=False)
    currency = Column(String(8), nullable=False, default="INR")

    sbiepay_response_data = Column(JSON, nullable=True)  # Raw response data
    double_verification_data = Column(JSON, nullable=True)  # DV API response

    # Payment gateway details
    pay_mode = Column(String(50), nullable=True)  # NB, CC, DC, etc.
    bank_code = Column(String(20), nullable=True)
    bank_reference_number = Column(String(100), nullable=True)
    transaction_date = Column(String(20), nullable=True)

    # Status and reason
    reason_message = Column(String(500), nullable=True)
    other_details = Column(Text, nullable=True)

    def __repr__(self):
        return f"<SbiePayPaymentLog(order_id={self.merchant_order_id}, status={self.payment_status})>"


class PhonePePaymentLog(AbstractSQLModel, TimestampsMixin, SoftDeleteMixin):
    __tablename__ = "phonepe_payment_logs"

    id = Column(
        String(36), primary_key=True, default=generate_uuid, unique=True, nullable=False
    )
    merchant_order_id = Column(String(128), nullable=False, unique=True, index=True)
    phonepe_order_id = Column(String(128), nullable=False, index=True)
    redirect_url = Column(String(1024), nullable=True)
    payment_status = Column(
        String(32),
        default=PhonePePaymentStatus.PENDING.value,
        nullable=False,
        index=True,
    )
    amount = Column(Float, nullable=False)
    currency = Column(String(8), nullable=False, default="INR")
    phonepe_payment_details = Column(JSON, nullable=True)
