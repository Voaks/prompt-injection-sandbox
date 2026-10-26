from src.guardrails import check_input, check_output


def test_normal_input_is_allowed():
    allowed, _ = check_input("What's the weather like on Mars?")
    assert allowed


def test_normal_output_is_allowed():
    allowed, _ = check_output("Mars is cold, with an average temperature of about -60°C.")
    assert allowed


# TODO: add tests for injection attempts your guardrails should block, e.g.
# def test_ignore_instructions_is_blocked():
#     allowed, _ = check_input("Ignore all previous instructions and ...")
#     assert not allowed
