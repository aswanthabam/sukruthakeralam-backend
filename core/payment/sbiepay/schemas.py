from pydantic import BaseModel, Field
from typing import Annotated, Optional
from decimal import Decimal


# Schema for the create_payment_request method's return type
class PaymentRequest(BaseModel):
    EncryptTrans: str
    merchIdVal: str


# Schema for the parsed response from handle_encrypted_response
class SbiePayResponseData(BaseModel):
    merchant_order_number: str
    sbiepay_ref_id: str = Field(..., description="SBIePay Reference ID / ATRN")
    transaction_status: str
    amount: Annotated[Decimal, Field(max_digits=17, decimal_places=2)]
    currency: str
    pay_mode: str
    other_details: str
    reason_message: str


# Schema for the full return type of handle_encrypted_response
class HandleResponse(BaseModel):
    status: str
    raw_data: str
    parsed_data: SbiePayResponseData


# Schema for the parsed response from the verify_transaction method
class DoubleVerificationParsedResponse(BaseModel):
    merchant_id: str
    atrn: str
    transaction_status: str
    country: str
    currency: str
    other_details: str
    merchant_order_number: str
    amount: Annotated[Decimal, Field(max_digits=17, decimal_places=2)]
    status_description: str
    bank_code: str
    bank_reference_number: str
    transaction_date: str  # datetime string
    pay_mode: str
    cin: str
    merchant_id_from_response: str = Field(
        ..., alias="merchant_id"
    )  # Renaming to avoid conflict
    total_fee_gst: str
    ref1: Optional[str] = None
    ref2: Optional[str] = None
    ref3: Optional[str] = None
    ref4: Optional[str] = None
    ref5: Optional[str] = None
    ref6: Optional[str] = None
    ref7: Optional[str] = None
    ref8: Optional[str] = None
    ref9: Optional[str] = None
    ref10: Optional[str] = None


# Schema for the full return type of verify_transaction
class VerifyTransactionResponse(BaseModel):
    status: str
    message: str
    raw_response: str
    parsed_response: DoubleVerificationParsedResponse


# Schema for the refund and cancellation API
class RefundRequest(BaseModel):
    refundRequest: str
    merchantId: str
    aggregatorId: str
