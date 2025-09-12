from pydantic import BaseModel, Field
from typing import Any, Dict, Optional
from decimal import Decimal


class PaymentRequest(BaseModel):
    """Model for the initial payment request that gets sent to SBIePay gateway"""

    EncryptTrans: str
    merchIdVal: str


class SbiePayResponseData(BaseModel):
    """Model for the decrypted response data from SBIePay"""

    merchant_order_number: Optional[str] = None
    sbiepay_ref_id: Optional[str] = None  # ATRN
    transaction_status: Optional[str] = None
    amount: Optional[Decimal] = None
    currency: Optional[str] = None
    pay_mode: Optional[str] = None
    other_details: Optional[str] = None
    reason_message: Optional[str] = None

    class Config:
        validate_assignment = True


class HandleResponse(BaseModel):
    """Response model for handling encrypted responses from SBIePay"""

    status: str  # "success" or "error"
    message: Optional[str] = None
    raw_data: str
    parsed_data: SbiePayResponseData


class DoubleVerificationParsedResponse(BaseModel):
    """Model for parsing the Double Verification API response"""

    merchant_id: Optional[str] = None
    atrn: Optional[str] = None  # SBIePay reference ID
    transaction_status: Optional[str] = None
    country: Optional[str] = None
    currency: Optional[str] = None
    other_details: Optional[str] = None
    merchant_order_number: Optional[str] = None
    amount: Optional[Decimal] = None
    status_description: Optional[str] = None
    bank_code: Optional[str] = None
    bank_reference_number: Optional[str] = None
    transaction_date: Optional[str] = None
    pay_mode: Optional[str] = None
    cin: Optional[str] = None
    merchant_id_from_response: Optional[str] = None
    total_fee_gst: Optional[str] = None
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
    status: Optional[str] = None  # For error handling

    class Config:
        validate_assignment = True

    @classmethod
    def construct(cls, _fields_set: Dict[str, Any] = None, **kwargs):
        """Allow construction with limited fields for error cases"""
        instance = cls(**kwargs)
        if _fields_set:
            for field, value in _fields_set.items():
                setattr(instance, field, value)
        return instance


class VerifyTransactionResponse(BaseModel):
    """Response model for the Double Verification/Query API"""

    status: str  # "success" or "error"
    message: str
    raw_response: str
    parsed_response: DoubleVerificationParsedResponse


class CreateSbiePayPaymentRequest(BaseModel):
    """Request model for creating a new SBIePay payment"""

    order_id: str
    amount: float
    customer_id: str
    meta_info: Optional[Dict[str, Any]] = Field(default_factory=dict)


class CreateSbiePayPaymentResponse(BaseModel):
    """Response model for SBIePay payment creation"""

    payment_form_data: Dict[str, str]  # Form data to post to SBIePay gateway
    gateway_url: str
    merchant_order_id: str
    encrypted_trans: str
