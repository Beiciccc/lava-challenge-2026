# Submission 001

Date: 2026-04-30

Competition: `lava-challenge-2026`

Submitted file: `submissions/submission_001_public_0.22.csv`

Kaggle message: `first baseline: char-tfidf evidence retrieval with snippet answers`

Status: `SubmissionStatus.COMPLETE`

Public score: `0.22`

Current leaderboard position observed: `8 / 11`

## Pre-Submit Checks

- Submission quota: Kaggle metadata reported `maxDailySubmissions=5`.
- Before submission: `kaggle competitions submissions -c lava-challenge-2026` returned no submissions.
- Code/Discussion scan: no useful competition-linked public notebooks; key host clarification says evidence pages are PDF ordinal page numbers starting at 1, not printed page labels.
- Test shape: 624 rows, 200 PDFs.
- Submission validation: 624 rows, columns `id,answer,evidence_page_number`, id order matched sample, no NaN, evidence lists parsed, page numbers within PDF page counts.

## Method

- Extracted PDF page text with PyMuPDF, falling back to pypdf.
- Retrieved evidence pages per question using character n-gram TF-IDF over pages from the same PDF.
- Answer generation was conservative: best retrieved-line snippet for string/list, first number in snippet for number questions.

## Local Validation

Training evidence F1 on 16 labeled examples:

- TF-IDF page retrieval: `0.6187`
- Always `[1]` baseline: `0.1917`

Known weakness:

- 36 / 200 test PDFs have zero extracted text, so this baseline falls back poorly for image-only or scan-heavy files.
- Answers are not true VQA outputs and are expected to be weak.

## Outcome

The first submission was accepted and scored `0.22` public.

## Next Rules / Direction

1. Keep the TF-IDF evidence retriever as the text baseline.
2. Add OCR/VLM handling for zero-text PDFs before the next submission.
3. Replace snippet answers with a real open-model QA stage constrained by retrieved pages.
4. Keep evidence page numbers as PDF ordinal pages starting at 1.
5. Re-check daily remaining submissions before every future submission.

## Server Sync

Remote SSH 认证在该轮次出现问题，已转为本地完成剩余实验准备。
待可用后将同步最新模型与提交产物。
