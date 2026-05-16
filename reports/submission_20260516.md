## LAVA Challenge 2026 - 2026-05-16 Final 5 Submissions

### 配额与执行
- 当日提交配额前查询：`0/5`（先前 60 条历史记录均为历史提交，未含当日记录）。
- 本轮直接提交 5 条未提交版本并持续轮询到 `SubmissionStatus.COMPLETE`：
  1. `submission_038_qwen32_max4_rel09_min004.csv`
  2. `submission_026_qwen009_ans_ev022.csv`
  3. `submission_027_qwen008_ans_ev022.csv`
  4. `submission_018_qwen_anchor_m3_s4_ffalse.csv`
  5. `submission_017_qwen_anchor_m2_s4_ffalse.csv`

### 本轮五条提交结果（最终）
| # | 文件 | 描述 | `publicScore` | 状态 |
| --- | --- | --- | --- | --- |
| 1 | `submission_038_qwen32_max4_rel09_min004.csv` | `final5_20260516_01_20260516_204226` | `0.27` | `SubmissionStatus.COMPLETE` |
| 2 | `submission_026_qwen009_ans_ev022.csv` | `final5_20260516_02_20260516_204613` | `0.28` | `SubmissionStatus.COMPLETE` |
| 3 | `submission_027_qwen008_ans_ev022.csv` | `final5_20260516_03_20260516_204616` | `0.28` | `SubmissionStatus.COMPLETE` |
| 4 | `submission_018_qwen_anchor_m3_s4_ffalse.csv` | `final5_20260516_04_20260516_204619` | `0.23` | `SubmissionStatus.COMPLETE` |
| 5 | `submission_017_qwen_anchor_m2_s4_ffalse.csv` | `final5_20260516_05_20260516_204622` | `0.22` | `SubmissionStatus.COMPLETE` |

### 结果总结
- 本轮最高分为 `0.28`，未超越当前历史最优（0.80/位于榜首）；
- 本轮提交全部为 `PENDING` 过程中较长（约 1.5 小时），显示公共评测队列延迟明显，后续建议继续使用批量提交后异步拉取状态。

### 关联文件
- 日志：`logs/kaggle_submit_20260516.log`
- 报告：`reports/submission_20260516.md`
- 该批提交文件见 `submissions/`（5 条新提交对应条目）
