import json
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

# Always in the project's logs folder, wherever the app is started from
LOG_FILE = Path(__file__).parent.parent / "logs" / "attempts.jsonl"

# This computer's (public ip, city, state), looked up once
_location = None


def locate() -> tuple[str, str, str]:
    """Return (public ip, city, state) for this computer using ipinfo.io."""
    global _location
    if _location:
        return _location
    try:
        with urllib.request.urlopen("https://ipinfo.io/json", timeout=3) as response:
            info = json.load(response)
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
        # Not cached, so it tries again next time
        return "Unknown", "Unknown", "Unknown"
    _location = (info.get("ip", "Unknown"), info.get("city", "Unknown"), info.get("region", "Unknown"))
    return _location


def log_attempt(stage: str, reason: str, text: str):
    """Record a blocked prompt injection or jailbreak attempt."""
    ip, city, state = locate()
    entry = {
        "time": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "ip": ip,
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
