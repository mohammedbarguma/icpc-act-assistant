"""Tests for section parsing and retrieval routing. Run: pytest"""

from src.ingestion import clean_title, locate_sections, parse_toc
from src.retrieval import find_section_number, retrieve

SAMPLE = (
    "CORRUPT PRACTICES ACT, 2000 \nEXPLANATORY MEMORANDUM \nThe act seeks to prohibit. \n"
    "ARRANGEMENT OF SECTIONS \nSections: \n"
    "1. Short title and commencement  \n2. Interpretation \n"
    "3. Establishment of the independent Corrupt Practices, etc .Commission, Composition \n"
    "4. Appointment of officers of the commission, Oath of office \n"
    "5. Powers and Immunities of officers of the Commission; Ca p.359LFN \n"
    "6. General duties of the Commission \n\n"
    "Short title and commencement 1\n(1) This Act may be cited as the Corrupt Practices Act.\n"
    "Interpretation 2\nIn this Act, Commission means the Commission.\n"
    "Establishment of the Commission 3\n(1) There is established a Commission.\n"
    "Appointment of officers 4\n(8) An officer appointed shall have powers.\n\n"
    "Powers and Immunities of officers of the Commission Cap. 359 LFN. 5\n"
    "(1) Subject to the provision of this Act, an officer when investigating has powers.\n"
    "General duties of the Commission 6\nIt shall be the duty of the Commission to receive complaints.\n"
)
PAGES = [(0, 1), (400, 2)]


def test_clean_title_removes_cap_reference():
    assert clean_title("Powers and Immunities of officers of the Commission; Ca p.359LFN") == \
        "Powers and Immunities of officers of the Commission"


def test_parse_toc_finds_all_sections_in_order():
    toc, _ = parse_toc(SAMPLE)
    assert list(toc) == [1, 2, 3, 4, 5, 6]
    assert toc[2] == "Interpretation"


def test_locate_sections_finds_body_not_toc():
    toc, toc_end = parse_toc(SAMPLE)
    sections, missing = locate_sections(SAMPLE, toc, toc_end, PAGES)
    assert missing == []
    s5 = next(s for s in sections if s["section"] == 5)
    assert "an officer when investigating" in s5["text"]
    assert "General duties" not in s5["text"]


def test_find_section_number():
    assert find_section_number("What does section 5 say?") == 5
    assert find_section_number("Explain s. 8 please") == 8
    assert find_section_number("What is gratification?") is None


class FakeStore:
    def __init__(self):
        self.calls = []

    def get(self, where):
        self.calls.append(("get", where))
        return {"documents": ["Section 5 text"], "metadatas": [{"section": 5, "page": 6}]}

    def similarity_search(self, question, k):
        self.calls.append(("search", question))
        return []


def test_section_question_uses_exact_lookup():
    store = FakeStore()
    docs = retrieve(store, "What does section 5 say?")
    assert store.calls[0] == ("get", {"section": 5})
    assert docs[0].metadata["section"] == 5


def test_general_question_uses_similarity_search():
    store = FakeStore()
    retrieve(store, "What is the penalty for bribery?")
    assert store.calls[0][0] == "search"
