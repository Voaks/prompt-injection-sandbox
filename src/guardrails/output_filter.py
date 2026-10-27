import re

from src import config


def check_output(text: str) -> tuple[bool, str]:
    """Check Claude's reply before it is shown to the user.

    Returns (allowed, reason). If allowed is False, the reply is hidden
    and reason is shown instead.
    """
    # The real key from .env
    key = config.ANTHROPIC_API_KEY
    if key and key in text:
        return False, "Reply contained the real API key"

    # Anything shaped like an Anthropic key, even one that isn't ours
    if re.search(r"sk-ant-[A-Za-z0-9_\-]{8,}", text):
        return False, "Reply contained something that looks like an API key"

    # Any mention of an API key at all
    if re.search(r"api[\s_\-.]*key", text, re.IGNORECASE):
        return False, "Reply talked about the API key"

    return True, ""
