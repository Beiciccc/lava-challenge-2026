#!/usr/bin/env python3
"""Patch submission 002 with open EasyOCR answers for short zero-text PDFs."""

from __future__ import annotations

import argparse
import ast
import json
from pathlib import Path

import pandas as pd

from make_baseline_submission import answer_for_row, load_or_build_page_cache, merge_ocr_cache


def ocr_file_ids(ocr_cache: Path) -> set[str]:
    ids: set[str] = set()
    with ocr_cache.open("r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            rec = json.loads(line)
            if rec.get("text", "").strip():
                ids.add(rec["file_id"])
    return ids


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="submissions/submission_002_tfidf_evidence_tuned.csv")
    parser.add_argument("--test", default="data/raw/test.csv")
    parser.add_argument("--sample", default="data/raw/sample_submission.csv")
    parser.add_argument("--pdf-root", default="data/raw/test_pdfs")
    parser.add_argument("--cache", default="data/processed/pdf_pages.jsonl")
    parser.add_argument("--ocr-cache", default="data/processed/ocr_pages_easyocr_small.jsonl")
    parser.add_argument("--output", default="submissions/submission_003_from_002_easyocr_small.csv")
    args = parser.parse_args()

    base = pd.read_csv(args.base)
    test = pd.read_csv(args.test)
    sample = pd.read_csv(args.sample)
    by_file = load_or_build_page_cache(Path(args.pdf_root), Path(args.cache))
    merge_ocr_cache(by_file, Path(args.ocr_cache))
    target_files = ocr_file_ids(Path(args.ocr_cache))

    test_by_id = test.set_index("id")
    patched = base.copy()
    changed = 0
    for idx, row in patched.iterrows():
        qid = row["id"]
        test_row = test_by_id.loc[qid]
        if test_row["file_id"] not in target_files:
            continue
        pages = by_file.get(test_row["file_id"], [])
        page_numbers = ast.literal_eval(str(row["evidence_page_number"]))
        new_answer = answer_for_row(test_row, pages, page_numbers)
        if str(new_answer) != str(row["answer"]):
            patched.at[idx, "answer"] = new_answer
            changed += 1

    if list(patched.columns) != list(sample.columns):
        raise ValueError("Bad output columns")
    if patched["id"].tolist() != sample["id"].tolist():
        raise ValueError("Bad id order")
    if patched.isna().any().any():
        raise ValueError("NaN in output")

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    patched.to_csv(out, index=False)
    print(f"wrote {out}")
    print(f"target_files={len(target_files)} changed_answers={changed}")
    print(patched[patched['id'].isin(test[test['file_id'].isin(target_files)]['id'])].head(20).to_string(index=False))


if __name__ == "__main__":
    main()
