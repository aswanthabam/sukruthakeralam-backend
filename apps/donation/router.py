from datetime import datetime
from fastapi import APIRouter, Body, Request

from apps.auth.dependency import AuthDependency
from apps.donation.schema import (
    DonationListResponse,
    DonationRequest,
    DonationStatusResponse,
    Form80SubmissionListResponse,
)
from apps.donation.service import DonationServiceDependency
from core.fastapi.response.pagination import (
    PaginatedResponse,
    PaginationParams,
    paginated_response,
)

router = APIRouter(
    prefix="/donation",
)


@router.post("/donate")
async def create_donation_endpoint(
    donation: DonationRequest, donation_service: "DonationServiceDependency"
):
    payment_log = await donation_service.submit_donation(donation_request=donation)
    return {
        "payment_url": payment_log.redirect_url,
        "merchant_order_id": payment_log.merchant_order_id,
        "amount": payment_log.amount,
    }


@router.get("/status/{order_id}")
async def get_donation_status_endpoint(
    order_id: str, donation_service: "DonationServiceDependency"
) -> DonationStatusResponse:
    donation, phonepe_log = await donation_service.get_donation_status(
        order_id=order_id
    )
    return {
        "order_id": donation.order_id,
        "full_name": donation.full_name,
        "amount": donation.amount,
        "status": donation.status,
        "need_g80_certificate": donation.need_g80_certificate,
        "payment_details": {
            "payment_status": phonepe_log.payment_status,
            "merchant_order_id": phonepe_log.merchant_order_id,
            "phonepe_order_id": phonepe_log.phonepe_order_id,
        },
        "donation": donation,
    }


@router.get("/total_amount")
async def get_total_donation_amount_endpoint(
    donation_service: "DonationServiceDependency",
    from_datetime: datetime | None = None,
    to_datetime: datetime | None = None,
):
    total_amount = await donation_service.total_donation_amount(
        from_datetime=from_datetime, to_datetime=to_datetime
    )
    return {"total_donation_amount": total_amount}


@router.get("/total_count")
async def get_total_donation_count_endpoint(
    donation_service: "DonationServiceDependency",
    from_datetime: datetime | None = None,
    to_datetime: datetime | None = None,
):
    total_count = await donation_service.total_donation_count(
        from_datetime=from_datetime, to_datetime=to_datetime
    )
    return {"total_donation_count": total_count}


@router.get("/total_form80_requests")
async def get_total_form80_requests_endpoint(
    donation_service: "DonationServiceDependency",
    from_datetime: datetime | None = None,
    to_datetime: datetime | None = None,
):
    total_count = await donation_service.total_form80_requests(
        from_datetime=from_datetime, to_datetime=to_datetime
    )
    return {"total_form80_requests": total_count}


@router.get("/list_donations")
async def list_donations_endpoint(
    request: Request,
    donation_service: "DonationServiceDependency",
    pagination: PaginationParams,
    auth: "AuthDependency",
    status: str | None = None,
    search: str | None = None,
    from_datetime: datetime | None = None,
    to_datetime: datetime | None = None,
) -> PaginatedResponse[DonationListResponse]:
    donations = await donation_service.list_donations(
        status=status,
        from_datetime=from_datetime,
        to_datetime=to_datetime,
        search=search,
        limit=pagination.limit,
        offset=pagination.offset,
    )
    return paginated_response(donations, request=request, schema=DonationListResponse)


@router.get("/list_form80_requests")
async def list_form80_requests_endpoint(
    request: Request,
    donation_service: "DonationServiceDependency",
    pagination: PaginationParams,
    auth: "AuthDependency",
    search: str | None = None,
    from_datetime: datetime | None = None,
    to_datetime: datetime | None = None,
    status: str | None = None,
) -> PaginatedResponse[Form80SubmissionListResponse]:
    form80_requests = await donation_service.list_form80_requests(
        from_datetime=from_datetime,
        to_datetime=to_datetime,
        status=status,
        search=search,
        limit=pagination.limit,
        offset=pagination.offset,
    )
    return paginated_response(
        form80_requests, request=request, schema=Form80SubmissionListResponse
    )


@router.post("/submit_form80/{form80_submission_id}")
async def update_form80_status_endpoint(
    form80_submission_id: str,
    donation_service: "DonationServiceDependency",
    auth: "AuthDependency",
    status: dict = Body(...),
):
    form80_submission = await donation_service.update_formg80_status(
        submission_id=form80_submission_id, new_status=status["status"]
    )
    return form80_submission


@router.get("/donation-details/{donation_id}")
async def get_donation_details_endpoint(
    donation_service: "DonationServiceDependency",
    auth: "AuthDependency",
    donation_id: str,
):
    donation, payment = await donation_service.get_donation_details(
        donation_id=donation_id
    )
    if not donation:
        return {"error": "Donation not found"}, 404
    if isinstance(payment.phonepe_payment_details, list):
        payment_details = payment.phonepe_payment_details[0]
    else:
        payment_details = payment.phonepe_payment_details
    return {
        "order_id": donation.order_id,
        "full_name": donation.full_name,
        "email": donation.email,
        "contact_number": donation.contact_number,
        "amount": donation.amount,
        "status": donation.status,
        "need_g80_certificate": donation.need_g80_certificate,
        "g80_certificate_id": (
            donation.g80_certificate.id if donation.g80_certificate else None
        ),
        "payment_details": {
            "payment_status": payment.payment_status,
            "merchant_order_id": payment.merchant_order_id,
            "phonepe_order_id": payment.phonepe_order_id,
            "payment_mode": (
                payment_details.get("paymentMode") if payment_details else None
            ),
        },
        "donation": donation,
    }
