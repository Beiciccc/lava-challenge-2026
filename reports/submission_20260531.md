# LAVA Challenge 2026 - 20260531 提交汇总

## 进度核验
- 提交前按 `kaggle competitions submissions -c lava-challenge-2026 --csv --page-size 200` 核验：2026-05-31 当日从 `0/5` 开始。
- 比赛截止时间按 Kaggle CLI 核验：`2026-05-31 15:00:00`。
- 公共 Code 巡检未发现 2026-05-31 新代码；仍只有 `nhutdataprojet/llava-colqwen`。
- 公开榜榜首仍为 `The Static Toaster`，public score `0.87`；2026-05-31 多个前排队伍更新到 `0.60-0.80` 区间。
- 本轮全部提交均以 Kaggle 接口接受记录和提交列表新增记录为准，最终当日额度达到 `5/5`。

## 本轮策略
- 延续 2026-05-30 的 merged-OCR evidence 检索主线，避免继续提交已验证回落的 `history_vote`。
- 训练集代理评估显示 `answer_terms_query` 在 `max_pages=3, rel_threshold=0.70` 附近局部最优，因此先测试 `mp3 rel0.70/0.75`。
- 纯 evidence 页扰动未能突破后，追加少量高置信答案修正候选，测试答案修正与证据页组合是否能打破 `0.31` 平台。
- 已生成但未全部提交的备用候选保留在 `submissions/`，便于复盘参数影响。

## 本轮5次提交结果

| # | 文件 | Description | 状态 | publicScore | 备注 |
| --- | --- | --- | --- | --- | --- |
| 1 | `submission_073_allocr_answer_terms_mp3_rel070_min005.csv` | `finalday11_01_20260531_061346` | `SubmissionStatus.COMPLETE` | `0.31` | answer terms query, mp3, rel 0.70 |
| 2 | `submission_074_allocr_answer_terms_mp3_rel075_min005.csv` | `finalday11_01_20260531_063629` | `SubmissionStatus.COMPLETE` | `0.31` | answer terms query, mp3, rel 0.75 |
| 3 | `submission_078_manual_front20_plus_qwen_highconf.csv` | `finalday11_manual_01_20260531_065725` | `SubmissionStatus.COMPLETE` | `0.31` | 12 个高置信答案修正，接近 `submission_062` 证据页 |
| 4 | `submission_082_manual_plus_q0023.csv` | `finalday11_q0023_01_20260531_071715` | `SubmissionStatus.COMPLETE` | `0.31` | 在 078 基础上追加 `q_0023` 修正，共 13 个答案修正 |
| 5 | `submission_083_manual_q0023_on_069_mp3_rel080.csv` | `finalday11_final083_01_20260531_074250` | `SubmissionStatus.COMPLETE` | `0.31` | 082 的答案修正 + `mp3 rel0.80` evidence 组合 |

## 结果
- 本轮最高 public score：`0.31`。
- 相比 2026-05-30 最高分 `0.31`，未继续提升。
- 结论一：`answer_terms_query` 的 evidence 页阈值扰动已经进入平台区，单独换页不能突破。
- 结论二：少量高置信答案修正没有带来公榜提升，说明当前错误不只在少数明显答案项，也可能包括页面检索召回、OCR 噪声和长尾问题类型。
- 结论三：继续冲高需要更强的视觉页面检索/重排和端到端 VLM 答案验证；只做 merged-OCR 的局部阈值搜索，预期上限仍在 `0.31` 左右。

## 备用候选
- 已生成未提交：`submission_075_allocr_answer_terms_mp3_rel080.csv`、`submission_076_allocr_answer_terms_mp2_rel095.csv`、`submission_077_answer_presence_mp2_m2_fb062.csv`。
- 已生成未提交：`submission_079_manual_highconf_on_069_mp3_rel080.csv`、`submission_080_manual_highconf_on_071_mp3_rel090.csv`、`submission_081_manual_highconf_on_072_answer_query.csv`。
- 本轮日志：`logs/kaggle_submit_20260531.log`。
