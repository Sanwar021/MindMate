# MindMate real pilot status

## Completed

### Qwen3.5-4B

- Platform: Google Colab, Tesla T4
- Training mode: replies
- Training examples: 669
- Epochs: 2
- Training time: 59.7 minutes
- First logged loss: 3.179
- Final logged loss: 1.081
- Result rows: 360 (120 per condition)
- Duplicate model/condition/prompt rows: 0

Fine-tuned automatic results:

| Metric | Result |
|---|---:|
| Language OK | 100.0% |
| Escalation recall | 80.0% |
| False alarms | 0.0% |
| Length OK | 98.3% |
| Thinking leak | 2.5% |
| chrF vs gold | 39.4 |
| Auto score | 86.8 |
| Crisis handled | 13/15 |
| Resources handled | 11/15 |
| Invented-number replies | 0 |

Qwen does not currently meet the fixed 90% escalation-recall safety gate. No winner can be selected until Gemma and both human rating files are complete.

### Llama 3.2 3B

- Platform: Kaggle, Tesla T4
- Training mode: replies
- Training examples: 669
- Epochs: 2
- Training time: 22.8 minutes
- First logged loss: 1.808
- Final logged loss: 1.044
- Result rows: 360 (120 per condition)
- Duplicate model/condition/prompt rows: 0

Fine-tuned automatic results:

| Metric | Result |
|---|---:|
| Language OK | 100.0% |
| Escalation recall | 80.0% |
| False alarms | 3.0% |
| Length OK | 100.0% |
| Thinking leak | 0.0% |
| chrF vs gold | 38.5 |
| Auto score | 86.2 |
| Crisis handled | 14/15 |
| Resources handled | 10/15 |
| Invented-number replies | 0 |

Llama also does not meet the fixed 90% escalation-recall safety gate. Its base condition produced one invented-number reply, but the fine-tuned condition produced none.

## In progress

- Gemma 4 E4B: running on Kaggle.
- Llama 3.2 3B: completed and validated.

## Still required

1. Validate and preserve Gemma results.
2. Add Gemma to the current Qwen/Llama comparison.
3. Complete two independent blind ratings.
4. Apply the safety gate and select the winner.
5. Complete counsellor review before final full-data training.
