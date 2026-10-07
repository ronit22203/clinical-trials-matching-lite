"""Turn raw medical PDFs into GraphRAG input text with Surya OCR v2.

Pages are rendered with pypdfium2 and recognized by Surya 2
(``surya-ocr`` >= 0.20). Block HTML is flattened to plain text and saved as
``.txt`` because GraphRAG's text loader only ingests that extension.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

_manager = None
_recognizer = None


def _load_env() -> None:
    env_path = REPO_ROOT / ".env"
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    load_dotenv(dotenv_path=env_path, override=False)


def _recognition_predictor():
    global _manager, _recognizer
    if _recognizer is None:
        try:
            from surya.inference import SuryaInferenceManager
            from surya.recognition import RecognitionPredictor
        except ImportError as error:
            raise SystemExit(
                "Surya OCR v2 is not installed. Install it with `uv pip install surya-ocr`. "
                "Apple Silicon also needs llama.cpp (`brew install llama.cpp`); "
                "an NVIDIA GPU uses vLLM."
            ) from error
        _manager = SuryaInferenceManager()
        _recognizer = RecognitionPredictor(_manager)
    return _recognizer


def _render_pdf(pdf_path: Path, scale: float = 2.0) -> list:
    import pypdfium2 as pdfium

    pdf = pdfium.PdfDocument(str(pdf_path))
    images: list = []
    try:
        for page in pdf:
            bitmap = page.render(scale=scale)
            images.append(bitmap.to_pil().convert("RGB"))
            bitmap.close()
    finally:
        pdf.close()
    return images


def _html_to_text(html: str) -> str:
    if not html or not html.strip():
        return ""
    from bs4 import BeautifulSoup

    return BeautifulSoup(html, "html.parser").get_text("\n", strip=True)


def extract_text_surya(pdf_path: Path) -> tuple[str, str]:
    """Extract reading-order text from a PDF with Surya OCR v2."""
    images = _render_pdf(pdf_path)
    if not images:
        return "", "surya_v2"

    predictor = _recognition_predictor()
    pages: list[str] = []
    batch_size = 4
    for start in range(0, len(images), batch_size):
        predictions = predictor(images[start : start + batch_size])
        for page_prediction in predictions:
            blocks = []
            for block in page_prediction.blocks:
                if getattr(block, "skipped", False):
                    continue
                text = _html_to_text(getattr(block, "html", "") or "")
                if text:
                    blocks.append(text)
            pages.append("\n\n".join(blocks))
    return "\n\n".join(page for page in pages if page.strip()), "surya_v2"


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
        text, reader_name = extract_text_surya(pdf_path)
        if not text.strip():
            print(f"skip {pdf_path.name}: {reader_name} returned no text", file=sys.stderr)
            continue
        output_path = destination / f"{pdf_path.stem}.txt"
        output_path.write_text(text, encoding="utf-8")
        written.append(output_path)
        print(f"{pdf_path.name} -> {output_path} ({reader_name})")
    return written


def main(argv: list[str] | None = None) -> None:
    _load_env()
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
