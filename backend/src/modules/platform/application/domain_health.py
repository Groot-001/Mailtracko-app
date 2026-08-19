import asyncio
import ipaddress
from datetime import UTC, datetime

import dns.resolver
from dns.exception import DNSException


def _txt_records(name: str) -> list[str]:
    try:
        answers = dns.resolver.resolve(name, "TXT", lifetime=8)
    except DNSException:
        return []
    records: list[str] = []
    for answer in answers:
        if hasattr(answer, "strings"):
            records.append(b"".join(answer.strings).decode(errors="replace"))
        else:
            records.append(str(answer).strip('"'))
    return records


def _has_dns(domain: str) -> bool:
    for record_type in ("MX", "A", "AAAA"):
        try:
            dns.resolver.resolve(domain, record_type, lifetime=8)
            return True
        except DNSException:
            pass
    return False


def _blacklist_status(domain: str) -> tuple[str, dict]:
    try:
        answers = dns.resolver.resolve(domain, "A", lifetime=8)
        addresses = [str(answer) for answer in answers]
    except DNSException:
        return "unknown", {"checked_ips": [], "listed_on": []}

    zones = ("zen.spamhaus.org", "bl.spamcop.net")
    listed_on: list[str] = []
    checked_ips: list[str] = []
    for address in addresses:
        try:
            ip = ipaddress.ip_address(address)
        except ValueError:
            continue
        if ip.version != 4:
            continue
        checked_ips.append(address)
        reversed_ip = ".".join(reversed(address.split(".")))
        for zone in zones:
            try:
                dns.resolver.resolve(f"{reversed_ip}.{zone}", "A", lifetime=4)
                listed_on.append(zone)
            except DNSException:
                pass
    return ("listed" if listed_on else "clear"), {
        "checked_ips": checked_ips,
        "listed_on": sorted(set(listed_on)),
    }


def _run_check(domain: str, selectors: list[str]) -> dict:
    normalized = domain.strip().lower().rstrip(".")
    dns_ok = _has_dns(normalized)
    root_txt = _txt_records(normalized)
    spf_ok = any(record.lower().startswith("v=spf1") for record in root_txt)
    dmarc_records = _txt_records(f"_dmarc.{normalized}")
    dmarc_ok = any(record.lower().startswith("v=dmarc1") for record in dmarc_records)

    dkim_matches: dict[str, list[str]] = {}
    for selector in selectors:
        records = _txt_records(f"{selector}._domainkey.{normalized}")
        if any(
            "v=dkim1" in record.lower() or "p=" in record.lower() for record in records
        ):
            dkim_matches[selector] = records
    dkim_ok = bool(dkim_matches)
    blacklist_status, blacklist_details = _blacklist_status(normalized)

    score = 0
    score += 20 if dns_ok else 0
    score += 25 if spf_ok else 0
    score += 25 if dkim_ok else 0
    score += 25 if dmarc_ok else 0
    score += 5 if blacklist_status == "clear" else 0
    return {
        "domain": normalized,
        "dns_status": "valid" if dns_ok else "invalid",
        "spf_status": "valid" if spf_ok else "missing",
        "dkim_status": "valid" if dkim_ok else "missing",
        "dmarc_status": "valid" if dmarc_ok else "missing",
        "blacklist_status": blacklist_status,
        "score": score,
        "details": {
            "spf_records": root_txt,
            "dmarc_records": dmarc_records,
            "dkim_selectors": sorted(dkim_matches),
            **blacklist_details,
        },
        "last_checked_at": datetime.now(UTC),
    }


async def check_domain_health(domain: str, selectors: list[str] | None = None) -> dict:
    return await asyncio.to_thread(
        _run_check,
        domain,
        selectors or ["google", "selector1", "selector2", "default"],
    )
