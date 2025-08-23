from datetime import datetime
from pydantic import BaseModel
from enum import Enum as PyEnum


class DonationStatus(PyEnum):
    PENDING = "pending"
    PAYMENT_FAILED = "payment_failed"
    COMPLETED = "completed"


class FormG80SubmissionStatus(PyEnum):
    PENDING = "pending"
    GIVEN = "given"


class Form80SubmissionRequest(BaseModel):
    pan_number: str
    full_address: str
    city: str
    state: str
    country: str
    pin_code: str


class DonationRequest(BaseModel):
    full_name: str
    email: str
    contact_number: str
    amount: float
    need_g80_certificate: bool
    confirmed_terms: bool
    form_g80: Form80SubmissionRequest | None = None


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
