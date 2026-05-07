#!/usr/bin/env python3
"""Re-answer a valid LAVA submission using deterministic text span rules.

This keeps evidence pages from a base submission and only replaces the answer
column from the retrieved page text. It is intended as a fast candidate when VLM
inference is not ready.
"""

from __future__ import annotations

import argparse
import ast
from pathlib import Path

import pandas as pd

from make_baseline_submission import load_or_build_page_cache, merge_ocr_cache
from make_submission_v3_rules import answer_for_row_v3, validate_submission


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--test", default="data/raw/test.csv")
    parser.add_argument("--sample", default="data/raw/sample_submission.csv")
    parser.add_argument("--base-submission", default="submissions/submission_003_tfidf_ocr_evidence.csv")
    parser.add_argument("--pdf-root", default="data/raw/test_pdfs")
    parser.add_argument("--cache", default="data/processed/pdf_pages.jsonl")
    parser.add_argument("--ocr-cache", default="data/processed/ocr_pages_vision.jsonl")
    parser.add_argument("--output", default="submissions/submission_004_rules_on_best_evidence.csv")
    args = parser.parse_args()

    test = pd.read_csv(args.test)
    sample = pd.read_csv(args.sample)
    base = pd.read_csv(args.base_submission)
    if base["id"].tolist() != sample["id"].tolist():
        raise ValueError("Base submission id order differs from sample")

    by_file = load_or_build_page_cache(Path(args.pdf_root), Path(args.cache))
    merge_ocr_cache(by_file, Path(args.ocr_cache) if args.ocr_cache else None)
    base_by_id = base.set_index("id")

    rows: list[dict[str, str]] = []
    changed = 0
    for _, row in test.iterrows():
        base_row = base_by_id.loc[row["id"]]
        page_numbers = ast.literal_eval(str(base_row["evidence_page_number"]))
        pages = by_file.get(row["file_id"], [])
        answer = answer_for_row_v3(row, pages, page_numbers)
        changed += int(str(answer) != str(base_row["answer"]))
        rows.append(
            {
                "id": row["id"],
                "answer": answer,
                "evidence_page_number": str(base_row["evidence_page_number"]),
            }
        )

    sub = pd.DataFrame(rows, columns=list(sample.columns))
    validate_submission(sub, sample)
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    sub.to_csv(out, index=False)
    print(f"wrote {out} changed_answers={changed}")
    print(sub.head(10).to_string(index=False))


if __name__ == "__main__":
    main()
