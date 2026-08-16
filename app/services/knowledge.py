"""Load the agency's product knowledge from ./knowledge into the agent prompt.

Drop .md or .txt files describing your life & health products into the
knowledge/ folder. PDFs work too if pypdf is installed
(pip install pypdf) — otherwise export PDFs to text first.
Content is capped so the prompt stays small and cheap.
"""
import os
from pathlib import Path

KNOWLEDGE_DIR = Path(os.environ.get("KNOWLEDGE_DIR", "knowledge"))
MAX_CHARS = 9000


def _read_pdf(path: Path) -> str:
    try:
        from pypdf import PdfReader
    except ImportError:
        return ""
    try:
        return "\n".join((p.extract_text() or "") for p in PdfReader(str(path)).pages)
    except Exception:
        return ""


def load_knowledge() -> str:
    if not KNOWLEDGE_DIR.exists():
        return ""
    chunks = []
    for f in sorted(KNOWLEDGE_DIR.iterdir()):
        if f.suffix.lower() in (".md", ".txt"):
            text = f.read_text(errors="ignore")
        elif f.suffix.lower() == ".pdf":
            text = _read_pdf(f)
        else:
            continue
        text = text.strip()
        if text:
            chunks.append(f"## {f.stem}\n{text}")
    joined = "\n\n".join(chunks)
    return joined[:MAX_CHARS]
