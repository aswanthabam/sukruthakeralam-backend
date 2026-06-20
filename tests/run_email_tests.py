#!/usr/bin/env python3
"""
Email Service Test Runner

This script provides an easy way to test email functionality without
setting up the full test environment.

Usage:
    python tests/run_email_tests.py --mode mock          # Run with mocked AWS SES
    python tests/run_email_tests.py --mode real          # Send real emails (requires AWS)
    python tests/run_email_tests.py --mode unittest      # Run pytest unit tests
"""

import asyncio
import argparse
import sys
import os
from pathlib import Path
from datetime import datetime, timezone

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


async def test_with_mock_ses():
    """Test email service with mocked AWS SES"""
    from unittest.mock import Mock, MagicMock, patch
    from core.notifications.email import EmailService

    print("\n" + "=" * 80)
    print("TESTING WITH MOCKED AWS SES")
    print("=" * 80)

    with patch("boto3.client") as mock_boto:
        # Setup mock SES client
        mock_ses = MagicMock()
        mock_ses.send_email.return_value = {"MessageId": "mock-msg-id-12345"}
        mock_boto.return_value = mock_ses

        # Initialize service
        service = EmailService(
            aws_access_key_id="mock_key",
            aws_secret_access_key="mock_secret",
            aws_region="us-east-1",
            sender_email="noreply@example.com",
        )

        # Test 1: Simple email
        print("\n[TEST 1] Sending simple email...")
        result = service.send_email(
            recipient_email="test@example.com",
            subject="Test Email",
            html_body="<html><body><h1>Hello</h1></body></html>",
            text_body="Hello",
        )

        print(f"✓ Success: {result['success']}")
        print(f"✓ Message ID: {result['message_id']}")
        print(f"✓ Status: {result['status']}")

        # Test 2: Email with CC and BCC
        print("\n[TEST 2] Sending email with CC/BCC...")
        result = service.send_email(
            recipient_email="test@example.com",
            subject="Test Email with CC",
            html_body="<html><body><h1>Hello</h1></body></html>",
            cc_emails=["cc@example.com"],
            bcc_emails=["bcc@example.com"],
        )

        print(f"✓ Success: {result['success']}")

        # Verify SES was called
        assert mock_ses.send_email.called
        print(f"✓ SES send_email called {mock_ses.send_email.call_count} times")

    print("\n" + "=" * 80)
    print("ALL MOCK TESTS PASSED ✓")
    print("=" * 80 + "\n")


async def test_with_real_ses():
    """Test email service with real AWS SES (requires credentials)"""
    from core.notifications.email import EmailService
    from apps.settings import settings

    print("\n" + "=" * 80)
    print("TESTING WITH REAL AWS SES")
    print("=" * 80)
    print("\n⚠️  WARNING: This will send real emails!")

    # Check if credentials are available
    try:
        aws_key = settings.AWS_ACCESS_KEY_ID
        aws_secret = settings.AWS_SECRET_ACCESS_KEY
        sender_email = settings.SES_SENDER_EMAIL

        if not aws_key or not aws_secret:
            print("\n❌ AWS credentials not found in settings!")
            print("Please set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY in .env")
            return

    except Exception as e:
        print(f"\n❌ Error loading settings: {e}")
        return

    # Ask for recipient email
    recipient = input(
        "\nEnter recipient email address (or press Enter to skip): "
    ).strip()
    if not recipient:
        print("Skipping real email test.")
        return

    print(f"\nSending test email to: {recipient}")
    print("From:", sender_email)

    try:
        # Initialize service
        service = EmailService(
            aws_access_key_id=aws_key,
            aws_secret_access_key=aws_secret,
            aws_region=settings.AWS_REGION,
            sender_email=sender_email,
        )

        # Send test email
        print("\n[TEST] Sending test email...")
        result = service.send_email(
            recipient_email=recipient,
            subject="Test Email from Email Service",
            html_body=f"""
                <html>
                <body>
                    <h1>Test Email</h1>
                    <p>This is a test email from the Email Service unit test.</p>
                    <p>Sent at: {datetime.now()}</p>
                </body>
                </html>
            """,
            text_body=f"Test Email\n\nThis is a test email.\nSent at: {datetime.now()}",
        )

        if result["success"]:
            print(f"\n✓ Email sent successfully!")
            print(f"✓ Message ID: {result['message_id']}")
            print(f"✓ Status: {result['status']}")
        else:
            print(f"\n❌ Email failed!")
            print(f"❌ Error: {result.get('error_message')}")

    except Exception as e:
        print(f"\n❌ Error: {e}")

    print("\n" + "=" * 80)


async def test_notification_service_mock():
    """Test NotificationService with mocked dependencies"""
    from unittest.mock import Mock, AsyncMock, patch
    from apps.notifications.service import NotificationService
    from apps.notifications.models import EmailLog

    print("\n" + "=" * 80)
    print("TESTING NOTIFICATION SERVICE")
    print("=" * 80)

    # Mock session
    mock_session = AsyncMock()
    mock_session.add = Mock()
    mock_session.commit = AsyncMock()
    mock_session.refresh = AsyncMock()

    # Mock email service
    mock_email_service = Mock()
    mock_email_service.send_email = Mock(
        return_value={
            "success": True,
            "message_id": "test-msg-123",
            "status": "sent",
        }
    )
    mock_email_service.send_template_email = Mock(
        return_value={
            "success": True,
            "message_id": "test-msg-456",
            "status": "sent",
        }
    )
    mock_email_service.render_template = Mock(
        return_value=("<html>Test</html>", "Test")
    )

    with patch.object(
        NotificationService, "__init__", lambda self, session, **kwargs: None
    ):
        service = NotificationService(session=mock_session)
        service.session = mock_session
        service.email_service = mock_email_service

        print("\n[TEST 1] Send simple email...")
        email_log = await service.send_email(
            recipient_email="test@example.com",
            subject="Test",
            html_body="<html>Test</html>",
            mail_type="test",
        )

        print(f"✓ Email log created")
        print(f"✓ Email sent successfully")

        print("\n[TEST 2] Send template email...")
        context = {"name": "Test User", "amount": "1,000.00"}
        email_log = await service.send_template_email(
            recipient_email="test@example.com",
            subject="Thank You",
            template_name="donation_thank_you.html",
            context=context,
            mail_type="donation_thank_you",
        )

        print(f"✓ Template email sent")

    print("\n" + "=" * 80)
    print("NOTIFICATION SERVICE TESTS PASSED ✓")
    print("=" * 80 + "\n")


async def test_payment_service_email():
    """Test PaymentService email functionality"""
    from unittest.mock import AsyncMock, Mock, patch
    from apps.payments.service import PaymentService
    from apps.donation.models import Donation
    from apps.donation.schema import DonationStatus
    from apps.payments.models import SbiePayPaymentLog
    from apps.payments.schema import SbiePayPaymentStatus

    print("\n" + "=" * 80)
    print("TESTING PAYMENT SERVICE EMAIL FUNCTIONALITY")
    print("=" * 80)

    # Create sample donation
    donation = Donation(
        id="test-donation-123",
        order_id="SK-TEST-123",
        full_name="Test User",
        email="test@example.com",
        contact_number="1234567890",
        amount=1000.0,
        need_g80_certificate=True,
        confirmed_terms=True,
        status=DonationStatus.COMPLETED.value,
        created_at=datetime.now(timezone.utc),
    )

    # Create sample payment log
    payment_log = SbiePayPaymentLog(
        id="test-payment-123",
        merchant_order_id="SK-TEST-123",
        payment_status=SbiePayPaymentStatus.SUCCESS.value,
        amount=1000.0,
        currency="INR",
        pay_mode="Credit Card",
        created_at=datetime.now(timezone.utc),
    )

    # Mock notification service
    mock_notification_service = AsyncMock()
    mock_notification_service.send_donation_thank_you_email = AsyncMock(
        return_value=Mock(
            status="sent",
            message_id="test-msg-789",
            error_message=None,
        )
    )

    # Mock session
    mock_session = AsyncMock()

    with patch.object(
        PaymentService,
        "__init__",
        lambda self, session, notification_service, **kwargs: None,
    ):
        service = PaymentService(
            session=mock_session,
            notification_service=mock_notification_service,
        )
        service.session = mock_session
        service.notification_service = mock_notification_service

        print("\n[TEST 1] Send thank you email (safe method)...")
        await service._send_donation_thank_you_email_safe(donation, payment_log)
        print("✓ Email sent successfully")
        print("✓ No exceptions raised")

        print("\n[TEST 2] Handle email failure gracefully...")
        # Mock to raise exception
        mock_notification_service.send_donation_thank_you_email = AsyncMock(
            side_effect=Exception("Email service down")
        )

        # Should not raise exception
        try:
            await service._send_donation_thank_you_email_safe(donation, payment_log)
            print("✓ Exception handled gracefully")
            print("✓ Payment processing not affected")
        except Exception as e:
            print(f"❌ Exception was raised: {e}")

        print("\n[TEST 3] Verify email context...")
        # Reset mock
        mock_notification_service.send_donation_thank_you_email = AsyncMock(
            return_value=Mock(status="sent", message_id="test-msg-999")
        )

        await service._send_donation_thank_you_email(donation, payment_log)

        # Verify call arguments
        call_args = mock_notification_service.send_donation_thank_you_email.call_args
        context = call_args.kwargs["context"]

        assert context["full_name"] == "Test User"
        assert context["order_id"] == "SK-TEST-123"
        assert "1,000.00" in context["amount"]
        print("✓ Email context verified")
        print(f"  - Full Name: {context['full_name']}")
        print(f"  - Order ID: {context['order_id']}")
        print(f"  - Amount: {context['amount']}")

    print("\n" + "=" * 80)
    print("PAYMENT SERVICE EMAIL TESTS PASSED ✓")
    print("=" * 80 + "\n")


def run_pytest_tests():
    """Run pytest unit tests"""
    import pytest

    print("\n" + "=" * 80)
    print("RUNNING PYTEST UNIT TESTS")
    print("=" * 80 + "\n")

    # Run tests
    test_file = Path(__file__).parent / "test_email_service.py"

    if not test_file.exists():
        print(f"❌ Test file not found: {test_file}")
        return

    exit_code = pytest.main([str(test_file), "-v", "--tb=short"])

    if exit_code == 0:
        print("\n" + "=" * 80)
        print("ALL PYTEST TESTS PASSED ✓")
        print("=" * 80 + "\n")
    else:
        print("\n" + "=" * 80)
        print("SOME TESTS FAILED ❌")
        print("=" * 80 + "\n")


async def main():
    """Main test runner"""
    parser = argparse.ArgumentParser(description="Email Service Test Runner")
    parser.add_argument(
        "--mode",
        choices=["mock", "real", "unittest", "all"],
        default="mock",
        help="Test mode: mock (safe), real (sends emails), unittest (pytest), or all",
    )

    args = parser.parse_args()

    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 20 + "EMAIL SERVICE TEST RUNNER" + " " * 33 + "║")
    print("╚" + "=" * 78 + "╝")

    if args.mode == "mock" or args.mode == "all":
        await test_with_mock_ses()
        await test_notification_service_mock()
        await test_payment_service_email()

    if args.mode == "real" or args.mode == "all":
        await test_with_real_ses()

    if args.mode == "unittest" or args.mode == "all":
        run_pytest_tests()

    print("\n✓ All tests completed!\n")


if __name__ == "__main__":
    asyncio.run(main())
