from enum import Enum as PyEnum


class PhonePePaymentStatus(PyEnum):
    PENDING = "pending"
    FAILED = "failed"
    COMPLETED = "completed"
