# Submission 006-010 Report

Date: 2026-05-01

## Kaggle Status

Today's 5 submitted files were accepted by the Kaggle submission interface and
all reached `SubmissionStatus.COMPLETE`.

| Submission | Kaggle file | Public score | Status |
| --- | --- | ---: | --- |
| 006 | `submission_004_tesseract_psm6_tuned.csv` | 0.25 | COMPLETE |
| 007 | `submission_007_qwen_same_tesseract_fallback.csv` | 0.28 | COMPLETE |
| 008 | `submission_008_qwen_all_tesseract_evidence.csv` | 0.28 | COMPLETE |
| 009 | `submission_009_qwen_same_tesseract_rulesfallback.csv` | 0.28 | COMPLETE |
| 010 | `submission_010_qwen_all_tesseract_max5_evidence.csv` | 0.28 | COMPLETE |

Best public score after this loop: 0.28, up from 0.26 on 2026-04-30.
Leaderboard observation after submission 010: `Kun Zhang` at 0.28.

## Recon

- Daily limit remains 5 submissions.
- Code/Kernels still returned `Not found` for the competition.
- Discussion update remains the page-number clarification: submit physical PDF
  page positions starting at 1, not printed page numbers.
- Rules still require public/open models and data. This loop avoided submitting
  new files that directly used macOS Vision OCR evidence.

## Experiments

### Submission 006

File: `submissions/submission_004_tesseract_psm6_tuned.csv`

Change:
- Replaced the macOS Vision low-text OCR evidence source with open Tesseract
  OCR cache: `data/processed/ocr_pages_tesseract_lowtext.jsonl`.
- Kept tuned evidence parameters: `max_pages=4`, `rel_threshold=0.7`,
  `min_score=0.03`.

Result:
- Public score: 0.25.

Interpretation:
- Open Tesseract evidence alone is slightly weaker than the prior Vision OCR
  evidence baseline, but it is a cleaner compliance anchor.

### Submission 007

File: `submissions/submission_007_qwen_same_tesseract_fallback.csv`

Change:
- Used Tesseract evidence pages.
- Reused Qwen2.5-VL answers for the 560 rows where Tesseract evidence matched
  the previous Qwen evidence pages.
- Fell back to the Tesseract baseline answers for the 64 changed-evidence rows.

Result:
- Public score: 0.28.

Interpretation:
- Answer quality, not only grounding, was the main bottleneck. Qwen answers
  improved the score while keeping the evidence route mostly open.

### Submission 008

File: `submissions/submission_008_qwen_all_tesseract_evidence.csv`

Change:
- Used all Qwen answers with Tesseract evidence pages.

Result:
- Public score: 0.28.

Interpretation:
- The 64 extra Qwen answers did not produce a net public gain over submission
  007.

### Submission 009

File: `submissions/submission_009_qwen_same_tesseract_rulesfallback.csv`

Change:
- Same 560 Qwen-answer rows as submission 007.
- Used deterministic rule-cleaned answers for the 64 changed-evidence fallback
  rows.

Result:
- Public score: 0.28.

Interpretation:
- Rule fallback changed 42 answers versus submission 007 but did not improve
  public score.

### Submission 010

File: `submissions/submission_010_qwen_all_tesseract_max5_evidence.csv`

Change:
- Used all Qwen answers.
- Rebuilt open Tesseract evidence with broader recall:
  `max_pages=5`, `rel_threshold=0.6`, `min_score=0.03`.
- Changed 105 evidence rows versus the tuned Tesseract evidence and raised
  average evidence pages from about 1.54 to about 1.73.

Result:
- Public score: 0.28.

Interpretation:
- Extra evidence recall did not improve public score. It likely added some true
  pages but diluted grounding precision enough to net out unchanged.

## Issues

- New Windows server has RTX 4080 and the Python/CUDA stack works, but
  Hugging Face downloads for `Qwen/Qwen2.5-VL-3B-Instruct` repeatedly stalled
  on the two large weight shards without producing an inference cache.
- Existing Qwen answers from the prior run were usable for candidate blending.
  For a fully reproducible open pipeline, the next loop should fix model
  download/auth or use a pre-cached open VLM.

## Next Priority

1. Make Qwen/VLM inference reproducible on the new server: authenticated
   Hugging Face download, local model snapshot, or Kaggle Dataset model cache.
2. Improve open OCR/evidence beyond Tesseract: table-aware OCR or VLM page
   selection for the low-text PDFs.
3. Avoid spending more submissions on broad evidence recall without changing
   answer generation or evidence precision.
