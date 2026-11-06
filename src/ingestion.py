"""Read the ICPC Act PDF, find its sections and build the vector store.

Sections are located using the Act's own table of contents
("Arrangement of Sections"), not a generic text splitter.
"""

import re

# ---------- PDF reading ----------

def read_pdf(pdf_path):
    """Return (full_text, page_starts). page_starts holds (char_offset, page_number)."""
    from pypdf import PdfReader

    reader = PdfReader(pdf_path)
    full_text, page_starts = "", []
    for i, page in enumerate(reader.pages):
        page_starts.append((len(full_text), i + 1))  # page number as printed
        full_text += (page.extract_text() or "") + "\n"
    return full_text, page_starts


def page_at(page_starts, offset):
    page = page_starts[0][1]
    for start, pg in page_starts:
        if start <= offset:
            page = pg
    return page


# ---------- Table of contents ----------

def clean_title(title):
    """Remove 'Cap. 359 LFN' style references and stray punctuation."""
    title = re.sub(r"[;,]?\s*Ca\s*p\.?\s*\d+\s*LFN.*$", "", title, flags=re.I)
    return title.strip(" .;,-")


_TOC_ANCHOR = re.compile(r"ARRANGEMENT\s+OF\s+SECTIONS", re.I)
_TOC_ENTRY = re.compile(r"^\s*(\d{1,3})\.\s*(.*)$", re.M)


def parse_toc(full_text, max_gap=3000):
    """Return (toc, toc_end). toc maps section number -> title.

    Only consecutive numbers (1, 2, 3, ...) are accepted.
    """
    anchor = _TOC_ANCHOR.search(full_text)
    toc_from = anchor.end() if anchor else 0

    toc, expected, toc_end = {}, 1, toc_from
    for m in _TOC_ENTRY.finditer(full_text, toc_from):
        if toc and m.start() - toc_end > max_gap:
            break
        if int(m.group(1)) == expected:
            toc[expected] = clean_title(m.group(2))
            toc_end = m.end()
            expected += 1
    return toc, toc_end


# ---------- Locating sections in the body ----------

def _title_pattern(title, n_words):
    words = re.findall(r"[A-Za-z]+", title)[:n_words]
    if not words:
        return None
    return re.compile(r"\W+".join(map(re.escape, words)), re.I)


def locate_sections(full_text, toc, toc_end, page_starts, window=20000):
    """Find each section's title in the body, searching forward.

    Returns (sections, missing). Missing sections are merged into the previous one.
    """
    starts, cursor = {}, toc_end
    for n in sorted(toc):
        for n_words in (4, 3, 2):
            pat = _title_pattern(toc[n], n_words)
            if pat is None:
                break
            m = pat.search(full_text, cursor, cursor + window)
            if m:
                starts[n] = m.start()
                cursor = m.end()
                break

    found = sorted(starts)
    sections = []
    for i, n in enumerate(found):
        begin = starts[n]
        end = starts[found[i + 1]] if i + 1 < len(found) else len(full_text)
        sections.append({
            "section": n,
            "title": toc[n],
            "page": page_at(page_starts, begin),
            "text": full_text[begin:end].strip(),
        })
    missing = [n for n in toc if n not in starts]
    return sections, missing


# ---------- Documents and vector store ----------

def build_documents(sections, chunk_size, chunk_overlap):
    from langchain_core.documents import Document
    from langchain_text_splitters import RecursiveCharacterTextSplitter

    splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    docs = []
    for s in sections:
        for piece in splitter.split_text(s["text"]):
            docs.append(Document(
                page_content=f"Section {s['section']} - {s['title']}\n{piece}",
                metadata={"section": s["section"], "title": s["title"], "page": s["page"]},
            ))
    return docs


def load_vector_store(pdf_path, embedding_model, chunk_size=1500, chunk_overlap=200,
                      collection_name="icpc_act"):
    """Full ingestion. Returns (vector_store, report)."""
    from langchain_chroma import Chroma
    from langchain_huggingface import HuggingFaceEmbeddings

    full_text, page_starts = read_pdf(pdf_path)
    if not full_text.strip():
        raise ValueError("No text could be read from the PDF. It may be a scanned copy that needs OCR.")

    toc, toc_end = parse_toc(full_text)
    if not toc:
        raise ValueError("Could not find the 'Arrangement of Sections' table of contents in the PDF.")

    sections, missing = locate_sections(full_text, toc, toc_end, page_starts)
    docs = build_documents(sections, chunk_size, chunk_overlap)

    embeddings = HuggingFaceEmbeddings(model_name=embedding_model)
    ids = [f"s{d.metadata['section']}-c{i}" for i, d in enumerate(docs)]
    store = Chroma.from_documents(docs, embeddings, ids=ids, collection_name=collection_name)

    report = {
        "pages": len(page_starts),
        "toc_sections": len(toc),
        "located": len(sections),
        "missing": missing,
        "chunks": len(docs),
    }
    return store, report
