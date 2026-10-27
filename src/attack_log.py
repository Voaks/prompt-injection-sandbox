import ipaddress
import json
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path

import geoip2.database
import geoip2.errors

LOG_FILE = Path("logs/attempts.jsonl")
# Free download from MaxMind (needs an account): https://dev.maxmind.com/geoip/geolite2-free-geolocation-data
GEOIP_DB = Path("data/GeoLite2-City.mmdb")


@lru_cache(maxsize=1024)
def locate(ip: str | None) -> tuple[str, str]:
    """Return (city, state) for an IP using the local GeoLite2 database."""
    if ip is None:
        return "Localhost", "Localhost"
    try:
        addr = ipaddress.ip_address(ip)
    except ValueError:
        return "Unknown", "Unknown"
    if addr.is_private or addr.is_loopback:
        return "Local network", "Local network"
    if not GEOIP_DB.exists():
        return "Unknown (no GeoIP database)", "Unknown (no GeoIP database)"

    try:
        with geoip2.database.Reader(GEOIP_DB) as reader:
            result = reader.city(ip)
    except geoip2.errors.AddressNotFoundError:
        return "Unknown", "Unknown"
    return result.city.name or "Unknown", result.subdivisions.most_specific.name or "Unknown"


def log_attempt(ip: str | None, stage: str, reason: str, text: str):
    """Record a blocked prompt injection or jailbreak attempt."""
    city, state = locate(ip)
    entry = {
        "time": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "ip": ip or "localhost",
        "city": city,
        "state": state,
        "stage": stage,
        "reason": reason,
        "excerpt": text[:200],
    }
    LOG_FILE.parent.mkdir(exist_ok=True)
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def read_attempts(limit: int = 200) -> list[dict]:
    """Return the most recent attempts, newest first."""
    if not LOG_FILE.exists():
        return []
    lines = LOG_FILE.read_text(encoding="utf-8").splitlines()
    return [json.loads(line) for line in reversed(lines[-limit:]) if line.strip()]
