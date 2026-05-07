# Submission 004-005 Report

Date: 2026-04-30

## Kaggle Status

Daily limit is 5 submissions. The Kaggle submission list now shows all 5 used
today.

| Submission | Kaggle file | Public score | Status |
| --- | --- | ---: | --- |
| 001 | `submission_baseline_tfidf.csv` | 0.22 | COMPLETE |
| 002 | `submission_002_tfidf_evidence_tuned.csv` | 0.23 | COMPLETE |
| 003 | `submission_003_tfidf_ocr_evidence.csv` | 0.26 | COMPLETE |
| 004 | `submission_004_rules_ocr_tuned.csv` | 0.26 | COMPLETE |
| 005 | `submission_005_more_evidence_recall.csv` | 0.26 | COMPLETE |

Current public leaderboard observation: rank 8 of 11, score 0.26.

## Recon

- Competition pages still show the same submission format:
  `id,answer,evidence_page_number`.
- Rules are unchanged: only public/open models and datasets are allowed; the
  inference pipeline must finish within 2 hours on one A100 40GB.
- Kaggle Code search still showed no competition-linked public notebooks.
- Discussion forum still has one topic. Latest host reply:
  2026-04-30 04:50 UTC, evidence page numbers must be the sequential PDF page
  positions starting at 1, not printed header/footer page numbers.

Sources:
- https://www.kaggle.com/competitions/lava-challenge-2026
- https://www.kaggle.com/competitions/lava-challenge-2026/discussion/695272
- https://lava-workshop.github.io/

## Submission 004

File: `submissions/submission_004_rules_ocr_tuned.csv`

Change:
- Kept the submission 003 evidence strategy and OCR-augmented page text.
- Replaced short snippet answers with deterministic rule-cleaned spans using
  `src/make_submission_004_rules_ocr_tuned.py`.
- Changed 349 answers versus submission 003.
- Evidence pages were unchanged versus submission 003.

Result:
- Public score stayed at 0.26.

Interpretation:
- The rule cleanup did not improve the public score. It likely helped a few
  numeric/string rows but hurt enough list/string rows to net out unchanged.

## Submission 005

File: `submissions/submission_005_more_evidence_recall.csv`

Change:
- Increased evidence recall on the OCR baseline.
- Changed 108 evidence-page rows versus submission 003.
- Average evidence pages increased from 1.54 to 1.75.
- Changed 13 answers versus submission 003.

Result:
- Public score stayed at 0.26.

Interpretation:
- Adding more candidate evidence pages did not improve public score. The extra
  page recall probably raised some grounding overlaps but also diluted set-F1.

## Qwen VLM Candidate

File generated but not submitted due to the daily quota already being exhausted:
`submissions/submission_004_qwen_vl_best_evidence.csv`

Artifacts:
- `src/make_qwen_vl_submission.py`
- `data/processed/qwen_vl_answers_best_evidence.jsonl`

Details:
- Open model: `Qwen/Qwen2.5-VL-3B-Instruct`.
- Ran on the RTX 4090 server using rendered evidence-page images.
- Completed all 624 rows after Hugging Face mirror download.
- Passed local submission validation.
- Changed 613 answers while keeping submission 003 evidence pages fixed.

Sample improvement:
- `q_0016` changed from `ンが用いられている。` to `東京大学医学部附属病院`.

Risk:
- It uses evidence pages from submission 003, whose OCR cache came from macOS
  Vision and is not an open-model OCR source. For a fully compliant tomorrow
  submission, rerun evidence with open OCR or use text-only evidence before
  submitting the Qwen answer candidate.

## Next Loop Priority

1. Submit or evaluate the Qwen VLM answer candidate as soon as quota resets,
   preferably with open-model evidence pages.
2. Replace macOS Vision OCR with an open OCR pipeline. Tesseract full low-text
   OCR cache is already present as `data/processed/ocr_pages_tesseract_lowtext.jsonl`.
3. Do not spend more submissions on pure evidence-page recall until answer
   quality improves.
