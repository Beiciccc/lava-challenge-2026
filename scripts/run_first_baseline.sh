#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

if [[ -f data/raw/lava-challenge-2026.zip && ! -d data/raw/test_pdfs ]]; then
  unzip -n data/raw/lava-challenge-2026.zip -d data/raw
fi

python3 src/make_baseline_submission.py \
  --test data/raw/test.csv \
  --sample data/raw/sample_submission.csv \
  --pdf-root data/raw/test_pdfs \
  --cache data/processed/pdf_pages.jsonl \
  --output submissions/submission_baseline_tfidf.csv

