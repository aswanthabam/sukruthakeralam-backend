import asyncio
import time
from typing import List, Optional, Dict, Any, Union
from enum import Enum
import aiohttp
from pydantic import BaseModel, Field
import logging
from apps.settings import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PhonePePaymentState(str, Enum):
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    EXPIRED = "EXPIRED"


class PhonePePaymentMode(str, Enum):
    PRODUCTION = "production"
    SANDBOX = "sandbox"


class PhonePeError(Exception):
    """Custom exception for PhonePe API errors"""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        response_data: Optional[Dict] = None,
    ):
        self.status_code = status_code
        self.response_data = response_data
        super().__init__(message)


class AuthTokenResponse(BaseModel):
    access_token: str
    expires_at: int
    token_type: str = "Bearer"


class PaymentFlowConfig(BaseModel):
    type: str = "PG_CHECKOUT"
    message: str
    merchant_urls: Dict[str, str] = Field(..., alias="merchantUrls")


class CreatePaymentRequest(BaseModel):
    merchant_order_id: str = Field(..., alias="merchantOrderId")
    amount: int
    expire_after: int = Field(..., alias="expireAfter")
    meta_info: Optional[Dict[str, Any]] = Field(default_factory=dict, alias="metaInfo")
    payment_flow: PaymentFlowConfig = Field(..., alias="paymentFlow")

    class Config:
        populate_by_name = True


class CreatePaymentResponse(BaseModel):
    order_id: str = Field(..., alias="orderId")
    state: PhonePePaymentState
    expire_at: int = Field(..., alias="expireAt")
    redirect_url: str = Field(..., alias="redirectUrl")

    class Config:
        populate_by_name = True


class OrderStatusResponse(BaseModel):
    order_id: str = Field(..., alias="orderId")
    state: PhonePePaymentState
    amount: int
    expire_at: Optional[int] = Field(None, alias="expireAt")
    payment_details: Optional[List[Dict[str, Any]]] = Field(
        None, alias="paymentDetails"
    )

    class Config:
        populate_by_name = True


class PhonePeClient:
    """Async PhonePe Payment Gateway Client"""

    _SANDBOX_API_ENDPOINTS = {
        "AUTH_TOKEN": "https://api-preprod.phonepe.com/apis/pg-sandbox/v1/oauth/token",
        "CREATE_PAYMENT": "https://api-preprod.phonepe.com/apis/pg-sandbox/checkout/v2/pay",
        "ORDER_STATUS": "https://api-preprod.phonepe.com/apis/pg-sandbox/checkout/v2/order/{merchant_order_id}/status",
    }

    _PROD_API_ENDPOINTS = {
        "AUTH_TOKEN": "https://api.phonepe.com/apis/identity-manager/v1/oauth/token",
        "CREATE_PAYMENT": "https://api.phonepe.com/apis/pg/checkout/v2/pay",
        "ORDER_STATUS": "https://api.phonepe.com/apis/pg/checkout/v2/order/{merchant_order_id}/status",
    }

    def __init__(
        self,
        client_id: str = settings.PHONEPE_CLIENT_ID,
        client_secret: str = settings.PHONEPE_CLIENT_SECRET,
        client_version: int = 1,
        timeout: int = 30,
    ):
        if not settings.DEBUG:
            print(f"Phonepe: Running in Production mode [{settings.DEBUG}]")
        else:
            print(f"Phonepe: Running in Sandbox mode [{settings.DEBUG}]")
        self._endpoints = (
            self._PROD_API_ENDPOINTS
            if not settings.DEBUG
            else self._SANDBOX_API_ENDPOINTS
        )
        self._client_id = client_id
        self._client_secret = client_secret
        self._client_version = client_version
        self._timeout = timeout
        self._auth_token: Optional[str] = None
        self._auth_token_expiry: int = 0
        self._session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        """Async context manager entry"""
        await self._create_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self._close_session()

    async def _create_session(self) -> None:
        """Create aiohttp session with proper timeout"""
        if not self._session or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=self._timeout)
            self._session = aiohttp.ClientSession(timeout=timeout)

    async def _close_session(self) -> None:
        """Close aiohttp session"""
        if self._session and not self._session.closed:
            await self._session.close()

    async def _make_request(
        self,
        method: str,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        data: Optional[Union[str, Dict]] = None,
        json_data: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """Make HTTP request with proper error handling"""
        await self._create_session()

        try:
            async with self._session.request(
                method=method, url=url, headers=headers, data=data, json=json_data
            ) as response:
                response_data = await response.json()

                if response.status == 200:
                    return response_data
                else:
                    error_msg = f"API request failed: {response.status}"
                    if response_data:
                        error_msg += (
                            f" - {response_data.get('message', 'Unknown error')}"
                        )

                    logger.error(f"PhonePe API Error: {error_msg}")
                    raise PhonePeError(
                        message=error_msg,
                        status_code=response.status,
                        response_data=response_data,
                    )
        except (aiohttp.ContentTypeError, ValueError) as e:
            # Handle non-JSON responses
            response_text = await response.text()

            logger.error(f"Non-JSON response received: {response_text}")
            response_data = {
                "error": "Non-JSON response",
                "raw_response": response_text,
            }
        except aiohttp.ClientError as e:
            logger.error(f"Network error: {str(e)}")
            raise PhonePeError(f"Network error: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            raise PhonePeError(f"Unexpected error: {str(e)}")

    async def _get_auth_token(self) -> str:
        """Get authentication token from PhonePe API"""
        payload = (
            f"client_id={self._client_id}"
            f"&client_secret={self._client_secret}"
            f"&grant_type=client_credentials"
            f"&client_version={self._client_version}"
        )
        headers = {"Content-Type": "application/x-www-form-urlencoded"}

        try:
            response_data = await self._make_request(
                method="POST",
                url=self._endpoints["AUTH_TOKEN"],
                headers=headers,
                data=payload,
            )

            auth_response = AuthTokenResponse(**response_data)
            self._auth_token = auth_response.access_token
            self._auth_token_expiry = auth_response.expires_at

            logger.info("Successfully obtained auth token")
            return self._auth_token

        except Exception as e:
            logger.error(f"Failed to get auth token: {str(e)}")
            raise PhonePeError(f"Authentication failed: {str(e)}")

    def _is_token_valid(self) -> bool:
        """Check if current auth token is valid"""
        if not self._auth_token:
            return False

        current_time = int(time.time() * 1000)  # Epoch milliseconds
        return current_time < self._auth_token_expiry

    async def _ensure_auth_token(self) -> None:
        """Ensure we have a valid auth token"""
        if not self._is_token_valid():
            await self._get_auth_token()

    async def create_payment(
        self,
        merchant_order_id: str,
        amount: float,
        redirect_url: str,
        expire_after: int = settings.PHONEPE_PAYMENT_EXPIRY_SECONDS,
        meta_info: Optional[Dict[str, Any]] = None,
        message: str = "Payment message used for collect requests",
    ) -> CreatePaymentResponse:
        """
        Create a new payment order

        Args:
            merchant_order_id: Unique order ID from merchant
            amount: Payment amount in rupees (float)
            expire_after: Order expiry time in seconds
            redirect_url: URL to redirect after payment
            meta_info: Additional metadata
            message: Payment message

        Returns:
            CreatePaymentResponse: Payment creation response
        """
        try:
            await self._ensure_auth_token()

            payment_request = CreatePaymentRequest(
                merchantOrderId=merchant_order_id,
                amount=amount * 100,
                expireAfter=expire_after,
                metaInfo=meta_info or {},
                paymentFlow=PaymentFlowConfig(
                    message=message, merchantUrls={"redirectUrl": redirect_url}
                ),
            )

            headers = {
                "Content-Type": "application/json",
                "Authorization": f"O-Bearer {self._auth_token}",
            }

            response_data = await self._make_request(
                method="POST",
                url=self._endpoints["CREATE_PAYMENT"],
                headers=headers,
                json_data=payment_request.model_dump(by_alias=True),
            )

            payment_response = CreatePaymentResponse(**response_data)
            logger.info(f"Payment created successfully: {payment_response.order_id}")
            return payment_response

        except Exception as e:
            logger.error(f"Failed to create payment: {str(e)}")
            raise PhonePeError(f"Payment creation failed: {str(e)}")

    async def get_order_status(self, merchant_order_id: str) -> OrderStatusResponse:
        """
        Get order status by merchant order ID

        Args:
            merchant_order_id: Merchant's order ID

        Returns:
            OrderStatusResponse: Order status details
        """
        try:
            await self._ensure_auth_token()

            headers = {
                "Authorization": f"O-Bearer {self._auth_token}",
                "Content-Type": "application/json",
            }

            url = self._endpoints["ORDER_STATUS"].format(
                merchant_order_id=merchant_order_id
            )

            response_data = await self._make_request(
                method="GET", url=url, headers=headers
            )

            status_response = OrderStatusResponse(**response_data)
            logger.info(
                f"Order status retrieved: {merchant_order_id} - {status_response.state}"
            )
            return status_response

        except Exception as e:
            logger.error(f"Failed to get order status: {str(e)}")
            raise PhonePeError(f"Order status retrieval failed: {str(e)}")


phonepe_client = PhonePeClient()
