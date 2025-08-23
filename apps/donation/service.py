import base64
from datetime import datetime
import hashlib
import json
from sqlalchemy import distinct, func, select
from typing_extensions import Annotated
from fastapi.params import Depends
from cryptography.fernet import Fernet
from sqlalchemy.orm import joinedload

from apps.payments.models import PhonePePaymentLog
from apps.payments.service import PaymentServiceDependency
from core.database.sqlalchamey.core import SessionDep
from core.exception.request import InvalidRequestException
from core.fastapi.dependency.service_dependency import AbstractService
from apps.donation.schema import (
    DonationRequest,
    DonationStatus,
    FormG80SubmissionStatus,
)
from apps.donation.models import Donation, FormG80Submission
from apps.settings import settings


class DonationService(AbstractService):

    DEPENDENCIES = {"session": SessionDep, "payment_service": PaymentServiceDependency}

    def __init__(
        self, session: SessionDep, payment_service: PaymentServiceDependency, **kwargs
    ):
        super().__init__(**kwargs)
        self.session = session
        self.payment_service = payment_service

    async def submit_donation(
        self, donation_request: DonationRequest
    ) -> PhonePePaymentLog:
        donation = await self.create_donation(
            full_name=donation_request.full_name,
            email=donation_request.email,
            contact_number=donation_request.contact_number,
            amount=donation_request.amount,
            need_g80_certificate=donation_request.need_g80_certificate,
            confirmed_terms=donation_request.confirmed_terms,
        )
        if donation.need_g80_certificate and donation_request.form_g80:
            form80 = await self.submit_formg80(
                donation_id=donation.id,
                pan_number=donation_request.form_g80.pan_number,
                full_address=donation_request.form_g80.full_address,
                city=donation_request.form_g80.city,
                state=donation_request.form_g80.state,
                country=donation_request.form_g80.country,
                pin_code=donation_request.form_g80.pin_code,
            )
        # Encrypt the donation request
        # Ensure the secret key is a valid 32-byte URL-safe base64-encoded string
        secret_key = base64.urlsafe_b64encode(
            hashlib.sha256(settings.SECRET_KEY.encode()).digest()
        )
        fernet = Fernet(secret_key)
        encrypted_data = fernet.encrypt(
            json.dumps(donation_request.model_dump()).encode()
        )

        payment_log = await self.payment_service.create_phonepe_payment(
            order_id=donation.order_id,
            amount=donation.amount,
            meta_info={"data": encrypted_data.decode()},
            redirect_url=f"{settings.BACKEND_DOMAIN}/api/payments/phonepe_redirect?order_id={donation.order_id}",
            message="Sukrutha Keralam Donation",
        )
        return payment_log

    async def create_donation(
        self,
        full_name: str,
        email: str,
        contact_number: str,
        amount: float,
        need_g80_certificate: bool,
        confirmed_terms: bool,
    ):
        order_id = self.payment_service.generate_unique_string(prefix="SK")
        donation = Donation(
            order_id=order_id,
            full_name=full_name,
            email=email,
            contact_number=contact_number,
            amount=amount,
            need_g80_certificate=need_g80_certificate,
            confirmed_terms=confirmed_terms,
            status=DonationStatus.PENDING.value,
        )
        self.session.add(donation)
        await self.session.commit()
        await self.session.refresh(donation)
        return donation

    async def submit_formg80(
        self,
        donation_id: str,
        pan_number: str,
        full_address: str,
        city: str,
        state: str,
        country: str,
        pin_code: str,
    ):
        # existing_submission = await self.session.execute(
        #     self.session.query(FormG80Submission).filter(
        #         FormG80Submission.donation_id == donation_id
        #     )
        # )
        # existing_submission = existing_submission.scalar_one_or_none()
        # if existing_submission:
        #     raise ValueError("Form G80 submission already exists for this donation.")
        form_g80_submission = FormG80Submission(
            donation_id=donation_id,
            pan_number=pan_number,
            full_address=full_address,
            city=city,
            state=state,
            country=country,
            pin_code=pin_code,
            status=FormG80SubmissionStatus.PENDING.value,
        )
        self.session.add(form_g80_submission)
        await self.session.commit()
        await self.session.refresh(form_g80_submission)
        return form_g80_submission

    async def update_formg80_status(self, submission_id: int, new_status: str):
        form_g80_submission = await self.session.execute(
            select(FormG80Submission).filter(FormG80Submission.id == submission_id)
        )
        form_g80_submission = form_g80_submission.scalar_one_or_none()
        if not form_g80_submission:
            raise ValueError("Form G80 submission not found.")
        form_g80_submission.status = new_status
        await self.session.commit()
        await self.session.refresh(form_g80_submission)
        return form_g80_submission

    async def get_donation_status(self, order_id: str):
        donation = await self.session.scalar(
            select(Donation).where(Donation.order_id == order_id)
        )
        phonepe_log = await self.session.scalar(
            select(PhonePePaymentLog).where(
                PhonePePaymentLog.merchant_order_id == order_id
            )
        )
        return donation, phonepe_log

    async def get_donation_details(
        self, donation_id: str | None = None, order_id: str | None = None
    ):
        if donation_id is not None:
            donation = await self.session.scalar(
                select(Donation)
                .where(Donation.id == donation_id)
                .options(joinedload(Donation.g80_certificate))
            )
        elif order_id is not None:
            donation = await self.session.scalar(
                select(Donation)
                .where(Donation.order_id == order_id)
                .options(joinedload(Donation.g80_certificate))
            )
        else:
            raise InvalidRequestException(
                "Either donation_id or order_id must be provided."
            )
        if not donation:
            raise InvalidRequestException("Donation not found.")
        payment = await self.session.scalar(
            select(PhonePePaymentLog).where(
                PhonePePaymentLog.merchant_order_id == donation.order_id
            )
        )
        return donation, payment

    async def total_donation_amount(
        self, from_datetime: datetime | None = None, to_datetime: datetime | None = None
    ) -> float:
        query = select(func.sum(Donation.amount)).where(
            Donation.status == DonationStatus.COMPLETED.value
        )
        if from_datetime is not None:
            query = query.where(Donation.created_at >= from_datetime)
        if to_datetime is not None:
            query = query.where(Donation.created_at <= to_datetime)
        total = await self.session.scalar(query)
        return total or 0.0

    async def total_donation_count(
        self, from_datetime: datetime | None = None, to_datetime: datetime | None = None
    ) -> int:
        query = select(func.count(distinct(Donation.id))).where(
            Donation.status == DonationStatus.COMPLETED.value
        )
        if from_datetime is not None:
            query = query.where(Donation.created_at >= from_datetime)
        if to_datetime is not None:
            query = query.where(Donation.created_at <= to_datetime)
        total = await self.session.scalar(query)
        return total or 0

    async def total_form80_requests(
        self, from_datetime: datetime | None = None, to_datetime: datetime | None = None
    ) -> int:
        query = select(func.count(distinct(Donation.id))).where(
            Donation.status == DonationStatus.COMPLETED.value,
            Donation.need_g80_certificate == True,
        )

        if from_datetime is not None:
            query = query.where(FormG80Submission.created_at >= from_datetime)
        if to_datetime is not None:
            query = query.where(FormG80Submission.created_at <= to_datetime)

        total = await self.session.scalar(query)
        return total or 0

    async def list_donations(
        self,
        from_datetime: datetime | None = None,
        to_datetime: datetime | None = None,
        search: str | None = None,
        status: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ):
        query = (
            select(Donation)
            .options(joinedload(Donation.g80_certificate))
            .order_by(Donation.created_at.desc())
        )
        if from_datetime is not None:
            query = query.where(Donation.created_at >= from_datetime)
        if to_datetime is not None:
            query = query.where(Donation.created_at <= to_datetime)
        if status is not None:
            query = query.where(Donation.status == status)
        if search is not None:
            query = query.where(
                Donation.full_name.ilike(f"%{search}%")
                | Donation.email.ilike(f"%{search}%")
                | Donation.contact_number.ilike(f"%{search}%")
                | Donation.order_id.ilike(f"%{search}%")
            )
        if offset is not None:
            query = query.offset(offset)
        if limit is not None:
            query = query.limit(limit)

        donations = await self.session.execute(query)
        return donations.scalars().all()

    async def list_form80_requests(
        self,
        from_datetime: datetime | None = None,
        to_datetime: datetime | None = None,
        search: str | None = None,
        status: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ):
        query = (
            select(FormG80Submission)
            .options(joinedload(FormG80Submission.donation))
            .where(
                Donation.status == DonationStatus.COMPLETED.value,
                Donation.need_g80_certificate == True,
            )
            .join(Donation, FormG80Submission.donation_id == Donation.id)
            .order_by(FormG80Submission.created_at.desc())
        )
        if from_datetime is not None:
            query = query.where(FormG80Submission.created_at >= from_datetime)
        if to_datetime is not None:
            query = query.where(FormG80Submission.created_at <= to_datetime)
        if status is not None:
            query = query.where(FormG80Submission.status == status)
        if search is not None:
            query = query.where(
                FormG80Submission.pan_number.ilike(f"%{search}%")
                | FormG80Submission.full_address.ilike(f"%{search}%")
                | FormG80Submission.city.ilike(f"%{search}%")
                | FormG80Submission.state.ilike(f"%{search}%")
                | FormG80Submission.country.ilike(f"%{search}%")
                | FormG80Submission.pin_code.ilike(f"%{search}%")
            )
        if offset is not None:
            query = query.offset(offset)
        if limit is not None:
            query = query.limit(limit)

        form80_requests = await self.session.execute(query)
        return form80_requests.scalars().all()


DonationServiceDependency = Annotated[DonationService, DonationService.get_dependency()]
