import anthropic

from src.chatbot import Chatbot
from src.guardrails import check_input, check_output


def main():
    bot = Chatbot()
    print("Chatbot ready. Type 'quit' to exit, 'reset' to clear the conversation.")

    while True:
        user_input = input("\nYou: ").strip()
        if not user_input:
            continue
        if user_input.lower() in ("quit", "exit"):
            break
        if user_input.lower() == "reset":
            bot.reset()
            print("[Conversation cleared]")
            continue

        allowed, reason = check_input(user_input)
        if not allowed:
            print(f"[Blocked by input guardrail: {reason}]")
            continue

        try:
            reply = bot.send(user_input)
        except anthropic.APIError as e:
            print(f"[API error: {e}]")
            continue

        allowed, reason = check_output(reply)
        if not allowed:
            print(f"[Blocked by output guardrail: {reason}]")
            continue

        print(f"\nClaude: {reply}")


if __name__ == "__main__":
    main()
