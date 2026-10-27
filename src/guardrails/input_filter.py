import re


def check_input(text: str) -> tuple[bool, str]:
    """Check a user message before it is sent to Claude.

    Returns (allowed, reason). If allowed is False, the message is blocked
    and reason is shown to the user.
    """
    # Phrases that suggest someone is after the API key.
    # [\s_\-.]* lets "api key", "api_key", "api-key" and "apikey" all match.
    blocked_patterns = [
        (r"api[\s_\-.]*key", "mentions the API key"),
        (r"anthropic[\s_\-.]*key", "mentions the Anthropic key"),
        (r"secret[\s_\-.]*key", "mentions a secret key"),
        (r"sk-ant", "contains an Anthropic key prefix"),
        (r"\.env\b", "mentions the .env file"),
    ]

    for pattern, reason in blocked_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return False, f"Message {reason}"
    return True, ""
