#!/usr/bin/env python3
"""Submit and monitor Kaggle competition submissions with daily limits and logging.

Usage:
    scripts/submit_and_monitor.py submissions/file1.csv submissions/file2.csv ...
"""

from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
import time
from collections.abc import Iterable
from datetime import datetime
from pathlib import Path
from typing import Any


def run_kaggle_csv(args: list[str]) -> list[dict[str, str]]:
    """Run a Kaggle CLI command and parse CSV output."""
    cmd = ["kaggle", "competitions"] + args + ["--csv"]
    proc = subprocess.run(cmd, check=False, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or proc.stdout.strip())
    rows: list[dict[str, str]] = []
    reader = csv.DictReader(proc.stdout.splitlines())
    for row in reader:
        rows.append({k: (v if v is not None else "") for k, v in row.items()})
    return rows


def count_today_submissions(rows: Iterable[dict[str, str]], today: str) -> int:
    """Count submissions with the same local date in `date` field."""
    total = 0
    for row in rows:
        date = row.get("date", "").split(" ", maxsplit=1)[0]
        if date == today:
            total += 1
    return total


def latest_matching_submission(
    rows: Iterable[dict[str, str]], file_name: str, message: str
) -> dict[str, str] | None:
    """Find the newest matching submission row."""
    for row in rows:
        if row.get("fileName") == file_name and row.get("description") == message:
            return row
    return None


def get_leaderboard_snapshot(competition: str) -> dict[str, Any]:
    top_rows = run_kaggle_csv(["leaderboard", "-c", competition, "--show"])
    best = top_rows[0] if top_rows else {}
    return {
        "team_id": best.get("teamId", ""),
        "team_name": best.get("teamName", ""),
        "top_score": best.get("score", ""),
        "top_submission_time": best.get("submissionDate", ""),
        "top_rows_fetched": len(top_rows),
    }


def get_team_leaderboard_row(
    competition: str, team_name: str
) -> dict[str, Any] | None:
    rows = run_kaggle_csv(["leaderboard", "-c", competition, "--show"])
    for idx, row in enumerate(rows, start=1):
        if row.get("teamName") == team_name:
            return {
                "rank": idx,
                "team_name": row.get("teamName", ""),
                "score": row.get("score", ""),
                "submission_time": row.get("submissionDate", ""),
            }
    return None


def call_submit(competition: str, file_path: str, message: str) -> None:
    cmd = [
        "kaggle",
        "competitions",
        "submit",
        "-c",
        competition,
        "-f",
        file_path,
        "-m",
        message,
    ]
    proc = subprocess.run(cmd, check=False, text=True, capture_output=True)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or proc.stdout.strip())


def safe_float(v: str) -> float | None:
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def wait_for_result(
    competition: str,
    file_name: str,
    message: str,
    poll_interval: int,
    max_wait_minutes: int,
    team_name: str | None,
    logger: Path,
) -> dict[str, Any]:
    start = time.time()
    deadline = start + max_wait_minutes * 60
    attempt = 0
    best_status = "PENDING"
    row: dict[str, str] | None = None

    while time.time() < deadline:
        attempt += 1
        rows = run_kaggle_csv(["submissions", "-c", competition, "--page-size", "200"])
        row = latest_matching_submission(rows, file_name, message)
        if row is None:
            status = "NOT_LISTED_YET"
            public_score = ""
        else:
            status = row.get("status", "UNKNOWN")
            public_score = row.get("publicScore", "")
            best_status = status

        leaderboard = get_leaderboard_snapshot(competition)
        team_entry = (
            get_team_leaderboard_row(competition, team_name)
            if team_name
            else None
        )

        payload = {
            "ts": datetime.now().isoformat(timespec="seconds"),
            "event": "poll",
            "competition": competition,
            "file": file_name,
            "message": message,
            "attempt": attempt,
            "status": status,
            "public_score": public_score,
            "leaderboard_top_team": leaderboard["team_name"],
            "leaderboard_top_score": leaderboard["top_score"],
            "team_leaderboard": team_entry,
        }
        with logger.open("a", encoding="utf-8") as f:
            f.write(json.dumps(payload, ensure_ascii=False) + "\n")

        if status in {
            "SubmissionStatus.COMPLETE",
            "SubmissionStatus.ERROR",
            "SubmissionStatus.INVALID",
            "SubmissionStatus.CANCELLED",
        }:
            break
        time.sleep(poll_interval)

    if row is None:
        row = {}

    return {
        "status": best_status,
        "public_score": row.get("publicScore", ""),
        "submitted_file": row.get("fileName", file_name),
        "description": row.get("description", message),
        "date": row.get("date", ""),
        "poll_attempts": attempt,
        "elapsed_minutes": (time.time() - start) / 60.0,
    }


def append_run_log(
    logger: Path,
    competition: str,
    file_path: str,
    message: str,
    result: dict[str, Any],
    team_name: str | None,
) -> None:
    payload = {
        "ts": datetime.now().isoformat(timespec="seconds"),
        "event": "result",
        "competition": competition,
        "file": file_path,
        "message": message,
        "team_name": team_name or "",
        **result,
    }
    with logger.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=False) + "\n")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("files", nargs="+", help="Submission CSV files to submit, sequentially.")
    p.add_argument(
        "--competition",
        default="lava-challenge-2026",
        help="Kaggle competition slug (default: %(default)s).",
    )
    p.add_argument("--max-daily", type=int, default=5, help="Max submissions today.")
    p.add_argument(
        "--poll-interval",
        type=int,
        default=45,
        help="Seconds between status polls.",
    )
    p.add_argument(
        "--max-wait-minutes",
        type=int,
        default=45,
        help="Max minutes to wait for each submission.",
    )
    p.add_argument(
        "--message-prefix",
        default="auto-submit",
        help="Message prefix for each submission.",
    )
    p.add_argument(
        "--team-name",
        default="",
        help="Exact team name used to capture your leaderboard row.",
    )
    p.add_argument(
        "--log",
        default="",
        help="JSONL log path. Default: logs/kaggle_submit_<date>.log.",
    )
    p.add_argument(
        "--max-retries",
        type=int,
        default=1,
        help="Retry times when Kaggle submit command fails (e.g. temporary CLI/network issue).",
    )
    return p.parse_args()


def main() -> None:
    args = parse_args()

    log_path = Path(args.log or f"logs/kaggle_submit_{datetime.now().strftime('%Y%m%d')}.log")
    log_path.parent.mkdir(parents=True, exist_ok=True)

    all_submissions = run_kaggle_csv(["submissions", "-c", args.competition, "--page-size", "200"])
    today = datetime.now().strftime("%Y-%m-%d")
    today_count = count_today_submissions(all_submissions, today)
    planned = len(args.files)
    if today_count + planned > args.max_daily:
        raise SystemExit(
            f"Quota risk: today={today} existing={today_count}, planned={planned}, max={args.max_daily}"
        )

    for idx, file_path in enumerate(args.files, start=1):
        file_path_obj = Path(file_path)
        if not file_path_obj.exists():
            raise SystemExit(f"Missing submission file: {file_path}")

        base = file_path_obj.name
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        message = f"{args.message_prefix}_{idx:02d}_{stamp}"
        print(
            f"[{idx}/{planned}] Submit {base} "
            f"| today used: {today_count + idx - 1}/{args.max_daily}"
        )

        attempts_left = args.max_retries + 1
        while True:
            try:
                call_submit(args.competition, str(file_path_obj), message)
                break
            except RuntimeError as exc:
                attempts_left -= 1
                if attempts_left <= 0:
                    raise SystemExit(f"Submit failed for {base}: {exc}")
                print(f"Submit failed, retrying ({attempts_left} left): {exc}")
                time.sleep(20)

        result = wait_for_result(
            args.competition,
            base,
            message,
            args.poll_interval,
            args.max_wait_minutes,
            args.team_name or None,
            log_path,
        )
        append_run_log(log_path, args.competition, base, message, result, args.team_name or None)

        status = result["status"]
        score = safe_float(result["public_score"] or "")
        print(
            f"Done file={base} status={status} "
            f"publicScore={score if score is not None else 'N/A'} attempts={result['poll_attempts']}"
        )


if __name__ == "__main__":
    try:
        main()
    except RuntimeError as exc:
        raise SystemExit(str(exc)) from None
