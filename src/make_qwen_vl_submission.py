#!/usr/bin/env python3
"""Generate LAVA answers with an open Qwen2.5-VL model.

The script keeps evidence pages from an existing valid submission, renders those
PDF pages, and asks Qwen2.5-VL to return only the answer in the required format.
This avoids human test annotation and keeps the model side reproducible with a
public Hugging Face model.
"""

from __future__ import annotations

import argparse
import ast
import json
import re
import time
from pathlib import Path

import fitz  # type: ignore
import pandas as pd
from PIL import Image


def parse_pages(raw: object, max_pages: int) -> list[int]:
    pages = ast.literal_eval(str(raw))
    if not isinstance(pages, list) or not pages:
        return [1]
    out = []
    for page in pages:
        if isinstance(page, int) and page >= 1 and page not in out:
            out.append(page)
        if len(out) >= max_pages:
            break
    return out or [1]


def pdf_path_for(pdf_root: Path, file_id: str) -> Path:
    direct = pdf_root / f"{file_id}.pdf"
    if direct.exists():
        return direct
    matches = list(pdf_root.rglob(f"{file_id}.pdf"))
    if not matches:
        raise FileNotFoundError(f"No PDF found for {file_id} under {pdf_root}")
    return matches[0]


def render_pages(pdf_path: Path, pages: list[int], zoom: float) -> list[Image.Image]:
    images: list[Image.Image] = []
    with fitz.open(pdf_path) as doc:
        for page_number in pages:
            if page_number < 1 or page_number > doc.page_count:
                continue
            page = doc[page_number - 1]
            pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=False)
            image = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            images.append(image)
    return images


def prompt_for(question: str, answer_format: str, language: str) -> str:
    if answer_format == "number":
        fmt = "Return a single number or number with unit. Do not explain."
    elif answer_format == "unordered_list":
        fmt = "Return a Python list of strings, for example ['item1', 'item2']. Order does not matter. Do not explain."
    elif answer_format == "ordered_list":
        fmt = "Return a Python list of strings in the correct order, for example ['first', 'second']. Do not explain."
    else:
        fmt = "Return a short answer only. Do not explain."
    return (
        "You are answering a document question from the provided PDF page image(s). "
        "Use only the visible document content. "
        f"Question language: {language}. Required answer format: {answer_format}. {fmt}\n"
        f"Question: {question}\n"
        "Answer:"
    )


def clean_answer(text: str, answer_format: str) -> str:
    text = text.strip()
    text = re.sub(r"^```(?:json|python)?", "", text, flags=re.I).strip()
    text = re.sub(r"```$", "", text).strip()
    text = re.sub(r"^(答え|回答|Answer)\s*[:：]\s*", "", text, flags=re.I).strip()
    text = text.splitlines()[0].strip() if answer_format in {"number", "string"} and "\n" in text else text
    if answer_format == "number":
        match = re.search(r"[-+]?\d+(?:[,.]\d+)?(?:\s*(?:%|％|円|人|倍|㎡/人|m²/人|ℓ|L|リットル))?", text)
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
        parts = [p.strip(" ・,，、;；") for p in re.split(r"[\n,，、;；]+", text) if p.strip()]
        return str(parts[:5] or ["Answer"])
    return text[:160].strip() or "Answer"


def load_done(path: Path) -> dict[str, str]:
    done: dict[str, str] = {}
    if not path.exists():
        return done
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            rec = json.loads(line)
            done[rec["id"]] = rec["answer"]
    return done


def append_jsonl(path: Path, rec: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        f.flush()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--test", default="data/raw/test.csv")
    parser.add_argument("--sample", default="data/raw/sample_submission.csv")
    parser.add_argument("--base-submission", default="submissions/submission_003_tfidf_ocr_evidence.csv")
    parser.add_argument("--pdf-root", default="data/raw/test_pdfs")
    parser.add_argument("--model", default="Qwen/Qwen2.5-VL-3B-Instruct")
    parser.add_argument("--answers-cache", default="data/processed/qwen_vl_answers.jsonl")
    parser.add_argument("--output", default="submissions/submission_004_qwen_vl_answers.csv")
    parser.add_argument("--zoom", type=float, default=1.15)
    parser.add_argument("--max-pages", type=int, default=2)
    parser.add_argument("--max-new-tokens", type=int, default=96)
    parser.add_argument("--limit", type=int, default=0)
    args = parser.parse_args()

    import torch
    from qwen_vl_utils import process_vision_info
    from transformers import AutoProcessor, Qwen2_5_VLForConditionalGeneration

    test = pd.read_csv(args.test)
    sample = pd.read_csv(args.sample)
    base = pd.read_csv(args.base_submission)
    if base["id"].tolist() != sample["id"].tolist():
        raise ValueError("Base submission id order differs from sample")

    cache_path = Path(args.answers_cache)
    done = load_done(cache_path)

    processor = AutoProcessor.from_pretrained(args.model, trust_remote_code=True)
    model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
        args.model,
        torch_dtype=torch.bfloat16 if torch.cuda.is_available() else "auto",
        device_map="auto",
        trust_remote_code=True,
    )
    model.eval()

    pdf_root = Path(args.pdf_root)
    base_by_id = base.set_index("id")
    total = len(test) if args.limit <= 0 else min(args.limit, len(test))
    started = time.time()

    for i, row in test.iloc[:total].iterrows():
        qid = row["id"]
        if qid in done:
            continue
        base_row = base_by_id.loc[qid]
        pages = parse_pages(base_row["evidence_page_number"], args.max_pages)
        images = render_pages(pdf_path_for(pdf_root, row["file_id"]), pages, args.zoom)
        if not images:
            answer = str(base_row["answer"])
        else:
            content = [{"type": "image", "image": image} for image in images]
            content.append({"type": "text", "text": prompt_for(row["question"], row["answer_format"], row["language"])})
            messages = [{"role": "user", "content": content}]
            text = processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
            image_inputs, video_inputs = process_vision_info(messages)
            inputs = processor(
                text=[text],
                images=image_inputs,
                videos=video_inputs,
                padding=True,
                return_tensors="pt",
            )
            inputs = inputs.to(model.device)
            with torch.inference_mode():
                generated_ids = model.generate(
                    **inputs,
                    max_new_tokens=args.max_new_tokens,
                    do_sample=False,
                    temperature=None,
                    top_p=None,
                )
            generated_ids_trimmed = [
                out_ids[len(in_ids) :] for in_ids, out_ids in zip(inputs.input_ids, generated_ids, strict=True)
            ]
            raw = processor.batch_decode(generated_ids_trimmed, skip_special_tokens=True, clean_up_tokenization_spaces=False)[0]
            answer = clean_answer(raw, row["answer_format"])
        done[qid] = answer
        append_jsonl(
            cache_path,
            {
                "id": qid,
                "file_id": row["file_id"],
                "answer": answer,
                "evidence_page_number": str(base_row["evidence_page_number"]),
            },
        )
        if (len(done) % 10) == 0:
            elapsed = time.time() - started
            rate = len(done) / elapsed if elapsed > 0 else 0.0
            eta = (len(test) - len(done)) / rate if rate > 0 else 0.0
            print(f"answered={len(done)}/{len(test)} rate={rate:.3f}/s eta_min={eta/60:.1f}", flush=True)

    rows = []
    for _, row in sample.iterrows():
        qid = row["id"]
        base_row = base_by_id.loc[qid]
        rows.append(
            {
                "id": qid,
                "answer": done.get(qid, str(base_row["answer"])),
                "evidence_page_number": str(base_row["evidence_page_number"]),
            }
        )
    out_df = pd.DataFrame(rows, columns=list(sample.columns))
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out_df.to_csv(out, index=False)
    print(f"wrote {out} answered={sum(qid in done for qid in sample['id'])}/{len(sample)}")


if __name__ == "__main__":
    main()
