#!/usr/bin/env python3
"""Build an open Tesseract OCR cache for low-text PDFs."""

from __future__ import annotations

import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
import json
import re
import subprocess
import tempfile
from pathlib import Path

import fitz  # type: ignore


Task = tuple[str, str, int, str, float, int]


def clean_text(text: str) -> str:
    text = text.replace("\x00", " ")
    text = re.sub(r"[ \t\r\f\v]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def text_totals(normal_cache: Path) -> dict[str, int]:
    totals: dict[str, int] = {}
    with normal_cache.open("r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
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


def ocr_image(image_path: Path, lang: str, psm: int) -> str:
    cmd = [
        "tesseract",
        str(image_path),
        "stdout",
        "-l",
        lang,
        "--psm",
        str(psm),
    ]
    proc = subprocess.run(cmd, check=False, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if proc.returncode != 0:
        return ""
    return clean_text(proc.stdout)


def ocr_task(task: Task) -> dict[str, object]:
    file_id, pdf_path_raw, page_number, lang, zoom, psm = task
    pdf_path = Path(pdf_path_raw)
    with tempfile.TemporaryDirectory() as tmpdir:
        image_path = Path(tmpdir) / f"{file_id}_{page_number:04d}.png"
        with fitz.open(pdf_path) as doc:
            page = doc[page_number - 1]
            pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=False)
            pix.save(image_path)
        text = ocr_image(image_path, lang=lang, psm=psm)
    return {
        "file_id": file_id,
        "page_number": page_number,
        "text": text,
        "source": f"tesseract_{lang}_psm{psm}",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pdf-root", default="data/raw/test_pdfs")
    parser.add_argument("--normal-cache", default="data/processed/pdf_pages.jsonl")
    parser.add_argument("--output", default="data/processed/ocr_pages_tesseract_lowtext.jsonl")
    parser.add_argument("--max-normal-chars", type=int, default=1000)
    parser.add_argument("--max-pages", type=int, default=100)
    parser.add_argument("--zoom", type=float, default=2.0)
    parser.add_argument("--psm", type=int, default=6)
    parser.add_argument("--workers", type=int, default=1)
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

    total_pages = 0
    for pdf in targets:
        with fitz.open(pdf) as doc:
            total_pages += doc.page_count
    print(
        f"targets={len(targets)} pages={total_pages} existing_pages={len(seen)} "
        f"output={output} zoom={args.zoom} psm={args.psm} workers={args.workers}",
        flush=True,
    )

    tasks: list[Task] = []
    file_page_counts: dict[str, int] = {}
    for pdf_path in targets:
        file_id = pdf_path.stem
        lang = "vie+eng" if file_id.startswith("v_") else "jpn+eng"
        with fitz.open(pdf_path) as doc:
            file_page_counts[file_id] = doc.page_count
            for page_idx in range(1, doc.page_count + 1):
                if (file_id, page_idx) in seen:
                    continue
                tasks.append((file_id, str(pdf_path), page_idx, lang, args.zoom, args.psm))

    processed = 0
    completed_by_file: dict[str, int] = {}
    with output.open("a", encoding="utf-8") as f:
        if args.workers <= 1:
            iterator = map(ocr_task, tasks)
        else:
            executor = ProcessPoolExecutor(max_workers=args.workers)
            iterator = as_completed([executor.submit(ocr_task, task) for task in tasks])

        try:
            for item in iterator:
                rec = item.result() if hasattr(item, "result") else item
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                f.flush()
                file_id = str(rec["file_id"])
                completed_by_file[file_id] = completed_by_file.get(file_id, 0) + 1
                processed += 1
                if completed_by_file[file_id] == file_page_counts[file_id]:
                    done_files = sum(
                        1 for fid, count in completed_by_file.items() if count == file_page_counts[fid]
                    )
                    print(
                        f"finished_pdf={done_files}/{len(targets)} {file_id} processed_pages={processed}",
                        flush=True,
                    )
                elif processed % 25 == 0:
                    print(f"processed_pages={processed}/{len(tasks)}", flush=True)
        finally:
            if args.workers > 1:
                executor.shutdown(wait=True, cancel_futures=True)

    print("done", flush=True)


if __name__ == "__main__":
    main()
