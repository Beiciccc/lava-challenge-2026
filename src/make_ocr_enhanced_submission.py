#!/usr/bin/env python3
"""Build an OCR-enhanced LAVA submission.

This reuses the text TF-IDF baseline, but fills pages from PDFs whose extracted
text is empty or very small using macOS Live Text via ocrmac. The OCR cache is
kept separate from the original PyMuPDF text cache.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from make_baseline_submission import Page, answer_for_row, load_or_build_page_cache, retrieve_pages


def file_text_len(pages: list[Page]) -> int:
    return sum(len(p.text or "") for p in pages)


def pdf_paths_by_stem(pdf_root: Path) -> dict[str, Path]:
    return {p.stem: p for p in pdf_root.rglob("*.pdf") if not p.name.startswith("._")}


def ocr_page(pdf_path: Path, page_index: int, scale: float) -> str:
    import fitz  # type: ignore
    from ocrmac import ocrmac  # type: ignore
    from PIL import Image

    with fitz.open(pdf_path) as doc:
        page = doc[page_index]
        pix = page.get_pixmap(matrix=fitz.Matrix(scale, scale), alpha=False)
        image = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

    records = ocrmac.OCR(image, framework="livetext", unit="line").recognize()
    lines = [str(item[0]).strip() for item in records if str(item[0]).strip()]
    return "\n".join(lines)


def load_ocr_cache(cache_path: Path) -> dict[tuple[str, int], str]:
    if not cache_path.exists():
        return {}
    out: dict[tuple[str, int], str] = {}
    with cache_path.open("r", encoding="utf-8") as f:
        for line in f:
            rec = json.loads(line)
            out[(rec["file_id"], int(rec["page_number"]))] = rec.get("text", "")
    return out


def append_ocr_cache(cache_path: Path, file_id: str, page_number: int, text: str) -> None:
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    with cache_path.open("a", encoding="utf-8") as f:
        f.write(
            json.dumps(
                {
                    "file_id": file_id,
                    "page_number": page_number,
                    "text": text,
                    "source": "ocrmac_livetext",
                },
                ensure_ascii=False,
            )
            + "\n"
        )


def build_ocr_enhanced_pages(
    by_file: dict[str, list[Page]],
    pdf_root: Path,
    ocr_cache_path: Path,
    file_text_threshold: int,
    page_text_threshold: int,
    scale: float,
) -> dict[str, list[Page]]:
    paths = pdf_paths_by_stem(pdf_root)
    cached = load_ocr_cache(ocr_cache_path)
    enhanced: dict[str, list[Page]] = {}

    targets = {
        file_id
        for file_id, pages in by_file.items()
        if file_text_len(pages) <= file_text_threshold
    }
    print(f"ocr target files={len(targets)} threshold={file_text_threshold}", flush=True)

    for file_i, (file_id, pages) in enumerate(sorted(by_file.items()), start=1):
        new_pages: list[Page] = []
        should_ocr_file = file_id in targets
        for page in pages:
            text = page.text
            should_ocr_page = should_ocr_file or len(text or "") <= page_text_threshold
            if should_ocr_page and file_id in paths:
                key = (file_id, page.page_number)
                if key in cached:
                    ocr_text = cached[key]
                else:
                    try:
                        ocr_text = ocr_page(paths[file_id], page.page_number - 1, scale)
                    except Exception as exc:
                        ocr_text = ""
                        print(f"OCR failed {file_id} p{page.page_number}: {exc}", flush=True)
                    append_ocr_cache(ocr_cache_path, file_id, page.page_number, ocr_text)
                    cached[key] = ocr_text
                    if len(cached) % 25 == 0:
                        print(f"ocr cached pages={len(cached)}", flush=True)
                if len(ocr_text) > len(text or ""):
                    text = ocr_text
            new_pages.append(Page(file_id, page.page_number, text))
        enhanced[file_id] = new_pages
        if file_i % 25 == 0:
            print(f"processed files={file_i}/{len(by_file)}", flush=True)
    return enhanced


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--test", default="data/raw/test.csv")
    parser.add_argument("--sample", default="data/raw/sample_submission.csv")
    parser.add_argument("--pdf-root", default="data/raw/test_pdfs")
    parser.add_argument("--text-cache", default="data/processed/pdf_pages.jsonl")
    parser.add_argument("--ocr-cache", default="data/processed/pdf_pages_ocrmac.jsonl")
    parser.add_argument("--output", default="submissions/submission_ocr_enhanced.csv")
    parser.add_argument("--file-text-threshold", type=int, default=1000)
    parser.add_argument("--page-text-threshold", type=int, default=0)
    parser.add_argument("--scale", type=float, default=2.0)
    args = parser.parse_args()

    test = pd.read_csv(args.test)
    sample = pd.read_csv(args.sample)
    by_file = load_or_build_page_cache(Path(args.pdf_root), Path(args.text_cache))
    by_file = build_ocr_enhanced_pages(
        by_file=by_file,
        pdf_root=Path(args.pdf_root),
        ocr_cache_path=Path(args.ocr_cache),
        file_text_threshold=args.file_text_threshold,
        page_text_threshold=args.page_text_threshold,
        scale=args.scale,
    )

    rows: list[dict[str, str]] = []
    for _, row in test.iterrows():
        pages = by_file.get(row["file_id"], [])
        page_numbers, _ = retrieve_pages(row["question"], pages)
        rows.append(
            {
                "id": row["id"],
                "answer": answer_for_row(row, pages, page_numbers),
                "evidence_page_number": str(page_numbers),
            }
        )

    sub = pd.DataFrame(rows, columns=list(sample.columns))
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    sub.to_csv(out, index=False)
    print(f"wrote {out}", flush=True)


if __name__ == "__main__":
    main()
