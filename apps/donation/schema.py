from datetime import datetime
from typing import Annotated
from pydantic import BaseModel, StringConstraints, field_validator
from enum import Enum as PyEnum
from pydantic.networks import validate_email


class DonationStatus(PyEnum):
    PENDING = "pending"
    PAYMENT_FAILED = "payment_failed"
    COMPLETED = "completed"


class FormG80SubmissionStatus(PyEnum):
    PENDING = "pending"
    GIVEN = "given"


class Form80SubmissionRequest(BaseModel):
    pan_number: Annotated[
        str, StringConstraints(min_length=10, max_length=10, pattern=r"^[A-Za-z0-9]+$")
    ]
    full_address: Annotated[
        str,
        StringConstraints(
            min_length=5, max_length=500, pattern=r"^[a-zA-Z0-9\s.,'#/-]+$"
        ),
    ]
    city: Annotated[
        str, StringConstraints(min_length=2, max_length=100, pattern=r"^[A-Za-z\s-]+$")
    ]
    state: Annotated[
        str, StringConstraints(min_length=2, max_length=100, pattern=r"^[A-Za-z\s-]+$")
    ]
    country: Annotated[
        str, StringConstraints(min_length=2, max_length=100, pattern=r"^[A-Za-z\s-]+$")
    ]
    pin_code: Annotated[
        str, StringConstraints(min_length=6, max_length=6, pattern=r"^[0-9]{6}$")
    ]

    # Normalize full_address
    @classmethod
    def model_validate(cls, data):
        if "full_address" in data and isinstance(data["full_address"], str):
            data["full_address"] = " ".join(data["full_address"].split())
        return super().model_validate(data)


class DonationRequest(BaseModel):
    full_name: Annotated[
        str,
        StringConstraints(
            min_length=2, max_length=100, pattern=r"^[A-Za-z][A-Za-z .'-]*[A-Za-z]$"
        ),
    ]
    email: str
    contact_number: Annotated[
        str,
        StringConstraints(
            min_length=5, max_length=25, pattern=r"^\+?[0-9]{1,4}[0-9]{5,14}$"
        ),
    ]
    amount: float
    need_g80_certificate: bool
    confirmed_terms: bool
    form_g80: Form80SubmissionRequest | None = None

    @field_validator("email", mode="before")
    def validate_email(cls, value):
        _, email = validate_email(value)
        return email

    @field_validator("contact_number", mode="before")
    def preprocess_contact_number(cls, value):
        if not isinstance(value, str):
            raise ValueError("Contact number must be a string")
        cleaned = "".join(value.split()).strip()
        return cleaned

    @field_validator("amount", mode="after")
    def validate_amount(cls, value):
        if value < 1000:
            raise ValueError("Minimum donation amount is 1000.")
        return value


class Form80SubmissionResponse(BaseModel):
    id: str
    donation_id: str
    pan_number: str
    full_address: str
    city: str
    state: str
    country: str
    pin_code: str
    status: FormG80SubmissionStatus


class DonationResponse(BaseModel):
    id: str
    order_id: str
    full_name: str
    email: str
    contact_number: str
    amount: float
    need_g80_certificate: bool
    confirmed_terms: bool
    status: DonationStatus
    form_g80: Form80SubmissionResponse | None = None


class PaymentResponse(BaseModel):
    payment_url: str
    merchant_order_id: str
    amount: float


class PaymentDetails(BaseModel):
    payment_status: str
    merchant_order_id: str
    phonepe_order_id: str
    is_payment_url_expired: bool | None
    payment_url: str | None


class DonationStatusResponse(BaseModel):
    order_id: str
    full_name: str
    amount: float
    status: str
    need_g80_certificate: bool
    payment_details: PaymentDetails


class DonationListResponse(BaseModel):
    id: str
    order_id: str
    full_name: str
    email: str
    amount: float
    status: str
    need_g80_certificate: bool
    created_at: datetime


class Form80SubmissionListResponse(BaseModel):
    id: str
    donation: DonationListResponse
    pan_number: str
    full_address: str
    city: str
    state: str
    country: str
    pin_code: str
    status: FormG80SubmissionStatus
    created_at: datetime
