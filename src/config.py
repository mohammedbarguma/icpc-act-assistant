"""Central settings. Override any value in the .env file."""

import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

PDF_PATH = os.getenv("PDF_PATH", str(BASE_DIR / "data" / "icpc act.pdf"))
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
LLM_MODEL = os.getenv("LLM_MODEL", "openai/gpt-oss-120b")
MODELS = [LLM_MODEL] + [m for m in ("openai/gpt-oss-120b", "openai/gpt-oss-20b") if m != LLM_MODEL]

CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "1500"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "200"))
COLLECTION_NAME = "icpc_act"

DISCLAIMER = (
    "Automated summary of the Act's text, not legal advice. "
    "Confirm against the official text."
)
