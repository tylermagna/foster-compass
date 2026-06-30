import os
import json
import streamlit as st
from anthropic import Anthropic

# Compass — a friendly resource guide for youth aging out of foster care.

MODEL = "claude-sonnet-4-6"   # Capable + cost-effective. Swap to "claude-haiku-4-5-20251001" to cut cost.
MAX_TOKENS = 700

st.set_page_config(page_title="Compass", page_icon="\U0001F9ED")

# ---- Load your API key. NEVER paste the key into this file. ----
# On Streamlit Community Cloud: add it under Settings > Secrets as ANTHROPIC_API_KEY.
# Running locally: set an environment variable named ANTHROPIC_API_KEY (see the README).
def get_api_key():
    try:
        return st.secrets["ANTHROPIC_API_KEY"]
    except Exception:
        return os.environ.get("ANTHROPIC_API_KEY")

api_key = get_api_key()
if not api_key:
    st.error("No API key found. Add ANTHROPIC_API_KEY in Streamlit secrets or your environment. See the README.")
    st.stop()

client = Anthropic(api_key=api_key)

# ---- Load the resource knowledge base from resources.json ----
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
    "6. If someone seems to be in crisis or danger, gently encourage them to contact emergency "
    "services or a crisis line right away.\n\n"
    "Here are the resources you can draw from:\n" + format_resources(resources)
)

# ---- Simple chat interface ----
st.title("\U0001F9ED Foster Compass")
st.caption(
    "A friendly guide to resources for youth aging out of foster care. "
    "This is not professional advice \u2014 for anything urgent, please talk to a real person."
)

if "messages" not in st.session_state:
    st.session_state.messages = []

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

prompt = st.chat_input("Ask a question \u2014 for example: I need help finding housing.")
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
