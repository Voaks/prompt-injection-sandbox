# Prompt Injection Sandbox

A personal side project: a chatbot built on the Claude API, with my own custom guardrails layered on top.

## What it does (planned)

- Chat with Claude from the terminal
- Check user input before it reaches the model, for things like prompt injection attempts
- Check model output before it's shown to the user
- Test the guardrails against known injection techniques

## Project structure

```
src/
  main.py              Entry point
  chatbot.py           Claude API calls
  config.py            Settings and environment variables
  guardrails/
    input_filter.py    Checks on user input
    output_filter.py   Checks on model output
tests/
  test_guardrails.py   Guardrail tests
```

## Setup

1. Copy `.env.example` to `.env` and add your Anthropic API key
2. Install dependencies: `pip install -r requirements.txt`
3. Run: `python -m src.main`

## Status

Early work in progress. The project is set up, but the code isn't written yet.
