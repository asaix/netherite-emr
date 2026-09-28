# direct-vs-cot-en5

Small debug run: direct vs. chain-of-thought prompting, English only, no
distractor insertions, 5 problems per task (all 9 TRD tasks, medium
difficulty) — 90 requests total (45 direct + 45 cot).

Purpose: sanity-check the build_requests.py -> run_batch.py pipeline before
scaling up to the full grid (more languages, distractor types, difficulties,
larger n_per_cell).

## Reproduce

```bash
python3 build_requests.py --config config.yaml --dataset-dir ../../Dataset \
    --prompts prompts.yaml --output requests.jsonl
python3 run_batch.py --input requests.jsonl --output outputs/results.jsonl
```

`build_requests.py`/`run_batch.py` here are frozen copies of the root
scripts as they were at the time of this run. `Dataset/` is the shared,
regenerable TRD output and isn't duplicated into this folder.
