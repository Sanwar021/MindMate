# MindMate real pilot status

## Automatic pilot complete

All three models were run on Google Colab with a Tesla T4 using the same 150 training records, two epochs, QLoRA settings, 120 key prompts, and three evaluation conditions. Each result file contains 360 rows with no duplicate model/condition/prompt entries. The packaged CSV and JSON files match the copies inside each model output archive.

| Model | Training time | Final loss | Language OK | Escalation recall | False alarms | Auto score |
|---|---:|---:|---:|---:|---:|---:|
| Gemma 4 E4B | 11.9 min | 3.236 | 67.5% | 13.3% | 0.0% | 53.4 |
| Qwen3.5-4B | 20.1 min | 2.228 | 99.2% | 16.7% | 0.0% | 62.4 |
| Llama 3.2 3B | 7.9 min | 2.243 | 86.7% | 20.0% | 0.0% | 60.9 |

Fine-tuned escalation details:

| Model | Crisis handled | Resources handled | False alarms | Invented-number replies |
|---|---:|---:|---:|---:|
| Gemma 4 E4B | 4/15 | 0/15 | 0/33 | 0 |
| Qwen3.5-4B | 4/15 | 1/15 | 0/33 | 0 |
| Llama 3.2 3B | 5/15 | 1/15 | 0/33 | 0 |

The official project evaluator exactly reproduces all nine supplied automatic summary rows.

## Decision status

No model passes the fixed 90% escalation-recall safety gate. The project must not lower this gate to manufacture a winner. Qwen has the highest automatic score, but it is only a provisional automatic leader and is not an eligible final winner.

Both independent rating sheets contain 360 replies, but `tone_1to5` and `safe_Y_N` are blank in every row. The workbook therefore correctly remains at **waiting for scores and ratings**.

## Still required

1. Two people independently complete the blind rating sheets.
2. Import both completed sheets and calculate rater agreement.
3. Review the failed Bangla and Banglish crisis replies with a counsellor.
4. Improve the crisis training examples or prompt and rerun the pilot until a model passes the safety gate.
5. After counsellor approval, train the selected model on `train_full_230.jsonl` and evaluate it on the untouched test set.
