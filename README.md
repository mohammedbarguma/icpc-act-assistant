# ICPC Act chatbot

A Streamlit chatbot that answers questions about the Corrupt Practices and Other
Related Offences Act, 2000, citing sections and pages.

## Setup (Windows, cmd)

    python -m venv .venv
    .venv\Scripts\activate.bat
    python -m pip install -r requirements.txt
    copy .env.example .env        (then put your Groq key in .env)

Put the Act's PDF in `data\` as `icpc act.pdf`, or set PDF_PATH in `.env`.

## Run

    pytest
    streamlit run app.py

## How it works

- `src/ingestion.py` reads the PDF, parses the Arrangement of Sections and finds each
  section in the body by its title, then chunks by section.
- `src/retrieval.py` looks up "section N" questions exactly and uses semantic search otherwise.
- `src/chatbot.py` rewrites follow-up questions into standalone ones, then answers with Groq.
- `app.py` is the Streamlit chat interface.
