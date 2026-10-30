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
- Thinking-on runs: `2026-10-25_test-reasoning-on` (questions 0-9 of every task and level, `reasoning_effort: low`, 16k tokens), 5,400 responses (byte-identical to `responses/ron/` on main).
- On main, `d7e7bfe` (29 Oct) has since filled in the 5 missing very-very-long questions (`responses/standard/`). This folder still uses the 6,745-question grid; adding 5 questions out of 6,750 does not change any conclusion here.
- Trace deletion (`2026-10-26_trace-deletion`) is still running and is not analysed here.

## How to rebuild

```bash
PY=../../../.venv/bin/python   # needs pandas scipy statsmodels matplotlib numpy pyyaml
$PY build_responses.py --parser mid       # one row per response -> outputs/data/responses_mid.pkl
$PY build_responses.py --parser current
$PY build_responses.py --source reasoning_on   # thinking-on responses -> outputs/data/responses_on_current.pkl
$PY analysis.py --scope mid --parser mid  # = the mid report, reproduced exactly
for s in mid new full4 full ron-off ron; do $PY analysis.py --scope $s; done
$PY extra.py          # new full-grid analyses -> outputs/extra
$PY reasoning_on.py   # thinking on vs off -> outputs/reasoning_on
$PY compare.py        # mid report vs full grid -> outputs/comparison.{md,csv}
$PY compare.py --pair reasoning   # thinking off vs on -> outputs/comparison_reasoning.{md,csv}
```

Run from this folder; the whole pipeline takes about 7 minutes. Files:
- `analysis.py` and `build_responses.py` are the mid-report scripts with only these changes: a `--scope` / `--parser` switch; all five levels; a third difficulty panel (all nine tasks); outputs go to `outputs/<scope>/` (`plots/` instead of the git-ignored `figures/`); `recurrence_k` and the extracted answer are kept per response.
- `temporal_answers.py` reads the five run folders directly instead of a merged copy (`load_records("reasoning_on")` reads the thinking-on runs).
- For thinking-on responses, the mid-report trace measures (words, target-language ratio, verification, distractor mention, answer in trace) use the visible response only, as in the mid report. The hidden trace (`reasoning_content`) gets its own `hidden_*` columns. `metrics.target_words` concatenates both fields, so `build_responses.py` passes them separately.
- `metrics.py` is the root `metrics.py` with the parser fix below; `metrics_mid.py` is the mid report's copy.

Scopes (`outputs/<scope>/`, each with `numbers.json`, `tables/*.tex` (incl. `macros.tex`), `plots/`):

| Scope | Questions | What it is |
|---|---|---|
| `mid-midparser` | 3,089 | Mid-report questions and parser. Reproduces every committed mid-report table and all 249 macros byte for byte. |
| `mid` | 3,089 | Same questions, current parser. Identical numbers (the parser changes do not touch these questions' scores). |
| `new` | 3,656 | Only questions not in the mid report: an out-of-sample check of the mid-report findings. Different cells (time and interval tasks at short to long, all of very-very-long), so not a like-for-like replication. |
| `full4` | 5,400 | Full grid, four levels (what the full grid looked like before very-very-long). |
| `full` | 6,745 | Full grid, five levels. **Use this for the paper.** |
| `ron-off` | 449 | Thinking off (main runs) on the questions that were also run with thinking on: questions 0-9 of every task and level, minus `very_very_long/time_subtraction/2`, which is missing from the thinking-off grid. |
| `ron` | 449 | The same questions with thinking on. |

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

Full mid-report analysis with thinking on: see the section "Mid-report analysis with thinking on" below.

## Other numbers that moved (full grid)
- Cut off before answering: English CoT 3.2%, Hindi CoT 0.7% (1.0% of all responses). Strict scoring (cut-off = wrong) gives CoT deltas +26.7 (English) and +4.2 (Hindi); the distraction-penalty conclusions are unchanged.
- Median CoT length: English 107 words / 356 tokens, Hindi 83 words / 213 tokens.
- Mention rates (time-related, with placebo): English 17.4% (9.9%), Hindi 33.8% (10.1%); unrelated: English 11.5% (5.9%), Hindi 30.4% (1.9%).
- Error types under CoT: off-by-one is 54% of English and 21% of Hindi errors (was 67% / 27%; the time and interval tasks add "other" errors).

## Mid-report analysis with thinking on (`outputs/ron`, `outputs/ron-off`, `outputs/comparison_reasoning.md`, `outputs/reasoning_on/numbers.json` → `hidden_traces`)

The mid-report pipeline was run unchanged on the thinking-on responses (`ron`) and on the same 449 questions with thinking off (`ron-off`), so each number has a paired baseline. With thinking on, both prompts get a hidden reasoning trace: "direct" means the visible answer has no reasoning, "CoT" means the visible answer also reasons step by step. `ron-off` is a small subset (about 150 questions per task-language cell, 50 per task-level cell), so treat thinking-off numbers here as a check on the subset, not as replacements for the full-grid numbers.

**1. CoT delta: the visible CoT prompt barely matters once the model thinks**

| | Thinking off: direct → CoT | Thinking on: direct → CoT |
|---|---|---|
| English | 63 → 90, +26.4 [+23.0, +30.0] | 98 → 99, +0.9 [+0.0, +1.9] |
| Hindi | 58 → 60, +2.5 [-1.1, +6.3] | 95 → 98, +3.0 [+1.6, +4.4] |

- With thinking on, Hindi gains slightly more from the visible CoT prompt than English does: the reverse of the thinking-off pattern.
- The Hindi tasks where visible CoT hurts with thinking off flip: date subtraction -26.7 → +1.4, interval date -21.6 → +14.8 [+6.4, +23.0]. With thinking on, no single task's CoT delta is significant after Holm correction in either language (about 50 questions per task-language cell). Uncorrected, the bootstrap intervals exclude zero only for Hindi interval date (+14.8) and English date duration (-2.7 [-5.4, -0.6]); English time addition (-0.7) and Hindi time addition (-2.0) are slightly negative.
- Time duration, the biggest thinking-off CoT gain, goes to +2.0 (Hindi) and 0.0 (English) because direct answers are already near 100%.
- Strict scoring reverses the sign: counting cut-off responses as wrong, CoT minus direct is -2.6 (English) and -1.0 (Hindi) with thinking on. Visible CoT on top of thinking makes cut-offs at 16k tokens more common (CoT 6.2% English, 8.2% Hindi; direct 2.7%, 4.2%), which costs more than CoT gains.

**2. Day of week: the guessing disappears**
- Direct answers go from guessing (17.3% English, 20.7% Hindi right; each offset 9-21%) to 97.9% and 95.0% right. The fixed default answer is gone: the most common weekday in direct answers drops from 34.7% (English, Friday) and 64.0% (Hindi, Sunday) to about 19-21%, close to the spread of the correct answers.
- Hindi CoT's off-by-one-late bias (23.1% one day late vs 18.9% right on this subset) becomes 1.8% vs 98.2%.

**3. Date recurrence: the shortcut goes, the Hindi template problem stays**
- First-step shortcuts disappear (English direct 14.8% → 0; Hindi CoT 2.7% → 0).
- Hindi mirror answers (right distance, wrong direction) fall from 14.7% to 4.1% (CoT) and 11.3% to 3.0% (direct), but do not vanish, and English has none. **8 of the 9 remaining Hindi mirror answers are at k = 1 ("1वीं आवृत्ति")**: 15% of Hindi k = 1 answers, against 0 of 54 in English. The wording problem survives thinking mode, which supports reading it as a template effect rather than a reasoning failure. These are also why "wrong direction" is 19% of the 26 remaining Hindi CoT errors.

**4. English-Hindi gap vs difficulty: it closes**
- All nine tasks, CoT gap by level: thinking off 24.7, 25.2, 28.9, 35.0, 32.3 points (short to very-very-long); thinking on 3.1, 0.4, 0.0, 0.0, 1.0. Direct gap: 4.1-6.0 off, 1.5-4.9 on.
- Five date tasks, CoT gap: short +27.8 → +6.1, very long +44.7 → -1.4 (n.s.).
- Accuracy is flat across difficulty with thinking on (`ron/plots/difficulty.pdf`; note the y-axis runs from 90 to 100). The thinking-off pattern of CoT pulling away at hard levels disappears because every condition is near ceiling.

**5. Distraction penalty: not testable on this subset**
- Every penalty estimate is near zero with intervals of about ±3-7 points, with thinking on and off: Hindi time-related -3.4 [-9.4, +2.6] off and -2.9 [-6.7, +0.8] on; English -1.9 off and -0.7 on.
- The thinking-off subset does not show the full-grid Hindi penalty (+2.2) either, so these 449 questions have too little power to say whether thinking removes it. Per-task penalties have intervals of ±10-20 points.
- What can be said: with thinking on, the distractor costs at most a few points in any condition (largest drop 2.9 points, Hindi direct, time-related).

**6. Distractor mention**
- Visible CoT traces mention the distractor above placebo about as often as without thinking (Hindi time-related +21.8 points above placebo, was +24.9; English +12.8, was +7.3).
- Hidden traces (after removing verbatim quotes of the distractor): English time-related 55% (CoT) and 47% (direct) vs placebo 27% and 28%; Hindi 59% and 33% vs placebo 14% and 2%. **Do not compare these across languages:** Hindi hidden traces are mostly English, so a Hindi distractor's words are only found when the model writes them in Hindi, and the long hidden traces raise the placebo rates.
- No odds ratio between mention and correctness is significant, visible or hidden, because almost every answer is right (most strata have no wrong answers).

**7. Distractor reuse in wrong answers:** too few wrong answers with thinking on (all p ≥ 0.6) to test.

**8-9. Language drift and verification**
- Visible Hindi CoT stays in Hindi: target-language ratio 0.999, 3 drifting traces (28 with thinking off). The drift odds ratio cannot be computed.
- The hidden Hindi trace is the opposite: 4% Devanagari (direct) and 27% (CoT), with no trace mostly in Hindi (0% and 1%). With thinking on, the model reasons in English and writes the visible answer in Hindi.
- Verification moves into the hidden trace. Visible CoT verification: English 86% → 22%, Hindi 1.0% → 8.2%. Hidden traces contain a verification cue 90% (English) and 98% (Hindi) of the time. So the mid report's "Hindi traces rarely check their work" (1.5%) is a property of thinking-off visible CoT, not of the model.

**10. Trace length**
- Visible CoT: English 109 → 94 median words, Hindi 80 → 90; completion tokens (including hidden reasoning) 357 → 1,883 (English) and 208 → 4,268 (Hindi).
- Hidden traces are 2.5-3x longer for Hindi (median 2,261 words direct, 1,657 CoT) than English (755, 621).
- Wrong answers have much longer hidden traces: English CoT 1,458 vs 614 median words, Hindi CoT 3,126 vs 1,636, Hindi direct 2,530 vs 2,243. Within task x level, "longer than the cell median" is not significantly related to correctness (ORs 0.48-2.20, all p ≥ 0.05), because there are few errors; the pooled difference is consistent with the overthinking notes in `2026-10-25_test-reasoning-on/ANALYSIS.txt`.

**11. Cross-lingual agreement: the English-only advantage disappears**
- CoT pairs where only English is right vs only Hindi: 392 vs 18 with thinking off → 20 vs 11 with thinking on (p = 0.15). Direct: 197 vs 125 → 55 vs 22 (p < 0.001, a small English edge remains).
- Both wrong: 114 → 1 (CoT), 371 → 3 (direct).

**What this means for the paper**
- The thinking-off findings (Hindi CoT deficit, CoT hurting Hindi date subtraction and intervals, the weekday and recurrence error patterns, the widening gap) describe Sarvam-105B with its thinking mode off, where the visible trace is the only reasoning. With thinking on, almost all of them disappear on these 449 questions; the exception is the Hindi k = 1 recurrence template.
- The most plausible reading: with thinking on, the model reasons in English in the hidden trace and only translates the answer, so the language of the visible trace no longer constrains the reasoning. This links directly to the drift finding (Hindi traces that drift into English are more accurate).
- This belongs in the limitations or discussion ("thinking mode off throughout" is already a planned limitation); it is a 10-questions-per-cell pilot with a larger token budget, so present it as exploratory.

## Caveats
- One model, one seed, temperature 0, thinking off for all main runs.
- The `new` scope is a different set of cells, so a failed replication there can reflect task and level, not chance alone. The full-grid estimates with cluster bootstrap and clustered regressions are the ones to report.
- Accuracy drops cut-off responses unless stated; strict scoring is in `extra/numbers.json` (`strict`).
- Heuristic measures (mention, reuse, drift, verification) were not hand-validated in this pass.
