import os
import json
import streamlit as st
from anthropic import Anthropic

MODEL = "claude-sonnet-4-6"
MAX_TOKENS = 700

st.set_page_config(page_title="Foster Compass", page_icon="\U0001F9ED")


def get_api_key():
    try:
        return st.secrets["ANTHROPIC_API_KEY"]
    except Exception:
        return os.environ.get("ANTHROPIC_API_KEY")


api_key = get_api_key()
if not api_key:
    st.error("No API key found. Set ANTHROPIC_API_KEY in Streamlit secrets or your environment.")
    st.stop()

client = Anthropic(api_key=api_key)

with open("resources.json", "r") as f:
    resources = json.load(f)


def format_resources(items):
    blocks = []
    for r in items:
        blocks.append(
            "- Name: {name}\n"
            "  Category: {category}\n"
            "  Who it helps: {who}\n"
            "  What it offers: {desc}\n"
            "  How to reach it: {contact}\n"
            "  Location: {loc}".format(
                name=r.get("name", ""),
                category=r.get("category", ""),
                who=r.get("who_it_helps", ""),
                desc=r.get("description", ""),
                contact=r.get("contact", ""),
                loc=r.get("location", ""),
            )
        )
    return "\n".join(blocks)


SYSTEM_PROMPT = (
    "You are Foster Compass, a warm, plain-spoken guide for young people who are aging out of "
    "(or have recently aged out of) foster care. Your job is to help them find the right "
    "resource for what they need.\n\n"
    "Rules you must follow:\n"
    "1. Answer ONLY using the resources listed below. Never invent organizations, phone "
    "numbers, websites, eligibility rules, or facts.\n"
    "2. When you point someone to a resource, name it clearly and include how to reach it.\n"
    "3. If a question is not covered by the resources below, say so plainly and suggest they "
    "reach out to a caseworker or the host organization. Do not guess.\n"
    "4. You are not a lawyer, doctor, or financial advisor. For anything legal, medical, or "
    "urgent, encourage them to talk to a real person and offer the most relevant resource.\n"
    "5. Keep answers short, kind, and easy to read. Assume the person may be stressed or in a hurry.\n"
    "6. If someone seems to be in crisis or in danger, treat it as the priority: point them to the "
    "crisis and safety resources below (such as 988 or the National Runaway Safeline), encourage "
    "them to reach out right away, and remind them they can call 911 for an immediate emergency.\n\n"
    "Here are the resources you can draw from:\n" + format_resources(resources)
)

EXAMPLES = [
    "I need help finding housing.",
    "How do I get health insurance after foster care?",
    "Can I get money for college?",
    "I need food this week.",
    "How do I get a copy of my birth certificate?",
    "I'm in crisis and need help now.",
]

if "messages" not in st.session_state:
    st.session_state.messages = []

queued = st.session_state.pop("pending", None)

st.title("\U0001F9ED Foster Compass")
st.caption(
    "A friendly guide to resources for youth aging out of foster care. "
    "This is not professional advice \u2014 for anything urgent, please talk to a real person."
)

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

if not st.session_state.messages and not queued:
    st.markdown("**Not sure where to start? Tap a question:**")
    cols = st.columns(2)
    for i, ex in enumerate(EXAMPLES):
        if cols[i % 2].button(ex, key="ex_{}".format(i), use_container_width=True):
            st.session_state.pending = ex
            st.rerun()

typed = st.chat_input("Ask a question \u2014 for example: I need help finding housing.")
prompt = typed or queued

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    with st.chat_message("assistant"):
        with st.spinner("Looking that up..."):
            resp = client.messages.create(
                model=MODEL,
                max_tokens=MAX_TOKENS,
                system=SYSTEM_PROMPT,
                messages=st.session_state.messages,
            )
            answer = resp.content[0].text
            st.markdown(answer)
    st.session_state.messages.append({"role": "assistant", "content": answer})
