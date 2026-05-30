# LAVA Challenge 2026 - 20260530 提交汇总

## 进度核验
- 赛前按 `kaggle competitions submissions -c lava-challenge-2026 --csv --page-size 200` 核验：2026-05-30 当日从 `0/5` 开始。
- 比赛状态按 `kaggle competitions list --search lava-challenge-2026` 核验：截止时间 `2026-05-31 15:00:00`。
- 本轮全部提交均以 Kaggle 接口接受记录和提交列表新增记录为准，最终当日额度达到 `5/5`。

## 本轮策略
- 放弃昨日简单 anchor 阈值变体。
- 新增 `src/make_hybrid_breakthrough_submission.py`，合并 PyMuPDF、Vision、Tesseract、ocrmac、EasyOCR 页文本后重做 evidence 检索。
- 先验证 pure question retrieval，再切到 `answer_terms_query`，用历史最优 `submission_004_qwen_vl_best_evidence.csv` 的答案列扩展检索 query。
- 公开 code 巡检发现的 ColQwen 方向说明视觉/页面检索仍是主要瓶颈；本地服务器当前不可连，故本轮走 CPU 可复现 merged-OCR 检索。

## 本轮5次提交结果

| # | 文件 | Description | 状态 | publicScore | 备注 |
| --- | --- | --- | --- | --- | --- |
| 1 | `submission_060_allocr_question_mp1.csv` | `breakthrough10_01_20260530_014944` | `SubmissionStatus.COMPLETE` | `0.28` | all-OCR question, mp1 |
| 2 | `submission_061_allocr_question_mp2.csv` | `breakthrough10_02_20260530_020727` | `SubmissionStatus.COMPLETE` | `0.30` | all-OCR question, mp2 |
| 3 | `submission_062_allocr_answer_terms_mp2.csv` | `breakthrough10_03_20260530_022809` | `SubmissionStatus.COMPLETE` | `0.31` | answer terms query, mp2 |
| 4 | `submission_063_history_vote_028_locked.csv` | `breakthrough10_01_20260530_024755` | `SubmissionStatus.COMPLETE` | `0.28` | history vote; score via submission list |
| 5 | `submission_070_allocr_answer_terms_mp2_rel070.csv` | `breakthrough10b_01_20260530_024926` | `SubmissionStatus.COMPLETE` | `0.31` | answer terms query, lower rel threshold |

## 结果
- 本轮最高 public score：`0.31`。
- 相比历史最高 `0.29`，提升 `+0.02`。
- 明确信号：`answer_terms_query` 优于 pure question retrieval；放宽到 rel `0.70` 没有继续涨分，说明 `submission_062` 附近是当前本地 merged-OCR 的较好点。
- 不利信号：历史投票 `submission_063` 回落到 `0.28`，不应继续作为主线。

## 备用候选
- 已生成但未提交：`submission_066_allocr_question_mp3_rel085.csv`、`submission_067_allocr_question_mp2_rel075.csv`、`submission_068_allocr_question_mp3_rel092.csv`、`submission_069_allocr_answer_terms_mp3_rel080.csv`、`submission_071_allocr_answer_terms_mp3_rel090.csv`、`submission_072_allocr_answer_query_mp2_rel080.csv`。
- 下一轮优先方向：以 `submission_062` 为基准，继续做 answer terms 检索的小范围扰动；若 GPU 恢复，优先补 ColQwen/ColPali 页检索。
