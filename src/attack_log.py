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
    """Record a blocked prompt injection or jailbreak attempt, with the full message."""
    ip, city, state = locate()
    entry = {
        "time": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "ip": ip,
        "city": city,
        "state": state,
        "stage": stage,
        "reason": reason,
        "message": text,
    }
    LOG_FILE.parent.mkdir(exist_ok=True)
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def _parse(line_number: int, line: str) -> dict:
    entry = json.loads(line)
    entry["id"] = line_number
    # Entries logged before full messages were saved only kept the first 200 characters
    entry.setdefault("message", entry.pop("excerpt", ""))
    return entry


def read_attempts(limit: int = 500) -> list[dict]:
    """Return the most recent attempts, newest first. Each has an id for get_attempt()."""
    if not LOG_FILE.exists():
        return []
    lines = LOG_FILE.read_text(encoding="utf-8").splitlines()
    first = max(len(lines) - limit, 0)
    entries = [_parse(i, line) for i, line in enumerate(lines[first:], start=first) if line.strip()]
    return entries[::-1]


def get_attempt(attempt_id: int) -> dict | None:
    """Return one attempt by its id (its line in the log file)."""
    if not LOG_FILE.exists():
        return None
    lines = LOG_FILE.read_text(encoding="utf-8").splitlines()
    if not isinstance(attempt_id, int) or not 0 <= attempt_id < len(lines) or not lines[attempt_id].strip():
        return None
    return _parse(attempt_id, lines[attempt_id])
