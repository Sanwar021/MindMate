import json
from pathlib import Path

import pandas as pd
import pytest

from compare_results import SUMMARY_COLUMNS, compare
from mindmate_eval import has_helpline, score_row, summarize, wrong_number
from run_pilot import make_examples

ROOT = Path(__file__).parents[1]


def read_jsonl(name):
    return [json.loads(line) for line in (ROOT / name).read_text(encoding="utf-8").splitlines() if line.strip()]


def test_data_counts_splits_and_system_prompt():
    prompt = (ROOT / "system_prompt.txt").read_text(encoding="utf-8").strip()
    train = read_jsonl("train_50.jsonl")
    full = read_jsonl("train_full_230.jsonl")
    tests = read_jsonl("test_prompts.jsonl")
    test_conversations = read_jsonl("test_20.jsonl")
    assert len(train) == 150
    assert len(tests) == 288
    assert sum(bool(row["key_turn"]) for row in tests) == 120
    train_ids = {row["conv_id"] for row in full}
    test_ids = {row["conv_id"] for row in test_conversations}
    assert train_ids.isdisjoint(test_ids)
    embedded = [row["messages"][0]["content"] for row in train + full + test_conversations]
    embedded += [row["context"][0]["content"] for row in tests]
    assert embedded and all(value.strip() == prompt for value in embedded)


def test_all_gold_replies_score_perfectly():
    rows = read_jsonl("test_prompts.jsonl")
    records = []
    for row in rows:
        scored = score_row(row, row["gold_reply"])
        assert scored["lang_ok"] is True
        assert scored["escalation_ok"] is not False
        assert scored["false_alarm"] is False
        assert scored["wrong_number"] is False
        assert scored["length_ok"] is True
        assert scored["think_leak"] is False
        assert scored["chrf_vs_gold"] == 100.0
        records.append({"model":"gold", "condition":"gold", **row, **scored})
    summary = summarize(pd.DataFrame(records)).iloc[0]
    for column in ("language_ok_%","escalation_recall_%","length_ok_%","chrF_vs_gold","auto_score"):
        assert summary[column] == 100.0
    assert summary["false_alarm_%"] == 0.0
    assert summary["think_leak_%"] == 0.0


def test_fake_helpline_is_rejected_and_flagged():
    fake = "Call 09612-119999 now"
    assert has_helpline(fake) is False
    assert wrong_number(fake) is True
    assert has_helpline("Call Kaan Pete Roi 09612-119911 or 999") is True
    assert wrong_number("Call Kaan Pete Roi 09612-119911 or 999") is False


class FakeTokenizer:
    def __call__(self, text, return_offsets_mapping=False, **_kwargs):
        ids = list(range(1, len(text) + 1))
        result = {"input_ids": ids}
        if return_offsets_mapping:
            result["offset_mapping"] = [(i, i + 1) for i in range(len(text))]
        return result


def fake_chat_text(messages, add_generation_prompt):
    text = "".join(f"<{m['role']}>{m['content']}<eot>" for m in messages)
    return text + ("<assistant>" if add_generation_prompt else "")


def test_make_examples_masks_context_and_trains_reply_plus_end_token():
    record = {"messages":[
        {"role":"system","content":"rules"},
        {"role":"assistant","content":"hello"},
        {"role":"user","content":"help"},
        {"role":"assistant","content":"reply"},
    ]}
    examples, bad, _ = make_examples([record], fake_chat_text, FakeTokenizer(), 1000)
    assert bad == 0 and len(examples) == 1
    example = examples[0]
    prefix = fake_chat_text(record["messages"][:3], True)
    full = fake_chat_text(record["messages"], False)
    assert full.startswith(prefix)
    assert example["labels"][:len(prefix)] == [-100] * len(prefix)
    assert example["labels"][len(prefix):] == example["input_ids"][len(prefix):]
    assert full[len(prefix):] == "reply<eot>"
    assert len([x for x in example["labels"] if x != -100]) == len("reply<eot>")


def test_compare_results_writes_exact_summary_columns(tmp_path):
    source = read_jsonl("test_prompts.jsonl")
    selected = [next(row for row in source if row["expected_escalation"] == kind)
                for kind in ("crisis", "resources", "none")]
    for model in ("gemma4_e4b", "qwen35_4b", "llama32_3b"):
        output = []
        for condition in ("A_base", "B_prompt", "C_finetuned"):
            for row in selected:
                scored = score_row(row, row["gold_reply"])
                output.append({"model":model,"condition":condition,**row,
                    "student_message":row["context"][-1]["content"],"model_reply":row["gold_reply"],**scored})
        pd.DataFrame(output).to_csv(tmp_path / f"results_{model}_all.csv", index=False)
    compare(str(tmp_path / "results_*_all.csv"), tmp_path)
    written = pd.read_csv(tmp_path / "comparison_summary.csv")
    assert list(written.columns) == SUMMARY_COLUMNS
    assert len(written) == 9
    for name in ("escalation_detail.csv","comparison_auto_score.png","blind_rating_sheet.csv","blind_key_DO_NOT_SHARE.csv"):
        assert (tmp_path / name).exists()
