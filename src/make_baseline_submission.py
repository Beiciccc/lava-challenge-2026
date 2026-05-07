#!/usr/bin/env python3
"""Build a deterministic first-pass submission for LAVA Challenge 2026.

The goal of this baseline is not to solve VQA yet. It produces a valid
submission and improves the evidence column over the sample submission by
retrieving the most relevant PDF page for each question using character n-gram
TF-IDF. Answers are conservative snippets/placeholders by requested format.
"""

from __future__ import annotations

import argparse
import ast
import json
import re
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


@dataclass
class Page:
    file_id: str
    page_number: int
    text: str


def clean_text(text: str) -> str:
    text = text.replace("\x00", " ")
    text = re.sub(r"[ \t\r\f\v]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def extract_with_pymupdf(pdf_path: Path) -> list[str]:
    import fitz  # type: ignore

    pages: list[str] = []
    with fitz.open(pdf_path) as doc:
        for page in doc:
            pages.append(clean_text(page.get_text("text")))
    return pages


def extract_with_pypdf(pdf_path: Path) -> list[str]:
    from pypdf import PdfReader

    reader = PdfReader(str(pdf_path))
    pages: list[str] = []
    for page in reader.pages:
        pages.append(clean_text(page.extract_text() or ""))
    return pages


def extract_pdf_pages(pdf_path: Path) -> list[str]:
    try:
        return extract_with_pymupdf(pdf_path)
    except Exception:
        return extract_with_pypdf(pdf_path)


def load_or_build_page_cache(pdf_root: Path, cache_path: Path, force: bool = False) -> dict[str, list[Page]]:
    if cache_path.exists() and not force:
        by_file: dict[str, list[Page]] = {}
        with cache_path.open("r", encoding="utf-8") as f:
            for line in f:
                rec = json.loads(line)
                page = Page(rec["file_id"], int(rec["page_number"]), rec.get("text", ""))
                by_file.setdefault(page.file_id, []).append(page)
        return by_file

    pdf_paths = sorted(p for p in pdf_root.rglob("*.pdf") if not p.name.startswith("._"))
    if not pdf_paths:
        raise FileNotFoundError(f"No PDFs found under {pdf_root}")

    cache_path.parent.mkdir(parents=True, exist_ok=True)
    by_file: dict[str, list[Page]] = {}
    with cache_path.open("w", encoding="utf-8") as f:
        for i, pdf_path in enumerate(pdf_paths, start=1):
            file_id = pdf_path.stem
            texts = extract_pdf_pages(pdf_path)
            for page_number, text in enumerate(texts, start=1):
                page = Page(file_id, page_number, text)
                by_file.setdefault(file_id, []).append(page)
                f.write(
                    json.dumps(
                        {
                            "file_id": file_id,
                            "page_number": page_number,
                            "text": text,
                        },
                        ensure_ascii=False,
                    )
                    + "\n"
                )
            if i % 25 == 0:
                print(f"extracted {i}/{len(pdf_paths)} PDFs", flush=True)
    return by_file


def merge_ocr_cache(by_file: dict[str, list[Page]], ocr_cache: Path | None) -> None:
    if ocr_cache is None or not ocr_cache.exists():
        return

    ocr_pages: dict[tuple[str, int], str] = {}
    with ocr_cache.open("r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            rec = json.loads(line)
            text = rec.get("text", "").strip()
            if text:
                ocr_pages[(rec["file_id"], int(rec["page_number"]))] = text

    for file_id, pages in by_file.items():
        for i, page in enumerate(pages):
            ocr_text = ocr_pages.get((file_id, page.page_number), "")
            if not ocr_text:
                continue
            if len(page.text.strip()) < 200:
                pages[i] = Page(file_id, page.page_number, ocr_text)
            else:
                pages[i] = Page(file_id, page.page_number, f"{page.text}\n{ocr_text}")


def retrieve_pages(
    question: str,
    pages: list[Page],
    max_pages: int = 2,
    rel_threshold: float = 0.92,
    min_score: float = 0.18,
) -> tuple[list[int], float]:
    if not pages:
        return [1], 0.0

    docs = [p.text if p.text else " " for p in pages]
    if sum(bool(d.strip()) for d in docs) == 0:
        return [1], 0.0

    vectorizer = TfidfVectorizer(
        analyzer="char_wb",
        ngram_range=(2, 5),
        min_df=1,
        sublinear_tf=True,
        norm="l2",
    )
    matrix = vectorizer.fit_transform(docs + [question])
    sims = cosine_similarity(matrix[-1], matrix[:-1]).ravel()
    order = np.argsort(-sims)
    best_idx = int(order[0])
    best_score = float(sims[best_idx])

    selected = []
    for raw_idx in order[:max_pages]:
        idx = int(raw_idx)
        score = float(sims[idx])
        if score >= best_score * rel_threshold and score >= min_score:
            selected.append(pages[idx].page_number)
    if not selected:
        selected = [pages[best_idx].page_number]
    return sorted(set(selected)), best_score


def best_line_snippet(question: str, pages: list[Page], page_numbers: list[int], max_chars: int = 120) -> str:
    page_map = {p.page_number: p for p in pages}
    lines: list[str] = []
    for page_number in page_numbers:
        text = page_map.get(page_number, Page("", page_number, "")).text
        lines.extend(clean_text(line) for line in text.splitlines())
    lines = [line for line in lines if len(line) >= 2]
    if not lines:
        return "Answer"

    vectorizer = TfidfVectorizer(
        analyzer="char_wb",
        ngram_range=(2, 5),
        min_df=1,
        sublinear_tf=True,
        norm="l2",
    )
    try:
        matrix = vectorizer.fit_transform(lines + [question])
        sims = cosine_similarity(matrix[-1], matrix[:-1]).ravel()
        line = lines[int(np.argmax(sims))]
    except ValueError:
        line = lines[0]

    line = re.sub(r"\s+", " ", line).strip()
    if len(line) > max_chars:
        line = line[:max_chars].rsplit(" ", 1)[0].strip() or line[:max_chars]
    return line or "Answer"


def numeric_answer_from_snippet(snippet: str) -> str:
    numbers = re.findall(r"[-+]?\d+(?:[,.]\d+)?", snippet)
    if not numbers:
        return "1"
    return numbers[0].replace(",", "")


def answer_for_row(row: pd.Series, pages: list[Page], page_numbers: list[int]) -> str:
    fmt = row["answer_format"]
    snippet = best_line_snippet(row["question"], pages, page_numbers)

    if fmt == "number":
        return numeric_answer_from_snippet(snippet)
    if fmt == "ordered_list":
        return str([snippet])
    if fmt == "unordered_list":
        return str([snippet])
    return snippet


def validate_submission(sub: pd.DataFrame, sample: pd.DataFrame) -> None:
    expected_cols = list(sample.columns)
    if list(sub.columns) != expected_cols:
        raise ValueError(f"Columns mismatch: got {list(sub.columns)}, expected {expected_cols}")
    if len(sub) != len(sample):
        raise ValueError(f"Row count mismatch: got {len(sub)}, expected {len(sample)}")
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
    parser.add_argument("--output", default="submissions/submission_baseline_tfidf.csv")
    parser.add_argument("--force-cache", action="store_true")
    parser.add_argument("--max-pages", type=int, default=2)
    parser.add_argument("--rel-threshold", type=float, default=0.92)
    parser.add_argument("--min-score", type=float, default=0.18)
    parser.add_argument("--ocr-cache", default="")
    args = parser.parse_args()

    test = pd.read_csv(args.test)
    sample = pd.read_csv(args.sample)
    by_file = load_or_build_page_cache(Path(args.pdf_root), Path(args.cache), force=args.force_cache)
    merge_ocr_cache(by_file, Path(args.ocr_cache) if args.ocr_cache else None)

    rows: list[dict[str, str]] = []
    missing_files: set[str] = set()
    retrieval_scores: list[float] = []
    for _, row in test.iterrows():
        file_id = row["file_id"]
        pages = by_file.get(file_id, [])
        if not pages:
            missing_files.add(file_id)
        page_numbers, score = retrieve_pages(
            row["question"],
            pages,
            max_pages=args.max_pages,
            rel_threshold=args.rel_threshold,
            min_score=args.min_score,
        )
        retrieval_scores.append(score)
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

    scores = np.asarray(retrieval_scores)
    print(f"wrote {out}")
    print(f"rows={len(sub)} missing_files={len(missing_files)}")
    print(f"retrieval_score mean={scores.mean():.4f} p50={np.median(scores):.4f} p10={np.quantile(scores, 0.1):.4f}")
    print(sub.head(10).to_string(index=False))


if __name__ == "__main__":
    main()
