#!/usr/bin/env python3
"""Build higher-variance LAVA submissions from merged OCR and history votes."""

from __future__ import annotations

import argparse
import ast
import csv
import json
import re
import subprocess
import sys
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

from make_baseline_submission import Page, retrieve_pages
from make_submission_v3_rules import validate_submission


OCR_CACHES = [
    "data/processed/ocr_pages_vision.jsonl",
    "data/processed/ocr_pages_tesseract_lowtext.jsonl",
    "data/processed/pdf_pages_ocrmac.jsonl",
    "data/processed/ocr_pages_easyocr_small.jsonl",
]


PUNCT_RE = re.compile(r"[\s\t\r\n、。，．・:：;；,.\-‐‑‒–—―_/／\\()（）\[\]【】{}「」『』<>＜＞\"'`]+")


def norm(text: object) -> str:
    return PUNCT_RE.sub("", unicodedata.normalize("NFKC", str(text))).lower()


def parse_pages(raw: object) -> list[int]:
    parsed = ast.literal_eval(str(raw))
    if not isinstance(parsed, list) or not parsed:
        return [1]
    return [int(x) for x in parsed if isinstance(x, int) or str(x).isdigit()] or [1]


def answer_terms(answer: object, answer_format: str) -> list[str]:
    raw = str(answer).strip()
    parts: list[str] = []
    if answer_format in {"ordered_list", "unordered_list"}:
        try:
            parsed = ast.literal_eval(raw)
        except Exception:
            parsed = []
        if isinstance(parsed, list):
            parts.extend(str(x).strip() for x in parsed)
    elif answer_format == "number":
        parts.extend(re.findall(r"[-+]?\d+(?:[,.]\d+)?", raw))
        parts.append(raw)
    else:
        parts.append(raw)
        parts.extend(p.strip() for p in re.split(r"[、。，．,;；/／\n]+", raw))
    out: list[str] = []
    seen: set[str] = set()
    for part in parts:
        key = norm(part)
        if len(key) < 2 and not key.isdigit():
            continue
        if key and key not in seen:
            seen.add(key)
            out.append(part)
    return out


def load_base_pages(path: Path) -> dict[str, dict[int, str]]:
    by_file: dict[str, dict[int, str]] = defaultdict(dict)
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            rec = json.loads(line)
            by_file[str(rec["file_id"])][int(rec["page_number"])] = str(rec.get("text", ""))
    return by_file


def append_cache(by_file: dict[str, dict[int, str]], path: Path) -> None:
    if not path.exists():
        return
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            rec = json.loads(line)
            text = str(rec.get("text", "")).strip()
            if not text:
                continue
            file_id = str(rec["file_id"])
            page = int(rec["page_number"])
            old = by_file[file_id].get(page, "")
            if norm(text) not in norm(old):
                by_file[file_id][page] = f"{old}\n{text}".strip()


def load_merged_pages(cache: Path, ocr_caches: list[str]) -> dict[str, list[Page]]:
    raw = load_base_pages(cache)
    for cache_name in ocr_caches:
        append_cache(raw, Path(cache_name))
    out: dict[str, list[Page]] = {}
    for file_id, pages in raw.items():
        out[file_id] = [Page(file_id, page, text) for page, text in sorted(pages.items())]
    return out


def run_kaggle_submissions() -> list[dict[str, str]]:
    proc = subprocess.run(
        ["kaggle", "competitions", "submissions", "-c", "lava-challenge-2026", "--csv", "--page-size", "200"],
        check=True,
        capture_output=True,
        text=True,
    )
    return list(csv.DictReader(proc.stdout.splitlines()))


def load_public_scores() -> dict[str, float]:
    scores: dict[str, float] = {}
    for row in run_kaggle_submissions():
        try:
            score = float(row.get("publicScore", ""))
        except ValueError:
            continue
        name = row.get("fileName", "")
        scores[name] = max(scores.get(name, -1.0), score)
    return scores


def history_vote(
    sample: pd.DataFrame,
    base: pd.DataFrame,
    submission_dir: Path,
    min_score: float,
    answer_locked: bool,
) -> pd.DataFrame:
    scores = load_public_scores()
    paths = [
        submission_dir / name
        for name, score in scores.items()
        if score >= min_score and (submission_dir / name).exists()
    ]
    if not paths:
        raise ValueError(f"No history submissions found with score >= {min_score}")

    rows: list[dict[str, str]] = []
    for i, sample_row in sample.iterrows():
        votes: Counter[tuple[str, str]] = Counter()
        for path in paths:
            df = pd.read_csv(path)
            score = scores[path.name]
            answer = str(base.loc[i, "answer"]) if answer_locked else str(df.loc[i, "answer"])
            evidence = str(df.loc[i, "evidence_page_number"])
            votes[(answer, evidence)] += int(round(score * 100))
        (answer, evidence), _ = votes.most_common(1)[0]
        rows.append({"id": sample_row["id"], "answer": answer, "evidence_page_number": evidence})
    return pd.DataFrame(rows, columns=list(sample.columns))


def retrieve_submission(
    test: pd.DataFrame,
    sample: pd.DataFrame,
    base: pd.DataFrame,
    by_file: dict[str, list[Page]],
    mode: str,
    max_pages: int,
    rel_threshold: float,
    min_score: float,
) -> pd.DataFrame:
    rows: list[dict[str, str]] = []
    for i, row in test.iterrows():
        pages = by_file.get(str(row["file_id"]), [])
        base_answer = str(base.loc[i, "answer"])
        query = str(row["question"])
        if mode == "answer_query":
            query = f"{query}\n{base_answer}"
        elif mode == "answer_terms_query":
            terms = " ".join(answer_terms(base_answer, str(row["answer_format"])))
            query = f"{query}\n{terms}".strip()
        page_numbers, _ = retrieve_pages(
            query,
            pages,
            max_pages=max_pages,
            rel_threshold=rel_threshold,
            min_score=min_score,
        )
        rows.append(
            {
                "id": row["id"],
                "answer": base_answer,
                "evidence_page_number": str(page_numbers),
            }
        )
    return pd.DataFrame(rows, columns=list(sample.columns))


def answer_presence_submission(
    test: pd.DataFrame,
    sample: pd.DataFrame,
    base: pd.DataFrame,
    fallback: pd.DataFrame,
    by_file: dict[str, list[Page]],
    max_pages: int,
    min_matches: int,
) -> pd.DataFrame:
    rows: list[dict[str, str]] = []
    for i, row in test.iterrows():
        answer = str(base.loc[i, "answer"])
        terms = [norm(t) for t in answer_terms(answer, str(row["answer_format"]))]
        scored: list[tuple[int, int]] = []
        for page in by_file.get(str(row["file_id"]), []):
            page_norm = norm(page.text)
            matches = sum(1 for term in terms if term and term in page_norm)
            if matches >= min_matches:
                scored.append((matches, page.page_number))
        if scored:
            scored.sort(key=lambda x: (-x[0], x[1]))
            pages = sorted({page for _, page in scored[:max_pages]})
        else:
            pages = parse_pages(fallback.loc[i, "evidence_page_number"])
        rows.append({"id": row["id"], "answer": answer, "evidence_page_number": str(pages)})
    return pd.DataFrame(rows, columns=list(sample.columns))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["retrieve", "history_vote", "answer_presence"], required=True)
    parser.add_argument("--retrieve-mode", choices=["question", "answer_query", "answer_terms_query"], default="question")
    parser.add_argument("--test", default="data/raw/test.csv")
    parser.add_argument("--sample", default="data/raw/sample_submission.csv")
    parser.add_argument("--base-submission", default="submissions/submission_004_qwen_vl_best_evidence.csv")
    parser.add_argument("--fallback-submission", default="submissions/submission_004_qwen_vl_best_evidence.csv")
    parser.add_argument("--cache", default="data/processed/pdf_pages.jsonl")
    parser.add_argument("--output", required=True)
    parser.add_argument("--max-pages", type=int, default=2)
    parser.add_argument("--rel-threshold", type=float, default=0.85)
    parser.add_argument("--min-score", type=float, default=0.03)
    parser.add_argument("--history-min-score", type=float, default=0.28)
    parser.add_argument("--history-free-answer", action="store_true")
    parser.add_argument("--answer-min-matches", type=int, default=1)
    args = parser.parse_args()

    test = pd.read_csv(args.test)
    sample = pd.read_csv(args.sample)
    base = pd.read_csv(args.base_submission)
    fallback = pd.read_csv(args.fallback_submission)
    if base["id"].tolist() != sample["id"].tolist():
        raise ValueError("base submission ids do not match sample")
    if fallback["id"].tolist() != sample["id"].tolist():
        raise ValueError("fallback submission ids do not match sample")

    if args.mode == "history_vote":
        sub = history_vote(
            sample,
            base,
            Path("submissions"),
            args.history_min_score,
            answer_locked=not args.history_free_answer,
        )
    else:
        by_file = load_merged_pages(Path(args.cache), OCR_CACHES)
        if args.mode == "retrieve":
            sub = retrieve_submission(
                test,
                sample,
                base,
                by_file,
                args.retrieve_mode,
                args.max_pages,
                args.rel_threshold,
                args.min_score,
            )
        else:
            sub = answer_presence_submission(
                test,
                sample,
                base,
                fallback,
                by_file,
                args.max_pages,
                args.answer_min_matches,
            )

    validate_submission(sub, sample)
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    sub.to_csv(out, index=False)
    avg_pages = sub["evidence_page_number"].astype(str).str.count(",").add(1).mean()
    base_diff = (
        sub["answer"].astype(str).ne(base["answer"].astype(str)).sum(),
        sub["evidence_page_number"].astype(str).ne(base["evidence_page_number"].astype(str)).sum(),
    )
    print(f"wrote {out}")
    print(f"diff_from_base_answers={base_diff[0]} diff_from_base_evidence={base_diff[1]} avg_pages={avg_pages:.3f}")
    print(sub.head(10).to_string(index=False))


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as exc:
        print(exc.stderr or exc.stdout, file=sys.stderr)
        raise SystemExit(exc.returncode) from None
