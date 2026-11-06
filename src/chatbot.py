"""Question rewriting and answer generation."""

from src.config import DISCLAIMER
from src.prompts import REWRITE_PROMPT, SYSTEM_PROMPT
from src.retrieval import format_docs, retrieve


def get_llm(model_name):
    from langchain_groq import ChatGroq
    return ChatGroq(model=model_name, temperature=0)


def rewrite_question(llm, question, history, turns=4):
    """Turn a follow-up into a standalone question using the last few messages."""
    recent = history[-turns:]
    if not recent:
        return question
    history_text = "\n".join(f"{m['role']}: {m['content']}" for m in recent)
    result = llm.invoke(REWRITE_PROMPT.format(history=history_text, question=question))
    rewritten = (result.content or "").strip().strip('"')
    return rewritten or question


def answer(store, question, history, model_name, k=5):
    """Return dict with answer, standalone question and source documents."""
    from langchain_core.output_parsers import StrOutputParser
    from langchain_core.prompts import ChatPromptTemplate

    llm = get_llm(model_name)
    standalone = rewrite_question(llm, question, history)
    docs = retrieve(store, standalone, k=k)

    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        ("human", "{question}"),
    ])
    chain = prompt | llm | StrOutputParser()
    text = chain.invoke({"context": format_docs(docs), "question": standalone})

    if DISCLAIMER.lower() not in text.lower():
        text = text.rstrip() + "\n\n_" + DISCLAIMER + "_"

    return {"answer": text, "standalone": standalone, "docs": docs}
