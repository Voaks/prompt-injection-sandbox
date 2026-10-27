import base64

import anthropic

from src import config
from src.attack_log import log_attempt, read_attempts
from src.attachments import ALLOWED_TYPES, MAX_FILE_MB, file_extension, is_text_file, read_text, to_content_block
from src.chatbot import Chatbot
from src.guardrails import check_input, check_output

# Shown when a guardrail blocks something, so the user can't tell it was caught and logged
REFUSAL = "Sorry, I can't help with that."


class Api:
    """Everything the app's pages can call, as window.pywebview.api.<name>().

    Attributes and helpers start with _ so pywebview doesn't expose them to the page.
    """

    def __init__(self):
        self._bot = Chatbot()
        # What's shown on screen. api_index points at the matching message in bot.messages,
        # or is None for messages Claude never saw (blocked messages, errors)
        self._history = []

    def state(self):
        return {"model": config.CLAUDE_MODEL, "allowed_types": ALLOWED_TYPES, "messages": self._public_history()}

    def chat(self, text, files):
        """Send a message. files is a list of {"name", "data"} with the data base64-encoded."""
        user_input = text.strip()
        if not user_input and not files:
            return {"error": "Message can't be empty."}

        user_entry = self._add("user", user_input, [f["name"] for f in files])

        allowed, reason = check_input(user_input)
        attachments, file_reply = self._build_attachments(files)
        if not allowed:
            log_attempt("Input filter", reason, user_input)
            self._add("assistant", REFUSAL)
        elif file_reply:
            self._add("assistant", file_reply)
        else:
            start = len(self._bot.messages)
            try:
                reply = self._bot.send(user_input, attachments)
            except anthropic.APIError as e:
                self._add("assistant", f"Something went wrong: {e}")
            else:
                allowed, reason = check_output(reply)
                if not allowed:
                    log_attempt("Output filter", reason, user_input)
                    self._add("assistant", REFUSAL)
                elif len(self._bot.messages) == start + 2:
                    self._add("assistant", reply, api_index=start + 1)
                else:
                    # Claude refused, so the exchange was dropped from its history
                    self._add("assistant", reply)
            # Link the user's message to Claude's history if it made it in
            if len(self._bot.messages) > start:
                user_entry["api_index"] = start

        return {"messages": self._public_history()}

    def edit(self, index, text):
        history = self._history
        new_text = text.strip()
        if not isinstance(index, int) or not 0 <= index < len(history) or history[index]["api_index"] is None:
            return {"error": "That message can't be edited."}
        entry = history[index]
        if not new_text and not entry["files"]:
            return {"error": "Message can't be empty."}

        # Edited text goes into the history Claude reads, so it has to pass the input filter too
        allowed, reason = check_input(new_text)
        if not allowed:
            log_attempt(f"Input filter (edited {entry['role']} message)", reason, new_text)
            return {"error": REFUSAL}

        self._bot.edit_message(entry["api_index"], new_text)
        entry["text"] = new_text
        entry["edited"] = True
        return {"messages": self._public_history()}

    def reset(self):
        self._bot.reset()
        self._history = []
        return {"messages": []}

    def attempts(self):
        return {"attempts": read_attempts()}

    def _add(self, role, text, files=(), api_index=None):
        entry = {"role": role, "text": text, "files": list(files), "api_index": api_index, "edited": False}
        self._history.append(entry)
        return entry

    def _public_history(self):
        """The conversation as the page sees it, without internal details."""
        return [
            {
                "role": e["role"],
                "text": e["text"],
                "files": e["files"],
                "editable": e["api_index"] is not None,
                "edited": e["edited"],
            }
            for e in self._history
        ]

    def _build_attachments(self, files):
        """Turn uploaded files into content blocks. Returns (blocks, reply to show instead or None)."""
        blocks = []
        for f in files:
            name = f["name"]
            data = base64.b64decode(f["data"])
            if file_extension(name) not in ALLOWED_TYPES:
                return [], f"Sorry, I can't read {name} files."
            if len(data) > MAX_FILE_MB * 1024 * 1024:
                return [], f"Sorry, {name} is over the {MAX_FILE_MB} MB limit."
            # Text files go through the input guardrail too, since they can hide injections
            if is_text_file(name):
                file_text = read_text(data)
                allowed, reason = check_input(file_text)
                if not allowed:
                    log_attempt(f"Input filter (file: {name})", reason, file_text)
                    return [], REFUSAL
            blocks.append(to_content_block(name, data))
        return blocks, None
