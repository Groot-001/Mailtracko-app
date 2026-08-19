$ErrorActionPreference = "Stop"

Write-Host "MailTracko Gmail diagnostic" -ForegroundColor Cyan
Write-Host "This does not print OAuth access tokens, refresh tokens, client secrets, or passwords."
Write-Host ""

$SenderEmail = "aadeshbudhathoki56@gmail.com"
$RecipientEmail = "aadeshbudhathoki3@gmail.com"

$python = @'
import asyncio
import os
import base64
from email.message import EmailMessage

import httpx
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from src.core.config.settings import config
from src.shared.infrastructure.encryption.fernet_encryption import decrypt


async def main():
    sender = os.environ["MT_SENDER"]
    recipient = os.environ["MT_RECIPIENT"]

    print("=== MAILTRACKO GMAIL DIAGNOSTIC ===")
    print("SENDER =", sender)
    print("RECIPIENT =", recipient)

    engine = create_async_engine(config.DATABASE_URL)

    async with engine.connect() as conn:
        account_result = await conn.execute(
            text("""
                SELECT
                    ea.id,
                    ea.email,
                    ea.status,
                    ea.health_status,
                    ea.health_score,
                    ea.oauth_config_id,
                    eoc.encrypted_refresh_token
                FROM email_accounts ea
                LEFT JOIN email_oauth_configs eoc
                    ON eoc.id = ea.oauth_config_id
                WHERE LOWER(ea.email) = LOWER(:email)
                  AND ea.deleted_at IS NULL
                ORDER BY ea.id DESC
                LIMIT 1
            """),
            {"email": sender},
        )
        row = account_result.mappings().first()

    await engine.dispose()

    if not row:
        print("ACCOUNT_FOUND = False")
        return

    print("ACCOUNT_FOUND = True")
    print("ACCOUNT_ID =", row["id"])
    print("ACCOUNT_STATUS =", row["status"])
    print("HEALTH_STATUS =", row["health_status"])
    print("HEALTH_SCORE =", row["health_score"])
    print("OAUTH_CONFIG_ID =", row["oauth_config_id"])

    encrypted = row["encrypted_refresh_token"]
    if not encrypted:
        print("REFRESH_TOKEN_STORED = False")
        return

    print("REFRESH_TOKEN_STORED = True")

    try:
        refresh_token = decrypt(encrypted)
    except Exception as exc:
        print("REFRESH_TOKEN_DECRYPT = FAILED")
        print("DECRYPT_ERROR_TYPE =", type(exc).__name__)
        return

    print("REFRESH_TOKEN_DECRYPT = OK")

    client_id = config.GOOGLE_MAIL_CLIENT_ID or config.GOOGLE_CLIENT_ID
    client_secret = config.GOOGLE_MAIL_CLIENT_SECRET or config.GOOGLE_CLIENT_SECRET

    async with httpx.AsyncClient(timeout=30) as client:
        token_response = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "client_id": client_id,
                "client_secret": client_secret,
                "refresh_token": refresh_token,
                "grant_type": "refresh_token",
            },
        )

        print("TOKEN_REFRESH_STATUS =", token_response.status_code)

        if token_response.status_code != 200:
            try:
                print("TOKEN_ERROR =", token_response.json())
            except Exception:
                print("TOKEN_ERROR =", token_response.text[:1500])
            return

        access_token = token_response.json().get("access_token")
        print("ACCESS_TOKEN_RECEIVED =", bool(access_token))

        if not access_token:
            return

        message = EmailMessage()
        message["From"] = sender
        message["To"] = recipient
        message["Subject"] = "MailTracko Gmail API Test"
        message.set_content(
            "MailTracko direct Gmail API diagnostic test after enabling Gmail API."
        )

        raw = base64.urlsafe_b64encode(message.as_bytes()).decode().rstrip("=")

        send_response = await client.post(
            "https://gmail.googleapis.com/gmail/v1/users/me/messages/send",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            },
            json={"raw": raw},
        )

        print("GMAIL_SEND_STATUS =", send_response.status_code)

        try:
            print("GMAIL_RESPONSE =", send_response.json())
        except Exception:
            print("GMAIL_RESPONSE =", send_response.text[:2000])


asyncio.run(main())
'@

$python | docker compose exec `
    -e MT_SENDER=$SenderEmail `
    -e MT_RECIPIENT=$RecipientEmail `
    -T api python -

Write-Host ""
Write-Host "=== RECENT API ERRORS ===" -ForegroundColor Cyan

docker compose logs api --since=5m --tail=400 2>&1 |
    Select-String -Pattern "gmail|Gmail|send|400|401|403|422|500|error|failed|traceback" -Context 3,8
