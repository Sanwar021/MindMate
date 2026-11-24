"""Run one MindMate model through A_base, B_prompt, and C_finetuned.

Heavy GPU dependencies are imported only inside main(), so make_examples can be
tested on a CPU-only machine.
"""
from __future__ import annotations

import argparse
import glob
import inspect
import json
import os
import random
import shutil
import time
from pathlib import Path

MODELS = {
    "gemma4_e4b": "unsloth/gemma-4-E4B-it",
    "qwen35_4b": "unsloth/Qwen3.5-4B",
    "llama32_3b": "unsloth/Llama-3.2-3B-Instruct",
}
TRAIN_FILE = "train_50.jsonl"
TRAIN_MODE = "replies"
EVAL_ONLY_KEY_TURNS = True
MAX_SEQ_LEN = 4096
MAX_NEW_TOKENS = 600
EPOCHS = 2
LEARNING_RATE = 2e-4
LORA_R = 16
BATCH_SIZE = 1
GRAD_ACCUM = 8
SEED = 3407


def find_file(name: str) -> str:
    for pattern in (f"/kaggle/input/**/{name}", f"/content/**/{name}", f"./**/{name}"):
        hits = glob.glob(pattern, recursive=True)
        if hits:
            return hits[0]
    raise FileNotFoundError(f"Upload {name} first")


def read_jsonl(path: str) -> list[dict]:
    with open(path, encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def make_examples(records, chat_text, tok, max_len):
    """Create one example per MindMate reply and mask all context tokens.

    The fixed greeting (assistant message at index 1) remains context-only. The
    unmasked labels cover the target reply and the template's end-of-turn token.
    """
    examples, bad, longest = [], 0, 0
    for record in records:
        messages = record["messages"]
        for index, message in enumerate(messages):
            if message["role"] != "assistant" or index < 2:
                continue
            prefix = chat_text(messages[:index], True)
            full = chat_text(messages[: index + 1], False)
            if not full.startswith(prefix):
                bad += 1
                continue
            prefix_ids = tok(prefix)["input_ids"]
            ids = tok(full)["input_ids"]
            boundary = 0
            for before, complete in zip(prefix_ids, ids):
                if before != complete:
                    break
                boundary += 1
            if boundary == 0 or boundary == len(ids):
                bad += 1
                continue
            labels = [-100] * boundary + ids[boundary:]
            longest = max(longest, len(ids))
            if len(ids) > max_len or all(label == -100 for label in labels):
                bad += 1
                continue
            examples.append({"input_ids": ids, "attention_mask": [1] * len(ids), "labels": labels})
    return examples, bad, longest


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", required=True, choices=MODELS)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    model_key = args.model
    try:
        import numpy as np
        import pandas as pd
        import torch
        from datasets import Dataset
        from mindmate_eval import escalation_detail, score_row, summarize
        from trl import SFTConfig, SFTTrainer
        from unsloth import FastLanguageModel, FastModel
    except ImportError as error:
        raise SystemExit(f"Missing GPU runtime dependency: {error}. Run the Kaggle/Colab install command from README_pilot.md.")
    if not torch.cuda.is_available():
        raise SystemExit("No CUDA GPU is available; pilot not run.")

    random.seed(SEED); np.random.seed(SEED); torch.manual_seed(SEED)
    train = read_jsonl(find_file(TRAIN_FILE))
    test_prompts = read_jsonl(find_file("test_prompts.jsonl"))
    print("train records:", len(train), "| test prompts:", len(test_prompts),
          "| key prompts:", sum(bool(row["key_turn"]) for row in test_prompts))

    text_only = model_key.startswith("llama")
    loader = FastLanguageModel if text_only else FastModel
    model, tokenizer = loader.from_pretrained(model_name=MODELS[model_key], max_seq_length=MAX_SEQ_LEN, load_in_4bit=True)
    tok = getattr(tokenizer, "tokenizer", tokenizer)
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token

    def chat_text(messages, add_generation_prompt):
        options = dict(tokenize=False, add_generation_prompt=add_generation_prompt, enable_thinking=False)
        try:
            text = tokenizer.apply_chat_template(messages, **options)
        except Exception:
            parts = [{"role": m["role"], "content": [{"type": "text", "text": m["content"]}]} for m in messages]
            text = tokenizer.apply_chat_template(parts, **options)
        if tok.bos_token and text.startswith(tok.bos_token):
            text = text[len(tok.bos_token):]
        return text

    def set_mode(training):
        function = getattr(loader, "for_training" if training else "for_inference", None)
        if function:
            try: function(model)
            except Exception as error: print("mode switch skipped:", error)

    def generate(messages):
        text = chat_text(messages, True)
        encoded = tok(text, return_tensors="pt").to(model.device)
        with torch.no_grad():
            output = model.generate(**encoded, max_new_tokens=MAX_NEW_TOKENS, do_sample=False,
                                    repetition_penalty=1.05, pad_token_id=tok.pad_token_id)
        return tok.decode(output[0][encoded["input_ids"].shape[1]:], skip_special_tokens=True).strip()

    keep = ["prompt_id", "conv_id", "language", "theme", "conv_risk_label", "risk_subtype",
            "student_turn", "turn_risk", "expected_escalation", "gold_reply"]

    def run_eval(condition):
        path = f"results_{model_key}_{condition}.csv"
        if os.path.exists(path):
            print(condition, "already finished -> reading", path)
            return pd.read_csv(path)
        set_mode(False)
        rows = [row for row in test_prompts if row["key_turn"] or not EVAL_ONLY_KEY_TURNS]
        output, started = [], time.time()
        for i, row in enumerate(rows):
            context = row["context"][1:] if condition == "A_base" else row["context"]
            item_started = time.time(); reply = generate(context)
            record = {"model": model_key, "condition": condition, **{key: row[key] for key in keep},
                      "student_message": row["context"][-1]["content"], "model_reply": reply,
                      "seconds": round(time.time() - item_started, 1)}
            record.update(score_row(row, reply)); output.append(record)
            if i % 10 == 0: print(f"{condition} {i+1}/{len(rows)}  {time.time()-started:.0f}s")
        frame = pd.DataFrame(output); frame.to_csv(path, index=False, encoding="utf-8-sig")
        return frame

    print("Loaded", MODELS[model_key]); print(chat_text(test_prompts[0]["context"], True)[-600:])
    probes = [next(row for row in test_prompts if row["key_turn"]),
              next(row for row in test_prompts if row["expected_escalation"] == "crisis" and row["language"] == "banglish")]
    set_mode(False)
    for row in probes:
        reply = generate(row["context"]); scored = score_row(row, reply)
        print("SMOKE REPLY:", reply[:500]); print({key: scored[key] for key in ("lang_detected","helpline_present","wrong_number","think_leak","words")})
        assert reply.strip(), "Empty smoke-test reply"

    frame_a, frame_b = run_eval("A_base"), run_eval("B_prompt")
    c_path = f"results_{model_key}_C_finetuned.csv"
    if os.path.exists(c_path):
        print("C_finetuned already finished -> training skipped")
    else:
        if text_only:
            model = FastLanguageModel.get_peft_model(model, r=LORA_R, lora_alpha=LORA_R, lora_dropout=0, bias="none",
                target_modules=["q_proj","k_proj","v_proj","o_proj","gate_proj","up_proj","down_proj"],
                use_gradient_checkpointing="unsloth", random_state=SEED)
        else:
            model = FastModel.get_peft_model(model, finetune_vision_layers=False, finetune_language_layers=True,
                finetune_attention_modules=True, finetune_mlp_modules=True, r=LORA_R, lora_alpha=LORA_R,
                lora_dropout=0, bias="none", random_state=SEED)
        examples, bad, longest = make_examples(train, chat_text, tok, MAX_SEQ_LEN)
        expected = sum(1 for record in train for i, m in enumerate(record["messages"]) if m["role"] == "assistant" and i >= 2)
        print(f"{len(examples)} reply examples ({expected} expected) | longest {longest} | skipped {bad}")
        assert len(examples) > .9 * expected, "too many examples skipped"
        base = model.get_base_model() if hasattr(model, "get_base_model") else model
        if "token_type_ids" in inspect.signature(base.forward).parameters:
            for example in examples: example["token_type_ids"] = [0] * len(example["input_ids"])
        from transformers import DataCollatorForSeq2Seq, Trainer, TrainingArguments
        from unsloth import is_bfloat16_supported
        training_args = TrainingArguments(per_device_train_batch_size=BATCH_SIZE, gradient_accumulation_steps=GRAD_ACCUM,
            warmup_steps=5, num_train_epochs=EPOCHS, learning_rate=LEARNING_RATE, logging_steps=10,
            optim="adamw_8bit", weight_decay=.01, lr_scheduler_type="linear",
            fp16=not is_bfloat16_supported(), bf16=is_bfloat16_supported(), seed=SEED,
            output_dir="outputs", report_to="none")
        trainer = Trainer(model=model, args=training_args, train_dataset=Dataset.from_list(examples),
            data_collator=DataCollatorForSeq2Seq(tokenizer=tok, padding=True, label_pad_token_id=-100))
        set_mode(True); stats = trainer.train()
        losses = [item["loss"] for item in trainer.state.log_history if "loss" in item]
        log = {"model": model_key, "train_mode": TRAIN_MODE, "train_file": TRAIN_FILE, "examples": len(examples),
               "epochs": EPOCHS, "max_seq_len": MAX_SEQ_LEN, "train_minutes": round(stats.metrics["train_runtime"]/60,1),
               "first_logged_loss": round(losses[0],3), "final_logged_loss": round(losses[-1],3)}
        Path(f"train_log_{model_key}.json").write_text(json.dumps(log, indent=2), encoding="utf-8")
        model.save_pretrained(f"lora_{model_key}"); tok.save_pretrained(f"lora_{model_key}")

    frame_c = run_eval("C_finetuned")
    all_results = pd.concat([frame_a, frame_b, frame_c], ignore_index=True)
    all_results.to_csv(f"results_{model_key}_all.csv", index=False, encoding="utf-8-sig")
    summary = summarize(all_results); summary.to_csv(f"summary_{model_key}.csv", index=False)
    print(summary.to_string(index=False)); print(escalation_detail(all_results).to_string(index=False))
    output_dir = Path("pilot_outputs"); output_dir.mkdir(exist_ok=True)
    for filename in glob.glob(f"results_{model_key}_*.csv") + glob.glob(f"summary_{model_key}.csv") + glob.glob(f"train_log_{model_key}.json"):
        shutil.copy(filename, output_dir)
    shutil.make_archive(f"pilot_outputs_{model_key}", "zip", output_dir)
    print("Saved", f"pilot_outputs_{model_key}.zip")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
