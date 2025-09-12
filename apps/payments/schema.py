from enum import Enum as PyEnum


class PhonePePaymentStatus(PyEnum):
    PENDING = "pending"
    FAILED = "failed"
    COMPLETED = "completed"


class SbiePayPaymentStatus(PyEnum):
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    EXPIRED = "expired"
