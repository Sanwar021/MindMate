# MindMate

MindMate is a functional capstone research prototype for Bangladeshi university students. It combines structured mental-wellness screening, supportive multilingual chat, independent crisis-language interruption, educational resources, student history, and anonymous research analytics.

The chatbot uses a hybrid local RAG design: a reviewed multilingual knowledge base is retrieved for every question and, when Ollama with `qwen2.5:3b` is installed, the local model writes a natural answer from that context. Without Ollama it remains usable in deterministic reviewed-knowledge mode.

The default fast mode includes 500 prewritten question-answer variants across 25 student-wellness topics in English, Bangla and Banglish. Indexed retrieval and caching answer routine questions without waiting for model generation. Set `ENABLE_LOCAL_GENERATION=true` only if you want Qwen to handle unmatched questions; it is disabled by default because CPU generation can be slow.

> This software is not a medical device, does not diagnose illness, and must not be deployed to real students without ethics approval, clinical oversight, security review, and verification of every crisis resource.

## Quick start in VS Code

Requirements: Node.js 20 or newer.

```powershell
npm install
npm run dev
```

Open `http://localhost:5173`. The API runs on `http://localhost:8080`.

### Optional local AI model

Install Ollama for Windows, then run `ollama pull qwen2.5:3b`. Restart MindMate. The chat header changes from **Reviewed knowledge mode** to **Local AI · qwen2.5:3b**.

Demo accounts:

- Student: `student@mindmate.local` / `Student123!`
- Admin: `admin@mindmate.local` / `Admin123!`

## Production-style local run

```powershell
npm run build
npm start
```

Open `http://localhost:8080`.

## Included modules

- Consent-aware registration and secure password hashing
- JWT authentication and student/admin roles
- Contextual assessment, PHQ-9, GAD-7 and PSS-4 scoring
- Non-diagnostic concern categories and contributing-factor explanations
- Assessment history and progress view
- Bangla/English/Banglish supportive chat interface
- Independent multilingual crisis-phrase detector that interrupts normal chat
- Human-help escalation interface
- Clinically bounded self-help resource library
- Anonymous administrator metrics without conversation exposure
- Persistent local JSON data for easy capstone demonstration
- Automated scoring and safety tests
- Responsive and accessible interface
- Admin model-selection pilot view based on the supplied 50-conversation training split and 20-conversation held-out test split
- Pilot safety gate requiring at least 90% escalation recall and 95% safe human ratings
- Admin imports for v2 `comparison_summary.csv`, `escalation_detail.csv`, `train_log_<model>.json`, `blind_key_DO_NOT_SHARE.csv`, and both completed blind-rating files
- In-app reproduction of the workbook's rater agreement, safety gate, weighted score, ranking, and winner decision

## Research package

The ZIP includes the model-selection notebook, fixed JSONL datasets, scoring scripts, split list, workbook, guide, genuine GPU training logs, and automatic results for Gemma 4 E4B, Qwen3.5-4B, and Llama 3.2 3B. The application loads these genuine results into the Admin research view; it does not invent missing evaluation data.

All three GPU training and automatic evaluation runs are complete. The current decision correctly remains **waiting for scores and ratings** because the two independent human blind ratings are not complete and no candidate reaches the fixed 90% escalation-recall safety gate. Completed rater CSVs can be imported incrementally from the Admin page. The decision view applies the workbook thresholds and weights, requires zero invented phone numbers, and selects a winner only when every required automatic and human input is present.

## Important prototype limitations

The risk detector is deliberately transparent and rule-based. It demonstrates the independent safety architecture but is **not clinically validated**. A real deployment requires an ethics-approved, expertly annotated Bangla/Banglish dataset; conservative model evaluation; clinical sign-off; human escalation operations; encryption; retention controls; database backups; rate limiting; and security testing.

The local JSON store is suitable for a demonstration, not real sensitive data. Replace it with PostgreSQL before any supervised pilot.

## Testing

```powershell
npm test
npm run build
```

## Suggested capstone extension path

1. Obtain ethics approval and a named clinical advisor.
2. Reconcile the supplied 22-question document with the requirement document's “35-question” reference.
3. Move persistence to PostgreSQL and introduce explicit consent/retention records.
4. Build an approved knowledge base and retrieval pipeline.
5. Benchmark multilingual classifiers on expert-annotated data.
6. Evaluate recall, false negatives, calibration, subgroup performance, and escalation usability.
7. Run synthetic red-team cases before any supervised student pilot.

## Environment

Copy `.env.example` to `.env` if you want custom settings. Never commit the real JWT secret.
