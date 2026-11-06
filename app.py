"""ICPC Act chatbot (Streamlit UI). Run: streamlit run app.py"""

import os

import streamlit as st

from src import config
from src.chatbot import answer
from src.ingestion import load_vector_store

st.set_page_config(page_title="ICPC Act assistant", page_icon="⚖️")
st.title("ICPC Act assistant")
st.caption("Ask about the Corrupt Practices and Other Related Offences Act, 2000. "
           "Answers cite sections and pages.")

# ---------- Checks ----------
if not os.getenv("GROQ_API_KEY"):
    st.error("GROQ_API_KEY is not set. Add it to the .env file in the project folder and restart.")
    st.stop()

if not os.path.exists(config.PDF_PATH):
    st.error(f"Could not find the PDF at: {config.PDF_PATH}. Put it in the data folder "
             "or set PDF_PATH in .env.")
    st.stop()


@st.cache_resource(show_spinner="Reading the Act and building the search index (first run only)...")
def get_store():
    return load_vector_store(
        config.PDF_PATH, config.EMBEDDING_MODEL,
        config.CHUNK_SIZE, config.CHUNK_OVERLAP, config.COLLECTION_NAME,
    )


try:
    store, report = get_store()
except ValueError as exc:
    st.error(str(exc))
    st.stop()

# ---------- Sidebar ----------
with st.sidebar:
    st.subheader("Settings")
    model_name = st.selectbox("Model", config.MODELS)
    k = st.slider("Passages to retrieve", 2, 10, 5)

    st.subheader("Index")
    st.write(f"{report['located']} of {report['toc_sections']} sections located, "
             f"{report['chunks']} passages, {report['pages']} pages.")
    if report["missing"]:
        st.warning(f"Sections not located (merged into the previous one): {report['missing']}")

    if st.button("Clear conversation"):
        st.session_state.messages = []
        st.rerun()
    st.caption(config.DISCLAIMER)


def show_sources(sources):
    with st.expander("Sources"):
        for s in sources:
            st.markdown(f"**Section {s['section']} — {s['title']}** (page {s['page']})")
            st.text(s["text"])


# ---------- Chat ----------
if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("standalone") and msg["standalone"] != msg["content"]:
            st.caption(f"Searched as: {msg['standalone']}")
        if msg.get("sources"):
            show_sources(msg["sources"])

if not st.session_state.messages:
    st.info("Try: What does section 5 say?")

question = st.chat_input("Ask about the ICPC Act")

if question:
    history = [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]

    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        try:
            with st.spinner("Searching the Act..."):
                result = answer(store, question, history, model_name, k)
            text, standalone = result["answer"], result["standalone"]
            sources = [{
                "section": d.metadata["section"],
                "title": d.metadata["title"],
                "page": d.metadata["page"],
                "text": d.page_content,
            } for d in result["docs"]]
        except Exception as exc:
            msg = str(exc)
            if "429" in msg or "rate" in msg.lower():
                text = "The model is rate limited right now. Wait a minute and try again."
            else:
                text = f"The request failed: {msg}"
            standalone, sources = question, []

        st.markdown(text)
        if sources:
            show_sources(sources)

    st.session_state.messages.append({"role": "user", "content": question, "standalone": standalone})
    st.session_state.messages.append({"role": "assistant", "content": text, "sources": sources})
    st.rerun()
