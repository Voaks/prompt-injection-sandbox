def check_input(text: str) -> tuple[bool, str]:
    """Check a user message before it is sent to Claude.

    Returns (allowed, reason). If allowed is False, the message is blocked
    and reason is shown to the user.
    """
    # TODO: add your input guardrails here (e.g. prompt injection detection)
    return True, ""
