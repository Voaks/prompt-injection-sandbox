import anthropic
import streamlit as st

from src import config
from src.attachments import ALLOWED_TYPES, MAX_FILE_MB, is_text_file, read_text, to_content_block
from src.chatbot import Chatbot
from src.guardrails import check_input, check_output

st.set_page_config(page_title="Prompt Injection Sandbox", page_icon="🛡️")
st.title("Prompt Injection Sandbox")

if "bot" not in st.session_state:
    st.session_state.bot = Chatbot()
    # What's shown on screen, as (role, text, file names) tuples
    st.session_state.history = []

with st.sidebar:
    st.caption(f"Model: {config.CLAUDE_MODEL}")
    if st.button("Reset conversation"):
        st.session_state.bot.reset()
        st.session_state.history = []
        st.rerun()


def render(role, text, files):
    with st.chat_message(role):
        if text:
            st.markdown(text)
        for name in files:
            st.caption(f"📎 {name}")


def show(role, text, files=()):
    st.session_state.history.append((role, text, list(files)))
    render(role, text, files)


def build_attachments(files):
    """Turn uploaded files into content blocks. Returns (blocks, error message or None)."""
    blocks = []
    for f in files:
        data = f.getvalue()
        if len(data) > MAX_FILE_MB * 1024 * 1024:
            return [], f"⚠️ **{f.name}** is over the {MAX_FILE_MB} MB limit"
        # Text files go through the input guardrail too, since they can hide injections
        if is_text_file(f.name):
            allowed, reason = check_input(read_text(data))
            if not allowed:
                return [], f"🚫 **Blocked by input guardrail ({f.name}):** {reason}"
        blocks.append(to_content_block(f.name, data))
    return blocks, None


for role, text, files in st.session_state.history:
    render(role, text, files)

if prompt := st.chat_input("Type a message...", accept_file="multiple", file_type=ALLOWED_TYPES):
    user_input = prompt.text.strip()
    show("user", user_input, [f.name for f in prompt.files])

    allowed, reason = check_input(user_input)
    attachments, error = build_attachments(prompt.files)
    if not allowed:
        show("assistant", f"🚫 **Blocked by input guardrail:** {reason}")
    elif error:
        show("assistant", error)
    else:
        try:
            with st.spinner("Thinking..."):
                reply = st.session_state.bot.send(user_input, attachments)
        except anthropic.APIError as e:
            show("assistant", f"⚠️ **API error:** {e}")
        else:
            allowed, reason = check_output(reply)
            if not allowed:
                show("assistant", f"🚫 **Blocked by output guardrail:** {reason}")
            else:
                show("assistant", reply)
