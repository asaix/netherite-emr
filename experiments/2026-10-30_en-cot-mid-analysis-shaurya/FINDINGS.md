# Mid-report analysis on en-cot

Rahul's full-grid pipeline (`2026-10-27_full-grid-analysis`, branch `feat/full-grid-analysis`) run on the en-cot responses (`responses/en-cot/`: Hindi question, English reasoning, Shi et al. 2023). No API calls.

## Setup

- 2,250 questions: the first 50 per task and level, the ones en-cot was run on. 27,000 responses, none dropped.
- Two scopes on exactly the same questions, so every number has a paired baseline:
  - `encot-off`: the standard responses (Hindi CoT is the normal Hindi CoT).
  - `encot`: the same responses with Hindi CoT replaced by en-cot.
- Direct answers and all English responses are identical in both scopes, so any row about them is the same in both columns (`compare.py`'s verdict column still labels some of those rows; ignore it there).
- Full table: `outputs/comparison_encot.md`. Per-scope numbers, LaTeX tables and plots: `outputs/encot/`, `outputs/encot-off/`.

## What changes when Hindi CoT reasons in English

**1. CoT delta: Hindi catches up with English**

| | Direct → CoT |
|---|---|
| English | +29.2 [+27.5, +30.9] |
| Hindi, Hindi CoT | +4.2 [+2.6, +5.9] |
| Hindi, en-cot | +27.7 [+26.0, +29.4] |

- The two tasks where Hindi CoT is significantly worse than direct flip: date subtraction -18.8 → +9.2, interval date -22.9 → -2.7 (n.s.).
- Biggest gains: date recurrence +17.3 → +67.5, day of week +5.8 → +37.3, time duration +35.4 → +53.5.

**2. The English-Hindi gap under CoT mostly closes, most at hard levels**
- Five date tasks, CoT gap: short +28.2 → +15.0, very long +40.6 → +5.5. Both still significant.
- Direct gaps are unchanged (same responses).

**3. Day of week:** Hindi CoT's "one day late more often than right" pattern reverses: +1-day minus correct goes from +4.3 to -28.5 points.

**4. Recurrence: the template problem stays**
- Mirror answers (right distance, wrong direction) barely move: 9.0% → 8.3% of Hindi CoT recurrence answers. This fits the full-grid finding that they come from the ungrammatical "1वीं / 2वीं आवृत्ति" template, i.e. from reading the Hindi question, not from reasoning in Hindi.
- First-step shortcuts fall slightly (8.7% → 5.9%).

**5. Distraction penalty: null either way on this subset**
- Hindi time-related: +0.2 [-2.6, +2.9] → +2.0 [-0.6, +4.4]; unrelated: -0.3 → -0.9. Neither significant.
- Per task, en-cot shows a time-related penalty on day of week (+12.5 [+2.3, +22.8]); the Hindi CoT penalty on date duration (+8.1) disappears. Both are single-task estimates on about 50 questions per cell, so treat them as weak.

**6. Traces:** en-cot traces are longer than Hindi CoT (median 311 vs 212 completion tokens) but shorter than English CoT (353). Cross-lingual agreement under CoT: English-only-correct minus Hindi-only-correct falls from +28.4 to +5.5 points of pairs.

## Caveats

- **Distractor mentions** are detected by matching the distractor's own words; the Hindi distractors are in Hindi and en-cot reasons in English, so en-cot's much lower mention rate (e.g. 23.8 → 3.6 points above placebo) is partly a measurement artifact.
- **Language drift** (section 8) and the Hindi-unrelated mention OR are not computable for en-cot: its traces are English by design.
- 50 questions per task and level, so per-task and per-level cells are smaller than in the full grid.

## How to rebuild

```bash
PY=python3   # needs pandas scipy statsmodels matplotlib numpy pyyaml
$PY build_responses.py --parser current
$PY build_responses.py --source en_cot --parser current
$PY analysis.py --scope encot-off
$PY analysis.py --scope encot
$PY compare.py --pair encot
```

Changes to Rahul's scripts: `temporal_answers.load_records("en_cot")` (standard records for the en-cot questions with Hindi CoT swapped for en-cot), a `--source en_cot` option in `build_responses.py`, `encot-off` / `encot` scopes in `analysis.py`, and `--pair encot` in `compare.py`.
