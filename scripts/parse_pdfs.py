"""Turn raw medical PDFs into GraphRAG input text.

Docling is preferred because it keeps layout and tables. When Docling is
installed with a Surya OCR backend, that is the reader it uses. Extracted
markdown is saved as ``.txt`` because GraphRAG's text loader only ingests
files matching ``*.txt``.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def _with_docling(pdf_path: Path) -> str:
    from docling.document_converter import DocumentConverter

    result = DocumentConverter().convert(str(pdf_path))
    return result.document.export_to_markdown()


def _with_pypdf(pdf_path: Path) -> str:
    from pypdf import PdfReader

    reader = PdfReader(str(pdf_path))
    pages = [(page.extract_text() or "") for page in reader.pages]
    return "\n\n".join(pages).strip()


def extract_text(pdf_path: Path) -> tuple[str, str]:
    """Return ``(text, reader_name)`` for one PDF."""
    try:
        return _with_docling(pdf_path), "docling"
    except ImportError:
        pass
    try:
        return _with_pypdf(pdf_path), "pypdf"
    except ImportError as error:
        raise SystemExit(
            "No PDF reader is installed. Install Docling for layout-aware OCR "
            "(`uv pip install docling`) or pypdf (`uv pip install pypdf`)."
        ) from error


def parse_pdfs(source: Path, destination: Path) -> list[Path]:
    """Write one ``.txt`` file per PDF found under ``source``."""
    if not source.is_dir():
        raise SystemExit(f"Input directory does not exist: {source}")
    pdfs = sorted(source.glob("*.pdf"))
    if not pdfs:
        raise SystemExit(f"No PDF files found in {source}")

    destination.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for pdf_path in pdfs:
        text, reader_name = extract_text(pdf_path)
        if not text.strip():
            print(f"skip {pdf_path.name}: {reader_name} returned no text", file=sys.stderr)
            continue
        output_path = destination / f"{pdf_path.stem}.txt"
        output_path.write_text(text, encoding="utf-8")
        written.append(output_path)
        print(f"{pdf_path.name} -> {output_path} ({reader_name})")
    return written


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("data/raw_documents"),
        help="Directory of raw medical PDFs",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/input"),
        help="Directory for GraphRAG text input",
    )
    args = parser.parse_args(argv)
    parse_pdfs(args.input, args.output)


if __name__ == "__main__":
    main()
