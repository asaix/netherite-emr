# Mid-report analysis on en-cot

This runs Rahul's full-grid analysis (`2026-10-27_full-grid-analysis`, branch `feat/full-grid-analysis`) on the en-cot responses in `responses/en-cot/` (Hindi question, English reasoning). No new API calls.

## Setup

- 2,250 questions: the first 50 per task and level, which is what en-cot was run on. 27,000 responses, none dropped.
- The analysis is run twice on the same questions:
  - `encot-off`: the normal responses, where Hindi CoT reasons in Hindi.
  - `encot`: the same responses, but Hindi CoT is replaced with en-cot.
- Direct answers and all English responses are the same in both runs, so rows about them show the same numbers twice. `compare.py` still prints a verdict for some of those rows; ignore it there.
- Full table: `outputs/comparison_encot.md`. Numbers, LaTeX tables and plots for each run: `outputs/encot/` and `outputs/encot-off/`.

## Results

**1. With English reasoning, Hindi gains about as much from CoT as English does**

| | Gain from CoT over direct (points) |
|---|---|
| English | +29.2 [+27.5, +30.9] |
| Hindi, normal Hindi CoT | +4.2 [+2.6, +5.9] |
| Hindi, en-cot | +27.7 [+26.0, +29.4] |

- The two tasks where Hindi CoT made things worse now help or stop hurting: date subtraction goes from -18.8 to +9.2, interval date from -22.9 to -2.7 (not significant).
- The biggest gains are date recurrence (+17.3 → +67.5), day of week (+5.8 → +37.3) and time duration (+35.4 → +53.5).

**2. The English-Hindi gap with CoT mostly closes, especially on hard questions**

- Five date tasks: the gap goes from +28.2 to +15.0 on short and from +40.6 to +5.5 on very long. Both are still significant.

**3. Day of week:** with normal Hindi CoT, "one day late" is more common than the right answer (by 4.3 points). With en-cot the right answer is 28.5 points more common than one day late.

**4. Recurrence: going backwards doesn't go away.** Hindi answers that go the right distance in the wrong direction barely change (9.0% → 8.3%). This matches Rahul's finding that they come from the ungrammatical "1वीं / 2वीं आवृत्ति" wording in the question. So the problem is reading the Hindi question, not reasoning in Hindi.

**5. Distractors make no significant difference either way here.** Hindi with a time-related distractor: +0.2 → +2.0 points of penalty; with an unrelated one: -0.3 → -0.9. None of these are significant. One task-level result, a day-of-week penalty of +12.5 for en-cot, rests on about 50 questions per cell, so don't lean on it.

**6. Length:** en-cot responses are longer than Hindi CoT (median 311 vs 212 tokens) and a bit shorter than English CoT (353).

## Caveats

- The distractor-mention check looks for the distractor's own words. The Hindi distractors are in Hindi and en-cot writes in English, so en-cot's much lower mention rate is partly just the check missing them.
- The language-drift test (section 8) can't be run on en-cot, because its reasoning is meant to be in English.
- With 50 questions per task and level, per-task and per-level numbers are noisier than in the full grid.

## How to rebuild

```bash
PY=python3   # needs pandas, scipy, statsmodels, matplotlib, numpy, pyyaml
$PY build_responses.py --parser current
$PY build_responses.py --source en_cot --parser current
$PY analysis.py --scope encot-off
$PY analysis.py --scope encot
$PY compare.py --pair encot
```

What I changed in Rahul's scripts: `temporal_answers.load_records("en_cot")` loads the normal responses for the en-cot questions and swaps Hindi CoT for en-cot, `build_responses.py` takes `--source en_cot`, `analysis.py` has the `encot-off` and `encot` scopes, and `compare.py` takes `--pair encot`.

## Report section

`report.py` makes the tables and figures for the final report in `outputs/report/` (same questions and methods as Rahul's CLP section: accuracy of answered responses, exact McNemar tests with Holm correction over tasks, 2,000-sample bootstrap over questions). It also puts en-cot next to CLP, which was run on the same 2,250 questions. Run it after the steps above.
