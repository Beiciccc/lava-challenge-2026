## LAVA Challenge 2026 - 20260525 最后5次提交（冲分）

### 配额与执行
- 先查 `kaggle competitions submissions -c lava-challenge-2026`：
  - 任务开始前今日配额：`0/5`。
- 按队列顺序提交 5 条并轮询到 `SubmissionStatus.COMPLETE`。
  1. `submission_005_candidate_max5_rel06_abs003.csv`
  2. `submission_005_candidate_max4_rel06_abs001.csv`
  3. `submission_004_rules_on_best_evidence.csv`
  4. `submission_004_rules_on_open_small_evidence.csv`（message：`final5_20260525c_01_20260525_090644`）
  5. `submission_004_rules_on_open_small_evidence.csv`（message：`final5_20260525b_02_20260525_090654`，同文件重复提交）

### 本轮五条提交结果（最终）
| # | 文件 | Description | 状态 | publicScore | PollAttempts | ElapsedMinutes |
| --- | --- | --- | --- | --- | --- |
| 1 | `submission_005_candidate_max5_rel06_abs003.csv` | `final5_20260525_01_20260525_075854` | `SubmissionStatus.COMPLETE` | `0.26` | `25` | `18.40` |
| 2 | `submission_005_candidate_max4_rel06_abs001.csv` | `final5_20260525_02_20260525_081722` | `SubmissionStatus.COMPLETE` | `0.26` | `11` | `3.12` |
| 3 | `submission_004_rules_on_best_evidence.csv` | `final5_20260525b_01_20260525_084031` | `SubmissionStatus.COMPLETE` | `0.26` | `35` | `26.01` |
| 4 | `submission_004_rules_on_open_small_evidence.csv` | `final5_20260525c_01_20260525_090644` | `SubmissionStatus.COMPLETE` | `0.24` | `29` | `21.50` |
| 5 | `submission_004_rules_on_open_small_evidence.csv` | `final5_20260525b_02_20260525_090654` | `SubmissionStatus.COMPLETE` | `0.24` | `31` | `23.02` |

### 结果结论
- 本轮最终最高分：`0.26`（第 1、2、3 条）。
- 本轮平均分：`0.252`。
- 当日配额用尽（`5/5`），提交循环结束。
- 本轮日志：`logs/kaggle_submit_20260525.log`
