"""
Unit tests for Email Service and Payment Service email functionality

Run with:
    pytest tests/test_email_service.py -v
    pytest tests/test_email_service.py::test_send_simple_email -v
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from core.notifications.email import EmailService
from apps.notifications.service import NotificationService
from apps.notifications.models import EmailLog
from apps.donation.models import Donation
from apps.donation.schema import DonationStatus
from apps.payments.models import SbiePayPaymentLog
from apps.payments.schema import SbiePayPaymentStatus
from apps.payments.service import PaymentService
from core.database.sqlalchamey.base import AbstractSQLModel


# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def email_service_mock():
    """Mock EmailService for testing"""
    service = Mock(spec=EmailService)

    # Mock successful email sending
    service.send_email = Mock(
        return_value={
            "success": True,
            "message_id": "mock-message-id-12345",
            "status": "sent",
            "recipient": "test@example.com",
        }
    )

    # Mock template email sending
    service.send_template_email = Mock(
        return_value={
            "success": True,
            "message_id": "mock-message-id-67890",
            "status": "sent",
            "recipient": "test@example.com",
        }
    )

    # Mock template rendering
    service.render_template = Mock(
        return_value=(
            "<html><body>Test Email</body></html>",
            "Test Email",
        )
    )

    return service


@pytest.fixture
async def async_session():
    """Create an in-memory async database session for testing"""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    async with engine.begin() as conn:
        await conn.run_sync(AbstractSQLModel.metadata.create_all)

    async_session_maker = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session_maker() as session:
        yield session

    await engine.dispose()


@pytest.fixture
def sample_donation():
    """Create a sample donation for testing"""
    return Donation(
        id="donation-123",
        order_id="SK-1234567890ABCD",
        full_name="Test User",
        email="test@example.com",
        contact_number="9876543210",
        amount=1000.0,
        need_g80_certificate=True,
        confirmed_terms=True,
        status=DonationStatus.COMPLETED.value,
        created_at=datetime.now(timezone.utc),
    )


@pytest.fixture
def sample_payment_log():
    """Create a sample SBIePay payment log for testing"""
    return SbiePayPaymentLog(
        id="payment-123",
        merchant_order_id="SK-1234567890ABCD",
        encrypted_trans="encrypted_data",
        payment_status=SbiePayPaymentStatus.SUCCESS.value,
        amount=1000.0,
        currency="INR",
        customer_id="customer-123",
        pay_mode="Credit Card",
        bank_code="SBI",
        bank_reference_number="REF123456",
        created_at=datetime.now(timezone.utc),
    )


# ============================================================================
# EMAIL SERVICE TESTS
# ============================================================================


class TestEmailService:
    """Test EmailService class"""

    def test_email_service_initialization(self):
        """Test EmailService initialization"""
        service = EmailService(
            aws_access_key_id="test_key",
            aws_secret_access_key="test_secret",
            aws_region="us-east-1",
            sender_email="sender@example.com",
            templates_dir="templates/emails",
        )

        assert service.sender_email == "sender@example.com"
        assert service.templates_dir is not None

    @patch("boto3.client")
    def test_send_email_success(self, mock_boto_client):
        """Test successful email sending"""
        # Mock SES client
        mock_ses = MagicMock()
        mock_ses.send_email.return_value = {"MessageId": "test-message-id-123"}
        mock_boto_client.return_value = mock_ses

        service = EmailService(
            aws_access_key_id="test_key",
            aws_secret_access_key="test_secret",
            aws_region="us-east-1",
            sender_email="sender@example.com",
        )

        result = service.send_email(
            recipient_email="test@example.com",
            subject="Test Subject",
            html_body="<html>Test</html>",
            text_body="Test",
        )

        assert result["success"] is True
        assert result["message_id"] == "test-message-id-123"
        assert result["status"] == "sent"

    @patch("boto3.client")
    def test_send_email_failure(self, mock_boto_client):
        """Test email sending failure"""
        from botocore.exceptions import ClientError

        # Mock SES client to raise error
        mock_ses = MagicMock()
        mock_ses.send_email.side_effect = ClientError(
            {"Error": {"Code": "MessageRejected", "Message": "Email rejected"}},
            "SendEmail",
        )
        mock_boto_client.return_value = mock_ses

        service = EmailService(
            aws_access_key_id="test_key",
            aws_secret_access_key="test_secret",
            aws_region="us-east-1",
            sender_email="sender@example.com",
        )

        result = service.send_email(
            recipient_email="test@example.com",
            subject="Test Subject",
            html_body="<html>Test</html>",
        )

        assert result["success"] is False
        assert result["status"] == "failed"
        assert "MessageRejected" in result["error_code"]


# ============================================================================
# NOTIFICATION SERVICE TESTS
# ============================================================================


class TestNotificationService:
    """Test NotificationService class"""

    @pytest.mark.asyncio
    async def test_send_email_creates_log(self, async_session, email_service_mock):
        """Test that sending email creates a log entry"""
        with patch.object(
            NotificationService, "__init__", lambda self, session, **kwargs: None
        ):
            service = NotificationService(session=async_session)
            service.session = async_session
            service.email_service = email_service_mock

            email_log = await service.send_email(
                recipient_email="test@example.com",
                subject="Test Subject",
                html_body="<html>Test</html>",
                mail_type="test",
            )

            assert email_log is not None
            assert email_log.recipient_email == "test@example.com"
            assert email_log.status == "sent"
            assert email_log.message_id == "mock-message-id-12345"

    @pytest.mark.asyncio
    async def test_send_template_email(self, async_session, email_service_mock):
        """Test sending template email"""
        with patch.object(
            NotificationService, "__init__", lambda self, session, **kwargs: None
        ):
            service = NotificationService(session=async_session)
            service.session = async_session
            service.email_service = email_service_mock

            context = {
                "full_name": "Test User",
                "order_id": "SK-123",
                "amount": "1,000.00",
            }

            email_log = await service.send_template_email(
                recipient_email="test@example.com",
                subject="Thank You",
                template_name="donation_thank_you.html",
                context=context,
                mail_type="donation_thank_you",
            )

            assert email_log is not None
            assert email_log.status == "sent"
            assert email_log.mail_type == "donation_thank_you"

    @pytest.mark.asyncio
    async def test_email_failure_is_logged(self, async_session):
        """Test that email failures are properly logged"""
        # Mock failing email service
        email_service_mock = Mock(spec=EmailService)
        email_service_mock.send_email = Mock(
            return_value={
                "success": False,
                "error_message": "Email sending failed",
                "status": "failed",
            }
        )

        with patch.object(
            NotificationService, "__init__", lambda self, session, **kwargs: None
        ):
            service = NotificationService(session=async_session)
            service.session = async_session
            service.email_service = email_service_mock

            email_log = await service.send_email(
                recipient_email="test@example.com",
                subject="Test Subject",
                html_body="<html>Test</html>",
                mail_type="test",
            )

            assert email_log.status == "failed"
            assert email_log.error_message == "Email sending failed"


# ============================================================================
# PAYMENT SERVICE EMAIL TESTS
# ============================================================================


class TestPaymentServiceEmail:
    """Test PaymentService email functionality"""

    @pytest.mark.asyncio
    async def test_send_thank_you_email_safe_success(
        self, async_session, sample_donation, sample_payment_log
    ):
        """Test that _send_donation_thank_you_email_safe handles success"""
        # Mock notification service
        notification_service_mock = AsyncMock(spec=NotificationService)
        notification_service_mock.send_donation_thank_you_email = AsyncMock(
            return_value=Mock(status="sent", message_id="msg-123", error_message=None)
        )

        with patch.object(
            PaymentService,
            "__init__",
            lambda self, session, notification_service, **kwargs: None,
        ):
            service = PaymentService(
                session=async_session,
                notification_service=notification_service_mock,
            )
            service.session = async_session
            service.notification_service = notification_service_mock

            # Should not raise any exception
            await service._send_donation_thank_you_email_safe(
                sample_donation, sample_payment_log
            )

            # Verify email was attempted
            notification_service_mock.send_donation_thank_you_email.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_thank_you_email_safe_handles_failure(
        self, async_session, sample_donation, sample_payment_log
    ):
        """Test that _send_donation_thank_you_email_safe handles email failures gracefully"""
        # Mock notification service to raise exception
        notification_service_mock = AsyncMock(spec=NotificationService)
        notification_service_mock.send_donation_thank_you_email = AsyncMock(
            side_effect=Exception("Email service unavailable")
        )

        with patch.object(
            PaymentService,
            "__init__",
            lambda self, session, notification_service, **kwargs: None,
        ):
            service = PaymentService(
                session=async_session,
                notification_service=notification_service_mock,
            )
            service.session = async_session
            service.notification_service = notification_service_mock

            # Should not raise exception even though email fails
            try:
                await service._send_donation_thank_you_email_safe(
                    sample_donation, sample_payment_log
                )
                exception_raised = False
            except Exception:
                exception_raised = True

            assert exception_raised is False

    @pytest.mark.asyncio
    async def test_send_thank_you_email_context(
        self, async_session, sample_donation, sample_payment_log
    ):
        """Test that email context is properly formatted"""
        notification_service_mock = AsyncMock(spec=NotificationService)

        with patch.object(
            PaymentService,
            "__init__",
            lambda self, session, notification_service, **kwargs: None,
        ):
            service = PaymentService(
                session=async_session,
                notification_service=notification_service_mock,
            )
            service.session = async_session
            service.notification_service = notification_service_mock

            await service._send_donation_thank_you_email(
                sample_donation, sample_payment_log
            )

            # Get the call arguments
            call_args = (
                notification_service_mock.send_donation_thank_you_email.call_args
            )

            assert call_args is not None
            context = call_args.kwargs["context"]

            # Verify context contains required fields
            assert context["full_name"] == "Test User"
            assert context["order_id"] == "SK-1234567890ABCD"
            assert "1,000.00" in context["amount"]
            assert context["need_g80_certificate"] is True
            assert context["payment_mode"] is not None

    @pytest.mark.asyncio
    async def test_retry_failed_email_success(self, async_session, sample_donation):
        """Test retry_failed_email with successful donation"""
        # Add donation to session
        async_session.add(sample_donation)
        await async_session.commit()

        # Mock notification service
        notification_service_mock = AsyncMock(spec=NotificationService)
        notification_service_mock.send_donation_thank_you_email = AsyncMock(
            return_value=Mock(status="sent", message_id="msg-retry-123")
        )

        # Mock payment log
        payment_log = SbiePayPaymentLog(
            merchant_order_id=sample_donation.order_id,
            payment_status=SbiePayPaymentStatus.SUCCESS.value,
            amount=1000.0,
        )
        async_session.add(payment_log)
        await async_session.commit()

        with patch.object(
            PaymentService,
            "__init__",
            lambda self, session, notification_service, **kwargs: None,
        ):
            service = PaymentService(
                session=async_session,
                notification_service=notification_service_mock,
            )
            service.session = async_session
            service.notification_service = notification_service_mock

            result = await service.retry_failed_email(sample_donation.id)

            assert result is True

    @pytest.mark.asyncio
    async def test_retry_failed_email_donation_not_found(self, async_session):
        """Test retry_failed_email with non-existent donation"""
        notification_service_mock = AsyncMock(spec=NotificationService)

        with patch.object(
            PaymentService,
            "__init__",
            lambda self, session, notification_service, **kwargs: None,
        ):
            service = PaymentService(
                session=async_session,
                notification_service=notification_service_mock,
            )
            service.session = async_session
            service.notification_service = notification_service_mock

            result = await service.retry_failed_email("non-existent-id")

            assert result is False


# ============================================================================
# INTEGRATION TESTS
# ============================================================================


class TestEmailIntegration:
    """Integration tests for complete email flow"""

    @pytest.mark.asyncio
    async def test_complete_donation_email_flow(
        self, async_session, sample_donation, sample_payment_log
    ):
        """Test complete flow from donation completion to email sent"""
        # Add models to session
        async_session.add(sample_donation)
        async_session.add(sample_payment_log)
        await async_session.commit()

        # Mock notification service
        notification_service_mock = AsyncMock(spec=NotificationService)
        email_log_mock = Mock(
            status="sent",
            message_id="integration-test-msg-id",
            error_message=None,
        )
        notification_service_mock.send_donation_thank_you_email = AsyncMock(
            return_value=email_log_mock
        )

        with patch.object(
            PaymentService,
            "__init__",
            lambda self, session, notification_service, **kwargs: None,
        ):
            service = PaymentService(
                session=async_session,
                notification_service=notification_service_mock,
            )
            service.session = async_session
            service.notification_service = notification_service_mock

            # Simulate payment completion
            await service._send_donation_thank_you_email_safe(
                sample_donation, sample_payment_log
            )

            # Verify email was sent
            notification_service_mock.send_donation_thank_you_email.assert_called_once()

            call_kwargs = (
                notification_service_mock.send_donation_thank_you_email.call_args.kwargs
            )
            assert call_kwargs["donation_id"] == sample_donation.id
            assert call_kwargs["recipient_email"] == sample_donation.email


# ============================================================================
# MANUAL TEST SCRIPT
# ============================================================================


async def manual_test_email_service():
    """
    Manual test script to verify email service with real AWS SES
    WARNING: This will send a real email!
    """
    print("=" * 80)
    print("MANUAL EMAIL SERVICE TEST")
    print("=" * 80)

    # Initialize email service with real credentials
    # Make sure to set these environment variables or replace with actual values
    import os

    email_service = EmailService(
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID", "your_key"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY", "your_secret"),
        aws_region=os.getenv("AWS_REGION", "us-east-1"),
        sender_email=os.getenv("SES_SENDER_EMAIL", "noreply@example.com"),
        templates_dir="templates/emails",
    )

    # Test 1: Send simple email
    print("\n[TEST 1] Sending simple email...")
    result = email_service.send_email(
        recipient_email="test@example.com",
        subject="Test Email from Unit Test",
        html_body="<html><body><h1>Test Email</h1><p>This is a test.</p></body></html>",
        text_body="Test Email\n\nThis is a test.",
    )
    print(f"Result: {result}")

    # Test 2: Send template email
    print("\n[TEST 2] Sending template email...")
    context = {
        "full_name": "Test User",
        "order_id": "TEST-123",
        "amount": "1,000.00",
        "status": "completed",
        "donation_date": "January 1, 2025 at 12:00 PM",
        "need_g80_certificate": True,
        "payment_mode": "Test Mode",
        "year": 2025,
    }

    try:
        result = email_service.send_template_email(
            recipient_email="test@example.com",
            subject="Thank You for Your Donation - Test",
            template_name="donation_thank_you.html",
            context=context,
        )
        print(f"Result: {result}")
    except Exception as e:
        print(f"Error: {e}")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    # Run pytest tests
    pytest.main([__file__, "-v"])

    # Uncomment to run manual test (requires AWS credentials)
    # asyncio.run(manual_test_email_service())
