# LAVA Challenge 2026

本仓库用于记录 `lava-challenge-2026` 的实验、提交与可复现脚本，包含：

- 方案代码（`src/`）
- 训练与推理脚本（`scripts/`）
- 处理后数据片段（`data/processed/`, `data/raw/` 中的轻量文件）
- 提交结果与实验记录（`submissions/`, `reports/`, `logs/`）

## 数据与产物说明

- `data/raw/train.csv`、`data/raw/test.csv`、`data/raw/sample_submission.csv`：用于本地验证与提交格式。
- `data/processed/`：OCR 与候选证据缓存（轻量 JSONL）。
- `submissions/`：实验输出提交文件（按版本归档）。
- `reports/`：每轮实验记录、得分、规则调整与复盘。

## 快速运行

安装依赖：

```bash
pip install -r requirements.txt
```

生成基线提交文件：

```bash
python3 src/make_baseline_submission.py \
  --train-csv data/raw/train.csv \
  --test-csv data/raw/test.csv \
  --out submissions/submission_baseline_tfidf.csv
```

## 日志

提交与排行榜监控日志写入 `logs/kaggle_submit_YYYYMMDD.log`，每条记录为 JSONL，包含：

- 提交文件与状态（如 `SubmissionStatus.PENDING/COMPLETE`）
- `public_score`
- 排行榜快照字段（用于趋势追踪）

查看当日提交列表：

```bash
kaggle competitions submissions -c lava-challenge-2026 --csv --page-size 20
```

查看排行榜：

```bash
kaggle competitions leaderboard -c lava-challenge-2026 --show --csv | head -n 2
```
