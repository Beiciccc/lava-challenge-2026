#!/usr/bin/env python3
"""Build candidate submissions by reusing an answer column and re-running
deterministic TF-IDF evidence retrieval with different parameters.

This is a low-cost local variant for qwen-based submissions: answers stay fixed
while evidence pages are regenerated using test PDFs and cached OCR-enhanced text.
"""

from __future__ import annotations

import argparse
import ast
from pathlib import Path

import pandas as pd

from make_baseline_submission import load_or_build_page_cache, merge_ocr_cache, retrieve_pages
from make_submission_v3_rules import validate_submission


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-submission", required=True, help="Submission to copy answer column from")
    parser.add_argument("--test", default="data/raw/test.csv")
    parser.add_argument("--sample", default="data/raw/sample_submission.csv")
    parser.add_argument("--pdf-root", default="data/raw/test_pdfs")
    parser.add_argument("--cache", default="data/processed/pdf_pages.jsonl")
    parser.add_argument("--ocr-cache", default="data/processed/ocr_pages_tesseract_lowtext.jsonl")
    parser.add_argument("--output", required=True)
    parser.add_argument("--max-pages", type=int, default=3)
    parser.add_argument("--rel-threshold", type=float, default=0.8)
    parser.add_argument("--min-score", type=float, default=0.03)
    args = parser.parse_args()

    test = pd.read_csv(args.test)
    sample = pd.read_csv(args.sample)
    base = pd.read_csv(args.base_submission)

    if base["id"].tolist() != sample["id"].tolist():
        raise ValueError("Base submission id order differs from sample")

    by_file = load_or_build_page_cache(Path(args.pdf_root), Path(args.cache))
    merge_ocr_cache(by_file, Path(args.ocr_cache) if args.ocr_cache else None)

    rows: list[dict[str, str]] = []
    changed = 0
    for _, row in test.iterrows():
        file_pages = by_file.get(row["file_id"], [])
        page_numbers, _ = retrieve_pages(
            row["question"],
            file_pages,
            max_pages=args.max_pages,
            rel_threshold=args.rel_threshold,
            min_score=args.min_score,
        )
        base_row = base.loc[base["id"] == row["id"]].iloc[0]
        changed += int(str(page_numbers) != str(ast.literal_eval(str(base_row["evidence_page_number"]))))
        rows.append(
            {
                "id": row["id"],
                "answer": str(base_row["answer"]),
                "evidence_page_number": str(page_numbers),
            }
        )

    sub = pd.DataFrame(rows, columns=list(sample.columns))
    validate_submission(sub, sample)
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    sub.to_csv(out, index=False)
    print(f"wrote {out}")
    print(f"changed_evidence_rows={changed}")


if __name__ == "__main__":
    main()
