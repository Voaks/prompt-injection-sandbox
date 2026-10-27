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

    def reset(self):
        self.messages = []
