import random
import string
from time import time
from typing import Annotated, Optional
from uuid import UUID as PyUUID
from sqlalchemy import select

from apps.donation.models import Donation
from apps.donation.schema import DonationStatus
from apps.payments.models import PhonePePaymentLog, SbiePayPaymentLog
from apps.payments.schema import PhonePePaymentStatus, SbiePayPaymentStatus
from core.database.sqlalchamey.core import SessionDep
from core.exception.request import InvalidRequestException
from core.fastapi.dependency.service_dependency import AbstractService
from core.payment.phonepe.client import phonepe_client
from core.payment.sbiepay import sbiepay_client


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

    # New SBI ePay methods
    async def create_sbiepay_payment(
        self,
        order_id: str,
        amount: float,
        customer_id: str = "NA",
    ):
        """Create a new SBIePay payment request"""
        response = await sbiepay_client.create_payment(
            merchant_order_id=order_id,
            amount=amount,
            customer_id=customer_id,
        )

        payment_log = SbiePayPaymentLog(
            merchant_order_id=order_id,
            encrypted_trans=response.encrypted_trans,
            payment_status=SbiePayPaymentStatus.PENDING.value,
            amount=amount,
            currency="INR",
            customer_id=customer_id,
        )

        self.session.add(payment_log)
        await self.session.commit()
        await self.session.refresh(payment_log)

        return {
            "payment_log": payment_log,
            "form_data": response.payment_form_data,
            "gateway_url": response.gateway_url,
        }

    async def handle_sbiepay_response(
        self, encrypted_response: str, order_id: str = None
    ):
        """Handle encrypted response from SBIePay gateway"""
        # Process the encrypted response
        response_data = await sbiepay_client.handle_payment_response(encrypted_response)

        if response_data["status"] == "success":
            parsed_data = response_data["data"]

            # Find the payment log
            payment_log = await self.session.scalar(
                select(SbiePayPaymentLog).where(
                    SbiePayPaymentLog.merchant_order_id
                    == parsed_data.merchant_order_number
                )
            )

            if not payment_log:
                if order_id:
                    # Try with provided order_id
                    payment_log = await self.session.scalar(
                        select(SbiePayPaymentLog).where(
                            SbiePayPaymentLog.merchant_order_id == order_id
                        )
                    )

                if not payment_log:
                    raise InvalidRequestException("Payment log not found")

            # Update payment log with response data
            payment_log.sbiepay_ref_id = parsed_data.sbiepay_ref_id
            payment_log.sbiepay_response_data = response_data["raw_data"]
            payment_log.pay_mode = parsed_data.pay_mode
            payment_log.reason_message = parsed_data.reason_message
            payment_log.other_details = parsed_data.other_details

            # Map transaction status to our payment status
            if parsed_data.transaction_status == "SUCCESS":
                payment_log.payment_status = SbiePayPaymentStatus.SUCCESS.value
            elif parsed_data.transaction_status in ["FAILED", "FAIL"]:
                payment_log.payment_status = SbiePayPaymentStatus.FAILED.value
            else:
                payment_log.payment_status = SbiePayPaymentStatus.PENDING.value

            await self.session.commit()
            await self.session.refresh(payment_log)

            # Update donation status
            await self._update_donation_status(
                payment_log.merchant_order_id, payment_log.payment_status
            )

            return payment_log
        else:
            raise InvalidRequestException(
                f"Failed to process payment response: {response_data.get('message')}"
            )

    async def verify_sbiepay_transaction(self, order_id: str, atrn: str = None):
        """Verify SBIePay transaction using Double Verification API"""
        payment_log = await self.session.scalar(
            select(SbiePayPaymentLog).where(
                SbiePayPaymentLog.merchant_order_id == order_id
            )
        )

        if not payment_log:
            raise InvalidRequestException("Payment information not found")

        # Use ATRN from payment log if not provided
        atrn_to_use = atrn or payment_log.sbiepay_ref_id

        verification_response = await sbiepay_client.verify_transaction(
            atrn=atrn_to_use, merchant_order_number=order_id, amount=payment_log.amount
        )

        if verification_response.status == "success":
            parsed_data = verification_response.parsed_response

            # Update payment log with verification data
            payment_log.double_verification_data = verification_response.raw_response
            payment_log.sbiepay_ref_id = parsed_data.atrn
            payment_log.bank_code = parsed_data.bank_code
            payment_log.bank_reference_number = parsed_data.bank_reference_number
            payment_log.transaction_date = parsed_data.transaction_date
            payment_log.pay_mode = parsed_data.pay_mode

            # Update payment status based on verification
            if parsed_data.transaction_status == "SUCCESS":
                payment_log.payment_status = SbiePayPaymentStatus.SUCCESS.value
            elif parsed_data.transaction_status in ["FAILED", "FAIL"]:
                payment_log.payment_status = SbiePayPaymentStatus.FAILED.value
            else:
                payment_log.payment_status = SbiePayPaymentStatus.PENDING.value

            await self.session.commit()
            await self.session.refresh(payment_log)

            # Update donation status
            await self._update_donation_status(order_id, payment_log.payment_status)

        return payment_log

    async def get_sbiepay_payment_status(self, order_id: str):
        """Get SBIePay payment status"""
        payment_log = await self.session.scalar(
            select(SbiePayPaymentLog).where(
                SbiePayPaymentLog.merchant_order_id == order_id
            )
        )

        if not payment_log:
            raise InvalidRequestException("Payment information not found")

        # Only perform verification if we have an ATRN (payment has been processed)
        if payment_log.sbiepay_ref_id:
            return await self.verify_sbiepay_transaction(order_id)

        # For new payments without ATRN, just return the current status
        return payment_log

    # Unified method for getting payment status (works with both gateways)
    async def get_payment_status(self, order_id: str):
        """Get payment status from either PhonePe or SBIePay based on what's available"""
        # First check PhonePe
        phonepe_log = await self.session.scalar(
            select(PhonePePaymentLog).where(
                PhonePePaymentLog.merchant_order_id == order_id
            )
        )

        if phonepe_log:
            return await self.get_phonepe_payment_status(order_id)

        # Then check SBIePay
        sbiepay_log = await self.session.scalar(
            select(SbiePayPaymentLog).where(
                SbiePayPaymentLog.merchant_order_id == order_id
            )
        )

        if sbiepay_log:
            return await self.get_sbiepay_payment_status(order_id)

        raise InvalidRequestException("Payment information not found")

    async def _update_donation_status(self, order_id: str, payment_status: str):
        """Helper method to update donation status based on payment status"""
        donation = await self.session.scalar(
            select(Donation).where(Donation.order_id == order_id)
        )

        if donation:
            if payment_status in [
                PhonePePaymentStatus.COMPLETED.value,
                SbiePayPaymentStatus.SUCCESS.value,
            ]:
                donation.status = DonationStatus.COMPLETED.value
            elif payment_status in [
                PhonePePaymentStatus.FAILED.value,
                SbiePayPaymentStatus.FAILED.value,
            ]:
                donation.status = DonationStatus.PAYMENT_FAILED.value
            else:
                donation.status = DonationStatus.PENDING.value

            await self.session.commit()
            await self.session.refresh(donation)


PaymentServiceDependency = Annotated[PaymentService, PaymentService.get_dependency()]
