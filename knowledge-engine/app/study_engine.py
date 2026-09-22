from __future__ import annotations

import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions, RapidOcrOptions
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling_core.transforms.chunker.hierarchical_chunker import HierarchicalChunker


PROJECT_ROOT = Path(__file__).resolve().parents[2]
ENGINE_ROOT = PROJECT_ROOT / "knowledge-engine"
CONFIG_FILE = ENGINE_ROOT / "config" / "settings.json"
INPUT_DIR = ENGINE_ROOT / "input"

MIN_CHUNK_CHARS = 80
MAX_CHUNK_CHARS = 6500


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_settings() -> dict:
    if not CONFIG_FILE.exists():
        raise FileNotFoundError(f"Missing settings file: {CONFIG_FILE}")

    with CONFIG_FILE.open("r", encoding="utf-8-sig") as f:
        return json.load(f)


def clean_text(text: str) -> str:
    if not text:
        return ""

    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = text.replace("\u00a0", " ")
    text = text.replace("\u00ad", "")

    lines = []
    blank = False

    for line in text.split("\n"):
        line = re.sub(r"[ \t]+", " ", line).strip()

        if not line:
            if not blank:
                lines.append("")
            blank = True
        else:
            lines.append(line)
            blank = False

    text = "\n".join(lines).strip()
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text


def split_text(text: str, limit: int = MAX_CHUNK_CHARS) -> list[str]:
    if len(text) <= limit:
        return [text]

    paragraphs = re.split(r"\n{2,}", text)
    parts = []
    current = ""

    for paragraph in paragraphs:
        paragraph = paragraph.strip()
        if not paragraph:
            continue

        candidate = (
            f"{current}\n\n{paragraph}".strip()
            if current
            else paragraph
        )

        if len(candidate) <= limit:
            current = candidate
            continue

        if current:
            parts.append(current)
            current = ""

        if len(paragraph) <= limit:
            current = paragraph
            continue

        words = paragraph.split()
        buffer = ""

        for word in words:
            candidate_word = (
                f"{buffer} {word}".strip()
                if buffer
                else word
            )

            if len(candidate_word) <= limit:
                buffer = candidate_word
            else:
                if buffer:
                    parts.append(buffer)
                buffer = word

        if buffer:
            current = buffer

    if current:
        parts.append(current)

    return [p.strip() for p in parts if p.strip()]


def get_pages(chunk) -> list[int]:
    pages = set()

    meta = getattr(chunk, "meta", None)
    doc_items = getattr(meta, "doc_items", None) if meta else None

    for item in doc_items or []:
        for prov in getattr(item, "prov", []) or []:
            page = getattr(prov, "page_no", None)

            if page is not None:
                try:
                    pages.add(int(page))
                except (TypeError, ValueError):
                    pass

    return sorted(pages)


def get_headings(chunk) -> list[str]:
    meta = getattr(chunk, "meta", None)
    headings = getattr(meta, "headings", None) if meta else None

    if not headings:
        return []

    return [
        str(h).strip()
        for h in headings
        if str(h).strip()
    ]


def main() -> int:
    start = time.perf_counter()

    print("=" * 70)
    print("AI Electrical BIM - Study Engine")
    print("PHASE 1 : Document -> Knowledge Dataset")
    print("=" * 70)

    settings = load_settings()

    library_path = Path(settings["library_path"])
    processed_path = Path(settings["processed_path"])

    INPUT_DIR.mkdir(parents=True, exist_ok=True)
    processed_path.mkdir(parents=True, exist_ok=True)

    supported = {
        ext.lower()
        for ext in settings.get(
            "supported_extensions",
            [".pdf", ".docx"]
        )
    }

    if len(sys.argv) > 1:
        source = Path(sys.argv[1])
        if not source.is_file():
            print()
            print("[ERROR] Source document not found:")
            print(source)
            return 1

    books = sorted(
        p for p in INPUT_DIR.iterdir()
        if p.is_file() and p.suffix.lower() in supported
    )

    if len(sys.argv) == 1 and not books:
        print()
        print("[ERROR] No source document found.")
        print(f"Put ONE PDF/DOCX inside:")
        print(INPUT_DIR)
        return 1

    if len(sys.argv) == 1 and len(books) > 1:
        print()
        print("[ERROR] More than one source document found.")
        for book in books:
            print(f"  - {book.name}")
        print()
        print("For the first test, keep ONE book only.")
        return 1

    source = Path(sys.argv[1]) if len(sys.argv) > 1 else books[0]
    book_name = source.stem
    book_output = processed_path / book_name
    book_output.mkdir(parents=True, exist_ok=True)

    print()
    print(f"[SOURCE] {source.name}")
    print(f"[OUTPUT] {book_output}")
    print()

    print("[1/5] Converting document with Docling...")
    pipeline_options = PdfPipelineOptions(ocr_options=RapidOcrOptions(lang=["arabic"], backend="onnxruntime"))
    converter = DocumentConverter(format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)})
    result = converter.convert(source)
    doc = result.document

    print("[OK] Conversion complete")

    print("[2/5] Saving native Docling document...")
    native_json = book_output / f"{book_name}.docling.json"
    doc.save_as_json(
        native_json,
        ensure_ascii=False
    )

    print("[3/5] Building hierarchical chunks...")
    chunker = HierarchicalChunker(merge_list_items=True)

    records = []
    page_set = set()
    raw_count = 0

    for base_chunk in chunker.chunk(doc):
        raw_count += 1

        text = getattr(base_chunk, "text", "") or ""
        contextualized = chunker.contextualize(base_chunk) or text
        cleaned = clean_text(contextualized)

        if len(cleaned) < MIN_CHUNK_CHARS:
            continue

        pages = get_pages(base_chunk)
        headings = get_headings(base_chunk)

        for piece_number, piece in enumerate(
            split_text(cleaned),
            start=1
        ):
            page_set.update(pages)

            records.append(
                {
                    "schema_version": "1.0",
                    "chunk_id": len(records) + 1,
                    "source": source.name,
                    "source_path": str(source),
                    "pages": pages,
                    "page_start": pages[0] if pages else None,
                    "page_end": pages[-1] if pages else None,
                    "headings": headings,
                    "text": piece,
                    "char_count": len(piece),
                    "parent_chunk": raw_count,
                    "piece_number": piece_number,
                    "created_at": now_iso(),
                }
            )

    if not records:
        print()
        print("[ERROR] No usable text chunks were produced.")
        print("The document may be scanned/image-only.")
        return 1

    print(f"[OK] Source chunks      : {raw_count}")
    print(f"[OK] Knowledge chunks   : {len(records)}")
    print(f"[OK] Pages with source  : {len(page_set)}")

    print("[4/5] Writing knowledge JSONL...")

    knowledge_jsonl = book_output / f"{book_name}.knowledge.jsonl"

    with knowledge_jsonl.open("w", encoding="utf-8") as f:
        for record in records:
            f.write(
                json.dumps(
                    record,
                    ensure_ascii=False
                )
                + "\n"
            )

    print("[5/5] Writing reading copy + manifest...")

    reading_md = book_output / f"{book_name}.reading.md"
    reading_md.write_text(
        f"# {source.name}\n\n"
        + doc.export_to_markdown(),
        encoding="utf-8"
    )

    manifest = {
        "schema_version": "1.0",
        "engine": "Study Engine",
        "phase": 1,
        "created_at": now_iso(),
        "source": {
            "filename": source.name,
            "path": str(source),
        },
        "library_path": str(library_path),
        "processed_path": str(processed_path),
        "output_folder": str(book_output),
        "docling": {
            "converter": "DocumentConverter",
            "chunker": "HierarchicalChunker",
        },
        "statistics": {
            "raw_chunks": raw_count,
            "knowledge_chunks": len(records),
            "pages_with_provenance": len(page_set),
        },
    }

    manifest_file = book_output / f"{book_name}.manifest.json"

    manifest_file.write_text(
        json.dumps(
            manifest,
            ensure_ascii=False,
            indent=2
        ),
        encoding="utf-8"
    )

    elapsed = time.perf_counter() - start

    print()
    print("=" * 70)
    print("PHASE 1 COMPLETE")
    print("=" * 70)
    print(f"Knowledge : {knowledge_jsonl}")
    print(f"Docling  : {native_json}")
    print(f"Reading  : {reading_md}")
    print(f"Manifest : {manifest_file}")
    print(f"Time     : {elapsed:.2f} seconds")
    print("=" * 70)

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print()
        print("[FATAL ERROR]")
        print(type(exc).__name__, ":", exc)
        sys.exit(1)
