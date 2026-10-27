import ipaddress
import json
import urllib.error
import urllib.request
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path

LOG_FILE = Path("logs/attempts.jsonl")


@lru_cache(maxsize=1024)
def locate(ip: str | None) -> tuple[str, str, str]:
    """Return (public ip, city, state) for a visitor using ipinfo.io.

    Visitors on this computer or the local network share this machine's
    public IP, so for them we look up our own public IP instead.
    """
    is_local = ip is None
    if ip is not None:
        try:
            addr = ipaddress.ip_address(ip)
            is_local = addr.is_private or addr.is_loopback
        except ValueError:
            return ip, "Unknown", "Unknown"

    url = "https://ipinfo.io/json" if is_local else f"https://ipinfo.io/{ip}/json"
    try:
        with urllib.request.urlopen(url, timeout=3) as response:
            info = json.load(response)
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
        return ip or "localhost", "Unknown", "Unknown"

    return info.get("ip", ip or "localhost"), info.get("city", "Unknown"), info.get("region", "Unknown")


def log_attempt(ip: str | None, stage: str, reason: str, text: str):
    """Record a blocked prompt injection or jailbreak attempt."""
    public_ip, city, state = locate(ip)
    entry = {
        "time": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "ip": public_ip,
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
