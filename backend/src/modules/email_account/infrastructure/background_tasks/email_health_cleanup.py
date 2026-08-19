import asyncio
import json

from sqlalchemy import text

from src.core.config.settings import config
from src.modules.email_account.infrastructure.constants import SMTP_SSL_PORTS, SMTP_STARTTLS_PORTS
from src.modules.email_account.infrastructure.health.health_score import compute_health_score
from src.shared.infrastructure.db import async_session
from src.shared.infrastructure.logger import logger

HEALTH_CHECK_INTERVAL_SECONDS = config.EMAIL_HEALTH_CHECK_INTERVAL
STALE_RECONNECT_INTERVAL_SECONDS = config.EMAIL_STALE_RECONNECT_INTERVAL
EXPIRED_CLEANUP_INTERVAL_SECONDS = config.EMAIL_EXPIRED_CLEANUP_INTERVAL


async def process_health_check():
    """Test all active email accounts and update health status + score."""
    try:
        async with async_session() as session:
            result = await session.execute(
                text(
                    "SELECT id, uuid, provider, email, smtp_config_id, oauth_config_id, "
                    "health_status, daily_sent_count, sending_limit, last_sent_date "
                    "FROM email_accounts "
                    "WHERE status = 'active' AND deleted_at IS NULL"
                )
            )
            accounts = result.mappings().all()

            for account in accounts:
                try:
                    smtp_host = None

                    if account["provider"] == "smtp":
                        if account["smtp_config_id"]:
                            healthy = await _test_smtp(session, account["smtp_config_id"])
                            cfg = await session.execute(
                                text("SELECT smtp_host FROM email_smtp_configs WHERE id = :id"),
                                {"id": account["smtp_config_id"]},
                            )
                            row = cfg.mappings().one_or_none()
                            if row:
                                smtp_host = row["smtp_host"]
                        else:
                            healthy = False
                    elif account["provider"] == "gmail":
                        healthy = await _test_oauth_token(session, account["oauth_config_id"], account["provider"])
                    else:
                        healthy = False

                    new_status = "healthy" if healthy else "unhealthy"

                    score, details = await asyncio.to_thread(
                        compute_health_score,
                        account={
                            "email": account["email"],
                            "provider": account["provider"],
                            "health_status": new_status,
                            "daily_sent_count": account["daily_sent_count"],
                            "sending_limit": account["sending_limit"],
                            "last_sent_date": account.get("last_sent_date"),
                        },
                        smtp_host=smtp_host,
                    )

                    await session.execute(
                        text(
                            "UPDATE email_accounts SET health_status = :status, "
                            "health_score = :score, health_details = :details, "
                            "updated_at = NOW() "
                            "WHERE id = :id"
                        ),
                        {
                            "status": new_status,
                            "score": score,
                            "details": json.dumps(details) if details else None,
                            "id": account["id"],
                        },
                    )
                except Exception as e:
                    logger.error("[HealthCheck] Failed to test account %s: %s", account["uuid"], str(e))

            await session.commit()
            if accounts:
                logger.info("[HealthCheck] Checked %d account(s)", len(accounts))
    except Exception as e:
        logger.error("[HealthCheck] Failed: %s", str(e))


async def _test_smtp(session, smtp_config_id: int | None) -> bool:
    if not smtp_config_id:
        return False
    import smtplib

    result = await session.execute(
        text("SELECT smtp_host, smtp_port, smtp_username, encrypted_password FROM email_smtp_configs WHERE id = :id"),
        {"id": smtp_config_id},
    )
    row = result.mappings().one_or_none()
    if not row:
        return False

    from src.shared.infrastructure.encryption.fernet_encryption import decrypt

    password = decrypt(row["encrypted_password"])

    def _sync():
        if row["smtp_port"] in SMTP_SSL_PORTS:
            s = smtplib.SMTP_SSL(row["smtp_host"], row["smtp_port"], timeout=10)
        else:
            s = smtplib.SMTP(row["smtp_host"], row["smtp_port"], timeout=10)
            if row["smtp_port"] in SMTP_STARTTLS_PORTS:
                s.starttls()
        with s:
            s.login(row["smtp_username"], password)
    try:
        await asyncio.to_thread(_sync)
        return True
    except Exception:
        return False


async def _test_oauth_token(session, oauth_config_id: int | None, provider: str) -> bool:
    if not oauth_config_id:
        return False
    from httpx import AsyncClient

    result = await session.execute(
        text("SELECT encrypted_refresh_token FROM email_oauth_configs WHERE id = :id"),
        {"id": oauth_config_id},
    )
    row = result.mappings().one_or_none()
    if not row:
        return False

    from src.shared.infrastructure.encryption.fernet_encryption import decrypt, encrypt

    refresh_token = decrypt(row["encrypted_refresh_token"])
    if not refresh_token:
        return False

    try:
        if provider != "gmail":
            return False
        url = "https://oauth2.googleapis.com/token"
        data = {
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
            "client_id": config.GOOGLE_MAIL_CLIENT_ID,
            "client_secret": config.GOOGLE_MAIL_CLIENT_SECRET,
        }

        async with AsyncClient() as client:
            resp = await client.post(url, data=data)
            if not resp.is_success:
                return False
            body = resp.json()
            new_refresh = body.get("refresh_token")
            if new_refresh:
                await session.execute(
                    text("UPDATE email_oauth_configs SET encrypted_refresh_token = :token, updated_at = NOW() WHERE id = :id"),
                    {"token": encrypt(new_refresh), "id": oauth_config_id},
                )
            return True
    except Exception:
        return False


async def process_stale_reconnect():
    """Set unhealthy OAuth accounts to reconnect_required. Log unhealthy SMTP accounts."""
    try:
        async with async_session() as session:
            result = await session.execute(
                text(
                    "SELECT id, uuid, provider, email FROM email_accounts "
                    "WHERE status = 'active' AND health_status = 'unhealthy' AND deleted_at IS NULL"
                )
            )
            accounts = result.mappings().all()
            if accounts:
                oauth_ids = []
                for acc in accounts:
                    if acc["provider"] == "gmail":
                        oauth_ids.append(acc["id"])
                    else:
                        logger.warning(
                            "[StaleReconnect] Unhealthy SMTP account: %s (%s)", 
                            acc["uuid"], acc["email"],
                        )

                if oauth_ids:
                    placeholders = ", ".join(f":id_{i}" for i in range(len(oauth_ids)))
                    params = {f"id_{i}": oid for i, oid in enumerate(oauth_ids)}
                    await session.execute(
                        text(
                            f"UPDATE email_accounts SET status = 'reconnect_required', updated_at = NOW() "
                            f"WHERE id IN ({placeholders})"
                        ),
                        params,
                    )
                    logger.warning("[StaleReconnect] Set %d OAuth account(s) to reconnect_required", len(oauth_ids))

                await session.commit()
    except Exception as e:
        logger.error("[StaleReconnect] Failed: %s", str(e))


async def process_expired_verification_cleanup():
    """Soft-delete email accounts whose verification has expired."""
    try:
        async with async_session() as session:
            result = await session.execute(
                text(
                    "UPDATE email_accounts "
                    "SET status = 'disconnected', deleted_at = NOW(), updated_at = NOW() "
                    "WHERE status = 'pending_verification' AND deleted_at IS NULL "
                    "AND smtp_config_id IS NOT NULL "
                    "AND EXISTS ("
                    "  SELECT 1 FROM email_smtp_configs esc "
                    "  WHERE esc.id = email_accounts.smtp_config_id "
                    "  AND esc.code_expires_at IS NOT NULL "
                    "  AND esc.code_expires_at <= NOW()"
                    ")"
                )
            )
            count = result.rowcount
            if count:
                logger.info("[ExpiredCleanup] Disconnected %d expired pending account(s)", count)
            await session.commit()
    except Exception as e:
        logger.error("[ExpiredCleanup] Failed: %s", str(e))


async def health_check_loop():
    while True:
        await process_health_check()
        await asyncio.sleep(HEALTH_CHECK_INTERVAL_SECONDS)


async def stale_reconnect_loop():
    """Log unhealthy accounts that may need reconnection."""
    while True:
        await process_stale_reconnect()
        await asyncio.sleep(STALE_RECONNECT_INTERVAL_SECONDS)


async def expired_verification_cleanup_loop():
    while True:
        await process_expired_verification_cleanup()
        await asyncio.sleep(EXPIRED_CLEANUP_INTERVAL_SECONDS)
