#!/usr/bin/env python3
"""Build a submission by anchoring existing answers back to open PDF text/OCR.

The Qwen answer cache improved VQA, but evidence retrieval plateaued. This
script keeps a strong answer column and replaces evidence pages when the answer
or answer items can be found in PyMuPDF/Tesseract page text.
"""

from __future__ import annotations

import argparse
import ast
import re
import unicodedata
from pathlib import Path

import pandas as pd

from make_baseline_submission import Page, load_or_build_page_cache, merge_ocr_cache
from make_submission_v3_rules import validate_submission


PUNCT_RE = re.compile(r"[\s\t\r\n、。，．・:：;；,.\-‐‑‒–—―_/／\\()（）\[\]【】{}「」『』<>＜＞\"'`]+")


def norm(text: object) -> str:
    text = unicodedata.normalize("NFKC", str(text))
    return PUNCT_RE.sub("", text).lower()


def parse_answer_terms(answer: object, answer_format: str) -> list[str]:
    raw = str(answer).strip()
    terms: list[str] = []
    if answer_format in {"ordered_list", "unordered_list"}:
        try:
            parsed = ast.literal_eval(raw)
        except Exception:
            parsed = []
        if isinstance(parsed, list):
            terms.extend(str(x).strip() for x in parsed if str(x).strip())
        else:
            terms.append(raw)
    elif answer_format == "number":
        terms.extend(re.findall(r"[-+]?\d+(?:[,.]\d+)?", raw))
        terms.append(raw)
    else:
        terms.append(raw)
        for part in re.split(r"[、。，．,;；/／\n]+", raw):
            if part.strip():
                terms.append(part.strip())

    out: list[str] = []
    seen: set[str] = set()
    for term in terms:
        term = term.strip()
        n = norm(term)
        if not n or n in seen:
            continue
        if len(n) < 2 and not n.isdigit():
            continue
        seen.add(n)
        out.append(term)
    return out


def page_match_score(page_text: str, terms: list[str], answer_format: str) -> float:
    page_norm = norm(page_text)
    if not page_norm:
        return 0.0

    score = 0.0
    matched = 0
    for term in terms:
        t = norm(term)
        if not t:
            continue
        if t in page_norm:
            matched += 1
            score += min(80.0, max(5.0, len(t)))
            continue
        if answer_format == "number":
            digits = re.sub(r"\D", "", t)
            if digits and digits in re.sub(r"\D", "", page_norm):
                matched += 1
                score += 8.0
    if matched >= 2:
        score += 12.0 * matched
    return score


def anchor_pages(
    pages: list[Page],
    answer: object,
    answer_format: str,
    max_pages: int,
    min_score: float,
) -> list[int]:
    terms = parse_answer_terms(answer, answer_format)
    if not terms or not pages:
        return []
    scored = [
        (page_match_score(page.text, terms, answer_format), page.page_number)
        for page in pages
    ]
    scored = [(score, page) for score, page in scored if score >= min_score]
    scored.sort(key=lambda x: (-x[0], x[1]))
    return sorted({page for _, page in scored[:max_pages]})


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--test", default="data/raw/test.csv")
    parser.add_argument("--sample", default="data/raw/sample_submission.csv")
    parser.add_argument("--answer-submission", default="submissions/submission_008_qwen_all_tesseract_evidence.csv")
    parser.add_argument("--fallback-submission", default="submissions/submission_008_qwen_all_tesseract_evidence.csv")
    parser.add_argument("--pdf-root", default="data/raw/test_pdfs")
    parser.add_argument("--cache", default="data/processed/pdf_pages.jsonl")
    parser.add_argument("--ocr-cache", default="data/processed/ocr_pages_tesseract_lowtext.jsonl")
    parser.add_argument("--output", default="submissions/submission_016_qwen_answer_anchor.csv")
    parser.add_argument("--max-pages", type=int, default=2)
    parser.add_argument("--min-score", type=float, default=8.0)
    parser.add_argument("--include-fallback-pages", action="store_true")
    args = parser.parse_args()

    test = pd.read_csv(args.test)
    sample = pd.read_csv(args.sample)
    answers = pd.read_csv(args.answer_submission)
    fallback = pd.read_csv(args.fallback_submission)
    if answers["id"].tolist() != sample["id"].tolist():
        raise ValueError("answer submission ids do not match sample")
    if fallback["id"].tolist() != sample["id"].tolist():
        raise ValueError("fallback submission ids do not match sample")

    by_file = load_or_build_page_cache(Path(args.pdf_root), Path(args.cache))
    merge_ocr_cache(by_file, Path(args.ocr_cache) if args.ocr_cache else None)

    rows: list[dict[str, str]] = []
    anchored = 0
    changed = 0
    for i, row in test.iterrows():
        pages = by_file.get(row["file_id"], [])
        answer = answers.loc[i, "answer"]
        fallback_pages = ast.literal_eval(str(fallback.loc[i, "evidence_page_number"]))
        page_numbers = anchor_pages(
            pages,
            answer,
            row["answer_format"],
            max_pages=args.max_pages,
            min_score=args.min_score,
        )
        if page_numbers:
            anchored += 1
            if args.include_fallback_pages:
                page_numbers = sorted(set(page_numbers) | {int(x) for x in fallback_pages})
        else:
            page_numbers = [int(x) for x in fallback_pages]
        changed += int(str(page_numbers) != str(fallback_pages))
        rows.append(
            {
                "id": row["id"],
                "answer": str(answer),
                "evidence_page_number": str(page_numbers),
            }
        )

    sub = pd.DataFrame(rows, columns=list(sample.columns))
    validate_submission(sub, sample)
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    sub.to_csv(out, index=False)
    avg_pages = sub["evidence_page_number"].astype(str).str.count(",").add(1).mean()
    print(f"wrote {out}")
    print(f"anchored_rows={anchored} changed_evidence_rows={changed} avg_pages={avg_pages:.3f}")
    print(sub.head(10).to_string(index=False))


if __name__ == "__main__":
    main()
