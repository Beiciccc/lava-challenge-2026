#!/usr/bin/env python3
"""Build an OCR text cache for scan-heavy LAVA PDFs using macOS Vision.

This is intentionally local-only and incremental. It targets PDFs whose normal
text extraction is empty or very small, then writes one JSONL record per page.
"""

from __future__ import annotations

import argparse
import json
import re
import tempfile
from pathlib import Path

import fitz  # type: ignore
from Foundation import NSURL
import Vision


def clean_text(text: str) -> str:
    text = text.replace("\x00", " ")
    text = re.sub(r"[ \t\r\f\v]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def existing_records(cache_path: Path) -> set[tuple[str, int]]:
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


def normal_text_totals(normal_cache: Path) -> dict[str, int]:
    totals: dict[str, int] = {}
    with normal_cache.open("r", encoding="utf-8") as f:
        for line in f:
            rec = json.loads(line)
            totals[rec["file_id"]] = totals.get(rec["file_id"], 0) + len(rec.get("text", "").strip())
    return totals


def ocr_image(image_path: Path, languages: list[str]) -> str:
    lines: list[str] = []

    def handler(request, error) -> None:  # noqa: ANN001
        if error:
            return
        for observation in request.results() or []:
            candidates = observation.topCandidates_(1)
            if candidates:
                lines.append(str(candidates[0].string()))

    request = Vision.VNRecognizeTextRequest.alloc().initWithCompletionHandler_(handler)
    request.setRecognitionLevel_(Vision.VNRequestTextRecognitionLevelAccurate)
    request.setUsesLanguageCorrection_(True)
    try:
        request.setRecognitionLanguages_(languages)
    except Exception:
        request.setRecognitionLanguages_(["ja-JP", "en-US"])

    url = NSURL.fileURLWithPath_(str(image_path.resolve()))
    image_handler = Vision.VNImageRequestHandler.alloc().initWithURL_options_(url, {})
    image_handler.performRequests_error_([request], None)
    return clean_text("\n".join(lines))


def languages_for_file(file_id: str) -> list[str]:
    if file_id.startswith("v_"):
        return ["vi-VN", "en-US", "ja-JP"]
    return ["ja-JP", "en-US", "vi-VN"]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pdf-root", default="data/raw/test_pdfs")
    parser.add_argument("--normal-cache", default="data/processed/pdf_pages.jsonl")
    parser.add_argument("--output", default="data/processed/ocr_pages_vision.jsonl")
    parser.add_argument("--min-normal-chars", type=int, default=1000)
    parser.add_argument("--zoom", type=float, default=2.0)
    parser.add_argument("--limit-files", type=int, default=0)
    args = parser.parse_args()

    pdf_root = Path(args.pdf_root)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)

    totals = normal_text_totals(Path(args.normal_cache))
    targets = {file_id for file_id, total in totals.items() if total < args.min_normal_chars}
    if args.limit_files:
        targets = set(sorted(targets)[: args.limit_files])

    pdfs = [p for p in sorted(pdf_root.rglob("*.pdf")) if not p.name.startswith("._") and p.stem in targets]
    seen = existing_records(output)

    print(f"targets={len(pdfs)} existing_pages={len(seen)} output={output}", flush=True)
    with output.open("a", encoding="utf-8") as f, tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        processed = 0
        for pdf_i, pdf_path in enumerate(pdfs, start=1):
            file_id = pdf_path.stem
            languages = languages_for_file(file_id)
            with fitz.open(pdf_path) as doc:
                for page_idx, page in enumerate(doc, start=1):
                    if (file_id, page_idx) in seen:
                        continue
                    image_path = tmp / f"{file_id}_{page_idx:04d}.png"
                    pix = page.get_pixmap(matrix=fitz.Matrix(args.zoom, args.zoom), alpha=False)
                    pix.save(image_path)
                    text = ocr_image(image_path, languages)
                    image_path.unlink(missing_ok=True)
                    f.write(
                        json.dumps(
                            {
                                "file_id": file_id,
                                "page_number": page_idx,
                                "text": text,
                                "source": "macos_vision",
                            },
                            ensure_ascii=False,
                        )
                        + "\n"
                    )
                    f.flush()
                    processed += 1
                    if processed % 25 == 0:
                        print(f"processed_pages={processed} pdf={pdf_i}/{len(pdfs)} last={file_id}:{page_idx}", flush=True)
            print(f"finished_pdf={pdf_i}/{len(pdfs)} {file_id}", flush=True)
    print("done", flush=True)


if __name__ == "__main__":
    main()

