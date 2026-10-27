from src import config


def check_output(text: str) -> tuple[bool, str]:
    """Check Claude's reply before it is shown to the user.

    Returns (allowed, reason). If allowed is False, the reply is hidden
    and reason is shown instead.
    """
    # Explaining how API keys work is fine. Printing the real one never is.
    key = config.ANTHROPIC_API_KEY
    if key and key in text:
        return False, "Reply contained the real API key"

    return True, ""
