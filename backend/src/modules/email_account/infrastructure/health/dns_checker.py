KNOWN_DKIM_SELECTORS: dict[str, list[str]] = {
    "gmail.com": ["google", "gm1", "gm2", "gm3"],
    "googlemail.com": ["google", "gm1", "gm2", "gm3"],
    "yahoo.com": ["s1024", "s2048"],
    "yahoo.co.uk": ["s1024", "s2048"],
    "aol.com": ["s1024", "s2048"],
    "protonmail.com": ["protonmail", "protonmail2"],
    "proton.me": ["protonmail", "protonmail2"],
    "zoho.com": ["zoho", "zohodesk"],
    "fastmail.com": ["fm1", "fm2", "fm3"],
    "icloud.com": ["sig1", "sig2"],
    "me.com": ["sig1", "sig2"],
}

COMMON_DKIM_SELECTORS: list[str] = [
    "default", "dkim", "mail", "email", "s1", "s2",
    "selector1", "selector2",
    "2023", "2024", "2025", "2026",
    "k1", "k2", "mx", "smtp",
]


try:
    import dns.resolver
    HAS_DNSPYTHON = True
except ImportError:
    HAS_DNSPYTHON = False


def _try_dns_lookup(record_type: str, query: str, timeout: float = 5.0) -> list[str] | None:
    if not HAS_DNSPYTHON:
        return None
    try:
        resolver = dns.resolver.Resolver()
        resolver.timeout = timeout
        resolver.lifetime = timeout
        answers = resolver.resolve(query, record_type)
        return [str(r) for r in answers]
    except Exception:
        return None


def check_mx(domain: str) -> dict:
    records = _try_dns_lookup("MX", domain)
    if records is None:
        return {"pass": False, "records": [], "error": "DNS lookup failed"}
    if not records:
        return {"pass": False, "records": [], "error": "No MX records found"}
    return {"pass": True, "records": records}


def check_spf(domain: str) -> dict:
    records = _try_dns_lookup("TXT", domain)
    if records is None:
        return {"pass": False, "record": None, "error": "DNS lookup failed"}
    spf_records = [r.strip('"') for r in records if "v=spf1" in r]
    if not spf_records:
        return {"pass": False, "record": None, "error": "No SPF record found"}
    return {"pass": True, "record": spf_records[0]}


def check_dmarc(domain: str) -> dict:
    records = _try_dns_lookup("TXT", f"_dmarc.{domain}")
    if records is None:
        return {"pass": False, "record": None, "error": "DNS lookup failed"}
    dmarc_records = [r.strip('"') for r in records if "v=DMARC1" in r]
    if not dmarc_records:
        return {"pass": False, "record": None, "error": "No DMARC record found"}
    return {"pass": True, "record": dmarc_records[0]}


def check_dkim(domain: str) -> dict:
    selectors = KNOWN_DKIM_SELECTORS.get(domain, COMMON_DKIM_SELECTORS)
    found = []
    for selector in selectors:
        records = _try_dns_lookup("TXT", f"{selector}._domainkey.{domain}")
        if records:
            found.append(selector)
    if not found:
        return {"pass": False, "selectors": [], "error": "No DKIM records found"}
    return {"pass": True, "selectors": found}


def check_dns(domain: str) -> dict:
    return {
        "mx": check_mx(domain),
        "spf": check_spf(domain),
        "dkim": check_dkim(domain),
        "dmarc": check_dmarc(domain),
    }
