#!/usr/bin/env python3
"""Generate LAVA answers with a text LLM over merged OCR page context."""

from __future__ import annotations

import argparse
import ast
import json
import re
import time
import unicodedata
from collections import defaultdict
from pathlib import Path

import pandas as pd


OCR_CACHES = [
    "data/processed/ocr_pages_vision.jsonl",
    "data/processed/ocr_pages_tesseract_lowtext.jsonl",
    "data/processed/pdf_pages_ocrmac.jsonl",
    "data/processed/ocr_pages_easyocr_small.jsonl",
]


def parse_pages(raw: object) -> list[int]:
    try:
        parsed = ast.literal_eval(str(raw))
    except Exception:
        return [1]
    if not isinstance(parsed, list):
        return [1]
    pages: list[int] = []
    for page in parsed:
        try:
            page_num = int(page)
        except Exception:
            continue
        if page_num >= 1 and page_num not in pages:
            pages.append(page_num)
    return pages or [1]


def norm(text: object) -> str:
    text = unicodedata.normalize("NFKC", str(text)).lower()
    return re.sub(r"\s+", "", text)


def load_base_pages(path: Path) -> dict[str, dict[int, str]]:
    by_file: dict[str, dict[int, str]] = defaultdict(dict)
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            rec = json.loads(line)
            by_file[str(rec["file_id"])][int(rec["page_number"])] = str(rec.get("text", ""))
    return by_file


def append_cache(by_file: dict[str, dict[int, str]], path: Path) -> None:
    if not path.exists():
        return
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            rec = json.loads(line)
            text = str(rec.get("text", "")).strip()
            if not text:
                continue
            file_id = str(rec["file_id"])
            page = int(rec["page_number"])
            old = by_file[file_id].get(page, "")
            if norm(text) not in norm(old):
                by_file[file_id][page] = f"{old}\n{text}".strip()


def load_merged_pages(cache: Path) -> dict[str, dict[int, str]]:
    by_file = load_base_pages(cache)
    for cache_name in OCR_CACHES:
        append_cache(by_file, Path(cache_name))
    return by_file


def clean_answer(text: str, answer_format: str) -> str:
    text = text.strip()
    text = re.sub(r"^```(?:json|python)?", "", text, flags=re.I).strip()
    text = re.sub(r"```$", "", text).strip()
    text = re.sub(r"^(答え|回答|Answer|Final answer)\s*[:：]\s*", "", text, flags=re.I).strip()
    if answer_format in {"number", "string"}:
        text = text.splitlines()[0].strip()
    if answer_format == "number":
        match = re.search(
            r"[-+]?\d+(?:[,.]\d+)?(?:\s*(?:%|％|円|人|件|回|倍|㎡/人|m²/人|ℓ|L|リットル|年|月|日|時|分))?",
            text,
        )
        return match.group(0).replace(",", "") if match else "1"
    if answer_format in {"ordered_list", "unordered_list"}:
        start = text.find("[")
        end = text.rfind("]")
        if start >= 0 and end > start:
            candidate = text[start : end + 1]
            try:
                parsed = ast.literal_eval(candidate)
                if isinstance(parsed, list) and parsed:
                    return str([str(x).strip() for x in parsed if str(x).strip()] or ["Answer"])
            except Exception:
                pass
        parts = [p.strip(" ・,，、;；") for p in re.split(r"[\n,，、;；]+", text) if p.strip(" ・,，、;；")]
        return str(parts[:6] or ["Answer"])
    return text[:180].strip() or "Answer"


def load_done(path: Path) -> dict[str, dict[str, str]]:
    done: dict[str, dict[str, str]] = {}
    if not path.exists():
        return done
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            rec = json.loads(line)
            done[str(rec["id"])] = {k: str(v) for k, v in rec.items()}
    return done


def append_jsonl(path: Path, rec: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        f.flush()


def context_for(
    by_file: dict[str, dict[int, str]],
    file_id: str,
    pages: list[int],
    chars_per_page: int,
    max_context_chars: int,
) -> str:
    chunks: list[str] = []
    for page in pages:
        text = by_file.get(str(file_id), {}).get(page, "").strip()
        if not text:
            continue
        chunks.append(f"[page {page}]\n{text[:chars_per_page]}")
    context = "\n\n".join(chunks)
    return context[:max_context_chars]


def build_messages(
    question: str,
    answer_format: str,
    language: str,
    context: str,
    previous_answer: str,
    mode: str,
) -> list[dict[str, str]]:
    if answer_format == "number":
        fmt = "Return one number or a number with its unit."
    elif answer_format == "ordered_list":
        fmt = "Return a Python list of strings in the correct order, like ['first', 'second']."
    elif answer_format == "unordered_list":
        fmt = "Return a Python list of strings, like ['item1', 'item2']; order does not matter."
    else:
        fmt = "Return a short string answer."

    system = (
        "You answer document questions using only OCR text from the provided PDF pages. "
        "Output only the final answer. Do not explain."
    )
    if mode == "verify":
        user = (
            f"Language: {language}\n"
            f"Required format: {answer_format}. {fmt}\n"
            f"Question: {question}\n"
            f"Previous answer: {previous_answer}\n"
            "If the previous answer is supported by the OCR context, return it unchanged. "
            "If it is contradicted or incomplete, return the corrected answer.\n\n"
            f"OCR context:\n{context}\n\nAnswer:"
        )
    else:
        user = (
            f"Language: {language}\n"
            f"Required format: {answer_format}. {fmt}\n"
            f"Question: {question}\n\n"
            f"OCR context:\n{context}\n\nAnswer:"
        )
    return [{"role": "system", "content": system}, {"role": "user", "content": user}]


def should_replace(answer_format: str, policy: str) -> bool:
    if policy == "all":
        return True
    if policy == "number_list":
        return answer_format in {"number", "ordered_list", "unordered_list"}
    if policy == "string":
        return answer_format == "string"
    return False


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--test", default="data/raw/test.csv")
    parser.add_argument("--sample", default="data/raw/sample_submission.csv")
    parser.add_argument("--base-submission", default="submissions/submission_062_allocr_answer_terms_mp2.csv")
    parser.add_argument("--evidence-submission", default="")
    parser.add_argument("--cache", default="data/processed/pdf_pages.jsonl")
    parser.add_argument("--answers-cache", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--model", default="Qwen/Qwen2.5-7B-Instruct")
    parser.add_argument("--mode", choices=["verify", "fresh"], default="verify")
    parser.add_argument("--replace-policy", choices=["all", "number_list", "string"], default="all")
    parser.add_argument("--chars-per-page", type=int, default=3500)
    parser.add_argument("--max-context-chars", type=int, default=8500)
    parser.add_argument("--max-new-tokens", type=int, default=128)
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--local-files-only", action="store_true")
    parser.add_argument("--load-in-4bit", action="store_true")
    args = parser.parse_args()

    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

    test = pd.read_csv(args.test)
    sample = pd.read_csv(args.sample)
    base = pd.read_csv(args.base_submission)
    evidence = pd.read_csv(args.evidence_submission or args.base_submission)
    if base["id"].tolist() != sample["id"].tolist():
        raise ValueError("base submission ids do not match sample")
    if evidence["id"].tolist() != sample["id"].tolist():
        raise ValueError("evidence submission ids do not match sample")

    by_file = load_merged_pages(Path(args.cache))
    cache_path = Path(args.answers_cache)
    done = load_done(cache_path)

    tokenizer = AutoTokenizer.from_pretrained(args.model, local_files_only=args.local_files_only)
    quantization_config = None
    if args.load_in_4bit:
        quantization_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_use_double_quant=True,
        )
    model = AutoModelForCausalLM.from_pretrained(
        args.model,
        torch_dtype=None if quantization_config is not None else (torch.float16 if torch.cuda.is_available() else "auto"),
        device_map="auto",
        quantization_config=quantization_config,
        local_files_only=args.local_files_only,
    )
    model.eval()

    base_by_id = base.set_index("id")
    evidence_by_id = evidence.set_index("id")
    total = len(test) if args.limit <= 0 else min(args.limit, len(test))
    started = time.time()

    for n, (_, row) in enumerate(test.iloc[:total].iterrows(), start=1):
        qid = str(row["id"])
        if qid in done:
            continue
        ev_row = evidence_by_id.loc[qid]
        base_row = base_by_id.loc[qid]
        pages = parse_pages(ev_row["evidence_page_number"])
        context = context_for(by_file, str(row["file_id"]), pages, args.chars_per_page, args.max_context_chars)
        if not context:
            answer = str(base_row["answer"])
            raw = ""
        else:
            messages = build_messages(
                str(row["question"]),
                str(row["answer_format"]),
                str(row["language"]),
                context,
                str(base_row["answer"]),
                args.mode,
            )
            text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
            inputs = tokenizer([text], return_tensors="pt").to(model.device)
            with torch.inference_mode():
                generated = model.generate(
                    **inputs,
                    max_new_tokens=args.max_new_tokens,
                    do_sample=False,
                    temperature=None,
                    top_p=None,
                    pad_token_id=tokenizer.eos_token_id,
                )
            raw = tokenizer.batch_decode(generated[:, inputs.input_ids.shape[1] :], skip_special_tokens=True)[0]
            answer = clean_answer(raw, str(row["answer_format"]))
        rec = {
            "id": qid,
            "file_id": str(row["file_id"]),
            "answer_format": str(row["answer_format"]),
            "answer": answer,
            "raw": raw,
            "previous_answer": str(base_row["answer"]),
            "evidence_page_number": str(ev_row["evidence_page_number"]),
            "mode": args.mode,
        }
        done[qid] = {k: str(v) for k, v in rec.items()}
        append_jsonl(cache_path, rec)
        completed = len(done)
        if completed % 10 == 0:
            elapsed = time.time() - started
            rate = n / elapsed if elapsed > 0 else 0.0
            eta = (total - n) / rate if rate > 0 else 0.0
            print(f"answered={completed}/{len(test)} rate={rate:.3f}/s eta_min={eta/60:.1f}", flush=True)

    rows: list[dict[str, str]] = []
    changed = 0
    generated_changed = 0
    for _, sample_row in sample.iterrows():
        qid = str(sample_row["id"])
        base_row = base_by_id.loc[qid]
        ev_row = evidence_by_id.loc[qid]
        answer_format = str(test.loc[test["id"] == qid, "answer_format"].iloc[0])
        generated_answer = done.get(qid, {}).get("answer", str(base_row["answer"]))
        use_generated = should_replace(answer_format, args.replace_policy)
        answer = generated_answer if use_generated else str(base_row["answer"])
        changed += int(answer != str(base_row["answer"]))
        generated_changed += int(generated_answer != str(base_row["answer"]))
        rows.append(
            {
                "id": qid,
                "answer": answer,
                "evidence_page_number": str(ev_row["evidence_page_number"]),
            }
        )

    out_df = pd.DataFrame(rows, columns=list(sample.columns))
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out_df.to_csv(out, index=False)
    avg_pages = out_df["evidence_page_number"].astype(str).str.count(",").add(1).mean()
    print(f"wrote {out}")
    print(
        f"generated_changed={generated_changed} output_changed={changed} "
        f"replace_policy={args.replace_policy} avg_pages={avg_pages:.3f}"
    )
    print(out_df.head(10).to_string(index=False))


if __name__ == "__main__":
    main()
