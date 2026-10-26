def check_output(text: str) -> tuple[bool, str]:
    """Check Claude's reply before it is shown to the user.

    Returns (allowed, reason). If allowed is False, the reply is hidden
    and reason is shown instead.
    """
    # TODO: add your output guardrails here (e.g. leaked system prompt detection)
    return True, ""
