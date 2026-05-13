## LAVA Challenge 2026 - 2026-05-13 Submission Cycle

### 配额与执行规则
- 执行前查询到当日已存在 1 条提交（`submission_042_qwen_evi_from_030_mp4_r075_s004.csv`）处于 `PENDING`，可用额度 4/5。
- 当日总共执行 4 次新的提交命令 + 先前 1 条未决，共计 **5/5**，已满额。
- 执行时按“提交后查询状态 → 等待公榜返回结果”的方式循环。

### 本轮提交记录
| 文件 | 描述 | 提交时间 | 结果 |
| --- | --- | --- | --- |
| `submission_042_qwen_evi_from_030_mp4_r075_s004.csv` | `agentB_20260513_01_20260513_023331` | 01:33:32 | `SubmissionStatus.COMPLETE`, `publicScore=0.28` |
| `submission_046_qwen32_max2_rel09_min005.csv` | `daily13b_01_20260513_023409` | 01:34:10 | `SubmissionStatus.COMPLETE`, `publicScore=0.27` |
| `submission_044_qwen_evi_from_031_mp5_r08_s004.csv` | `daily13b_01_20260513_023440` | 01:34:41 | `SubmissionStatus.COMPLETE`, `publicScore=0.28` |
| `submission_045_qwen_evi_from_031_mp4_r085_s003.csv` | `daily13c_01_20260513_023630` | 01:36:32 | `SubmissionStatus.COMPLETE`, `publicScore=0.28` |
| `submission_043_qwen_evi_from_030_mp5_r075_s005.csv` | `agentB_20260513_01_20260513_023646` | 01:36:47 | `SubmissionStatus.COMPLETE`, `publicScore=0.27` |

### 验证与日志
- 变更文件已写入：`logs/kaggle_submit_20260513.log`
- 验证文件（如需复查）：
  - [submissions/submission_042_qwen_evi_from_030_mp4_r075_s004.csv](/Volumes/Z/LAVA%20Challenge%202026/submissions/submission_042_qwen_evi_from_030_mp4_r075_s004.csv)
  - [submissions/submission_046_qwen32_max2_rel09_min005.csv](/Volumes/Z/LAVA%20Challenge%202026/submissions/submission_046_qwen32_max2_rel09_min005.csv)
  - [submissions/submission_044_qwen_evi_from_031_mp5_r08_s004.csv](/Volumes/Z/LAVA%20Challenge%202026/submissions/submission_044_qwen_evi_from_031_mp5_r08_s004.csv)
  - [submissions/submission_045_qwen_evi_from_031_mp4_r085_s003.csv](/Volumes/Z/LAVA%20Challenge%202026/submissions/submission_045_qwen_evi_from_031_mp4_r085_s003.csv)
  - [submissions/submission_043_qwen_evi_from_030_mp5_r075_s005.csv](/Volumes/Z/LAVA%20Challenge%202026/submissions/submission_043_qwen_evi_from_030_mp5_r075_s005.csv)

### 当前建议（下一轮）
- 本轮最佳分数未突破 0.28（与前日最优一致），说明这类 EVI 参数变体在短窗口内收益趋稳。
- 下轮建议优先尝试不同证据约束策略（例如更严格的 `max_pages/min-score` 限制 + 规则答案替换验证），再回看 Qwen 系候选。
- 本地新增但未提交用于后续实验的文件：
  - `submission_047_rules_from_046_qwen_evi.csv`
  - `submission_048_anchor_score9_union.csv`
  - `submission_049_anchor_score7_union.csv`
