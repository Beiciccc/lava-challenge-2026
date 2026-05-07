# Submission 011-015 Report

Date: 2026-05-02

## Kaggle Status

Five submissions were accepted by the Kaggle interface for the 2026-05-02 loop
and all reached `SubmissionStatus.COMPLETE`.

| Submission | Kaggle file | Public score | Status |
| --- | --- | ---: | --- |
| 011 | `submission_012_qwen_all_tesseract_max2_rel07.csv` | 0.28 | COMPLETE |
| 012 | `submission_014_qwen_all_tesseract_max4_rel085.csv` | 0.27 | COMPLETE |
| 013 | `submission_013_qwen_all_tesseract_max3_rel08.csv` | 0.28 | COMPLETE |
| 014 | `submission_011_qwen_all_tesseract_top1.csv` | 0.26 | COMPLETE |
| 015 | `submission_015_qwen_all_textonly_tuned.csv` | 0.27 | COMPLETE |

Best public score after this loop remains 0.28.
Leaderboard observation after submission 015: `Kun Zhang` at 0.28.

## Recon

- The local submission list had no 2026-05-02 entries before this loop.
- Leaderboard had new movement from other teams; top score observed at 0.57.
- Competition Code/Kernels still returned `Not found`.
- No usable new Discussion content was found. The known page-number rule still
  applies: evidence pages are PDF physical page positions, 1-based.

## Experiment Theme

Yesterday's submissions 007-010 showed that Qwen answers with open Tesseract
evidence plateaued at 0.28. Today tested whether changing evidence precision
or OCR dependence around the same Qwen answers could move the public score.

All submitted candidates used the Qwen answer column from
`submission_008_qwen_all_tesseract_evidence.csv`; only evidence pages changed.
This stayed on the open/compliant route and avoided submitting the macOS Vision
OCR evidence candidate.

## Submissions

### Submission 011

File: `submissions/submission_012_qwen_all_tesseract_max2_rel07.csv`

Change:
- Tesseract evidence with `max_pages=2`, `rel_threshold=0.7`,
  `min_score=0.03`.
- Average evidence pages: about 1.31.
- Changed 92 evidence rows versus submission 008.

Result:
- Public score: 0.28.

Interpretation:
- More precise evidence did not improve the public score, but did not hurt.

### Submission 012

File: `submissions/submission_014_qwen_all_tesseract_max4_rel085.csv`

Change:
- Stricter Tesseract evidence with `max_pages=4`, `rel_threshold=0.85`,
  `min_score=0.05`.
- Average evidence pages: about 1.11.
- Changed 165 evidence rows versus submission 008.

Result:
- Public score: 0.27.

Interpretation:
- This became too narrow or selected the wrong page on enough rows to lose
  grounding score.

### Submission 013

File: `submissions/submission_013_qwen_all_tesseract_max3_rel08.csv`

Change:
- Middle evidence shape with `max_pages=3`, `rel_threshold=0.8`,
  `min_score=0.03`.
- Average evidence pages: about 1.32.
- Changed 108 evidence rows versus submission 008.

Result:
- Public score: 0.28.

Interpretation:
- Equivalent public score to submissions 008, 010, and 011.

### Submission 014

File: `submissions/submission_011_qwen_all_tesseract_top1.csv`

Change:
- Top-1 Tesseract evidence only.
- Average evidence pages: 1.00.
- Changed 191 evidence rows versus submission 008.

Result:
- Public score: 0.26.

Interpretation:
- Single-page evidence is too narrow for this task.

### Submission 015

File: `submissions/submission_015_qwen_all_textonly_tuned.csv`

Change:
- Text-only evidence without low-text Tesseract OCR.
- Tuned baseline evidence parameters: `max_pages=4`, `rel_threshold=0.7`,
  `min_score=0.03`.
- Average evidence pages: about 1.49.
- Changed 86 evidence rows versus submission 008.

Result:
- Public score: 0.27.

Interpretation:
- Open OCR still matters; removing it loses score.

## Conclusions

- Current open Tesseract evidence plus cached Qwen answers is stable at 0.28.
- Evidence-only tuning around this retrieval method is unlikely to break 0.28.
- Overly narrow evidence hurts: top-1 fell to 0.26 and strict rel0.85 fell to
  0.27.
- The next useful improvement must change the answer/evidence joint pipeline,
  not just the number of evidence pages.

## Next Priority

1. Fix reproducible Qwen/VLM inference on the Windows RTX 4080 server so answers
   can be regenerated against each candidate evidence set.
2. Build a better open OCR/evidence layer for low-text PDFs, preferably
   table-aware, instead of relying on simple Tesseract text.
3. Consider targeted per-question-type strategies for arithmetic/table/list
   questions, because the same Qwen answers plateau across evidence variants.
