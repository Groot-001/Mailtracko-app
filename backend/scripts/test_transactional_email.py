"""Send one real transactional email using MailTracko's production email adapter."""
from __future__ import annotations

import argparse
import asyncio

from scripts.validate_runtime_config import validate_real_transactional_email
from src.shared.infrastructure.notification.adapter.email.email_notification import (
    EmailMessageData,
    EmailNotification,
)


async def _send(recipient: str) -> None:
    problems = validate_real_transactional_email()
    if problems:
        raise RuntimeError("; ".join(problems))

    await EmailNotification().send(
        EmailMessageData(
            subject="MailTracko real email delivery test",
            template_name="system/smtp_test.html",
            context={},
            recipient=[recipient],
        )
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--recipient", required=True, help="Real inbox that should receive the test email")
    args = parser.parse_args()
    recipient = args.recipient.strip()
    if "@" not in recipient:
        parser.error("--recipient must be a valid email address")

    asyncio.run(_send(recipient))
    print(f"SMTP test submitted successfully to {recipient}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
