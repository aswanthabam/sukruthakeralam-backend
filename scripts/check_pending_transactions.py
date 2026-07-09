#!/usr/bin/env python3
"""
Pending Transaction Status Checker (SBIePay)

Finds SBIePay payments still marked PENDING and re-checks their status
against the gateway, updating the payment log + donation status (and
firing the thank-you email) exactly like the normal callback flow does.

Meant to run every 30 minutes via cron to catch transactions where the
gateway's browser/webhook response never reached us (dropped callback,
user closed browser mid-payment, etc.) and the record would otherwise
sit as PENDING forever.

Run manually (uses the defaults below):
    python scripts/check_pending_transactions.py

Run manually with custom thresholds, e.g. to sweep everything regardless
of age for a one-off check:
    python scripts/check_pending_transactions.py --min-age-minutes 0 --max-age-hours 720

Crontab entry (every 30 minutes, adjust paths):
    */30 * * * * cd /path/to/project && /path/to/venv/bin/python scripts/check_pending_transactions.py >> logs/cron.log 2>&1
"""

import argparse
import asyncio
import logging
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Make apps/ and core/ importable regardless of cwd this is invoked from
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import select  # noqa: E402

from apps.notifications.service import NotificationService  # noqa: E402
from apps.payments.models import SbiePayPaymentLog  # noqa: E402
from apps.payments.schema import SbiePayPaymentStatus  # noqa: E402
from apps.payments.service import PaymentService  # noqa: E402
from core.database.sqlalchamey.core import AsyncSessionLocal  # noqa: E402

# --- Defaults (overridable via CLI flags — see --help) ---
# Don't re-check transactions younger than this — give the normal callback
# flow a chance to land first before we start hammering the gateway.
DEFAULT_MIN_AGE_MINUTES = 10
# Stop re-checking transactions older than this — beyond this age they're
# effectively abandoned/stale and unlikely to resolve; avoids the job
# growing unbounded and re-querying ancient rows forever.
DEFAULT_MAX_AGE_HOURS = 72
# -----------------------------------------------------------

os.makedirs(project_root / "logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(project_root / "logs" / "pending_transaction_check.log"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger("pending_transaction_check")

LOCK_FILE = project_root / "logs" / ".pending_check.lock"


def acquire_lock() -> bool:
    """Simple PID-file lock so overlapping cron runs don't stack up."""
    if LOCK_FILE.exists():
        try:
            pid = int(LOCK_FILE.read_text().strip())
            os.kill(pid, 0)  # raises OSError if process is not alive
            logger.warning(
                f"Another run (pid={pid}) appears to be in progress. Skipping."
            )
            return False
        except (ValueError, ProcessLookupError, PermissionError):
            pass  # stale lock file — process is gone, safe to continue
    LOCK_FILE.write_text(str(os.getpid()))
    return True


def release_lock() -> None:
    LOCK_FILE.unlink(missing_ok=True)


async def check_pending_transactions(min_age_minutes: int, max_age_hours: int) -> None:
    now = datetime.now(timezone.utc)
    newest_allowed = now - timedelta(minutes=min_age_minutes)
    oldest_allowed = now - timedelta(hours=max_age_hours)

    logger.info(
        f"Checking SBIePay pending transactions between "
        f"{oldest_allowed.isoformat()} and {newest_allowed.isoformat()} "
        f"(min_age_minutes={min_age_minutes}, max_age_hours={max_age_hours})"
    )

    stats = {
        "checked": 0,
        "resolved_success": 0,
        "resolved_failed": 0,
        "still_pending": 0,
        "errors": 0,
    }

    async with AsyncSessionLocal() as session:
        notification_service = NotificationService(session=session)
        payment_service = PaymentService(
            session=session, notification_service=notification_service
        )

        # --- SBIePay pending transactions ---
        sbiepay_pending = await session.scalars(
            select(SbiePayPaymentLog).where(
                SbiePayPaymentLog.payment_status == SbiePayPaymentStatus.PENDING.value,
                SbiePayPaymentLog.created_at <= newest_allowed,
                SbiePayPaymentLog.created_at >= oldest_allowed,
            )
        )
        for payment_log in sbiepay_pending:
            stats["checked"] += 1
            order_id = payment_log.merchant_order_id
            try:
                updated = await payment_service.get_sbiepay_payment_status(order_id)
                _record_result(updated.payment_status, order_id, stats)
            except Exception as e:
                stats["errors"] += 1
                logger.error(f"[SBIePay] Error checking {order_id}: {e}")

    logger.info(
        "Run complete — checked=%(checked)d resolved_success=%(resolved_success)d "
        "resolved_failed=%(resolved_failed)d still_pending=%(still_pending)d errors=%(errors)d"
        % stats
    )


def _record_result(new_status: str, order_id: str, stats: dict) -> None:
    if new_status == SbiePayPaymentStatus.SUCCESS.value:
        stats["resolved_success"] += 1
        logger.info(f"[SBIePay] {order_id} -> SUCCESS")
    elif new_status == SbiePayPaymentStatus.FAILED.value:
        stats["resolved_failed"] += 1
        logger.info(f"[SBIePay] {order_id} -> FAILED")
    else:
        stats["still_pending"] += 1
        logger.info(f"[SBIePay] {order_id} -> still pending")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Re-check pending SBIePay transactions against the gateway."
    )
    parser.add_argument(
        "--min-age-minutes",
        type=int,
        default=DEFAULT_MIN_AGE_MINUTES,
        help=(
            "Skip transactions younger than this (minutes). Gives the normal "
            f"callback a chance to land first. Default: {DEFAULT_MIN_AGE_MINUTES}"
        ),
    )
    parser.add_argument(
        "--max-age-hours",
        type=int,
        default=DEFAULT_MAX_AGE_HOURS,
        help=(
            "Skip transactions older than this (hours) — treated as abandoned. "
            f"Default: {DEFAULT_MAX_AGE_HOURS}"
        ),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if not acquire_lock():
        return 0
    try:
        asyncio.run(
            check_pending_transactions(
                min_age_minutes=args.min_age_minutes,
                max_age_hours=args.max_age_hours,
            )
        )
        return 0
    except Exception as e:
        logger.exception(f"Fatal error in pending transaction check: {e}")
        return 1
    finally:
        release_lock()


if __name__ == "__main__":
    sys.exit(main())
