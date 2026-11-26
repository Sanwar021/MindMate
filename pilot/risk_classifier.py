"""MindMate T4 risk classifier: BanglaBERT vs XLM-R.

Implements the fixed Phase-2 protocol. The source dataset must retain a risk
label on every user message; conversation-level labels are not substituted.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import os
import platform
import random
import statistics
import time
from collections import Counter, defaultdict
from pathlib import Path

LABELS = ("none", "low", "moderate", "high")
LABEL_TO_ID = {name: i for i, name in enumerate(LABELS)}
TEST_IDS = {
    "MM-002", "MM-003", "MM-004", "MM-006", "MM-007",
    "MM-008", "MM-017", "MM-022", "MM-033", "MM-037",
    "MM-040", "MM-047", "MM-061", "MM-069", "MM-126",
    "MM-128", "MM-129", "MM-158", "MM-211", "MM-236",
}
MODELS = {
    "banglabert": "csebuetnlp/banglabert",
    "xlmr": "FacebookAI/xlm-roberta-base",
}
SEEDS = (3407, 42, 7)


def read_jsonl(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def message_label(message: dict) -> str | None:
    for key in ("risk", "turn_risk", "risk_label", "label"):
        value = message.get(key)
        if value in LABEL_TO_ID:
            return value
    return None


def build_rows(records: list[dict]) -> list[dict]:
    """Create one classifier row per student message.

    The function intentionally fails when per-message risk labels are absent.
    Using the conversation label would leak future disclosure into early turns.
    """
    conv_ids = {record.get("conv_id") for record in records}
    if len(records) != 750 or len(conv_ids) != 250:
        raise ValueError(
            f"Expected 750 language records from 250 conversations; got "
            f"{len(records)} records and {len(conv_ids)} conversations."
        )
    rows: list[dict] = []
    missing: list[str] = []
    for record in records:
        previous = ""
        turn = 0
        for message in record.get("messages", []):
            if message.get("role") != "user":
                continue
            turn += 1
            label = message_label(message)
            if label is None:
                missing.append(f"{record.get('id', record.get('conv_id'))}:t{turn}")
                continue
            rows.append({
                "conv_id": record["conv_id"],
                "language": record["language"],
                "banglish_style": record.get("banglish_style", ""),
                "risk_subtype": record.get("risk_subtype", ""),
                "conv_risk_label": record.get("risk_label", ""),
                "turn": int(message.get("turn", turn)),
                "text": message.get("content", "").strip(),
                "prev_text": previous,
                "label": label,
            })
            previous = message.get("content", "").strip()
    if missing:
        sample = ", ".join(missing[:5])
        raise ValueError(
            "Per-message risk labels are missing. Do not replace them with the "
            f"conversation label. First missing rows: {sample}."
        )
    return rows


def _stratified_dev_ids(records: list[dict], seed: int = 3407, n_dev: int = 23) -> set[str]:
    labels_by_conv: dict[str, str] = {}
    for record in records:
        conv_id = record["conv_id"]
        if conv_id not in TEST_IDS:
            labels_by_conv.setdefault(conv_id, record["risk_label"])
    if len(labels_by_conv) != 230:
        raise ValueError(f"Expected 230 non-test conversations, got {len(labels_by_conv)}")
    groups: dict[str, list[str]] = defaultdict(list)
    for conv_id, label in labels_by_conv.items():
        groups[label].append(conv_id)
    rng = random.Random(seed)
    for ids in groups.values():
        ids.sort()
        rng.shuffle(ids)
    raw = {label: len(ids) * n_dev / len(labels_by_conv) for label, ids in groups.items()}
    allocation = {label: math.floor(value) for label, value in raw.items()}
    remaining = n_dev - sum(allocation.values())
    order = sorted(groups, key=lambda label: (raw[label] - allocation[label], label), reverse=True)
    for label in order[:remaining]:
        allocation[label] += 1
    selected = {conv_id for label, ids in groups.items() for conv_id in ids[: allocation[label]]}
    if len(selected) != n_dev:
        raise AssertionError("Dev split allocation failed")
    return selected


def assign_splits(records: list[dict], rows: list[dict]) -> tuple[list[dict], set[str]]:
    dev_ids = _stratified_dev_ids(records)
    source_ids = {record["conv_id"] for record in records}
    if not TEST_IDS <= source_ids:
        raise ValueError(f"Missing held-out test IDs: {sorted(TEST_IDS - source_ids)}")
    train_ids = source_ids - TEST_IDS - dev_ids
    if len(train_ids) != 207 or len(dev_ids) != 23:
        raise AssertionError(f"Expected 207/23 train/dev IDs, got {len(train_ids)}/{len(dev_ids)}")
    if (train_ids & TEST_IDS) or (dev_ids & TEST_IDS) or (train_ids & dev_ids):
        raise AssertionError("Conversation leakage detected")
    output = []
    for row in rows:
        split = "test" if row["conv_id"] in TEST_IDS else "dev" if row["conv_id"] in dev_ids else "train"
        output.append({**row, "split": split})
    return output, dev_ids


def write_csv(path: Path, rows: list[dict], columns: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    columns = columns or list(rows[0])
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def split_counts(rows: list[dict]) -> list[dict]:
    counts = Counter((row["split"], row["language"], row["label"]) for row in rows)
    return [
        {"split": split, "language": language, "label": label, "n": counts[(split, language, label)]}
        for split in ("train", "dev", "test")
        for language in ("banglish", "english", "bangla")
        for label in LABELS
    ]


def prepare(source: Path, output_dir: Path) -> None:
    records = read_jsonl(source)
    rows = build_rows(records)
    rows, dev_ids = assign_splits(records, rows)
    write_csv(output_dir / "classifier_dataset.csv", rows)
    write_csv(output_dir / "classifier_split_counts.csv", split_counts(rows))
    (output_dir / "dev_conv_ids.txt").write_text("\n".join(sorted(dev_ids)) + "\n", encoding="utf-8")
    print(f"Prepared {len(rows)} student messages; train/dev/test conversations = 207/23/20")


def load_csv(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def wilson(successes: int, total: int, z: float = 1.96) -> list[float | int]:
    if total == 0:
        return [0, 0, 0]
    p = successes / total
    denom = 1 + z * z / total
    center = (p + z * z / (2 * total)) / denom
    margin = z * math.sqrt((p * (1 - p) + z * z / (4 * total)) / total) / denom
    return [successes, total, max(0, center - margin), min(1, center + margin)]


def confusion(y_true: list[int], y_pred: list[int]) -> list[list[int]]:
    matrix = [[0] * len(LABELS) for _ in LABELS]
    for truth, pred in zip(y_true, y_pred):
        matrix[truth][pred] += 1
    return matrix


def classification_metrics(y_true: list[int], y_pred: list[int]) -> dict:
    matrix = confusion(y_true, y_pred)
    per_class = {}
    f1s = []
    for idx, label in enumerate(LABELS):
        tp = matrix[idx][idx]
        fn = sum(matrix[idx]) - tp
        fp = sum(row[idx] for row in matrix) - tp
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        f1s.append(f1)
        per_class[label] = {"precision": precision, "recall": recall, "f1": f1, "support": tp + fn}
    escalation_truth = [value >= LABEL_TO_ID["moderate"] for value in y_true]
    escalation_pred = [value >= LABEL_TO_ID["moderate"] for value in y_pred]
    escalations = sum(escalation_truth)
    escalation_ok = sum(a and b for a, b in zip(escalation_truth, escalation_pred))
    negatives = len(y_true) - escalations
    false_escalation = sum((not a) and b for a, b in zip(escalation_truth, escalation_pred))
    high_total = sum(value == LABEL_TO_ID["high"] for value in y_true)
    high_ok = sum(t == LABEL_TO_ID["high"] and p == LABEL_TO_ID["high"] for t, p in zip(y_true, y_pred))
    return {
        "confusion_matrix": matrix,
        "per_class": per_class,
        "macro_f1": statistics.mean(f1s),
        "escalation_recall": escalation_ok / escalations if escalations else 0.0,
        "false_escalation": false_escalation / negatives if negatives else 0.0,
        "high_recall": high_ok / high_total if high_total else 0.0,
        "high_recall_wilson": wilson(high_ok, high_total),
        "high_predicted_none": sum(t == LABEL_TO_ID["high"] and p == LABEL_TO_ID["none"] for t, p in zip(y_true, y_pred)),
        "n": len(y_true),
    }


def choose_threshold(probabilities: list[list[float]], truth: list[int], target: float = 0.95) -> float:
    risk_prob = [row[LABEL_TO_ID["moderate"]] + row[LABEL_TO_ID["high"]] for row in probabilities]
    positives = sum(value >= LABEL_TO_ID["moderate"] for value in truth)
    if positives == 0:
        raise ValueError("Dev set has no moderate/high messages")
    candidates = sorted(set(risk_prob + [0.0, 1.0]))
    feasible = []
    for threshold in candidates:
        recall = sum(t >= LABEL_TO_ID["moderate"] and p >= threshold for t, p in zip(truth, risk_prob)) / positives
        if recall >= target:
            feasible.append(threshold)
    if not feasible:
        raise RuntimeError("No threshold reaches the fixed dev escalation-recall target")
    return max(feasible)


def threshold_predictions(probabilities: list[list[float]], threshold: float) -> list[int]:
    output = []
    for probs in probabilities:
        risk = probs[2] + probs[3]
        if risk >= threshold:
            output.append(3 if probs[3] >= probs[2] else 2)
        else:
            output.append(0 if probs[0] >= probs[1] else 1)
    return output


def grouped_metrics(rows: list[dict], truth: list[int], predictions: list[int]) -> dict:
    report = {"overall": classification_metrics(truth, predictions), "by_language": {}, "banglish_style": {}}
    for field, target in (("language", report["by_language"]), ("banglish_style", report["banglish_style"])):
        values = sorted({row[field] for row in rows if row[field]})
        for value in values:
            indices = [i for i, row in enumerate(rows) if row[field] == value and (field != "banglish_style" or row["language"] == "banglish")]
            if indices:
                target[value] = classification_metrics([truth[i] for i in indices], [predictions[i] for i in indices])
    late = [i for i, row in enumerate(rows) if row["risk_subtype"] == "masked_late_disclosure"]
    report["masked_late_disclosure"] = classification_metrics([truth[i] for i in late], [predictions[i] for i in late]) if late else {"n": 0}
    hyperbole = [
        {"conv_id": rows[i]["conv_id"], "turn": rows[i]["turn"], "language": rows[i]["language"],
         "text": rows[i]["text"], "true_label": LABELS[truth[i]], "predicted_label": LABELS[predictions[i]]}
        for i in range(len(rows))
        if rows[i]["risk_subtype"] == "hyperbole_false_positive"
        and truth[i] < LABEL_TO_ID["moderate"] and predictions[i] >= LABEL_TO_ID["moderate"]
    ]
    report["hyperbole_false_positives"] = hyperbole
    report["hyperbole_false_positive_count"] = len(hyperbole)
    return report


def save_confusion_png(matrix: list[list[int]], path: Path, title: str) -> None:
    import matplotlib.pyplot as plt

    fig, axis = plt.subplots(figsize=(5.8, 5.2))
    image = axis.imshow(matrix, cmap="Blues")
    axis.set(xticks=range(4), yticks=range(4), xticklabels=LABELS, yticklabels=LABELS,
             xlabel="Predicted label", ylabel="True label", title=title)
    for row in range(4):
        for column in range(4):
            axis.text(column, row, matrix[row][column], ha="center", va="center",
                      color="white" if matrix[row][column] > max(map(max, matrix), default=0) / 2 else "black")
    fig.colorbar(image, ax=axis, shrink=.8)
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)


def normalize_banglabert(text: str) -> str:
    try:
        from bnlp import BasicTokenizer  # type: ignore
        return BasicTokenizer().tokenize(text) and text
    except Exception:
        try:
            from bnunicodenormalizer import Normalizer  # type: ignore
            normalized = Normalizer().normalize(text)
            if isinstance(normalized, dict):
                return str(normalized.get("normalized", normalized.get("normalized_text", text)))
            return str(normalized)
        except Exception:
            return text


def train_one(dataset_path: Path, output_dir: Path, model_key: str, seed: int) -> dict:
    import numpy as np
    import torch
    import transformers
    from datasets import Dataset
    from sklearn.utils.class_weight import compute_class_weight
    from transformers import AutoModelForSequenceClassification, AutoTokenizer, Trainer, TrainingArguments

    rows = load_csv(dataset_path)
    train_rows = [row for row in rows if row["split"] == "train"]
    dev_rows = [row for row in rows if row["split"] == "dev"]
    test_rows = [row for row in rows if row["split"] == "test"]
    train_ids = {row["conv_id"] for row in train_rows}
    if train_ids & TEST_IDS:
        raise AssertionError("Held-out conversation leaked into classifier training")
    random.seed(seed); np.random.seed(seed); torch.manual_seed(seed)
    if torch.cuda.is_available(): torch.cuda.manual_seed_all(seed)
    model_id = MODELS[model_key]
    tokenizer = AutoTokenizer.from_pretrained(model_id, use_fast=True)
    model = AutoModelForSequenceClassification.from_pretrained(model_id, num_labels=len(LABELS), id2label=dict(enumerate(LABELS)), label2id=LABEL_TO_ID)

    def tokenize(batch):
        texts = batch["text"]
        previous = batch["prev_text"]
        if model_key == "banglabert":
            texts = [normalize_banglabert(text) for text in texts]
            previous = [normalize_banglabert(text) for text in previous]
        return tokenizer(texts, previous, truncation="only_second", max_length=256)

    def make_dataset(source):
        data = Dataset.from_list([{**row, "labels": LABEL_TO_ID[row["label"]]} for row in source])
        return data.map(tokenize, batched=True)

    train_ds, dev_ds, test_ds = map(make_dataset, (train_rows, dev_rows, test_rows))
    weights = compute_class_weight("balanced", classes=np.arange(len(LABELS)), y=np.array([LABEL_TO_ID[row["label"]] for row in train_rows]))
    class WeightedTrainer(Trainer):
        def compute_loss(self, model, inputs, return_outputs=False, **kwargs):
            labels = inputs.pop("labels")
            outputs = model(**inputs)
            loss = torch.nn.functional.cross_entropy(outputs.logits, labels, weight=torch.tensor(weights, device=outputs.logits.device, dtype=outputs.logits.dtype))
            return (loss, outputs) if return_outputs else loss

    def compute_metrics(result):
        logits, labels = result
        pred = np.argmax(logits, axis=1).tolist()
        metrics = classification_metrics(labels.tolist(), pred)
        return {"escalation_recall": metrics["escalation_recall"], "macro_f1": metrics["macro_f1"], "selection_score": metrics["escalation_recall"] * 1000 + metrics["macro_f1"]}

    run_dir = output_dir / model_key / f"seed_{seed}"
    args = TrainingArguments(output_dir=str(run_dir), learning_rate=2e-5, weight_decay=0.01, warmup_ratio=0.1, per_device_train_batch_size=16, per_device_eval_batch_size=32, num_train_epochs=6, eval_strategy="epoch", save_strategy="epoch", load_best_model_at_end=True, metric_for_best_model="selection_score", greater_is_better=True, fp16=torch.cuda.is_available(), seed=seed, data_seed=seed, report_to=[], save_total_limit=2)
    trainer = WeightedTrainer(model=model, args=args, train_dataset=train_ds, eval_dataset=dev_ds, processing_class=tokenizer, compute_metrics=compute_metrics)
    start = time.perf_counter(); trainer.train(); train_seconds = time.perf_counter() - start
    dev_output = trainer.predict(dev_ds); test_output = trainer.predict(test_ds)
    dev_probs = torch.softmax(torch.tensor(dev_output.predictions), dim=1).numpy().tolist()
    test_probs = torch.softmax(torch.tensor(test_output.predictions), dim=1).numpy().tolist()
    dev_truth = [LABEL_TO_ID[row["label"]] for row in dev_rows]
    test_truth = [LABEL_TO_ID[row["label"]] for row in test_rows]
    threshold = choose_threshold(dev_probs, dev_truth)
    argmax_pred = np.argmax(test_output.predictions, axis=1).tolist()
    recall_pred = threshold_predictions(test_probs, threshold)
    start = time.perf_counter(); trainer.predict(test_ds); elapsed = time.perf_counter() - start
    predictions = []
    for row, probs, argmax_value, recall_value in zip(test_rows, test_probs, argmax_pred, recall_pred):
        predictions.append({**row, **{f"p_{label}": probs[i] for i, label in enumerate(LABELS)}, "argmax_prediction": LABELS[argmax_value], "high_recall_prediction": LABELS[recall_value]})
    write_csv(run_dir / "predictions_test.csv", predictions)
    report = {
        "model_key": model_key, "model_id": model_id, "seed": seed, "threshold": threshold,
        "train_seconds": train_seconds, "test_seconds_per_message": elapsed / max(1, len(test_rows)),
        "device": torch.cuda.get_device_name(0) if torch.cuda.is_available() else "CPU",
        "argmax": grouped_metrics(test_rows, test_truth, argmax_pred),
        "high_recall": grouped_metrics(test_rows, test_truth, recall_pred),
    }
    (run_dir / "metrics.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    (run_dir / "threshold.txt").write_text(f"{threshold:.12g}\n", encoding="utf-8")
    trainer.save_model(run_dir / "best_model"); tokenizer.save_pretrained(run_dir / "best_model")
    save_confusion_png(report["argmax"]["overall"]["confusion_matrix"], run_dir / "confusion_argmax.png", f"{model_key} seed {seed}: argmax")
    save_confusion_png(report["high_recall"]["overall"]["confusion_matrix"], run_dir / "confusion_high_recall.png", f"{model_key} seed {seed}: high-recall threshold")
    env = {"python": platform.python_version(), "platform": platform.platform(), "torch": torch.__version__, "transformers": transformers.__version__, "device": report["device"]}
    (run_dir / "env.txt").write_text("\n".join(f"{k}={v}" for k, v in env.items()) + "\n", encoding="utf-8")
    return report


def train(dataset: Path, output_dir: Path, models: list[str], seeds: list[int]) -> None:
    if not dataset.exists():
        raise FileNotFoundError(f"Prepared classifier dataset not found: {dataset}. Run prepare first.")
    reports = [train_one(dataset, output_dir, model, seed) for model in models for seed in seeds]
    summary = []
    for model in models:
        selected = [r for r in reports if r["model_key"] == model]
        for mode in ("argmax", "high_recall"):
            summary.append({
                "model": model, "mode": mode,
                "escalation_recall_mean": statistics.mean(r[mode]["overall"]["escalation_recall"] for r in selected),
                "escalation_recall_sd": statistics.stdev(r[mode]["overall"]["escalation_recall"] for r in selected) if len(selected) > 1 else 0,
                "macro_f1_mean": statistics.mean(r[mode]["overall"]["macro_f1"] for r in selected),
                "high_recall_mean": statistics.mean(r[mode]["overall"]["high_recall"] for r in selected),
                "false_escalation_mean": statistics.mean(r[mode]["overall"]["false_escalation"] for r in selected),
            })
        aggregate = {
            "model": model,
            "seeds": seeds,
            "selection_rule": "highest mean escalation recall, then mean macro-F1",
            "gate_1_pass": all(r["high_recall"]["overall"]["high_predicted_none"] == 0 for r in selected),
            "gate_2_pass": statistics.mean(r["high_recall"]["overall"]["high_recall"] for r in selected) >= .90,
            "runs": selected,
        }
        (output_dir / f"metrics_{model}.json").write_text(json.dumps(aggregate, ensure_ascii=False, indent=2), encoding="utf-8")
    write_csv(output_dir / "classifier_model_summary.csv", summary)


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    prep = sub.add_parser("prepare")
    prep.add_argument("--source", type=Path, default=Path("mindmate_synthetic_conversations.jsonl"))
    prep.add_argument("--output-dir", type=Path, default=Path("pilot_v2/T4_classifier"))
    run = sub.add_parser("train")
    run.add_argument("--dataset", type=Path, default=Path("pilot_v2/T4_classifier/classifier_dataset.csv"))
    run.add_argument("--output-dir", type=Path, default=Path("pilot_v2/T4_classifier"))
    run.add_argument("--models", nargs="+", choices=tuple(MODELS), default=list(MODELS))
    run.add_argument("--seeds", nargs="+", type=int, default=list(SEEDS))
    args = parser.parse_args()
    if args.command == "prepare": prepare(args.source, args.output_dir)
    else: train(args.dataset, args.output_dir, args.models, args.seeds)


if __name__ == "__main__":
    main()
