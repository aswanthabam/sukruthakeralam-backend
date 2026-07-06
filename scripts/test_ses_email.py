#!/usr/bin/env python3
"""
SES Integration Test Script

Sends one real test email through your existing EmailService, so you can
confirm SES + IAM role/credentials are wired up correctly end-to-end.

Run from the project root (so `apps` and `core` are importable), e.g.
inside the running container:

    docker compose -f docker-compose.prod.yml exec backend \
        python test_ses_email.py someone@example.com

or directly on the instance inside your venv:

    python test_ses_email.py someone@example.com

It also prints which credential source boto3 actually resolved
(explicit keys vs. IAM role/instance profile vs. none found), so you can
confirm the fallback is behaving the way you expect.
"""

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

# Make sure project root is importable when run from elsewhere
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))


def show_resolved_credentials(ses_client) -> None:
    """Report where boto3 actually pulled credentials from."""
    creds = ses_client._request_signer._credentials
    if creds is None:
        print("  Credential source : NONE FOUND (this call will fail)")
        return

    method = getattr(creds, "method", "unknown")
    source_map = {
        "explicit": "Explicit keys passed to boto3.client(...)",
        "env": "Environment variables",
        "shared-credentials-file": "~/.aws/credentials file",
        "container-role": "ECS container role",
        "iam-role": "EC2 instance profile / IAM role (via IMDS)",
        "assume-role": "Assumed role",
    }
    print(f"  Credential source : {source_map.get(method, method)}")
    print(f"  Access Key (masked): {creds.access_key[:4]}...{creds.access_key[-4:]}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Send a real test email via SES")
    parser.add_argument("email", help="Recipient email address to send the test to")
    parser.add_argument(
        "--subject",
        default="SES Integration Test",
        help="Subject line for the test email (default: 'SES Integration Test')",
    )
    args = parser.parse_args()

    print("=" * 70)
    print("SES INTEGRATION TEST")
    print("=" * 70)

    try:
        from apps.settings import settings
        from core.notifications.email import EmailService
    except ImportError as e:
        print(f"\n❌ Could not import project modules: {e}")
        print("   Run this script from the project root, inside the venv/container")
        print("   where 'apps' and 'core' packages are importable.")
        return 1

    print(f"\nRegion       : {settings.AWS_REGION}")
    print(f"Sender email : {settings.SES_SENDER_EMAIL}")
    print(
        f"Explicit keys in settings: "
        f"{'YES' if settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY else 'NO (expecting IAM role)'}"
    )

    service = EmailService(
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        aws_region=settings.AWS_REGION,
        sender_email=settings.SES_SENDER_EMAIL,
    )

    print("\nResolved credentials:")
    show_resolved_credentials(service.ses_client)

    print(f"\nSending test email to: {args.email}")
    result = service.send_email(
        recipient_email=args.email,
        subject=args.subject,
        html_body=(
            "<html><body>"
            "<h2>SES Integration Test</h2>"
            f"<p>This is a test email sent at {datetime.now(timezone.utc).isoformat()} UTC "
            "to confirm your SES + credential setup is working end-to-end.</p>"
            "</body></html>"
        ),
        text_body=(
            "SES Integration Test\n\n"
            f"This is a test email sent at {datetime.now(timezone.utc).isoformat()} UTC "
            "to confirm your SES + credential setup is working end-to-end."
        ),
    )

    print("\n" + "-" * 70)
    if result["success"]:
        print(f"✅ SUCCESS — Message ID: {result['message_id']}")
        print("-" * 70)
        return 0
    else:
        print(f"❌ FAILED — {result.get('error_code', '')} {result.get('error_message', '')}")
        print("-" * 70)
        print("\nCommon causes:")
        print("  - Recipient/sender not verified (SES sandbox mode)")
        print("  - IAM role/user missing ses:SendEmail permission")
        print("  - Wrong AWS_REGION (SES identity verified in a different region)")
        return 1


if __name__ == "__main__":
    sys.exit(main())
