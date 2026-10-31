# CLP analysis (mid-report analysis applied to the cross-lingual prompting run)

RQ4: does cross-lingual prompting (CLP; Qin et al., 2023) improve Hindi temporal reasoning, and does it bring Hindi closer to English? This folder runs the mid-report analysis (`2026-10-02_mid-report-analysis`, as rerun in `2026-10-27_full-grid-analysis` on `feat/full-grid-analysis`) on the CLP responses, compared with the other conditions on the same questions. The edit-distance (RDS) and logistic-regression analyses are done elsewhere and are not repeated here. No API calls are made.

## Data

All responses come from `responses/` on `main` (`responses/INFO.txt`):

| Condition | Source | Reasoning |
|---|---|---|
| English direct, English CoT, Hindi direct, Hindi CoT | `responses/standard/` | standard prompts, thinking off, temperature 0, 4,096 tokens |
| Hindi en-CoT | `responses/en-cot/` | Hindi question, one-stage step-by-step reasoning in English (Shi et al., 2023) |
| Hindi CLP | `responses/clp/` (= `2026-10-29_clp/outputs`) | Hindi question; stage 1: "act as an expert in multi-lingual understanding in Hindi … understand the task in English step-by-step"; stage 2: "resolve the task you understand above step-by-step" in English, ending with the Answer line; thinking off, temperature 0, 4,096 tokens per stage |

CLP and en-CoT were run on questions 0–49 of every task and level (2,250 questions × 3 distractor conditions = 6,750 responses each), so every comparison here uses the standard responses for the same 2,250 questions (27,000 responses). The CLP answer is the Answer line of stage 2; day-of-week answers are requested as Hindi weekday names and scored by weekday, as in the main study.

## How to rebuild

```bash
PY=../../../.venv/bin/python   # needs pandas numpy scipy statsmodels matplotlib
$PY build_responses.py   # one row per response -> outputs/data/responses.pkl, outputs/data/checks.json
$PY analysis.py          # tables -> outputs/analysis.md, every number -> outputs/numbers.json, plots -> outputs/plots/
```

Run from this folder, on a branch that has `responses/` from `main`. `outputs/` is git-ignored on `main`; add it with `git add -f` if it should be committed.

## Files

- `temporal_answers.py`: the full-grid copy, unchanged except that responses are read from `responses/` instead of the run folders (the run-folder and mid-report loaders were removed).
- `metrics.py`: the full-grid copy (root `metrics.py` with the parser fix described in the full-grid FINDINGS: a captured answer may not start with another answer marker). It changes no score; it only stops two wrong Hindi CoT answers of the form `उत्तर है:\nAnswer: सोमवार` from being classified as invalid instead of off by one.
- `build_responses.py`: the full-grid `build_responses.py` extended to en-CoT and CLP. Same columns and rules, plus `cell`, word counts per script, and stage-1 columns for CLP.
- `analysis.py`: the mid-report analyses for the six conditions.

## Checks

- **Pipeline identity.** On the 27,000 standard responses, `build_responses.py` reproduces the full-grid `build_responses.py` exactly: 0 differences over 16 columns (answer, scored, correct, cut-off, tokens, verification, error type, weekday offset, predicted weekday, recurrence pattern, distractor reuse ×2, distractor mention ×2, answer in reasoning, reasoning ends at gold).
- **Independent recomputation.** A separate script that reads the raw JSON (own answer regex, own weekday map, no shared code) reproduces every condition's overall, strict, per-distractor and three per-task accuracies, and the McNemar discordant counts for CLP vs Hindi CoT, CLP vs en-CoT and English CoT vs CLP, with no differences.
- **Consistency with the en-CoT analysis** (`2026-10-28_en-cot-analysis-shaurya`): strict accuracies for English direct 59.6, English CoT 86.0, Hindi direct 55.2, Hindi CoT 59.0 and en-CoT 80.8 are identical.
- **Inputs** (`outputs/data/checks.json`): for every CLP and en-CoT record, the question text and gold answer equal those of the standard Hindi record. English and Hindi gold answers differ only for day of week (750 records), where the gold is a weekday name in each language.
- **Stage-1 measure.** Stage 1 often prints "**Answer:**" as a heading with the answer on the next line, so its Answer line is not used. Instead the last date stage 1 writes is compared with the gold and with stage 2's answer, only for the three tasks whose answers are dates (date addition, subtraction, recurrence). On times and durations this reading is unreliable (12-hour clock times, "(or 3:58 PM)", "February has 29 days"), so those tasks are left out. 12 random date-task responses were checked by hand; the measure was right in all 12.

## Results

`outputs/analysis.md` has every table; `outputs/numbers.json` every number with its interval. Summary:

- **CLP helps Hindi:** 70.3% vs 59.4% for Hindi CoT (+10.9 [+9.6, +12.2]) and 55.2% for Hindi direct (+15.1); better than Hindi CoT on all nine tasks (Holm-corrected).
- **CLP is worse than reasoning in English in one stage:** en-CoT 82.9% (CLP −12.6 [−13.9, −11.3]); en-CoT is better on all nine tasks. English CoT is 88.9%.
- **The gap narrows but still widens with difficulty:** English CoT minus Hindi CLP is +16.0 at short and +21.4 at very very long, against +23.6 and +35.0 for Hindi CoT.
- **Stage 2 mostly follows stage 1:** on date tasks, stage 1 already ends at a date in 98.6% of responses; when it ends at the gold date, stage 2 is right 97.5% of the time, otherwise 20.1%. 461 of 695 wrong stage-2 answers repeat stage 1's date. Date recurrence is the extreme case: stage 1 reaches the gold in 18.9%, CLP is right in 27.0%, en-CoT in 70.3%.
- **Distractors do not hurt CLP:** drop with the time-related distractor −0.1 [−2.1, +2.0]; with the unrelated one CLP is 3.1 points more accurate [+1.1, +5.1]. Stage 1 mentions the distractor in 62.9% (time-related) and 83.7% (unrelated) of responses, stage 2 in 17.2% and 8.7% (placebo 9.7% and 2.3%).
- **CLP fails on different questions from English:** within task × level, φ between CLP and English CoT is 0.10 (Hindi CoT 0.07, en-CoT 0.02).
