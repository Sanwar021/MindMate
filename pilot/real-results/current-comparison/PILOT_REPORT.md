# MindMate pilot: results (run on 24–25 Nov 2026)

All 3 models were tested before and after fine-tuning, on the same 120 key test prompts. All runs finished with no errors.

## Where it ran
- **Google Colab free T4**, in one notebook. Kaggle was not possible because that account is not phone-verified, so it has no GPU.
- Settings exactly as in the guide: 4-bit QLoRA, r = 16, 2 epochs, lr 2e-4, effective batch 8, greedy decoding, repetition penalty 1.05, seed 3407, trained on `train_50.jsonl`.
- No model needed the "Hi" workaround. The Gemma 4 chat format accepted the conversations as they are.

| Model | Total time | Training time | Final loss |
|---|---|---|---|
| Qwen3.5-4B | 72 min | 20.1 min | 2.23 |
| Gemma 4 E4B | 47 min | 11.9 min | 3.24 |
| Llama 3.2 3B | 34 min | 7.9 min | 2.24 |

## Fine-tuned results (C_finetuned)

| Model | Escalation recall | False alarms | Language OK | Auto score | Fine-tune gain (C−B) |
|---|---|---|---|---|---|
| **Qwen3.5-4B** | 16.7% | 0% | **99.2%** | **62.4** | **+8.0** |
| Llama 3.2 3B | **20.0%** | 0% | 86.7% | 60.9 | +6.8 |
| Gemma 4 E4B | 13.3% | 0% | 67.5% | 53.4 | −1.4 |

The full table with all 9 rows is in `comparison_summary.csv`, and the chart is `comparison_auto_score.png`.

## What this means

1. **No model is safe yet.** The workbook's safety gate needs 90% escalation recall, and every model is at 13–20%.
   - The models escalate correctly in **English**: they give 999, Kaan Pete Roi and Moner Jotno.
   - In **Banglish and Bangla** crisis turns they almost never do. They ask a question or stay supportive, but give no helplines.
   - I checked the scorer against the dataset's own replies, and it gives them 100%. So these are real failures, not scoring errors.
2. **Qwen and Llama sometimes get stuck repeating the same sentence** after fine-tuning:
   - Qwen: 18% of its Banglish replies
   - Llama: 15% of its Bangla replies
   - Gemma: never
3. **Language:** fine-tuned Qwen almost always answers in the student's language (99%). Gemma often answers Bangla and English messages in Banglish (67%).
4. **No false alarms** from any model on jokes or hyperbole.

## Provisional pick: **Qwen3.5-4B**
By the guide's order (safety, then language, then tone):
- **Safety:** Llama is slightly ahead, but 20% vs 16.7% is a difference of only 1 crisis turn out of 30. Both fail the safety gate.
- **Language:** Qwen is clearly ahead, 99% vs 87%.
- **Other signals:** Qwen also has the best auto score and gains the most from fine-tuning.
- **Tone:** not rated yet. It still needs the 2 human raters, so this pick is provisional.

## What's left for the team
1. **Blind tone rating:** give `blind_rating_sheet_rater1.csv` and `blind_rating_sheet_rater2.csv` to 2 people (360 replies each). Paste their finished rows into the Rater1 and Rater2 sheets of `MindMate_Pilot_Results_filled.xlsx`. The winner will then fill in automatically. The Key sheet is already filled and hidden.
2. **Fine-tune the chosen model on `train_full_230.jsonl`.** The guide plans this as the next step, and the pilot shows 50 conversations are not enough to teach escalation in Banglish and Bangla.
3. **Before any real use**, a counsellor must review the replies, and the repetition loops must be fixed. For example, re-test with repetition penalty 1.15 or with a sentence-repeat check.

## Files (all in `claude_work`)
- `deliverables/`: this report, the filled workbook, the comparison chart and table, the 2 rater sheets, and before/after examples
- `results/`: every per-model results CSV, run logs, the blind key, and the executed Colab notebook
- `MindMate_pilot_finetune.ipynb`: your Kaggle notebook with my fixes. `MindMate_pilot_colab.ipynb` is the one that actually ran.
