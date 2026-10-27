import streamlit as st

from src.attack_log import read_attempts

st.set_page_config(page_title="Attack Feed", page_icon="🚨", layout="wide")
st.title("🚨 Attack Feed")
st.caption("Prompt injection and jailbreak attempts caught by the guardrails. Updates every 2 seconds.")


@st.fragment(run_every=2)
def feed():
    attempts = read_attempts()
    if not attempts:
        st.info("No attempts logged yet.")
        return

    st.metric("Recent attempts", len(attempts))
    st.dataframe(
        attempts,
        column_order=["time", "ip", "city", "state", "stage", "reason", "excerpt"],
        column_config={
            "time": "Time (UTC)",
            "ip": "IP",
            "city": "City",
            "state": "State",
            "stage": "Caught by",
            "reason": "Reason",
            "excerpt": "Message",
        },
        hide_index=True,
        width="stretch",
    )


feed()
