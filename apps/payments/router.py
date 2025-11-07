import logging
from fastapi import APIRouter, Query, Request
from fastapi.params import Body
from fastapi.responses import RedirectResponse

from apps.donation.service import DonationServiceDependency
from apps.payments.service import PaymentServiceDependency
from apps.settings import settings
from core.exception.request import InvalidRequestException

router = APIRouter(
    prefix="/payments",
)

logger = logging.getLogger(__name__)


@router.get("/phonepe_redirect")
async def phonepe_redirect(
    payment_service: PaymentServiceDependency,
    order_id: str = Query(...),
):
    payment_log = await payment_service.get_payment_status(order_id)
    redirect_url = settings.FRONTEND_DOMAIN + "/thankyou?order_id=" + order_id
    return RedirectResponse(url=redirect_url, status_code=303)


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


@router.post("/payment/sbiepay_success", description="SBIePay Success Callback")
async def sbiepay_success(request: Request, payment_service: PaymentServiceDependency):
    """
    Endpoint to handle SBIePay success callback.
    Expects encrypted response data in the request body.
    """
    try:
        form_data = await request.form()

        encrypted_response = form_data.get("encData")

        if not encrypted_response:
            logger.error("No encrypted response received in success callback")
            raise InvalidRequestException("Invalid response format")

        logger.info("Processing SBIePay success callback")

        # Process the encrypted response
        payment_log = await payment_service.handle_sbiepay_response(encrypted_response)

        # Redirect to frontend with success status
        redirect_url = f"{settings.FRONTEND_DOMAIN}/thankyou?order_id={payment_log.merchant_order_id}&status=success"
        return RedirectResponse(url=redirect_url, status_code=303)

    except Exception as e:
        logger.error(f"Error processing SBIePay success callback: {str(e)}")
        redirect_url = (
            f"{settings.FRONTEND_DOMAIN}/thankyou?message=Payment processing failed"
        )
        return RedirectResponse(url=redirect_url, status_code=303)


@router.post("/payment/sbiepay_failure", description="SBIePay Failure Callback")
async def sbiepay_failure(request: Request, payment_service: PaymentServiceDependency):
    """
    Endpoint to handle SBIePay failure callback.
    Expects encrypted response data in the request body.
    """
    try:
        form_data = await request.form()
        encrypted_response = form_data.get("encData")

        logger.info(f"Processing SBIePay failure callback for order")

        if not encrypted_response:
            logger.error("No encrypted response received in success callback")
            raise InvalidRequestException("Invalid response format")

        payment_log = await payment_service.handle_sbiepay_response(encrypted_response)
        order_id = payment_log.merchant_order_id
        redirect_url = (
            f"{settings.FRONTEND_DOMAIN}/thankyou?order_id={order_id}&status=failed"
        )
        return RedirectResponse(url=redirect_url, status_code=303)

        # Redirect to frontend with failure status

    except Exception as e:
        logger.error(f"Error processing SBIePay failure callback: {str(e)}")
        redirect_url = f"{settings.FRONTEND_DOMAIN}/thankyou?message=Payment failed"
        return RedirectResponse(url=redirect_url, status_code=303)


@router.post(
    "/payment/sbiepay_pushresponse", description="SBIePay Push Response Callback"
)
async def sbiepay_pushresponse(
    request: Request, payment_service: PaymentServiceDependency
):
    """
    Endpoint to handle SBIePay push response callback.
    Expects encrypted response data in the request body.
    """
    try:
        # Get form data from the request
        form_data = await request.form()

        # SBIePay sends encrypted response in 'msg' parameter
        encrypted_response = form_data.get("pushRespData")

        if not encrypted_response:
            logger.error("No encrypted response received in server callback")
            return {"status": "error", "message": "Invalid response format"}

        logger.info("Processing SBIePay server-to-server callback")

        # Process the encrypted response
        payment_log = await payment_service.handle_sbiepay_response(encrypted_response)

        # Perform double verification for final status
        verified_log = await payment_service.verify_sbiepay_transaction(
            payment_log.merchant_order_id, payment_log.sbiepay_ref_id
        )

        logger.info(
            f"SBIePay callback processed successfully for order: {verified_log.merchant_order_id}"
        )

        # Return success response to SBIePay
        return {"status": "success", "message": "Payment processed successfully"}

    except Exception as e:
        logger.error(f"Error processing SBIePay server callback: {str(e)}")
        return {"status": "error", "message": str(e)}
