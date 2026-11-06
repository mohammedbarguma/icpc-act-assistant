"""Retrieval: exact lookup for 'section N', semantic search otherwise."""

import re

SECTION_REF = re.compile(r"\b(?:section|sec\.?|s\.)\s*(\d{1,3})", re.I)


def find_section_number(question):
    m = SECTION_REF.search(question)
    return int(m.group(1)) if m else None


def retrieve(store, question, k=5):
    from langchain_core.documents import Document

    num = find_section_number(question)
    if num is not None:
        got = store.get(where={"section": num})
        hits = [Document(page_content=t, metadata=md)
                for t, md in zip(got["documents"], got["metadatas"])]
        if hits:
            return hits
    return store.similarity_search(question, k=k)


def format_docs(docs):
    return "\n\n---\n\n".join(
        f"[Section {d.metadata['section']}, p.{d.metadata['page']}]\n{d.page_content}"
        for d in docs
    )
