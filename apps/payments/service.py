from datetime import datetime
import random
import string
import logging
import traceback
from time import time
from typing import Annotated, Optional
from uuid import UUID as PyUUID
from sqlalchemy import select

from apps.donation.models import Donation
from apps.donation.schema import DonationStatus
from apps.payments.models import PhonePePaymentLog, SbiePayPaymentLog
from apps.payments.schema import PhonePePaymentStatus, SbiePayPaymentStatus
from apps.notifications.service import NotificationServiceDependency
from core.database.sqlalchamey.core import SessionDep
from core.exception.request import InvalidRequestException
from core.fastapi.dependency.service_dependency import AbstractService
from core.payment.phonepe.client import phonepe_client
from core.payment.sbiepay import sbiepay_client

logger = logging.getLogger(__name__)


class PaymentService(AbstractService):
    DEPENDENCIES = {
        "session": SessionDep,
        "notification_service": NotificationServiceDependency,
    }

    def __init__(
        self,
        session: SessionDep,
        notification_service: NotificationServiceDependency,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.session = session
        self.notification_service = notification_service

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

    async def get_phonepe_payment_status(self, order_id: str):
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
            previous_status = donation.status
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

            # Send email if status changed to completed
            if (
                previous_status != DonationStatus.COMPLETED.value
                and donation.status == DonationStatus.COMPLETED.value
            ):
                await self._send_donation_thank_you_email_safe(
                    donation, phonepe_payment_log
                )

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

            # Store previous status for email trigger
            previous_status = payment_log.payment_status

            # Update payment log with response data
            payment_log.sbiepay_ref_id = parsed_data.sbiepay_ref_id
            payment_log.sbiepay_response_data = response_data["raw_data"]
            payment_log.pay_mode = parsed_data.pay_mode
            payment_log.reason_message = parsed_data.reason_message
            payment_log.other_details = parsed_data.other_details
            payment_log.bank_code = parsed_data.bank_code
            payment_log.bank_reference_number = parsed_data.bank_reference_number
            payment_log.transaction_date = parsed_data.transaction_date

            # Map transaction status to our payment status
            if parsed_data.transaction_status == "SUCCESS":
                payment_log.payment_status = SbiePayPaymentStatus.SUCCESS.value
            elif parsed_data.transaction_status in ["FAILED", "FAIL"]:
                payment_log.payment_status = SbiePayPaymentStatus.FAILED.value
            else:
                payment_log.payment_status = SbiePayPaymentStatus.PENDING.value

            await self.session.commit()
            await self.session.refresh(payment_log)

            # Update donation status and send email if completed
            donation = await self._update_donation_status(
                payment_log.merchant_order_id, payment_log.payment_status
            )

            # Send email if payment just completed
            if (
                previous_status != SbiePayPaymentStatus.SUCCESS.value
                and payment_log.payment_status == SbiePayPaymentStatus.SUCCESS.value
                and donation
            ):
                await self._send_donation_thank_you_email_safe(donation, payment_log)

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

        # Store previous status for email trigger
        previous_status = payment_log.payment_status

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

            # Update donation status and send email if completed
            donation = await self._update_donation_status(
                order_id, payment_log.payment_status
            )

            # Send email if payment just completed
            if (
                previous_status != SbiePayPaymentStatus.SUCCESS.value
                and payment_log.payment_status == SbiePayPaymentStatus.SUCCESS.value
                and donation
            ):
                await self._send_donation_thank_you_email_safe(donation, payment_log)

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

        return payment_log

    # Unified method for getting payment status (works with both gateways)
    async def get_payment_status(self, order_id: str):
        """Get payment status from either PhonePe or SBIePay based on what's available"""
        # First check donation to know which provider
        donation = await self.session.scalar(
            select(Donation).where(Donation.order_id == order_id)
        )
        if not donation:
            raise InvalidRequestException("Donation details not found")

        if donation.payment_provider == "phonepe":
            return await self.get_phonepe_payment_status(order_id)
        elif donation.payment_provider == "sbiepay":
            return await self.get_sbiepay_payment_status(order_id)
        raise InvalidRequestException("Payment information not found")

    async def _update_donation_status(
        self, order_id: str, payment_status: str
    ) -> Optional[Donation]:
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

        return donation

    async def _send_donation_thank_you_email_safe(
        self, donation: Donation, payment_log
    ):
        """
        Safely send thank you email with comprehensive error handling.
        This method ensures email failures don't affect payment processing.

        Args:
            donation: Donation object
            payment_log: Payment log object (PhonePePaymentLog or SbiePayPaymentLog)
        """
        try:
            if donation.email:
                await self._send_donation_thank_you_email(donation, payment_log)
                logger.info(
                    f"Thank you email sent successfully for donation: {donation.id}, order: {donation.order_id}"
                )
        except Exception as e:
            # Log the error but don't raise it
            # This ensures payment processing continues even if email fails
            logger.error(
                f"Failed to send thank you email for donation {donation.id}, "
                f"order {donation.order_id}: {str(e)}"
            )
            logger.error(f"Email error traceback:\n{traceback.format_exc()}")

            # Optionally, try to log the email failure to database
            try:
                # The email log is already created by notification service
                # with failed status, so we don't need to do anything else
                pass
            except Exception as log_error:
                logger.error(
                    f"Failed to log email error for donation {donation.id}: {str(log_error)}"
                )

    async def _send_donation_thank_you_email(self, donation: Donation, payment_log):
        """
        Send thank you email after successful donation.

        Args:
            donation: Donation object
            payment_log: Payment log object (PhonePePaymentLog or SbiePayPaymentLog)

        Raises:
            Exception: If email sending fails (caught by _send_donation_thank_you_email_safe)
        """
        if not donation.email:
            return
        # Extract payment mode and details from payment log
        payment_mode = None
        payment_details = None

        # Handle PhonePe payment log
        if isinstance(payment_log, PhonePePaymentLog):
            if payment_log.phonepe_payment_details:
                if isinstance(payment_log.phonepe_payment_details, list):
                    if len(payment_log.phonepe_payment_details) > 0:
                        payment_details = payment_log.phonepe_payment_details[0]
                        payment_mode = payment_details.get("paymentMode")
                elif isinstance(payment_log.phonepe_payment_details, dict):
                    payment_mode = payment_log.phonepe_payment_details.get(
                        "paymentMode"
                    )

        # Handle SBIePay payment log
        elif isinstance(payment_log, SbiePayPaymentLog):
            payment_mode = payment_log.pay_mode
            # You can add more details from SBIePay if needed
            payment_details = {
                "paymentMode": payment_log.pay_mode,
                "bankCode": payment_log.bank_code,
                "bankReferenceNumber": payment_log.bank_reference_number,
            }

        # Prepare email context with all donation details
        context = {
            "full_name": donation.full_name,
            "order_id": donation.order_id,
            "amount": f"{donation.amount:,.2f}",
            "status": donation.status,
            "donation_date": donation.created_at.strftime("%B %d, %Y at %I:%M %p"),
            "need_g80_certificate": donation.need_g80_certificate,
            "payment_mode": payment_mode or "Online Payment",
            "year": datetime.now().year,
            "organization_name": "Sukrutha Keralam",
            "contact_email": "support@sukruthakeralam.org",
        }

        logger.info(
            f"Preparing to send thank you email to: {donation.email} "
            f"for order: {donation.order_id}"
        )

        # Send email using notification service
        email_log = await self.notification_service.send_donation_thank_you_email(
            donation_id=donation.id,
            recipient_email=donation.email,
            context=context,
        )

        if email_log.status == "sent":
            logger.info(
                f"Email successfully sent to {donation.email} "
                f"with message_id: {email_log.message_id}"
            )
        else:
            logger.warning(
                f"Email sending failed for {donation.email}. "
                f"Error: {email_log.error_message}"
            )
            # Even though email failed, we don't raise exception
            # The email_log already contains the failure details

    async def retry_failed_email(self, donation_id: str) -> bool:
        """
        Retry sending email for a specific donation.
        Useful for manual retry of failed emails.

        Args:
            donation_id: Donation ID to retry email for

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Get donation
            donation = await self.session.scalar(
                select(Donation).where(Donation.id == donation_id)
            )
            if not donation.email:
                return True

            if not donation:
                logger.error(f"Donation not found: {donation_id}")
                return False

            if donation.status != DonationStatus.COMPLETED.value:
                logger.error(
                    f"Cannot send email for non-completed donation: {donation_id}"
                )
                return False

            # Get payment log based on provider
            payment_log = None
            if donation.payment_provider == "phonepe":
                payment_log = await self.session.scalar(
                    select(PhonePePaymentLog).where(
                        PhonePePaymentLog.merchant_order_id == donation.order_id
                    )
                )
            elif donation.payment_provider == "sbiepay":
                payment_log = await self.session.scalar(
                    select(SbiePayPaymentLog).where(
                        SbiePayPaymentLog.merchant_order_id == donation.order_id
                    )
                )

            if not payment_log:
                logger.error(f"Payment log not found for donation: {donation_id}")
                return False

            # Send email
            await self._send_donation_thank_you_email(donation, payment_log)
            logger.info(f"Email retry successful for donation: {donation_id}")
            return True

        except Exception as e:
            logger.error(f"Email retry failed for donation {donation_id}: {str(e)}")
            logger.error(f"Retry error traceback:\n{traceback.format_exc()}")
            return False


PaymentServiceDependency = Annotated[PaymentService, PaymentService.get_dependency()]
