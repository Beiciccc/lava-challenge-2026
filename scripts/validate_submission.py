#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ast
from pathlib import Path

import fitz  # type: ignore
import pandas as pd


def page_count(pdf_path: Path) -> int:
    with fitz.open(pdf_path) as doc:
        return doc.page_count


def parse_int_list(value: object, field: str) -> list[int]:
    parsed = ast.literal_eval(str(value))
    if not isinstance(parsed, list) or not parsed:
        raise ValueError(f"{field} is not a non-empty list: {value}")
    if not all(isinstance(x, int) and x >= 1 for x in parsed):
        raise ValueError(f"{field} must contain positive ints: {value}")
    return parsed


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("submission")
    parser.add_argument("--test", default="data/raw/test.csv")
    parser.add_argument("--sample", default="data/raw/sample_submission.csv")
    parser.add_argument("--pdf-root", default="data/raw/test_pdfs")
    args = parser.parse_args()

    sub = pd.read_csv(args.submission)
    test = pd.read_csv(args.test)
    sample = pd.read_csv(args.sample)

    if list(sub.columns) != list(sample.columns):
        raise SystemExit(f"Bad columns: {list(sub.columns)} != {list(sample.columns)}")
    if len(sub) != len(sample):
        raise SystemExit(f"Bad row count: {len(sub)} != {len(sample)}")
    if sub["id"].tolist() != sample["id"].tolist():
        raise SystemExit("Submission id order differs from sample_submission.csv")
    if sub.isna().any().any():
        raise SystemExit("Submission contains NaN")

    file_to_count: dict[str, int] = {}
    for pdf in Path(args.pdf_root).rglob("*.pdf"):
        if pdf.name.startswith("._"):
            continue
        file_to_count[pdf.stem] = page_count(pdf)

    id_to_file = dict(zip(test["id"], test["file_id"]))
    id_to_fmt = dict(zip(test["id"], test["answer_format"]))

    for _, row in sub.iterrows():
        qid = row["id"]
        pages = parse_int_list(row["evidence_page_number"], "evidence_page_number")
        file_id = id_to_file[qid]
        max_page = file_to_count[file_id]
        if any(page > max_page for page in pages):
            raise SystemExit(f"{qid}: page out of range {pages}; {file_id} has {max_page} pages")

        if id_to_fmt[qid] in {"ordered_list", "unordered_list"}:
            parsed = ast.literal_eval(str(row["answer"]))
            if not isinstance(parsed, list):
                raise SystemExit(f"{qid}: list answer is not a list string: {row['answer']}")

    print(f"OK: {args.submission}")
    print(f"rows={len(sub)} pdfs={len(file_to_count)}")


if __name__ == "__main__":
    main()
