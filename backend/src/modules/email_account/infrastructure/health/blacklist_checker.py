import socket

BLACKLIST_DNS = [
    "zen.spamhaus.org",
    "bl.spamcop.net",
    "dnsbl.sorbs.net",
    "b.barracudacentral.org",
]


def _reverse_ip(ip: str) -> str:
    return ".".join(reversed(ip.split(".")))


def _resolve_ip(hostname: str) -> str | None:
    try:
        return socket.gethostbyname(hostname)
    except Exception:
        return None


def check_blacklist(host: str) -> dict:
    ip = _resolve_ip(host)
    if not ip:
        return {"pass": None, "ip": None, "listed_on": [], "error": "Could not resolve hostname"}

    rev_ip = _reverse_ip(ip)
    listed_on = []

    for bl in BLACKLIST_DNS:
        query = f"{rev_ip}.{bl}"
        try:
            socket.gethostbyname(query)
            listed_on.append(bl)
        except Exception:
            pass

    return {
        "pass": len(listed_on) == 0,
        "ip": ip,
        "listed_on": listed_on,
    }
