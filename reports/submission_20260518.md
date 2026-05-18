## LAVA Challenge 2026 - 2026-05-18 最后5次提交（复盘）

### 配额与执行
- 当日配额前查询：`0/5`（先通过 `kaggle competitions submissions -c lava-challenge-2026` 与提交列表确认）。
- 本轮提交 5 条并按顺序轮询至 `SubmissionStatus.COMPLETE`：
  1. `submission_016_qwen_anchor_m1_s4_ffalse.csv`
  2. `submission_019_qwen_anchor_m2_s8_ffalse.csv`
  3. `submission_020_qwen_anchor_m2_s2_ftrue.csv`
  4. `submission_021_qwen_postproc_trim.csv`
  5. `submission_022_qwen_max3_replay.csv`

### 本轮五条提交结果（最终）
| # | 文件 | Description | 状态 | publicScore |
| --- | --- | --- | --- | --- |
| 1 | `submission_016_qwen_anchor_m1_s4_ffalse.csv` | `final5_20260518_01_20260518_055123` | `SubmissionStatus.COMPLETE` | `0.21` |
| 2 | `submission_019_qwen_anchor_m2_s8_ffalse.csv` | `final5_20260518_02_20260518_061245` | `SubmissionStatus.COMPLETE` | `0.25` |
| 3 | `submission_020_qwen_anchor_m2_s2_ftrue.csv` | `final5_20260518_03_20260518_063229` | `SubmissionStatus.COMPLETE` | `0.26` |
| 4 | `submission_021_qwen_postproc_trim.csv` | `final5_20260518_04_20260518_064914` | `SubmissionStatus.COMPLETE` | `0.28` |
| 5 | `submission_022_qwen_max3_replay.csv` | `final5_20260518_05_01_20260518_070811` | `SubmissionStatus.COMPLETE` | `0.28` |

### 结果结论
- 本轮最终最高分：`0.28`（第 4、5 条），本轮平均分为 `0.256`。
- 4、5 号都在队列末端完成；5/5 使用后当日配额用尽，提交循环结束。
- 本轮日志与提交流程见：`logs/kaggle_submit_20260518.log`

### 附录：文件变更
- 新增提交文件：
  - `submissions/submission_016_qwen_anchor_m1_s4_ffalse.csv`
  - `submissions/submission_019_qwen_anchor_m2_s8_ffalse.csv`
  - `submissions/submission_020_qwen_anchor_m2_s2_ftrue.csv`
  - `submissions/submission_021_qwen_postproc_trim.csv`
  - `submissions/submission_022_qwen_max3_replay.csv`
