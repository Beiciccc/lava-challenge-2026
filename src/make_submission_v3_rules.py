#!/usr/bin/env python3
"""Rule-cleaned text baseline for LAVA Challenge 2026.

This submission stays fully deterministic and only uses extracted PDF text. It
keeps the conservative evidence strategy from v2, then cleans answer candidates
more aggressively so the judge sees short spans or list items instead of broken
long lines.
"""

from __future__ import annotations

import argparse
import ast
import re
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from make_baseline_submission import Page, clean_text, load_or_build_page_cache
from make_submission_v2 import retrieve_pages_v2


BAD_LINE_PATTERNS = [
    r"^\s*[-―ー]?\s*\d+\s*[-―ー]?\s*$",
    r"^図\s*\d+",
    r"^表\s*\d+",
    r"^出所[:：]",
    r"^注[:：]",
    r"^\s*ページ\s*\d+",
]


def normalize_answer_text(text: str, max_chars: int = 80) -> str:
    text = clean_text(text)
    text = re.sub(r"^[\s・\-—–、。，．:：;；]+", "", text)
    text = re.sub(r"[\s、。，．:：;；]+$", "", text)
    text = re.sub(r"\s+", " ", text)
    if len(text) > max_chars:
        cut = text[:max_chars]
        for sep in ["。", "、", "，", ",", " "]:
            if sep in cut[20:]:
                cut = cut[: cut.rfind(sep)]
                break
        text = cut.strip() or text[:max_chars].strip()
    return text or "Answer"


def split_segments(text: str) -> list[str]:
    rough: list[str] = []
    for line in text.splitlines():
        line = clean_text(line)
        if not line:
            continue
        rough.extend(re.split(r"(?<=[。．.])\s+|[;；]", line))

    segments: list[str] = []
    for seg in rough:
        seg = normalize_answer_text(seg, max_chars=160)
        if len(seg) < 2:
            continue
        if any(re.search(pattern, seg) for pattern in BAD_LINE_PATTERNS):
            continue
        segments.append(seg)
    return segments


def score_segments(question: str, pages: list[Page], page_numbers: list[int]) -> list[tuple[float, int, str]]:
    page_map = {p.page_number: p for p in pages}
    records: list[tuple[int, str]] = []
    for page_number in page_numbers:
        text = page_map.get(page_number, Page("", page_number, "")).text
        for seg in split_segments(text):
            records.append((page_number, seg))

    if not records:
        return [(0.0, page_numbers[0] if page_numbers else 1, "Answer")]

    docs = [seg for _, seg in records]
    try:
        vec = TfidfVectorizer(analyzer="char_wb", ngram_range=(1, 5), min_df=1, sublinear_tf=True, norm="l2")
        mat = vec.fit_transform(docs + [question])
        sims = cosine_similarity(mat[-1], mat[:-1]).ravel()
    except ValueError:
        sims = np.zeros(len(records), dtype=float)

    scored = [(float(score), page, seg) for score, (page, seg) in zip(sims, records, strict=True)]
    scored.sort(key=lambda x: (-x[0], x[1]))
    return scored


def numeric_answer(question: str, scored: list[tuple[float, int, str]]) -> str:
    preferred_units: list[str] = []
    if "％" in question or "%" in question or "割合" in question:
        preferred_units.extend(["%", "％"])
    if "円" in question or "いくら" in question:
        preferred_units.append("円")
    if "倍" in question:
        preferred_units.append("倍")
    if "人" in question:
        preferred_units.append("人")
    if "ℓ" in question or "L" in question or "リットル" in question:
        preferred_units.extend(["ℓ", "L", "リットル"])

    candidates: list[tuple[int, str]] = []
    number_re = re.compile(r"[-+]?\d+(?:[,.]\d+)?\s*(?:％|%|円|倍|人|㎡/人|ℓ|L|リットル)?")
    for rank, (_, _, seg) in enumerate(scored[:12]):
        for match in number_re.finditer(seg):
            raw = match.group(0).strip()
            if not raw:
                continue
            score = 0
            if any(unit in raw for unit in preferred_units):
                score += 10
            if "." in raw or "," in raw:
                score += 2
            if len(re.sub(r"\D", "", raw)) >= 2:
                score += 1
            candidates.append((score - rank, raw.replace(",", "")))

    if not candidates:
        return "1"
    candidates.sort(key=lambda x: x[0], reverse=True)
    return candidates[0][1]


def list_answer(scored: list[tuple[float, int, str]], ordered: bool) -> str:
    chosen: list[str] = []
    seen: set[str] = set()
    items = scored if not ordered else sorted(scored[:8], key=lambda x: x[1])
    for _, _, seg in items:
        parts = re.split(r"[、,，]\s*|・|／|/", seg)
        parts = [normalize_answer_text(p, max_chars=50) for p in parts]
        parts = [p for p in parts if 2 <= len(p) <= 50 and not re.fullmatch(r"\d+", p)]
        for part in parts or [normalize_answer_text(seg, max_chars=50)]:
            if part in seen or part == "Answer":
                continue
            seen.add(part)
            chosen.append(part)
            if len(chosen) >= (2 if ordered else 3):
                return str(chosen)
    return str(chosen or ["Answer"])


def answer_for_row_v3(row: pd.Series, pages: list[Page], page_numbers: list[int]) -> str:
    scored = score_segments(row["question"], pages, page_numbers)
    fmt = row["answer_format"]
    if fmt == "number":
        return numeric_answer(row["question"], scored)
    if fmt == "ordered_list":
        return list_answer(scored, ordered=True)
    if fmt == "unordered_list":
        return list_answer(scored, ordered=False)
    return normalize_answer_text(scored[0][2], max_chars=80)


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
    answer_text = sub["answer"].astype(str)
    maybe_lists = answer_text.str.startswith("[") & answer_text.str.endswith("]")
    for raw in sub.loc[maybe_lists, "answer"]:
        parsed = ast.literal_eval(str(raw))
        if not isinstance(parsed, list):
            raise ValueError(f"Bad list answer: {raw}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--test", default="data/raw/test.csv")
    parser.add_argument("--sample", default="data/raw/sample_submission.csv")
    parser.add_argument("--pdf-root", default="data/raw/test_pdfs")
    parser.add_argument("--cache", default="data/processed/pdf_pages.jsonl")
    parser.add_argument("--output", default="submissions/submission_003_rules_cleaned.csv")
    args = parser.parse_args()

    test = pd.read_csv(args.test)
    sample = pd.read_csv(args.sample)
    by_file = load_or_build_page_cache(Path(args.pdf_root), Path(args.cache))

    rows: list[dict[str, str]] = []
    for _, row in test.iterrows():
        pages = by_file.get(row["file_id"], [])
        page_numbers, _ = retrieve_pages_v2(row["question"], pages)
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
    print(sub.head(10).to_string(index=False))


if __name__ == "__main__":
    main()
