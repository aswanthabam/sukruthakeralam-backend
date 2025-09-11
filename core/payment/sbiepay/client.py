import base64
import hashlib
import os
import requests
from Crypto.Cipher import AES
from decimal import Decimal

# Assuming your schemas are defined in a schemas.py file
from .schemas import (
    PaymentRequest,
    HandleResponse,
    SbiePayResponseData,
    VerifyTransactionResponse,
    DoubleVerificationParsedResponse,
)
from .settings import settings


class SbiePayClient:
    """
    A Python client for the SBIePay Aggregator-Hosted 'P' model integration.
    This class handles request formatting, encryption, and API calls for
    payments and status checks.
    """

    def __init__(self):
        """
        Initializes the client with all necessary configuration.

        Args:
            merchant_id: Your unique SBIePay merchant ID.
            encryption_key: Your merchant-specific AES encryption key.
            aggregator_id: The aggregator ID, always 'SBIEPAY'.
            success_url: The URL to which SBIePay redirects on successful payment.
            fail_url: The URL for failed payments.
            push_response_url: The Server-to-Server push response URL.
            sbiepay_gateway_url: The base URL for the transaction request.
            dv_query_url: The URL for the Double Verification/Query API.
        """
        self.merchant_id = settings.SBIEPAY_MERCHANT_ID
        self.encryption_key = settings.SBIEPAY_ENCRYPTION_KEY
        self.aggregator_id = settings.SBIEPAY_AGGREGATOR_ID
        self.success_url = settings.SBIEPAY_SUCCESS_URL
        self.fail_url = settings.SBIEPAY_FAIL_URL
        self.push_response_url = settings.SBIEPAY_PUSH_RESPONSE_URL
        self.sbiepay_gateway_url = settings.SBIEPAY_GATEWAY_URL
        self.dv_query_url = settings.SBIEPAY_DV_QUERY_URL

    def pad(self, byte_array):
        BLOCK_SIZE = 16
        pad_len = BLOCK_SIZE - len(byte_array) % BLOCK_SIZE
        return byte_array + (bytes([pad_len]) * pad_len)

    def unpad(self, byte_array):
        last_byte = byte_array[-1]
        return byte_array[0:-last_byte]

    def _encrypt(self, message, shaType="SHA256"):
        checksum256 = "SHA256"
        checksum512 = "SHA512"

        if shaType == checksum256:
            result = hashlib.sha256(message.encode())
        elif shaType == checksum512:
            result = hashlib.sha512(message.encode())
        else:
            result = hashlib.sha256(message.encode())

        concatePipe = message + "|" + result.hexdigest()
        byte_array = concatePipe.encode("UTF-8")
        padded = self.pad(byte_array)
        iv = os.urandom(AES.block_size)

        cipher = AES.new(self.encryption_key.encode("UTF-8"), AES.MODE_CBC, iv)

        encrypted = cipher.encrypt(padded)
        return base64.b64encode(iv + encrypted).decode("UTF-8")

    def _decrypt(self, message):
        byte_array = base64.b64decode(message)
        iv = byte_array[0:16]
        messagebytes = byte_array[16:]
        cipher = AES.new(self.encryption_key.encode("UTF-8"), AES.MODE_CBC, iv)
        decrypted_padded = cipher.decrypt(messagebytes)
        decrypted = self.unpad(decrypted_padded)
        return decrypted.decode("UTF-8")

    def create_payment_request(
        self, amount: float, order_id: str, customer_id: str
    ) -> PaymentRequest:
        """
        Creates and encrypts the transaction request for the 'P' model.
        Returns an instance of PaymentRequest model.
        """
        transaction_packet = (
            f"{self.merchant_id}|DOM|IN|INR|{amount}|NA|"
            f"{self.success_url}|{self.fail_url}|"
            f"{self.aggregator_id}|{order_id}|{customer_id}|NB|ONLINE|ONLINE"
        )
        encrypted_packet = self._encrypt(transaction_packet)
        return PaymentRequest(
            EncryptTrans=encrypted_packet,
            merchIdVal=self.merchant_id,
        )

    def verify_transaction(
        self, atrn: str = None, merchant_order_number: str = None, amount: float = None
    ) -> VerifyTransactionResponse:
        """
        Calls the Double Verification/Query API to confirm a transaction's status.
        This request is sent in plain text. Returns a VerifyTransactionResponse model.
        """
        if not (atrn or merchant_order_number):
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

        try:
            response = requests.post(self.dv_query_url, data=payload)
            response.raise_for_status()

            response_data = response.text.split("|")
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

            return VerifyTransactionResponse(
                status="success",
                message="Double verification successful",
                raw_response=response.text,
                parsed_response=parsed_data,
            )
        except requests.exceptions.RequestException as e:
            return VerifyTransactionResponse(
                status="error",
                message=f"API call failed: {e}",
                raw_response="",
                parsed_response=DoubleVerificationParsedResponse.construct(
                    _fields_set={"status": "error"}
                ),
            )
        except (IndexError, ValueError) as e:
            return VerifyTransactionResponse(
                status="error",
                message=f"Failed to parse API response: {e}",
                raw_response=response.text,
                parsed_response=DoubleVerificationParsedResponse.construct(
                    _fields_set={"status": "error"}
                ),
            )

    def handle_encrypted_response(self, encrypted_data: str) -> HandleResponse:
        """
        Decrypts an incoming response from SBIePay and returns a HandleResponse model.
        """
        try:
            decrypted_string = self._decrypt(encrypted_data)
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
            )

            return HandleResponse(
                status="success",
                raw_data=decrypted_string,
                parsed_data=parsed_data,
            )
        except Exception as e:
            return HandleResponse(
                status="error",
                message=f"Decryption failed: {e}",
                raw_data=encrypted_data,
                parsed_data=SbiePayResponseData.construct(
                    _fields_set={"transaction_status": "FAIL"}
                ),
            )
