#!/usr/bin/env python3
"""Second-pass deterministic submission for LAVA Challenge 2026.

This variant keeps the first baseline's answer generation mostly unchanged and
only adjusts evidence retrieval. On the tiny labeled set, adding a second page
only when the TF-IDF signal is weak improves grounding F1 without the broad
penalty of always submitting top-2 pages.
"""

from __future__ import annotations

import argparse
import ast
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from make_baseline_submission import Page, answer_for_row, load_or_build_page_cache, merge_ocr_cache


def retrieve_pages_v2(question: str, pages: list[Page]) -> tuple[list[int], float]:
    if not pages:
        return [1], 0.0

    docs = [p.text if p.text else " " for p in pages]
    if sum(bool(d.strip()) for d in docs) == 0:
        return [1], 0.0

    vectorizer = TfidfVectorizer(
        analyzer="char_wb",
        ngram_range=(1, 5),
        min_df=1,
        sublinear_tf=True,
        norm="l2",
    )
    matrix = vectorizer.fit_transform(docs + [question])
    sims = cosine_similarity(matrix[-1], matrix[:-1]).ravel()
    order = np.argsort(-sims)
    best_idx = int(order[0])
    best_score = float(sims[best_idx])

    selected = [pages[best_idx].page_number]
    if len(order) > 1 and best_score < 0.03:
        selected.append(pages[int(order[1])].page_number)
    return sorted(set(selected)), best_score


def validate_submission(sub: pd.DataFrame, sample: pd.DataFrame) -> None:
    if list(sub.columns) != list(sample.columns):
        raise ValueError(f"Columns mismatch: {list(sub.columns)} != {list(sample.columns)}")
    if len(sub) != len(sample):
        raise ValueError(f"Row count mismatch: {len(sub)} != {len(sample)}")
    if sub["id"].tolist() != sample["id"].tolist():
        raise ValueError("Submission ids/order do not match sample submission")
    if sub.isna().any().any():
        raise ValueError("Submission contains NaN values")

    for raw in sub["evidence_page_number"]:
        parsed = ast.literal_eval(str(raw))
        if not isinstance(parsed, list) or not parsed:
            raise ValueError(f"Bad evidence_page_number: {raw}")
        if not all(isinstance(x, int) and x >= 1 for x in parsed):
            raise ValueError(f"Bad evidence_page_number values: {raw}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--test", default="data/raw/test.csv")
    parser.add_argument("--sample", default="data/raw/sample_submission.csv")
    parser.add_argument("--pdf-root", default="data/raw/test_pdfs")
    parser.add_argument("--cache", default="data/processed/pdf_pages.jsonl")
    parser.add_argument("--ocr-cache", default="")
    parser.add_argument("--output", default="submissions/submission_002_evidence_low_sim_top2.csv")
    args = parser.parse_args()

    test = pd.read_csv(args.test)
    sample = pd.read_csv(args.sample)
    by_file = load_or_build_page_cache(Path(args.pdf_root), Path(args.cache))
    merge_ocr_cache(by_file, Path(args.ocr_cache) if args.ocr_cache else None)

    rows: list[dict[str, str]] = []
    scores: list[float] = []
    expanded = 0
    for _, row in test.iterrows():
        pages = by_file.get(row["file_id"], [])
        page_numbers, score = retrieve_pages_v2(row["question"], pages)
        scores.append(score)
        expanded += int(len(page_numbers) > 1)
        rows.append(
            {
                "id": row["id"],
                "answer": answer_for_row(row, pages, page_numbers),
                "evidence_page_number": str(page_numbers),
            }
        )

    sub = pd.DataFrame(rows, columns=list(sample.columns))
    validate_submission(sub, sample)
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    sub.to_csv(out, index=False)

    arr = np.asarray(scores)
    print(f"wrote {out}")
    print(f"rows={len(sub)} expanded={expanded}")
    print(f"retrieval_score mean={arr.mean():.4f} p50={np.median(arr):.4f} p10={np.quantile(arr, 0.1):.4f}")
    print(sub.head(10).to_string(index=False))


if __name__ == "__main__":
    main()
