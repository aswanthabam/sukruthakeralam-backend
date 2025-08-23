from fastapi import APIRouter, Query
from fastapi.responses import RedirectResponse

from apps.donation.service import DonationServiceDependency
from apps.payments.service import PaymentServiceDependency
from apps.settings import settings

router = APIRouter(
    prefix="/payments",
)


@router.get("/phonepe_redirect")
async def phonepe_redirect(
    payment_service: PaymentServiceDependency,
    order_id: str = Query(...),
):
    payment_log = await payment_service.get_payment_status(order_id)
    redirect_url = settings.FRONTEND_DOMAIN + "/thankyou?order_id=" + order_id
    return RedirectResponse(url=redirect_url)


@router.get("/payment_status/{order_id}")
async def get_payment_status(
    payment_service: PaymentServiceDependency,
    order_id: str,
):
    payment_log = await payment_service.get_payment_status(order_id)
    if not payment_log:
        return {"error": "Payment not found"}, 404
    return {
        "order_id": payment_log.order_id,
        "amount": payment_log.amount,
        "status": payment_log.payment_status,
        "created_at": payment_log.created_at,
        "updated_at": payment_log.updated_at,
    }
