# T4 risk classifier: BanglaBERT vs XLM-R

This implements Phase 2 Task T4 without changing the fixed safety gates. It trains `csebuetnlp/banglabert` and `FacebookAI/xlm-roberta-base` with seeds 3407, 42, and 7, selects a high-recall threshold on dev only, and reports argmax and high-recall test results.

## Required source file

Place `mindmate_synthetic_conversations.jsonl` in this directory. It must contain all 750 language records from 250 conversations and retain a risk label on each user message. The checked-in `train_full_230.jsonl` is not a valid substitute because it has only conversation-level risk. The script stops if message-level labels or any held-out test conversation are missing.

## Colab or Kaggle GPU run

```bash
pip install -r requirements-classifier.txt
python -m pytest -v tests/test_risk_classifier.py
python risk_classifier.py prepare --source mindmate_synthetic_conversations.jsonl
python risk_classifier.py train
```

Expected conversation split: 207 train, 23 dev, and the fixed 20 held-out test IDs. The preparation step writes `pilot_v2/T4_classifier/classifier_dataset.csv`, `classifier_split_counts.csv`, and `dev_conv_ids.txt`.

Training writes one folder per model and seed with `metrics.json`, `predictions_test.csv`, `threshold.txt`, `env.txt`, and the best checkpoint. The combined `classifier_model_summary.csv` reports mean and standard deviation across the three seeds.

The high-recall threshold is the largest dev-set value that reaches at least 0.95 dev escalation recall. The test set is not read when choosing it. Selection still requires no high-risk message predicted as none and test high-risk recall of at least 0.90. If neither model passes, no model is selected; evaluate the documented train-only keyword fallback separately.

## Current execution status

The supplied 750-record message-labelled source file passed preparation. It
produced 3,243 student-message rows: 2,658 train (207 conversations), 297 dev
(23 conversations), and 288 held-out test (20 conversations). The four CPU
pipeline tests pass.

GPU training is **not run** on the local development computer because it has
no NVIDIA GPU. Run the commands above on Kaggle or Colab with a T4. No
BanglaBERT or XLM-R score has been invented.
