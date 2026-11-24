"""Combine completed MindMate model result CSVs and create comparison artifacts."""
from __future__ import annotations

import argparse
import glob
from pathlib import Path

SUMMARY_COLUMNS = ["model", "condition", "n", "language_ok_%", "escalation_recall_%",
                   "false_alarm_%", "length_ok_%", "avg_words", "think_leak_%",
                   "chrF_vs_gold", "auto_score"]


def compare(pattern="results_*_all.csv", output_dir="."):
    import matplotlib.pyplot as plt
    import pandas as pd
    from mindmate_eval import escalation_detail, summarize

    files = sorted(set(glob.glob(pattern, recursive=True)))
    if not files:
        raise FileNotFoundError(f"No result files matched {pattern!r}")
    results = pd.concat([pd.read_csv(path) for path in files], ignore_index=True)
    comparison = summarize(results)[SUMMARY_COLUMNS]
    destination = Path(output_dir); destination.mkdir(parents=True, exist_ok=True)
    comparison.to_csv(destination / "comparison_summary.csv", index=False)
    escalation_detail(results).to_csv(destination / "escalation_detail.csv", index=False)

    pivot = comparison.pivot(index="model", columns="condition", values="auto_score")
    axis = pivot.plot(kind="bar", figsize=(8,4), rot=0)
    axis.set_ylabel("Auto score (0-100)"); axis.set_title("MindMate pilot: auto score by model and condition")
    plt.tight_layout(); plt.savefig(destination / "comparison_auto_score.png", dpi=200); plt.close()

    blind = results[results["condition"] == "C_finetuned"].sample(frac=1, random_state=7).reset_index(drop=True)
    blind["rating_id"] = [f"R{i+1:03d}" for i in range(len(blind))]
    sheet = blind[["rating_id","language","conv_risk_label","student_message","model_reply"]].copy()
    sheet["tone_1to5"] = ""; sheet["safe_Y_N"] = ""; sheet["comment"] = ""
    sheet.to_csv(destination / "blind_rating_sheet.csv", index=False, encoding="utf-8-sig")
    blind[["rating_id","model","prompt_id"]].to_csv(destination / "blind_key_DO_NOT_SHARE.csv", index=False)
    return comparison


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pattern", default="results_*_all.csv")
    parser.add_argument("--output-dir", default=".")
    args = parser.parse_args()
    table = compare(args.pattern, args.output_dir)
    print(table.sort_values(["condition","auto_score"], ascending=[True,False]).to_string(index=False))


if __name__ == "__main__":
    main()
