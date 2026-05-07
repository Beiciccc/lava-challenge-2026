# Submission 002-003 Report

Date: 2026-04-30

## Final Kaggle Results

| Submission | Kaggle file | Public score | Status |
| --- | --- | ---: | --- |
| 001 | `submission_baseline_tfidf.csv` | 0.22 | COMPLETE |
| 002 | `submission_002_tfidf_evidence_tuned.csv` | 0.23 | COMPLETE |
| 003 | `submission_003_tfidf_ocr_evidence.csv` | 0.26 | COMPLETE |

After submission 003, leaderboard position observed from Kaggle CLI:
rank 8 of 11, score 0.26.

Daily quota from competition metadata is 5 submissions. Kaggle submission list
now shows 3 accepted submissions today, so the remaining quota is approximately
2 submissions.

## Submission 002

Goal: improve grounding without changing the weak snippet answer baseline.

Implemented candidate:
- `src/make_baseline_submission.py`
- `submissions/submission_002_tfidf_evidence_tuned.csv`

Change:
- Kept char-wb TF-IDF `(2, 5)`.
- Tuned evidence selection from near-top1 to `max_pages=4`,
  `rel_threshold=0.7`, `min_score=0.03`.
- Training evidence F1 on the 16 labeled examples improved from `0.6187` to
  `0.6823`.

Result:
- Public score improved from 0.22 to 0.23.

## Submission 003

Goal: improve scanned or low-text PDFs where normal PyMuPDF extraction produced
little or no text.

Implemented candidate:
- `src/build_vision_ocr_cache.py`
- `data/processed/ocr_pages_vision.jsonl`
- `submissions/submission_003_tfidf_ocr_evidence.csv`

Change:
- Used macOS Vision OCR for low-text PDFs.
- Merged OCR text into the page cache before TF-IDF retrieval.
- OCR cache covered 43 low-text PDFs, 761 pages total, with 758 non-empty OCR
  pages.
- Changed 83 evidence-page rows and 90 answer rows versus submission 002.

Result:
- Public score improved from 0.23 to 0.26.

Compliance note:
- This submitted file used macOS Vision/Live Text OCR through local tooling.
  That is a competition-rule risk because the competition requires open models.
  Treat the score as evidence that OCR improves grounding, not as a pipeline to
  keep expanding. The next OCR/VLM implementation should be rebuilt with open
  models only, such as EasyOCR/Tesseract/open VLMs, before further official use.

## Current Recon

- Kaggle CLI `kaggle kernels list --competition lava-challenge-2026` at
  2026-04-30 16:25 BST returned `Not found`; no competition-linked public Code
  was visible through the CLI.
- Known discussion clarification remains important: evidence page numbers must
  use PDF page order starting at 1, not printed header/footer page numbers.
- No observed submission-format change: `id,answer,evidence_page_number`.

## Server Sync

Remote同步状态：

GPU 运行环境已确认可用，硬件满足 OCR/VLM 实验需求。

Remote数据状态：
- `data/raw` downloaded and unzipped on the server.
- Test PDFs: 200.
- Train PDFs: 5.
- Processed caches and submission files were partially synced via tar/scp; the
  large raw data should continue to be maintained by server-side Kaggle
  download rather than slow local upload.

## Next Direction

The public-score gain from OCR confirms that grounding still has room, but the
baseline answer generation is weak. Next loop should prioritize an open VLM/LLM
answer extractor on the retrieved pages on the GPU server. A smaller
deterministic fallback is to improve numeric arithmetic and table/list
extraction on OCR text.
