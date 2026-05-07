# Submission 016-022 Report (2026-05-04)

## Kaggle Status Snapshot

This round completed 5 submissions and used the full daily quota available for
2026-05-04.

| No | Submission file | Message | Status | Public score |
| --- | --- | --- | --- | ---: |
| 1 | `submission_016_qwen_anchor_m1_s4_ffalse.csv` | `anchor_m1_s4_ffalse` | COMPLETE | 0.21 |
| 2 | `submission_019_qwen_anchor_m2_s8_ffalse.csv` | `anchor_m2_s8` | COMPLETE | 0.25 |
| 3 | `submission_020_qwen_anchor_m2_s2_ftrue.csv` | `anchor_m2_s2_union` | COMPLETE | 0.26 |
| 4 | `submission_021_qwen_postproc_trim.csv` | `postproc_trim8` | COMPLETE | 0.28 |
| 5 | `submission_022_qwen_max3_replay.csv` | `replay_013` | COMPLETE | 0.28 |

Best public score in this cycle remained `0.28`.

## Experiment Log

- 先提交了 3 个锚定式 evidence 重排方案（`make_answer_anchored_submission.py`）：
  - `max_pages=1,min_score=4` (`016`)
  - `max_pages=2,min_score=8` (`019`)
  - `max_pages=2,min_score=2, include_fallback_pages` (`020`)
- 这三类表现均显著低于基线（`0.21 / 0.25 / 0.26`），判定为高风险方向。
- 按规则回退：改为轻量后处理（仅修正 6 行异常字符串/列表长度）：
  - `submission_021_qwen_postproc_trim.csv`，得到 0.28。
- 第5次为了保留可复现高分对照，提交了 `submission_013_qwen_all_tesseract_max3_rel08.csv` 的语义等价复刻：
  - `submission_022_qwen_max3_replay.csv`，得到 0.28。

## 当前结论

- 纯 anchor（基于答案文本反锚定 evidence）在本地参数下并不稳定，均明显拖分。
- 轻量后处理可在不动证据的前提下维持 0.28。
- 最稳的候选仍是 max3/rellike 的 qwen-open OCR 组合（保留作为基线）与小幅裁剪后处理版本。

## 文件变更

- 新增提交文件：
  - `submissions/submission_016_qwen_anchor_m1_s4_ffalse.csv`
  - `submissions/submission_019_qwen_anchor_m2_s8_ffalse.csv`
  - `submissions/submission_020_qwen_anchor_m2_s2_ftrue.csv`
  - `submissions/submission_021_qwen_postproc_trim.csv`
  - `submissions/submission_022_qwen_max3_replay.csv`
