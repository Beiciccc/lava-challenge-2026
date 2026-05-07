#!/usr/bin/env python3
"""Build an open-model EasyOCR cache for low-text PDFs.

By default this keeps the original cheap behavior: OCR only very short
zero-text PDFs. Pass a higher page limit and --gpu on the remote server to cover
the scan-heavy low-text set with an open model.
"""

from __future__ import annotations

import argparse
import json
import re
import tempfile
import warnings
from pathlib import Path

import easyocr
import fitz  # type: ignore


warnings.filterwarnings("ignore", message=".*pin_memory.*")


def clean_text(text: str) -> str:
    text = text.replace("\x00", " ")
    text = re.sub(r"[ \t\r\f\v]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def text_totals(normal_cache: Path) -> dict[str, int]:
    totals: dict[str, int] = {}
    with normal_cache.open("r", encoding="utf-8") as f:
        for line in f:
            rec = json.loads(line)
            totals[rec["file_id"]] = totals.get(rec["file_id"], 0) + len(rec.get("text", "").strip())
    return totals


def existing(cache_path: Path) -> set[tuple[str, int]]:
    seen: set[tuple[str, int]] = set()
    if not cache_path.exists():
        return seen
    with cache_path.open("r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            rec = json.loads(line)
            seen.add((rec["file_id"], int(rec["page_number"])))
    return seen


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pdf-root", default="data/raw/test_pdfs")
    parser.add_argument("--normal-cache", default="data/processed/pdf_pages.jsonl")
    parser.add_argument("--output", default="data/processed/ocr_pages_easyocr_small.jsonl")
    parser.add_argument("--max-normal-chars", type=int, default=20)
    parser.add_argument("--max-pages", type=int, default=2)
    parser.add_argument("--zoom", type=float, default=1.2)
    parser.add_argument("--gpu", action="store_true")
    args = parser.parse_args()

    totals = text_totals(Path(args.normal_cache))
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    seen = existing(output)

    targets: list[Path] = []
    for pdf in sorted(Path(args.pdf_root).rglob("*.pdf")):
        if pdf.name.startswith("._"):
            continue
        if totals.get(pdf.stem, 0) > args.max_normal_chars:
            continue
        with fitz.open(pdf) as doc:
            if doc.page_count <= args.max_pages:
                targets.append(pdf)

    ja_reader: easyocr.Reader | None = None
    vi_reader: easyocr.Reader | None = None

    print(f"targets={len(targets)} existing_pages={len(seen)} output={output}", flush=True)
    processed = 0
    with output.open("a", encoding="utf-8") as f, tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        for pdf_i, pdf_path in enumerate(targets, start=1):
            file_id = pdf_path.stem
            if file_id.startswith("v_"):
                if vi_reader is None:
                    vi_reader = easyocr.Reader(["vi", "en"], gpu=args.gpu, verbose=False)
                reader = vi_reader
            else:
                if ja_reader is None:
                    ja_reader = easyocr.Reader(["ja", "en"], gpu=args.gpu, verbose=False)
                reader = ja_reader

            with fitz.open(pdf_path) as doc:
                for page_idx, page in enumerate(doc, start=1):
                    if (file_id, page_idx) in seen:
                        continue
                    image_path = tmp / f"{file_id}_{page_idx:04d}.png"
                    pix = page.get_pixmap(matrix=fitz.Matrix(args.zoom, args.zoom), alpha=False)
                    pix.save(image_path)
                    parts = reader.readtext(str(image_path), detail=0, paragraph=True)
                    image_path.unlink(missing_ok=True)
                    text = clean_text("\n".join(str(x) for x in parts))
                    f.write(
                        json.dumps(
                            {
                                "file_id": file_id,
                                "page_number": page_idx,
                                "text": text,
                                "source": "easyocr",
                            },
                            ensure_ascii=False,
                        )
                        + "\n"
                    )
                    f.flush()
                    processed += 1
            print(f"finished_pdf={pdf_i}/{len(targets)} {file_id} processed_pages={processed}", flush=True)

    print("done", flush=True)


if __name__ == "__main__":
    main()
