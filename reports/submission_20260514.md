## LAVA Challenge 2026 - 2026-05-14 Submission Cycle

### 配额与观察说明
- 按 `2026-05-14` 的 Kaggle `submissions` 列表，今日共出现 **5/5** 条提交，额度已用满。
- 我方直接执行并核验了 1 条提交：`submission_047_rules_from_046_qwen_evi.csv`（`longwatch_20260514_01_20260514_031011`）。
  - 提交前配额：`0/5`
  - 提交后配额：`1/5`
  - Kaggle 已接受并进入 `SubmissionStatus.PENDING`
- 随后观察到另外 4 条同日提交已由其他并发流程写入 Kaggle 队列，因此停止继续发新提交，转为统一状态跟踪。
- 对这 4 条并发提交通道，无法补做“提交前/后”的实时本地探针，只能依据 Kaggle 列表确认它们已被接受并处于 `PENDING`，随后继续跟踪到终态。

### 今日五条提交结果
| # | 文件 | 描述 | Kaggle 接受并到达 `PENDING` | 最终状态 | `publicScore` |
| --- | --- | --- | --- | --- | --- |
| 1 | `submission_047_rules_from_046_qwen_evi.csv` | `longwatch_20260514_01_20260514_031011` | 是 | `SubmissionStatus.COMPLETE` | `0.25` |
| 2 | `submission_045_qwen_evi_from_031_mp4_r085_s003.csv` | `daily14_remote_01_20260514_031105` | 是 | `SubmissionStatus.COMPLETE` | `0.28` |
| 3 | `submission_046_qwen_evi_from_032_mp3_r065_s003.csv` | `daily14_remote_01_20260514_031201` | 是 | `SubmissionStatus.COMPLETE` | `0.28` |
| 4 | `submission_047_rules_from_046_qwen_evi.csv` | `daily14_remote_01_20260514_031211` | 是 | `SubmissionStatus.COMPLETE` | `0.25` |
| 5 | `submission_049_anchor_score7_union.csv` | `daily14_remote_01_20260514_031300` | 是 | `SubmissionStatus.COMPLETE` | `0.27` |

### 终态时间线
- `03:31` 左右观察到 `submission_046_qwen_evi_from_032_mp3_r065_s003.csv` 首先变为 `COMPLETE (0.28)`。
- `03:33` 左右观察到 `submission_045_qwen_evi_from_031_mp4_r085_s003.csv` 与 `longwatch_20260514_01_20260514_031011` 变为 `COMPLETE`。
- `03:35` 左右剩余两条 `submission_049_anchor_score7_union.csv` 与 `daily14_remote_01_20260514_031211` 也变为 `COMPLETE`。

### 相关文件
- 日志：[logs/kaggle_submit_20260514.log](/Volumes/Z/LAVA%20Challenge%202026/logs/kaggle_submit_20260514.log)
- 报告：[reports/submission_20260514.md](/Volumes/Z/LAVA%20Challenge%202026/reports/submission_20260514.md)
