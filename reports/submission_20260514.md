## LAVA Challenge 2026 - 2026-05-14 Submission Cycle

### 配额与执行规则
- 事前查询：当日提交列表中已有 1 条 `SubmissionStatus.PENDING`（`submission_047_rules_from_046_qwen_evi.csv`）
- 当日可用额度：`4/5`（以提交列表新增/接受记录为准）
- 按“先查额度→提交→查询列表确认接收→等待排行榜返回分数”的流程执行

### 本轮提交记录
| 文件 | 描述 | 提交时间 | 接受/状态 | 公榜分数 |
| --- | --- | --- | --- | --- |
| `submission_045_qwen_evi_from_031_mp4_r085_s003.csv` | `daily14_remote_01_20260514_031105` | 02:11:07 | `accepted_by_kaggle=True`, `SubmissionStatus.PENDING` | 无 |
| `submission_046_qwen_evi_from_032_mp3_r065_s003.csv` | `daily14_remote_01_20260514_031201` | 02:12:02 | `accepted_by_kaggle=True`, `SubmissionStatus.PENDING` | 无 |
| `submission_047_rules_from_046_qwen_evi.csv` | `daily14_remote_01_20260514_031211` | 02:12:13 | `accepted_by_kaggle=True`, `SubmissionStatus.PENDING` | 无 |
| `submission_049_anchor_score7_union.csv` | `daily14_remote_01_20260514_031300` | 02:13:01 | `accepted_by_kaggle=True`, `SubmissionStatus.PENDING`（持续轮询中） | 无 |
| `submission_048_anchor_score9_union.csv`（边界测试） | `quota_check_...` | 03:24:xx | `Submit failed: 403 Client Error: Forbidden` | 无 |

### 运行日志
- 变更文件：`logs/kaggle_submit_20260514.log`
- 当日日志中 `submission_049_anchor_score7_union` 已持续 `poll attempt 19`，仍为 `SubmissionStatus.PENDING`

### 复盘与建议
- 当天额度已占满（含已有 1 条 + 当日新提交 4 条），因此再次提交会被拒。
- 目前 4 条本轮提交均未出榜分数，疑似评分队列堵塞/延迟。
- 下轮建议：
  - 先保持仅提交一次，观察 49/047 两类 `pending` 在公榜恢复后的实际 `publicScore`
  - 若超过 30 分钟仍无 `COMPLETE`，改用短周期重试，避免一次性耗尽额度后阻塞
  - 待队列回稳后再执行新 `anchor/evidence` 变体实验

### 关联文件
- [日志 JSONL](/Volumes/Z/LAVA%20Challenge%202026/logs/kaggle_submit_20260514.log)
- [提交文件](/Volumes/Z/LAVA%20Challenge%202026/submissions/submission_045_qwen_evi_from_031_mp4_r085_s003.csv)
- [提交文件](/Volumes/Z/LAVA%20Challenge%202026/submissions/submission_046_qwen_evi_from_032_mp3_r065_s003.csv)
- [提交文件](/Volumes/Z/LAVA%20Challenge%202026/submissions/submission_047_rules_from_046_qwen_evi.csv)
- [提交文件](/Volumes/Z/LAVA%20Challenge%202026/submissions/submission_049_anchor_score7_union.csv)
