from fastapi import APIRouter

from apps.donation.schema import DonationRequest, DonationStatusResponse
from apps.donation.service import DonationServiceDependency

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
):
    total_amount = await donation_service.total_donation_amount()
    return {"total_donation_amount": total_amount}
