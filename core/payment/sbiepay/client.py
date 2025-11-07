import base64
import hashlib
import logging
import os
from decimal import Decimal
from typing import Any, Dict, Optional

import aiohttp
from Crypto.Cipher import AES

# Assuming your schemas are defined in a schemas.py file
from .schemas import (
    CreateSbiePayPaymentResponse,
    PaymentRequest,
    HandleResponse,
    SbiePayResponseData,
    VerifyTransactionResponse,
    DoubleVerificationParsedResponse,
)
from .settings import settings


class SbiePayError(Exception):
    """Custom exception for SBIePay API errors"""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        response_data: Optional[Dict] = None,
    ):
        self.status_code = status_code
        self.response_data = response_data
        super().__init__(message)


class SbiePayClient:
    """
    A unified Python client for the SBIePay Aggregator-Hosted 'P' model integration.
    This class handles request formatting, encryption, API calls, and response
    decryption in a single, cohesive unit.
    """

    def __init__(self):
        """Initializes the client with necessary configuration and logging."""
        self.logger = logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO)
        self.logger.info(
            f"SBIePay: Running in {'Sandbox' if settings.DEBUG else 'Production'} mode"
        )

        self.merchant_id = settings.SBIEPAY_MERCHANT_ID
        self.encryption_key = settings.SBIEPAY_ENCRYPTION_KEY
        self.aggregator_id = settings.SBIEPAY_AGGREGATOR_ID
        self.success_url = settings.SBIEPAY_SUCCESS_URL
        self.fail_url = settings.SBIEPAY_FAIL_URL
        self.sbiepay_gateway_url = settings.SBIEPAY_GATEWAY_URL
        self.dv_query_url = settings.SBIEPAY_DV_QUERY_URL

    def _pad(self, byte_array: bytes) -> bytes:
        """Pads a byte array for AES encryption."""
        BLOCK_SIZE = 16
        pad_len = BLOCK_SIZE - len(byte_array) % BLOCK_SIZE
        return byte_array + (bytes([pad_len]) * pad_len)

    def _unpad(self, byte_array: bytes) -> bytes:
        """Unpads a byte array after AES decryption."""
        last_byte = byte_array[-1]
        return byte_array[0:-last_byte]

    def _encrypt(self, message: str, shaType: str = "SHA256") -> str:
        """Encrypts the message packet using AES."""
        try:
            if shaType == "SHA256":
                result = hashlib.sha256(message.encode()).hexdigest()
            elif shaType == "SHA512":
                result = hashlib.sha512(message.encode()).hexdigest()
            else:
                result = hashlib.sha256(message.encode()).hexdigest()

            concatePipe = message
            print(concatePipe)
            byte_array = concatePipe.encode("UTF-8")
            padded = self._pad(byte_array)
            iv = os.urandom(AES.block_size)

            cipher = AES.new(self.encryption_key.encode("UTF-8"), AES.MODE_CBC, iv)
            encrypted = cipher.encrypt(padded)
            return base64.b64encode(iv + encrypted).decode("UTF-8")
        except Exception as e:
            print(e)
            self.logger.error(f"Encryption failed: {e}")
            raise SbiePayError("Encryption failed during payment request creation.")

    def _decrypt(self, message: str) -> str:
        """Decrypts the message packet using AES."""
        try:
            byte_array = base64.b64decode(message)
            iv = byte_array[0:16]
            messagebytes = byte_array[16:]
            cipher = AES.new(self.encryption_key.encode("UTF-8"), AES.MODE_CBC, iv)
            decrypted_padded = cipher.decrypt(messagebytes)
            decrypted = self._unpad(decrypted_padded)
            return decrypted.decode("UTF-8")
        except Exception as e:
            self.logger.error(f"Decryption failed: {e}")
            raise SbiePayError("Decryption failed during response handling.")

    async def create_payment(
        self,
        merchant_order_id: str,
        amount: float,
        customer_id: str = "NA",
    ) -> CreateSbiePayPaymentResponse:
        """
        Creates a new payment request for SBIePay.

        Args:
            merchant_order_id: The merchant's unique order ID.
            amount: The transaction amount.
            customer_id: The customer ID.

        Returns:
            A CreateSbiePayPaymentResponse model with the necessary data
            for the frontend to submit the payment form.

        Raises:
            SbiePayError: If payment creation fails.
        """
        try:
            self.logger.info(
                f"Creating SBIePay payment: order_id={merchant_order_id}, amount={amount}"
            )

            transaction_packet = (
                f"{self.merchant_id}|DOM|IN|INR|{amount}|NA|"
                f"{self.success_url}|{self.fail_url}|"
                f"{self.aggregator_id}|{merchant_order_id}|{customer_id}|NB|ONLINE|ONLINE"
            )

            encrypted_packet = self._encrypt(transaction_packet)
            print("encrypted_packet:", encrypted_packet)
            print("decrypted_packet:", self._decrypt(encrypted_packet))

            payment_request = PaymentRequest(
                EncryptTrans=encrypted_packet,
                merchIdVal=self.merchant_id,
            )

            form_data = {
                "EncryptTrans": payment_request.EncryptTrans,
                "merchIdVal": payment_request.merchIdVal,
            }

            response = CreateSbiePayPaymentResponse(
                payment_form_data=form_data,
                gateway_url=self.sbiepay_gateway_url,
                merchant_order_id=merchant_order_id,
                encrypted_trans=payment_request.EncryptTrans,
            )

            self.logger.info(
                f"SBIePay payment created successfully: {merchant_order_id}"
            )
            return response

        except SbiePayError as e:
            raise e
        except Exception as e:
            self.logger.error(f"Failed to create SBIePay payment: {str(e)}")
            raise SbiePayError(f"Payment creation failed: {str(e)}")

    async def handle_payment_response(self, encrypted_response: str) -> Dict[str, Any]:
        """
        Handles and decrypts the response from the SBIePay gateway.

        Args:
            encrypted_response: The encrypted response string from SBIePay.

        Returns:
            A dictionary containing the status and parsed data of the response.

        Raises:
            SbiePayError: If response handling or decryption fails.
        """
        self.logger.info("Processing SBIePay response")

        try:
            decrypted_string = self._decrypt(encrypted_response)
            response_fields = decrypted_string.split("|")

            parsed_data = SbiePayResponseData(
                merchant_order_number=response_fields[0],
                sbiepay_ref_id=response_fields[1],
                transaction_status=response_fields[2],
                amount=Decimal(response_fields[3]),
                currency=response_fields[4],
                pay_mode=response_fields[5],
                other_details=response_fields[6],
                reason_message=response_fields[7],
                bank_code=response_fields[8],
                bank_reference_number=response_fields[9],
                transaction_date=response_fields[10],
                country=response_fields[11],
                cin=response_fields[12],
                merchent_id=response_fields[13],
                total_fee_gst=response_fields[14],
                ref1=response_fields[15] if len(response_fields) > 15 else None,
                ref2=response_fields[16] if len(response_fields) > 16 else None,
                ref3=response_fields[17] if len(response_fields) > 17 else None,
                ref4=response_fields[18] if len(response_fields) > 18 else None,
                ref5=response_fields[19] if len(response_fields) > 19 else None,
                ref6=response_fields[20] if len(response_fields) > 20 else None,
                ref7=response_fields[21] if len(response_fields) > 21 else None,
                ref8=response_fields[22] if len(response_fields) > 22 else None,
                ref9=response_fields[23] if len(response_fields) > 23 else None,
            )

            self.logger.info(
                f"SBIePay response processed successfully: {parsed_data.merchant_order_number}"
            )
            return {
                "status": "success",
                "data": parsed_data,
                "raw_data": decrypted_string,
            }

        except SbiePayError as e:
            self.logger.error(f"Failed to process SBIePay response: {e}")
            return {
                "status": "error",
                "message": str(e),
                "data": SbiePayResponseData.construct(
                    _fields_set={"transaction_status": "FAIL"}
                ),
            }
        except Exception as e:
            self.logger.error(f"Error handling SBIePay response: {str(e)}")
            raise SbiePayError(f"Response handling failed: {str(e)}")

    async def verify_transaction(
        self, atrn: str = None, merchant_order_number: str = None, amount: float = None
    ) -> VerifyTransactionResponse:
        """
        Verifies a transaction's status using the Double Verification/Query API.

        Args:
            atrn: The SBIePay transaction reference number.
            merchant_order_number: The merchant's order number.
            amount: The transaction amount.

        Returns:
            A VerifyTransactionResponse model with the verification details.

        Raises:
            SbiePayError: If transaction verification fails.
        """
        try:
            self.logger.info(
                f"Verifying SBIePay transaction: atrn={atrn}, order={merchant_order_number}"
            )

            if not (atrn or merchant_order_number):
                self.logger.warning("Verification request failed: Missing parameters.")
                return VerifyTransactionResponse(
                    status="error",
                    message="Either atrn or merchant_order_number is required.",
                    raw_response="",
                    parsed_response=DoubleVerificationParsedResponse.construct(
                        _fields_set={"status": "error"}
                    ),
                )

            query_request_string = (
                f"{atrn if atrn else ''}|{self.merchant_id}|"
                f"{merchant_order_number if merchant_order_number else ''}|"
                f"{amount if amount else ''}"
            )

            payload = {
                "queryRequest": query_request_string,
                "aggregatorId": self.aggregator_id,
                "merchantId": self.merchant_id,
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(self.dv_query_url, data=payload) as response:
                    response.raise_for_status()
                    response_text = await response.text()

            response_data = response_text.split("|")
            parsed_data = DoubleVerificationParsedResponse(
                merchant_id=response_data[0],
                atrn=response_data[1],
                transaction_status=response_data[2],
                country=response_data[3],
                currency=response_data[4],
                other_details=response_data[5],
                merchant_order_number=response_data[6],
                amount=Decimal(response_data[7]),
                status_description=response_data[8],
                bank_code=response_data[9],
                bank_reference_number=response_data[10],
                transaction_date=response_data[11],
                pay_mode=response_data[12],
                cin=response_data[13],
                merchant_id_from_response=response_data[14],
                total_fee_gst=response_data[15],
                ref1=response_data[16] if len(response_data) > 16 else None,
                ref2=response_data[17] if len(response_data) > 17 else None,
                ref3=response_data[18] if len(response_data) > 18 else None,
                ref4=response_data[19] if len(response_data) > 19 else None,
                ref5=response_data[20] if len(response_data) > 20 else None,
                ref6=response_data[21] if len(response_data) > 21 else None,
                ref7=response_data[22] if len(response_data) > 22 else None,
                ref8=response_data[23] if len(response_data) > 23 else None,
                ref9=response_data[24] if len(response_data) > 24 else None,
                ref10=response_data[25] if len(response_data) > 25 else None,
            )

            self.logger.info(
                f"Transaction verification successful: {parsed_data.transaction_status}"
            )
            return VerifyTransactionResponse(
                status="success",
                message="Double verification successful",
                raw_response=response_text,
                parsed_response=parsed_data,
            )

        except aiohttp.ClientError as e:
            self.logger.error(f"API call failed during verification: {e}")
            raise SbiePayError(f"API call failed: {e}")
        except (IndexError, ValueError) as e:
            self.logger.error(f"Failed to parse API response during verification: {e}")
            raise SbiePayError(f"Failed to parse API response: {e}")
        except Exception as e:
            self.logger.error(f"Error verifying transaction: {str(e)}")
            raise SbiePayError(f"Transaction verification failed: {str(e)}")
