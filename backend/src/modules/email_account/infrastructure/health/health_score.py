from datetime import UTC, datetime
from typing import Any

from src.modules.email_account.infrastructure.health.blacklist_checker import check_blacklist
from src.modules.email_account.infrastructure.health.dns_checker import check_dns


def compute_health_score(account: dict[str, Any], smtp_host: str | None = None) -> tuple[int, dict]:
    details: dict = {}
    total = 0

    health_status = account.get("health_status", "unknown")
    email = account.get("email", "")
    provider = account.get("provider", "")
    daily_sent_count = account.get("daily_sent_count", 0)
    sending_limit = account.get("sending_limit", 100)

    # 1. Connection status (40 points)
    if health_status == "healthy":
        total += 40
        details["connection"] = {"pass": True, "points": 40}
    elif health_status == "unhealthy":
        details["connection"] = {"pass": False, "points": 0}
    else:
        details["connection"] = {"pass": None, "points": 0}

    # 2. DNS check (30 points) — SPF: 10, DKIM: 10, DMARC: 10
    domain = email.split("@")[-1] if "@" in email else ""
    dns_results = check_dns(domain)
    details["dns"] = dns_results

    dns_points = 0
    if dns_results["spf"].get("pass"):
        dns_points += 10
    if dns_results["dkim"].get("pass"):
        dns_points += 10
    if dns_results["dmarc"].get("pass"):
        dns_points += 10
    total += dns_points

    # 3. Blacklist check (20 points)
    if provider == "smtp" and smtp_host:
        bl_result = check_blacklist(smtp_host)
        details["blacklist"] = bl_result
        if bl_result.get("pass"):
            bl_points = 20
        elif bl_result.get("pass") is None:
            bl_points = 10
        else:
            bl_points = 0
    else:
        details["blacklist"] = {"pass": True, "note": "N/A for OAuth accounts", "points": 10}
        bl_points = 10
    total += bl_points

    # 4. Daily limit usage (10 points)
    if sending_limit > 0:
        usage_ratio = daily_sent_count / sending_limit
        limit_points = max(0, int(10 * (1 - usage_ratio)))
        details["daily_limit"] = {"used": daily_sent_count, "limit": sending_limit, "ratio": usage_ratio, "points": limit_points}
    else:
        limit_points = 0
        details["daily_limit"] = {"used": daily_sent_count, "limit": sending_limit, "points": 0}
    total += limit_points

    total = min(100, max(0, total))
    details["score"] = total
    details["checked_at"] = datetime.now(UTC).isoformat()

    return total, details
