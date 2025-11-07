import uuid
from sqlalchemy import Column, String, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship

from core.database.sqlalchamey.base import AbstractSQLModel
from core.database.sqlalchamey.mixins import TimestampsMixin, SoftDeleteMixin


def generate_uuid():
    return str(uuid.uuid4())


class EmailLog(AbstractSQLModel, TimestampsMixin, SoftDeleteMixin):
    __tablename__ = "email_logs"

    id = Column(
        String(36), primary_key=True, default=generate_uuid, unique=True, nullable=False
    )
    donation_id = Column(
        String(36), ForeignKey("donations.id"), nullable=True, index=True
    )
    recipient_email = Column(String(255), nullable=False, index=True)
    mail_type = Column(
        String(50), nullable=False, index=True
    )  # e.g., 'donation_thank_you', 'form_g80_confirmation'
    subject = Column(String(500), nullable=False)
    mail_content = Column(Text, nullable=True)  # Store rendered email content
    status = Column(
        String(20), nullable=False, default="pending", index=True
    )  # pending, sent, failed
    message_id = Column(String(255), nullable=True)  # AWS SES Message ID
    error_message = Column(Text, nullable=True)
    additional_data = Column(JSON, nullable=True)  # Store additional context/data

    donation = relationship("Donation", backref="email_logs")
