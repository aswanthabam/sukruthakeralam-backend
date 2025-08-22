import random
import string
from time import time
from typing import Annotated

from sqlalchemy import select

from apps.donation.models import Donation
from apps.donation.schema import DonationStatus
from apps.payments.models import PhonePePaymentLog
from apps.payments.schema import PhonePePaymentStatus
from core.database.sqlalchamey.core import SessionDep
from core.exception.request import InvalidRequestException
from core.fastapi.dependency.service_dependency import AbstractService
from core.payment.phonepe.client import phonepe_client


class PaymentService(AbstractService):
    DEPENDENCIES = {"session": SessionDep}

    def __init__(self, session: SessionDep, **kwargs):
        super().__init__(**kwargs)
        self.session = session

    def generate_unique_string(self, prefix: str, sep="-") -> str:
        timestamp = int(time())  # current epoch time in seconds
        rand_suffix = "".join(
            random.choices(string.ascii_uppercase + string.digits, k=4)
        )
        return f"{prefix}{sep}{timestamp}{rand_suffix}"

    async def create_phonepe_payment(
        self,
        order_id: str,
        amount: float,
        meta_info: dict,
        redirect_url: str,
        message: str,
    ):
        response = await phonepe_client.create_payment(
            merchant_order_id=order_id,
            amount=amount,
            meta_info=meta_info,
            redirect_url=redirect_url,
            message=message,
        )
        payment_log = PhonePePaymentLog(
            merchant_order_id=order_id,
            phonepe_order_id=response.order_id,
            redirect_url=response.redirect_url,
            payment_status=PhonePePaymentStatus.PENDING.value,
            amount=amount,
            currency="INR",
        )
        self.session.add(payment_log)
        await self.session.commit()
        await self.session.refresh(payment_log)
        return payment_log

    async def get_payment_status(self, order_id: str):
        phonepe_payment_log = await self.session.scalar(
            select(PhonePePaymentLog).where(
                PhonePePaymentLog.merchant_order_id == order_id
            )
        )
        if not phonepe_payment_log:
            raise InvalidRequestException("Payment information not found")

        response = await phonepe_client.get_order_status(merchant_order_id=order_id)
        print("phonepe response:", response)
        if response.state.value == "COMPLETED":
            phonepe_payment_log.payment_status = PhonePePaymentStatus.COMPLETED.value
            pass
        elif response.state == "FAILED":
            phonepe_payment_log.payment_status = PhonePePaymentStatus.FAILED.value
            pass
        else:
            phonepe_payment_log.payment_status = PhonePePaymentStatus.PENDING.value

        if response.payment_details:
            phonepe_payment_log.phonepe_payment_details = response.payment_details

        await self.session.commit()
        await self.session.refresh(phonepe_payment_log)

        donation = await self.session.scalar(
            select(Donation).where(
                Donation.order_id == phonepe_payment_log.merchant_order_id
            )
        )
        if donation:
            donation.status = (
                DonationStatus.COMPLETED.value
                if phonepe_payment_log.payment_status
                == PhonePePaymentStatus.COMPLETED.value
                else (
                    DonationStatus.PAYMENT_FAILED.value
                    if phonepe_payment_log.payment_status
                    == PhonePePaymentStatus.FAILED.value
                    else DonationStatus.PENDING.value
                )
            )
            await self.session.commit()
            await self.session.refresh(donation)
        return phonepe_payment_log


PaymentServiceDependency = Annotated[PaymentService, PaymentService.get_dependency()]
