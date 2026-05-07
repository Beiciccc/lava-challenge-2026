#!/usr/bin/env python3
"""Rule-cleaned answers on top of the tuned OCR evidence baseline."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from make_baseline_submission import load_or_build_page_cache, merge_ocr_cache, retrieve_pages
from make_submission_v3_rules import answer_for_row_v3, validate_submission


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--test", default="data/raw/test.csv")
    parser.add_argument("--sample", default="data/raw/sample_submission.csv")
    parser.add_argument("--pdf-root", default="data/raw/test_pdfs")
    parser.add_argument("--cache", default="data/processed/pdf_pages.jsonl")
    parser.add_argument("--ocr-cache", default="data/processed/ocr_pages_vision.jsonl")
    parser.add_argument("--output", default="submissions/submission_004_rules_ocr_tuned.csv")
    parser.add_argument("--max-pages", type=int, default=4)
    parser.add_argument("--rel-threshold", type=float, default=0.7)
    parser.add_argument("--min-score", type=float, default=0.03)
    args = parser.parse_args()

    test = pd.read_csv(args.test)
    sample = pd.read_csv(args.sample)
    by_file = load_or_build_page_cache(Path(args.pdf_root), Path(args.cache))
    merge_ocr_cache(by_file, Path(args.ocr_cache))

    rows: list[dict[str, str]] = []
    for _, row in test.iterrows():
        pages = by_file.get(row["file_id"], [])
        page_numbers, _ = retrieve_pages(
            row["question"],
            pages,
            max_pages=args.max_pages,
            rel_threshold=args.rel_threshold,
            min_score=args.min_score,
        )
        rows.append(
            {
                "id": row["id"],
                "answer": answer_for_row_v3(row, pages, page_numbers),
                "evidence_page_number": str(page_numbers),
            }
        )

    sub = pd.DataFrame(rows, columns=list(sample.columns))
    validate_submission(sub, sample)
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    sub.to_csv(out, index=False)
    print(f"wrote {out}")
    print(sub.head(15).to_string(index=False))


if __name__ == "__main__":
    main()

