# Full-grid analysis: mid-report analysis rerun on all completed runs

Working notes for the team (not paper text). This folder reruns every mid-report analysis (`2026-10-02_mid-report-analysis`) on the completed Sarvam-105B grid, says what got stronger, weaker or stayed the same, and adds analyses the full grid and the thinking-on runs make possible. No API calls are made.

## Data

| Level | Run folder | Responses |
|---|---|---|
| short | `2026-10-17_run-short-leftover-rahul` | 16,200 |
| medium | `2026-10-17_run-medium-leftover-rahul` | 16,200 |
| long | `2026-10-16_finish-run-long-adi` | 16,200 |
| very long | `2026-10-18_run-very-long-leftover-aayush` | 16,200 |
| very very long | `2026-10-18-very_very_long-aayush` | 16,195 |

- Each completed run contains the original mid-report records unchanged (checked record by record), with the same prompts and settings (temperature 0, thinking off, 4,096 tokens). So the mid-report data is an exact subset of this data.
- 5 very-very-long time questions lack all 12 responses (API errors) and are dropped: 6,745 questions, 80,940 responses (of 6,750 / 81,000 planned).
- Thinking-on runs: `2026-10-25_test-reasoning-on` (questions 0-9 of every task and level, `reasoning_effort: low`, 16k tokens), 5,400 responses.
- Trace deletion (`2026-10-26_trace-deletion`) is still running and is not analysed here.

## How to rebuild

```bash
PY=../../../.venv/bin/python   # needs pandas scipy statsmodels matplotlib numpy pyyaml
$PY build_responses.py --parser mid       # one row per response -> outputs/data/responses_mid.pkl
$PY build_responses.py --parser current
$PY analysis.py --scope mid --parser mid  # = the mid report, reproduced exactly
for s in mid new full4 full; do $PY analysis.py --scope $s; done
$PY extra.py          # new full-grid analyses -> outputs/extra
$PY reasoning_on.py   # thinking on vs off -> outputs/reasoning_on
$PY rds.py            # exploratory edit distance (about 5 min) -> outputs/rds
$PY compare.py        # mid report vs full grid -> outputs/comparison.{md,csv}
```

Run from this folder; the whole pipeline takes about 7 minutes. Files:
- `analysis.py` and `build_responses.py` are the mid-report scripts with only these changes: a `--scope` / `--parser` switch; all five levels; a third difficulty panel (all nine tasks); outputs go to `outputs/<scope>/` (`plots/` instead of the git-ignored `figures/`); `recurrence_k` and the extracted answer are kept per response.
- `temporal_answers.py` reads the five run folders directly instead of a merged copy.
- `metrics.py` is the root `metrics.py` with the parser fix below; `metrics_mid.py` is the mid report's copy.
- `rds/` holds unchanged copies of `parser.py`, `ed.py` and `config/parser.yaml` from branch `metrics/ed-lr` at `32ac1bd`.

Scopes (`outputs/<scope>/`, each with `numbers.json`, `tables/*.tex` (incl. `macros.tex`), `plots/`):

| Scope | Questions | What it is |
|---|---|---|
| `mid-midparser` | 3,089 | Mid-report questions and parser. Reproduces every committed mid-report table and all 249 macros byte for byte. |
| `mid` | 3,089 | Same questions, current parser. Identical numbers (the parser changes do not touch these questions' scores). |
| `new` | 3,656 | Only questions not in the mid report: an out-of-sample check of the mid-report findings. Different cells (time and interval tasks at short to long, all of very-very-long), so not a like-for-like replication. |
| `full4` | 5,400 | Full grid, four levels (what the full grid looked like before very-very-long). |
| `full` | 6,745 | Full grid, five levels. **Use this for the paper.** |

## Bug found and fixed in the root parser

The 25 Oct parser change (`8d20d63`) lets `\s*` after `उत्तर है:` run into the next line, so a response ending in `उत्तर है:\nAnswer: सोमवार` was read as `Answer: सोमवार` and scored wrong. Fixed on this branch in the root `metrics.py` (separate commit): the captured answer may not start with another answer marker. In the full grid this changes the extracted answer of 5 responses (4 misread by the 25 Oct parser, 1 also misread by the mid-report parser); all 5 are wrong answers either way, so no score changes. Every other effect of the 25 Oct change (`उत्तर है`, `जवाब`, `से` for intervals) is kept.

## What changed since the mid report

Full table with all four scopes and verdicts: `outputs/comparison.md`. Verdicts compare the full grid (5 levels) with the mid report. "Replicates" asks whether the effect is significant in the same direction on the 3,656 new questions alone.

**Same or stronger**
- CoT helps English far more than Hindi: English +29.5 [+28.5, +30.5] (was +27.9), Hindi +4.6 [+3.7, +5.6] (was +5.1). English CoT is never worse than direct in any task or any task x level cell (39/45 cells significantly better).
- CoT significantly hurts Hindi in date subtraction (-17.6, was -14.0) and interval date (-21.8, was -17.2). Both replicate on new questions. Hindi now has 6 significantly positive tasks (was 5).
- The English-Hindi gap is a CoT gap that widens with difficulty (unchanged on the mid-report panels; now confirmed on all nine tasks, below).
- Day of week: direct answers are still guessing (each weekday offset 13-15%; modal answer Friday 34.4% in English, Sunday 58.7% in Hindi); Hindi CoT is still more often one day late (24.3%) than right (21.8%); the gap is largest at short (33.9% vs 22.0%) and about even at the other levels.
- Hindi traces that drift into English are more often right: Mantel-Haenszel OR 2.08 [1.66, 2.60] (was 1.94), replicates.
- Distractor reuse in wrong Hindi direct answers: 11.3% vs 4.1% placebo (p < 0.001), replicates.
- Cross-lingual agreement: under CoT, English-only correct 5,943 vs Hindi-only 503 of 19,457 pairs; within-cell phi 0.06 (CoT) vs 0.28 (direct).

**Weaker**
- The main hypothesis (CoT distraction penalty, Hindi, time-related distractor): +2.2 [+0.6, +3.9], was +5.2 [+2.9, +7.3]. Still significant, but less than half the size. On the new questions alone it is -0.3 [-2.7, +2.1]: +1.1 [-1.8, +4.2] on new questions at the first four levels, -2.7 [-6.8, +1.3] at very-very-long. The mid-report estimate was an overestimate.
- Time duration penalty (Hindi, time-related): +11.4 [+5.6, +16.8], was +22.1; replicates on 451 new questions (+8.5 [+1.3, +15.5]).
- Mentioning the time-related distractor goes with lower accuracy in Hindi: OR 0.84 [0.74, 0.95] (was 0.77), significant in the full grid but not on new questions alone (0.88 [0.75, 1.04]).
- Recurrence first-step shortcut and mirror answers are rarer overall (Hindi CoT mirror 7.4%, was 11.8%), because they live in specific template cells (below).

**No longer significant**
- Hindi, unrelated distractor penalty: +0.7 [-0.9, +2.3] (was +2.8 [+0.7, +4.9]).
- Hindi, day of week penalty: +2.4 [-2.8, +7.2] (was +8.0).
- English: mentioning the time-related distractor and accuracy: OR 0.92 [0.72, 1.17] (was 0.64 [0.44, 0.93]); on new questions 1.18. The mid-report English result was most likely noise.

**Newly significant**
- English, unrelated distractor: CoT *protects*: penalty -1.9 [-3.2, -0.6] (direct drops 1.9 points, CoT does not drop). Replicates on new questions (-2.9 [-4.8, -1.1]).
- Hindi date recurrence penalty: +4.5 [+0.5, +8.4] (was +5.8, borderline).
- English direct answers also reuse the distractor: 6.1% vs 3.4% (p = 0.004).
- English verification steps go with slightly higher accuracy within task x level: OR 1.28 [1.01, 1.63], p = 0.03 (was 1.33, p = 0.13). Pooled, they still look harmful (87.5% vs 95.2%) because they are common in hard tasks.

## New analyses (full grid)

### 1. Difficulty, all nine tasks (`extra/tables/difficulty_profile.tex`, `full/plots/difficulty.pdf` panel c)
With every task at every level there is no task-mix confound left.

| | Short | Medium | Long | Very long | V. v. long |
|---|---|---|---|---|---|
| English CoT - direct | +15.4 | +23.2 | +28.5 | +33.7 | +46.6 |
| Hindi CoT - direct | **-4.3** | +1.5 (n.s.) | +2.9 | +5.8 | +17.3 |
| Gap (En - Hi), direct | 4.3 | 2.7 | 2.7 | 5.8 | 5.7 |
| Gap (En - Hi), CoT | 24.0 | 24.4 | 28.3 | 33.7 | 35.0 |

- CoT's benefit grows with difficulty in both languages (logit: OR per level 1.34 English, 1.32 Hindi). In Hindi CoT starts significantly harmful at short and only pays off at the hardest level, where direct answering collapses (30.5%).
- The gap under direct answering is small at every level; the gap under CoT grows from 24 to 35 points.
- CoT delta by task x level (`extra/plots/cot_delta_task_level.pdf`): Hindi CoT is significantly worse than direct in 15 of 45 cells (interval date at all 5 levels, date subtraction medium to very-very-long, time addition short to long, time subtraction short and medium, date duration short); English in none.

### 2. CoT distraction penalty by difficulty and in a regression (`extra/tables/did_difficulty.tex`, `extra/tables/logit.tex`, `extra/plots/did_by_difficulty.pdf`)
- Hindi, time-related: short +4.3*, medium +2.4, long +3.9*, very long +3.2, very-very-long -2.7. The penalty is present at the first four levels and gone at the hardest. Logit trend: the CoT x distractor interaction weakens per level (OR 1.10 per level, p = 0.014).
- Logistic regression, correctness ~ CoT x distractor x language + task + level, SEs clustered by question: Hindi CoT x time-related OR 0.87 [0.79, 0.96], p = 0.006; English 0.94 [0.83, 1.07], n.s. With a fixed effect for every task x level x language x condition cell: Hindi 0.87 [0.78, 0.97], English 0.98 [0.85, 1.12].
- **But the Hindi-vs-English difference in the penalty is not significant** for the time-related distractor (ratio 0.92 [0.79, 1.08], p = 0.33). It is for the unrelated distractor (0.84 [0.71, 0.99], p = 0.03), mostly because English CoT protects there. Counting cut-off responses as wrong makes English's time-related interaction significant too (0.86 [0.77, 0.97]) and removes the language difference (1.01).
- Per task (time-related): Hindi date duration +8.8*, time duration +11.4*, recurrence +4.5*, date subtraction -4.5* (CoT protects). English time duration -8.0* and time addition -6.0* (CoT protects), recurrence +8.4*.
- Robustness: without date recurrence (template issue below), Hindi time-related is +2.0 [+0.2, +3.8] and English -1.5 [-2.9, -0.1].
- So what the data supports: "in Hindi, CoT makes a time-related distractor more harmful (about 2 points, odds ratio 0.87), and this is absent in English", but not "the penalty is significantly larger in Hindi than in English" for the time-related distractor.

### 3. The Hindi recurrence problem is one template cell (`extra/recurrence_by_k.csv`)
Splitting date recurrence by the occurrence k asked for:
- k = 1 ("1वीं आवृत्ति", short level only): **64% (direct) and 66% (CoT) of Hindi answers go backwards in time** (mirror), against 6% and 2% in English.
- k = 2 (short and medium): Hindi answers today + N (first-step shortcut) 84-87% (direct) and 50-58% (CoT); English CoT 0-0.5%, English direct 91-92%.
- k >= 3: mirror answers disappear; first-step answers fall to 13-27% of direct answers in both languages and 0-6% of CoT answers.
- This pins the mid report's wording concern to the non-standard ordinals 1वीं / 2वीं ("पहली" / "दूसरी" would be standard). Hindi recurrence accuracy at short and medium is driven by these two cells; mention it when reporting recurrence.

### 4. Thinking mode on vs off (`reasoning_on/`)
Same 450 questions, paired by response (5,388 pairs):

| | Off | On | On - off |
|---|---|---|---|
| English direct | 64.2 | 97.9 | +33.6 [+30.1, +37.3] |
| English CoT | 91.4 | 98.9 | +7.5 [+5.7, +9.5] |
| Hindi direct | 59.1 | 94.9 | +35.7 [+32.0, +39.6] |
| Hindi CoT | 64.1 | 97.9 | +33.8 [+30.4, +37.2] |

- With thinking on, the English-Hindi gap under CoT falls from 27.3 to 1.0 points, and accuracy is flat across difficulty (93-99% at every level).
- The hidden reasoning for Hindi prompts is mostly English: Devanagari share of the hidden trace 4% (direct) and 25% (CoT), while the visible answer stays 99.6-99.9% Hindi. Hindi hidden traces are 2.5x longer (median 5,191 vs 1,958 reasoning tokens, direct) and mention the language rule a median 56 times (direct), confirming the notes in `ANALYSIS.txt`.
- Distractor penalties under thinking-on: none significant (small sample, CIs about ±4 points).
- Caveats: 10 questions per cell; thinking-on had a 16k budget vs 4k; cut-offs rise to 3-8%. This suggests the Hindi CoT deficit comes from forcing the *visible* reasoning into Hindi with thinking off, which is worth stating as a limitation or discussion point.

### 5. Edit distance between English and Hindi traces (exploratory, `rds/`)
Aditya's parser (unchanged copy of `metrics/ed-lr` at `32ac1bd`) on all 20,235 English-Hindi CoT pairs.
- Mean normalized edit distance 0.86 (full tokens) and 0.71 (operation types only); both grow with difficulty (ops: 0.67 short to 0.75 very-very-long) and are lowest when both languages are right (ops 0.67 vs 0.74-0.80).
- **Caution: full-token RDS leaks correctness.** Tokens carry their values (`ANSWER 2025-08-29`), so any wrong answer raises the distance mechanically; that is why it "predicts" errors so well (AUROC 0.82 -> 0.89 in Hindi). Do not use full-token RDS as a predictor of errors.
- Operation-type RDS (no values) does predict Hindi errors (OR 1.13 per 0.1, p < 0.001) but adds almost nothing: AUROC 0.818 -> 0.820, while log trace length alone gives 0.834. In English it has no effect (p = 0.58). This matches the handoff's warning that text-only trace features carry weak signal.

## Other numbers that moved (full grid)
- Cut off before answering: English CoT 3.2%, Hindi CoT 0.7% (1.0% of all responses). Strict scoring (cut-off = wrong) gives CoT deltas +26.7 (English) and +4.2 (Hindi); the distraction-penalty conclusions are unchanged.
- Median CoT length: English 107 words / 356 tokens, Hindi 83 words / 213 tokens.
- Mention rates (time-related, with placebo): English 17.4% (9.9%), Hindi 33.8% (10.1%); unrelated: English 11.5% (5.9%), Hindi 30.4% (1.9%).
- Error types under CoT: off-by-one is 54% of English and 21% of Hindi errors (was 67% / 27%; the time and interval tasks add "other" errors).

## Caveats
- One model, one seed, temperature 0, thinking off for all main runs.
- The `new` scope is a different set of cells, so a failed replication there can reflect task and level, not chance alone. The full-grid estimates with cluster bootstrap and clustered regressions are the ones to report.
- Accuracy drops cut-off responses unless stated; strict scoring is in `extra/numbers.json` (`strict`).
- Heuristic measures (mention, reuse, drift, verification, RDS parser) were not hand-validated in this pass.
