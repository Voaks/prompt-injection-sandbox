import os

from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-haiku-5-5")
MAX_TOKENS = int(os.getenv("MAX_TOKENS", "1024"))

# TODO: write your own system prompt
SYSTEM_PROMPT = "You are a helpful assistant."
