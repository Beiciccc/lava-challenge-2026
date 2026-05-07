#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ast
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from make_baseline_submission import load_or_build_page_cache, retrieve_pages  # noqa: E402


def f1(pred: list[int], truth: list[int]) -> float:
    p, t = set(pred), set(truth)
    if not p or not t:
        return 0.0
    return 2 * len(p & t) / (len(p) + len(t))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--train", default="data/raw/train.csv")
    parser.add_argument("--pdf-root", default="data/raw/train_pdfs")
    parser.add_argument("--cache", default="data/processed/train_pdf_pages.jsonl")
    parser.add_argument("--max-pages", type=int, default=2)
    parser.add_argument("--rel-threshold", type=float, default=0.92)
    parser.add_argument("--min-score", type=float, default=0.18)
    args = parser.parse_args()

    train = pd.read_csv(args.train)
    by_file = load_or_build_page_cache(Path(args.pdf_root), Path(args.cache))
    scores = []
    baseline_scores = []
    for _, row in train.iterrows():
        truth = ast.literal_eval(str(row["evidence_page_number"]))
        pred, score = retrieve_pages(
            row["question"],
            by_file.get(row["file_id"], []),
            max_pages=args.max_pages,
            rel_threshold=args.rel_threshold,
            min_score=args.min_score,
        )
        scores.append(f1(pred, truth))
        baseline_scores.append(f1([1], truth))
        print(row["id"], row["file_id"], "truth=", truth, "pred=", pred, f"score={scores[-1]:.3f}", f"sim={score:.4f}")

    print(f"mean_f1={np.mean(scores):.4f}")
    print(f"sample_[1]_mean_f1={np.mean(baseline_scores):.4f}")


if __name__ == "__main__":
    main()
