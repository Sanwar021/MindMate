# MindMate pilot package: v2 changes (23 Nov 2026)

## What changed

| # | Problem found in v1 | Fix in v2 |
|---|---|---|
| 1 | Training put the loss on everything: the system prompt, the greeting and the student's messages, not only MindMate's replies. | `TRAIN_MODE = "replies"` (new setting, same for all models). One training example per MindMate reply, loss only on that reply and its end-of-turn token. The Step 8 cell prints one example of the trained text so you can check it. `TRAIN_MODE = "v1"` restores the old behaviour. |
| 2 | Qwen-style chat templates add an empty think block only to the last assistant turn, so earlier replies were trained in a different format than the one used at test time. | The per-reply examples render the context exactly as at test time (generation prompt on), so every target has the test-time format for any template. |
| 3 | The Banglish detector marked 5% of the Banglish gold replies as English. | Marker words come from the training replies. Result: 0 errors on all 288 gold test replies and on 2,955 training replies. |
| 4 | `999` matched inside longer numbers; a number that only started like a real helpline (09612-119999) counted as a helpline; Bangla-digit numbers and Mindspace VENT were not recognised. | A helpline counts only if the reply names a real service, gives 999 as a whole number, or gives a complete real number (Latin or Bangla digits). |
| 5 | Nothing flagged an invented helpline number. | New per-row flag `wrong_number`, counted per model in `escalation_detail.csv`. Must be 0. |
| 6 | Escalation is tested on only 15 crisis + 15 resources prompts per model, but only percentages were shown. | New `escalation_detail()` and `escalation_detail.csv`: k of n with a 95% Wilson interval. Winner rules now say a gap of 1 or 2 replies is not a real difference. |
| 7 | An unclosed `<think>` block was not removed. | It is removed and flagged as `think_leak`. |
| 8 | README promised that a rerun skips finished conditions, but the notebook did not do it. | `run_eval` reads an existing results CSV; Step 8 is skipped if the C_finetuned CSV exists. |
| 9 | Template or thinking problems showed up only after about 40 minutes. | A 1-minute smoke test (2 prompts) after Step 6. |
| 10 | Run_Log needs training time and loss. | Step 8 writes `train_log_<model>.json` (mode, examples, minutes, first and last logged loss), included in the zip. |

## What did NOT change
`comparison_summary.csv` has the same columns, so `MindMate_Pilot_Results.xlsx` works as before (checked against the `Auto_Scores` headers). The 9 summary metrics, the `auto_score` weights, the data files, the blind rating sheet format (A-H) and the other settings are unchanged.

## What was tested here (no GPU)
- Scorer: the 288 gold replies score 100 on every metric; edge cases for numbers, 999, unclosed think blocks.
- Training-example builder: three simulated chat templates (ChatML with the Qwen think quirk, Llama-style, Gemma-style) on `train_50.jsonl`: 669 of 669 replies became examples, trained text equals the reply plus the end token, about 7% of tokens carry loss.
- Step 7/10 logic with mock replies: resume cache, comparison, blind sheet, workbook column match.

## Not tested
Model loading, `Trainer` with the real Unsloth models, and the real chat templates of Gemma 4, Qwen3.5 and Llama 3.2. The fallback to `v1` is there for this reason. The training time estimate (15-45 min) is a guess; the notebook prints the real time. More examples (669 vs 150) also means more optimizer steps than v1, with the same learning rate.

## Command-line hardening

- Added `run_pilot.py` with the same fixed models, settings, three conditions, resume behavior, reply-only training, smoke test, logging, and output archive as the notebook.
- Added `compare_results.py` for the unchanged summary schema, escalation detail, chart, and blind-rating files.
- Added CPU-only pytest coverage for data integrity, scorer edge cases, reply-only label masking, and comparison outputs.
- Fixed a blocking notebook bug: `TRAIN_MODE` was used in Step 8 but was missing from the settings cell.
- Replaced offset-based reply masking with a token-prefix boundary so special end-of-turn tokens remain training targets even when a tokenizer reports no character offsets for them.
