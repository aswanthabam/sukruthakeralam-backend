import uuid
from sqlalchemy import Column, String, Boolean, Float, ForeignKey
from sqlalchemy.orm import relationship

from apps.donation.schema import DonationStatus, FormG80SubmissionStatus
from core.database.sqlalchamey.base import AbstractSQLModel
from core.database.sqlalchamey.mixins import TimestampsMixin, SoftDeleteMixin


def generate_uuid():
    return str(uuid.uuid4())


class Donation(AbstractSQLModel, TimestampsMixin, SoftDeleteMixin):
    __tablename__ = "donations"

    id = Column(
        String(36), primary_key=True, default=generate_uuid, unique=True, nullable=False
    )
    order_id = Column(String(50), nullable=False, unique=True)
    full_name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False)
    contact_number = Column(String(20), nullable=False)
    amount = Column(Float, nullable=False)
    need_g80_certificate = Column(Boolean, default=False, nullable=False)
    confirmed_terms = Column(Boolean, default=False, nullable=False)
    status = Column(String(50), nullable=False, default=DonationStatus.PENDING.value)

    g80_certificate = relationship(
        "FormG80Submission",
        back_populates="donation",
        uselist=False,
    )


class FormG80Submission(AbstractSQLModel, TimestampsMixin, SoftDeleteMixin):
    __tablename__ = "form_g80_submissions"

    id = Column(
        String(36), primary_key=True, default=generate_uuid, unique=True, nullable=False
    )
    donation_id = Column(String(36), ForeignKey("donations.id"), nullable=False)
    pan_number = Column(String(20), nullable=False)
    full_address = Column(String(1000), nullable=False)
    city = Column(String(128), nullable=False)
    state = Column(String(128), nullable=False)
    country = Column(String(128), nullable=False)
    pin_code = Column(String(16), nullable=False)
    status = Column(
        String(50), nullable=False, default=FormG80SubmissionStatus.PENDING.value
    )

    donation = relationship("Donation", back_populates="g80_certificate")
