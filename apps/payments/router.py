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
