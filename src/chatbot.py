import anthropic

from src import config


class Chatbot:
    def __init__(self):
        self.client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
        self.messages = []

    def send(self, user_message: str, attachments: list[dict] | None = None) -> str:
        if attachments:
            # Files go before the text so Claude reads them first
            content = list(attachments)
            if user_message:
                content.append({"type": "text", "text": user_message})
        else:
            content = user_message
        self.messages.append({"role": "user", "content": content})

        response = self.client.messages.create(
            model=config.CLAUDE_MODEL,
            max_tokens=config.MAX_TOKENS,
            system=config.SYSTEM_PROMPT,
            output_config={"effort": "low"},
            messages=self.messages,
        )

        if response.stop_reason == "refusal":
            # Drop the refused message so it doesn't stay in the history
            self.messages.pop()
            return "[Claude declined to answer that]"

        # Keep the full content (including thinking blocks) so the history stays valid
        self.messages.append({"role": "assistant", "content": response.content})

        reply = "".join(block.text for block in response.content if block.type == "text")
        if response.stop_reason == "max_tokens":
            reply += "\n[Reply cut off - raise MAX_TOKENS in .env]"
        return reply

    def edit_message(self, index: int, new_text: str):
        """Replace the text of an earlier message in the history."""
        message = self.messages[index]
        if message["role"] == "assistant" or isinstance(message["content"], str):
            message["content"] = new_text
        else:
            # Keep any attached files, replace only the typed text
            content = [block for block in message["content"] if block.get("type") != "text"]
            if new_text:
                content.append({"type": "text", "text": new_text})
            message["content"] = content

        # Claude's thinking blocks are tied to the exact history they were written in,
        # so after an edit the API would reject them. Remove them all.
        for message in self.messages:
            if message["role"] == "assistant" and isinstance(message["content"], list):
                message["content"] = [
                    block for block in message["content"]
                    if block.type not in ("thinking", "redacted_thinking")
                ] or "(no reply)"

    def reset(self):
        self.messages = []
