# MindMate — complete project

This folder contains the complete local software and the model-selection pilot in one place.

## What is included

- `software/` — the MindMate student application, screening, multilingual support chat, safety interruption, resources, history, and admin research dashboard.
- `pilot/` — the unchanged datasets, system prompt, v2 notebook, CPU scripts, evaluator, comparison script, workbook, guide, and tests.
- `Start-MindMate.ps1` — installs the software dependencies when needed and starts the website.
- `Verify-Project.ps1` — runs both the software tests and the CPU-only pilot tests.

## Start the software

1. Right-click `Start-MindMate.ps1` and choose **Run with PowerShell**.
2. Wait until the terminal prints `MindMate API running at http://localhost:8080`.
3. Open <http://localhost:8080/>.

Keep the PowerShell window open while using MindMate. Closing it stops the software and causes a `Failed to fetch` login error.

Demo accounts:

- Student: `student@mindmate.local` / `Student123!`
- Admin: `admin@mindmate.local` / `Admin123!`

The admin page accepts the real pilot result files after the GPU runs are completed.

## Verify everything that works without a GPU

Right-click `Verify-Project.ps1` and choose **Run with PowerShell**. A successful verification ends with:

- software tests passing;
- the production website build completing;
- five pilot tests passing.

## Run the model pilot

A CUDA GPU is required for new model runs. Genuine Gemma 4 E4B, Qwen3.5-4B, and Llama 3.2 3B automatic pilot results are included and visible in the Admin dashboard.

Upload `pilot/` to Kaggle or Colab, enable a T4 GPU, and run one model per session:

```bash
pip install -q --upgrade unsloth pytest pandas matplotlib
python -m pytest -v
python run_pilot.py --model gemma4_e4b
python run_pilot.py --model qwen35_4b
python run_pilot.py --model llama32_3b
```

Each model can be run on a separate Kaggle account in parallel. After all three finish, place their `results_<model>_all.csv` files together and run:

```bash
python compare_results.py --pattern "results_*_all.csv" --output-dir comparison
```

Two people must then complete separate copies of `blind_rating_sheet.csv`. Import the comparison summary, escalation detail, hidden key, training logs, and both completed rating files into the software's Admin page. The software calculates the safety gate and winner.

## What remains unfinished

The automatic three-model pilot is complete. The remaining work requires human and counsellor review:

1. Complete two independent human blind ratings.
2. Import both completed rating outputs in Admin.
3. Improve and rerun the pilot because no model reaches the fixed 90% escalation-recall gate.
4. Use a safety-passing winner for final full-data training after counsellor review.

Until those steps are complete, the correct project status is **waiting for scores and ratings**.
