"""Convert a product PDF into agent knowledge.

Usage:
    pip install pypdf
    python -m scripts.import_pdf path/to/brochure.pdf

Writes docs/<name>.txt, which the agent loads as PRODUCT KNOWLEDGE.
Review the output file and trim it to what matters — cleaner knowledge
means better answers.
"""
import sys
from pathlib import Path


def main():
    if len(sys.argv) < 2:
        print("Usage: python -m scripts.import_pdf <file.pdf>")
        sys.exit(1)
    src = Path(sys.argv[1])
    if not src.exists():
        print(f"File not found: {src}")
        sys.exit(1)
    try:
        from pypdf import PdfReader
    except ImportError:
        print("Missing dependency. Run:  pip install pypdf")
        sys.exit(1)

    docs = Path(__file__).resolve().parent.parent / "docs"
    docs.mkdir(exist_ok=True)
    out = docs / (src.stem + ".txt")

    reader = PdfReader(str(src))
    text = "\n".join((page.extract_text() or "") for page in reader.pages)
    out.write_text(text.strip())
    print(f"Wrote {out} ({len(text)} chars from {len(reader.pages)} pages)")
    print("Review + trim that file, then restart the app to load it.")


if __name__ == "__main__":
    main()
