# Prompt Injection Sandbox

Chatbot built on the Claude API, with my own custom guardrails layered on top.

## What it does (planned)

- Chat with Claude from the terminal
- Check user input before it reaches the model, for things like prompt injection attempts
- Check model output before it's shown to the user
- Test the guardrails against known injection techniques

## Project structure

```
Sandbox.pyw            Double-click to launch the app
src/
  desktop.py           Opens the app in its own window (python -m src.desktop)
  api.py               What the app's pages call: chat, edit, reset, attack log
  main.py              Terminal version (python -m src.main)
  chatbot.py           Claude API calls
  config.py            Settings and environment variables
  attachments.py       Turns uploaded files into something Claude can read
  attack_log.py        Logs blocked attempts with IP and location
  web/                 Chat page and attack feed (HTML, CSS, JS)
  guardrails/
    input_filter.py    Checks on user input
    output_filter.py   Checks on model output
tests/
  test_guardrails.py   Guardrail tests
```