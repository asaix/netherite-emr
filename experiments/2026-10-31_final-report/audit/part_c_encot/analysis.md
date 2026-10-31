# Part C (en-CoT) audit

Saved by the main session from the audit agent's hand-back, because the harness refused the agent's own write of this file. Content is the agent's, unchanged.

Scope: sections C.1 to C.8 and Appendix C of `docs/final/netherite final analysis.pdf`.

Conventions. "Answered" means accuracy over responses with an extractable Answer line, as in the draft. "Strict" counts unanswered responses as wrong. Unless stated otherwise, intervals are percentile cluster bootstraps over questions, B = 10,000, seed 20261031, unstratified. `verify.py` also keeps B = 2,000 seed 0 to reproduce the draft.

How to run: `.venv/bin/python build.py`, then `.venv/bin/python verify.py [section ...]`, then `.venv/bin/python make_claims.py`. Tables are in `tables/`. Sections were run separately; there was no single end-to-end run.

Reused code: `build.py` re-implements scoring from the raw JSON. The answer regex, the verification regex, the mention stop list and the error-class rules were copied from the team's `metrics.py`, `temporal_answers.py` and `build_responses.py` so the same rules could be tested. Nothing is imported from those scripts.

## Verdict

| Headline claim | Verdict |
|---|---|
| en-CoT beats Hindi CoT (+23.5), Hindi direct (+27.7), CLP (+12.6) | Holds, in every distractor condition and under strict scoring. |
| Beats Hindi CoT and CLP "on all nine tasks" | Holds pooled. Against Hindi CoT it holds in each distractor condition. Against CLP it holds for only 8, 6 and 3 of 9 tasks (none, time-related, unrelated). |
| Interval date "level with Hindi direct" | Overclaimed. The pooled −2.7 [−7.6, +2.2] hides −12.7 [−20.0, −5.6] under the time-related distractor and −15.3 [−24.4, −6.5] at short. |
| Gap "shrinks as questions get harder" | The pooled trend is real (+5.9 [+2.3, +9.5]) but comes from recurrence. Without recurrence: +1.8 [−1.5, +5.2]. Without k ≤ 2 recurrence cells: +0.8 [−2.5, +4.1]. Appendix C's "Strong" should go. |
| Time-related distractor costs 3.2 points; "only condition" | The drop survives Holm over 12 tests (p = 0.029). "Only" is wrong under strict scoring (English CoT 2.7, Holm p = 0.016). There is no significant distraction penalty against direct (+2.0 [−0.5, +4.5]). It is concentrated in interval date and day of week. |
| "Fails on different questions" (φ 0.02) | Not supported. φ is uninformative here: it is undefined in 11 of 45 cells, and each condition agrees with itself across distractors only about as well (0.06 to 0.10). Over all cells, en-CoT errors are associated with English errors (MH OR 1.99 [1.62, 2.46]). |
| C.6 "from reading the Hindi question, not reasoning in Hindi" | The direction holds for backwards answers, but these are k = 1 only (55 of 58), not k = 1 and 2. It identifies the Hindi recurrence template in this model, not Hindi reading in general. |
| "What is left comes mostly from" backwards recurrence and the weekday slip | Overclaimed. Backwards answers are about 0.9 and excess one-day-late about 0.9 of the 6.0-point gap, so about 30%. |
| Day-of-week "same slip" | Verified as the main mechanism in both conditions, with exceptions. |
| Candidate: reasoning language explains more of the gap than question language | Supported as a descriptive decomposition: 23.5 vs 6.0 points, 79.7% [76.5, 82.8]. Not causal; one cell of the design is missing. |

## Data existence

| Item | Status |
|---|---|
| `responses/en-cot/` | 6,750 records, 2,250 questions (qn 0 to 49), 3 insertions, one run date (2026-10-28). All have `sarvam-105b`, 4,096 tokens, temperature 0, top_p 1, reasoning_effort null. Matches the design. |
| `responses/standard/` | 81,000 records; 27,000 used for the 2,250 questions. Run dates span 2026-09-29 to 2026-10-29. |
| `responses/clp/` | 6,750 records, one date (2026-10-29). |
| `responses/ron/` | 5,400 records on questions 0 to 9. |
| `dataset/` | Every prompt in all five response sets contains the dataset question for that insertion, and every gold matches (100%). |
| `experiments/2026-10-30_en-cot-mid-analysis-shaurya/outputs/report/` | Exists. `outputs/data/*.pkl`, which `report.py` reads, does not exist, so `report.py` cannot be rerun as checked in. |
| `experiments/2026-10-31_clp-analysis-rahul` (Part A's cited source) | **Missing** from the working tree and from every local and remote branch checked. |

**Is `outputs/report/` current?** Yes in substance. Commit 7552481, the last change to `report.py`, also changed the CSVs and `numbers.json`. My independent recomputation with the same seed reproduces every accuracy, difference and CI in the printed tables, including differences taken from unrounded values (+23.6, not 23.7). The `np.float64(...)` text in the CI columns is a cosmetic artefact of `str()` on a list. The values are right, and `ci()` should return floats.

## Corrected results

### Single CI version (Part A vs Part C)

Point estimates are identical. Over 100 seeds at B = 2,000, the Monte Carlo SD of each endpoint is about 0.1 point, and all ten Part A interval pairs fall inside the seed range (`tables/ci_partA_vs_partC.csv`). Part C is reproduced exactly with `default_rng(0)`. So the cause is consistent with different bootstrap draws, not different data. I can't confirm Part A's seed or code because its script is missing, and 27.0 sits at the edge of the seed range. Use one set, for both parts:

| Level | En CoT | Hi CoT | CLP | en-CoT | En − Hi CoT | En − CLP | En − en-CoT | Strict En − en-CoT |
|---|---|---|---|---|---|---|---|---|
| Short | 93.2 | 69.5 | 77.2 | 83.0 | +23.6 [20.6, 26.8] | +16.0 [13.1, 19.0] | +10.2 [7.7, 12.9] | +10.2 [7.7, 12.9] |
| Medium | 91.6 | 65.4 | 75.7 | 84.9 | +26.2 [23.3, 29.2] | +15.9 [13.2, 18.6] | +6.7 [4.5, 8.8] | +6.4 [4.2, 8.7] |
| Long | 89.3 | 60.4 | 71.3 | 84.4 | +28.9 [25.7, 32.1] | +18.0 [15.1, 20.8] | +4.9 [3.0, 6.8] | +3.3 [1.4, 5.2] |
| Very long | 87.2 | 53.7 | 65.8 | 83.5 | +33.5 [30.1, 36.8] | +21.4 [18.3, 24.6] | +3.6 [1.4, 5.9] | +3.3 [1.2, 5.5] |
| Very very long | 82.9 | 47.9 | 61.5 | 78.5 | +35.0 [31.6, 38.5] | +21.4 [18.1, 24.6] | +4.3 [1.9, 6.8] | +2.8 [0.4, 5.3] |

### Headline accuracy, both conventions, by distractor

| en-CoT minus | Convention | Pooled | None | Time-related | Unrelated |
|---|---|---|---|---|---|
| Hindi CoT | Answered | +23.5 [22.1, 24.9] | +23.9 [21.8, 26.1] | +22.0 [19.9, 24.2] | +24.5 [22.4, 26.6] |
| Hindi CoT | Strict | +21.7 [20.4, 23.1] | +22.4 [20.4, 24.6] | +19.7 [17.6, 21.9] | +23.0 [20.9, 25.1] |
| Hindi direct | Answered | +27.7 [26.0, 29.5] | +28.1 [25.8, 30.4] | +26.1 [23.8, 28.3] | +29.0 [26.8, 31.2] |
| Hindi direct | Strict | +25.6 [23.9, 27.3] | +26.2 [24.0, 28.4] | +23.3 [21.1, 25.6] | +27.2 [25.0, 29.5] |
| CLP | Answered | +12.6 [11.3, 13.9] | +14.9 [12.9, 16.9] | +11.6 [9.6, 13.6] | +11.3 [9.2, 13.3] |
| CLP | Strict | +10.9 [9.6, 12.1] | +13.3 [11.3, 15.3] | +9.5 [7.5, 11.4] | +9.7 [7.7, 11.7] |
| English CoT | Answered | −6.0 [−7.0, −5.0] | −5.2 [−6.9, −3.5] | −7.2 [−8.9, −5.5] | −5.6 [−7.3, −3.9] |
| English CoT | Strict | −5.2 [−6.3, −4.2] | −4.4 [−6.1, −2.7] | −5.7 [−7.5, −4.0] | −5.5 [−7.2, −3.8] |

The conclusion holds in every split.

"All nine tasks": Holm-corrected task wins are 9, 9, 9 against Hindi CoT and 8, 6, 3 against CLP (none, time-related, unrelated). By level against CLP they are 1, 3, 3, 6, 5 of 9 (short to very very long). Pooled and Holm-corrected, the nine-task claim is true. Say "pooled over distractors and levels" next to it (`tables/c1_task_by_distractor.csv`, `tables/c1_task_by_level.csv`).

Interval date against Hindi direct: −2.7 [−7.6, +2.2], McNemar 124 vs 148, p = 0.163; strict −3.6 [−8.5, +1.2]. Non-significance isn't equivalence: the 90% interval [−6.8, +1.5] doesn't fit inside ±5 points. Split: none +3.0 [−4.5, +10.4], time-related −12.7 [−20.0, −5.6] (p = 0.0004), unrelated +1.7 [−6.4, +9.4]. By level: short −15.3 [−24.4, −6.5], medium −0.6, long −6.0, very long +2.6, very very long +5.2 (`tables/c1_interval_vs_direct.csv`). Suggested wording: "not distinguishable from Hindi direct overall, and below it under the time-related distractor".

Cut-offs: every unanswered response has `finish_reason = length`, so "all cut off" holds (174, 43, 221 of 6,750; 2.6%, 0.6%, 3.3%). Two further en-CoT and five CLP responses were cut off but contain an earlier Answer line and are scored as answered and wrong. The counts aren't a robustness ranking:

- Cut-offs concentrate in day of week (English 120, en-CoT 91, Hindi CoT 27) and recurrence (47, 52, 4). Answered-only accuracy therefore flatters English CoT most on day of week: 69.5 answered vs 58.4 strict; en-CoT 52.5 vs 46.1.
- The gap to English falls from 6.0 to 5.2 under strict scoring, and day-of-week from 17.0 to 12.3.
- Hindi CoT's low count reflects shorter traces, not better completion. When Hindi CoT is cut off it is usually looping: the last 120 characters repeat earlier in 58% of cut-offs, against 14% for en-CoT and 1.4% for English CoT.
- Cut-offs rise under the time-related distractor (English 68 to 107, en-CoT 51 to 76).

### Does the gap shrink with difficulty?

| Subset | Short | Medium | Long | Very long | VVL | Short − VVL | Slope per level |
|---|---|---|---|---|---|---|---|
| All, answered | 10.2 | 6.7 | 4.9 | 3.6 | 4.3 | +5.9 [2.3, 9.5] | −1.48 [−2.26, −0.70] |
| All, strict | 10.2 | 6.4 | 3.3 | 3.3 | 2.8 | +7.4 [3.8, 11.0] | −1.79 [−2.59, −1.01] |
| Recurrence only | 51.8 | 23.0 | 11.1 | −2.3 | 13.7 | +38.1 [25.3, 51.2] | −10.13 [−13.00, −7.34] |
| No k = 1 | 6.7 | 6.7 | 4.9 | 3.6 | 4.3 | +2.4 [−1.0, 5.7] | −0.78 [−1.52, −0.04] |
| No k ≤ 2 | 5.1 | 5.2 | 4.9 | 3.6 | 4.3 | +0.8 [−2.5, 4.1] | −0.32 [−1.06, +0.42] |
| No k ≤ 2, strict | 5.0 | 5.1 | 3.3 | 3.3 | 2.8 | +2.2 [−1.2, 5.5] | −0.61 [−1.36, +0.12] |
| No recurrence | 5.1 | 4.6 | 4.1 | 4.3 | 3.3 | +1.8 [−1.5, 5.2] | −0.39 [−1.13, +0.34] |
| No recurrence, strict | 5.0 | 4.5 | 2.6 | 3.6 | 1.7 | +3.3 [−0.0, 6.7] | −0.76 [−1.51, −0.02] |
| No recurrence, no day of week | 2.6 | 2.7 | 2.9 | 2.9 | 1.9 | +0.6 [−2.5, 3.8] | −0.11 [−0.78, +0.57] |

- Per task, only recurrence has a slope that survives Holm over nine tasks (p = 0.0009). Day of week is next: +13.1 [−1.8, +28.2], Holm p = 0.52.
- A GEE logistic model with task fixed effects gives an English × level interaction of −0.225 (SE 0.044, p < 0.001). Dropping recurrence weakens it to −0.098 (SE 0.047, p = 0.035). A small residual narrowing may exist on the logit and strict scales. It isn't robust to choice of scale and subset.
- By distractor, answered: none +5.6 [0.0, 11.0], time-related +7.4 [1.6, 13.2], unrelated +4.8 [−1.0, 10.6].
- The narrowing is also driven by English falling further: English CoT loses 10.3 [7.3, 13.3] points from short to very very long, en-CoT 4.4 [0.5, 8.3].

Corrected claim: en-CoT's gap to English is about 5 points at most levels once the k ≤ 2 recurrence cells are set aside. The pooled gap goes from +10.2 to +4.3 mainly because recurrence at k = 1, 2 occurs only at short and medium. What does separate en-CoT from Hindi CoT and CLP is the absence of widening.

### C.4 Distractor

| Condition | Drop, time-related (answered) | Holm 12 | Drop, time-related (strict) | Holm 12 |
|---|---|---|---|---|
| English direct | +0.7 [−1.0, +2.5] | 1.00 | +0.8 [−0.9, +2.6] | 1.00 |
| English CoT | +1.2 [−0.4, +2.7] | 1.00 | **+2.7 [+1.1, +4.3]** | 0.016 |
| Hindi direct | +1.2 [−0.6, +2.9] | 1.00 | +1.2 [−0.6, +2.9] | 1.00 |
| Hindi CoT | +1.3 [−1.0, +3.5] | 1.00 | +1.3 [−1.0, +3.5] | 1.00 |
| CLP | −0.1 [−2.1, +1.9] | 1.00 | +0.2 [−1.8, +2.2] | 1.00 |
| en-CoT | **+3.2 [+1.3, +5.0]** | 0.029 | **+4.0 [+2.2, +5.8]** | 0.0003 |

Unrelated distractor, en-CoT: +0.6 [−1.2, +2.3]. CLP improves with it: −3.1 [−5.1, −1.1], Holm 0.029.

- **"Only":** the point estimate is positive in five of six conditions, so "the only condition that loses accuracy" should be "the only one whose answered-only drop is significant". Under strict scoring English CoT also drops significantly.
- **Penalty against direct:** en-CoT +2.0 [−0.5, +4.5], strict +2.8 [+0.4, +5.4] (Holm over 14 contrasts p = 0.25). Against Hindi CoT +1.8 [−1.0, +4.6]; against English CoT +2.0 [−0.3, +4.4]. Only against CLP does strict scoring reach significance (+3.8, Holm 0.042). So after correction en-CoT is not shown to be more distractible than English CoT, Hindi CoT or direct. This reconciles the draft with `FINDINGS.md` item 5, which reported the penalty as not significant; the two documents use different quantities.
- **Tasks:** interval date 50.2 to 36.9 (+13.3 [5.2, 21.7], Holm9 0.038) and day of week 58.5 to 44.3 (+14.1 [4.8, 23.4], Holm9 0.18). Leaving out interval: +1.9 [0.2, 3.7], p = 0.09. Leaving out day of week: +1.8 [0.0, 3.5], p = 0.035. Five of the other seven tasks sit within ±2.
- **Sentences:** no sentence survives Holm. The largest are "सोमवार की सुबह कठिन होती है।" on interval date (54.1 to 26.2, 23 lost vs 6 gained, raw p = 0.002, Holm 0.10) and "क्या धूप वाला दिन होगा?" on day of week (56.1 to 26.8, 14 vs 2, raw p = 0.004, Holm 0.18). The first names the anchor weekday in a task that asks about Mondays, so a real interaction is plausible but untested.
- **Premise reading (exploratory):** "आखिरी साप्ताहिक प्रतिबद्धता जनवरी में थी।" on recurrence gives 24 of 44 en-CoT cut-offs against 1 of 44 without it. The trace I read treats it as a fact about the recurrence ("the most recent occurrence ... was in January 2025"). English CoT does the same on the English sentence (29 of 44 vs 2 of 44; answered accuracy 93.3 to 53.3), so this is a sentence effect, not a Hindi one. It fits the draft's "carried into the reasoning" guess only in general form (`tables/c4_similar_by_sentence.csv`).
- **Full-grid context:** on standard conditions, the Hindi CoT time-related drop is 1.3 in the first 50, 3.2 in the rest and 2.6 over all 150. Hindi direct is 1.2, −0.0 and 0.4. So the document's full-grid penalty of +2.2 is reproduced by 2.6 − 0.4. The subset is underpowered for penalties of this size.

**Mention rate.** en-CoT's numbers come entirely from the English word list.

| Word list on en-CoT | Time-related (placebo) | Net | Unrelated (placebo) | Net |
|---|---|---|---|---|
| Hindi only (the actual mid-report rule) | 3.6 (0.0) | +3.6 [2.8, 4.4] | 0.4 (0.0) | +0.4 [0.2, 0.7] |
| English only | 22.0 (9.3) | +12.7 [10.9, 14.5] | 17.0 (5.5) | +11.5 [10.0, 13.0] |
| Union (draft) | 22.0 (9.3) | +12.7 [10.9, 14.5] | 17.0 (5.5) | +11.5 [10.0, 13.0] |

The union adds nothing over the English list, and the placebo already absorbs chance matches, so it isn't inflating en-CoT against a like-for-like English list. It does make "the mid-report rule" inaccurate as a label, and "about half as often as Hindi CoT" compares different word lists. The English distractors are often longer and aren't literal translations of the Hindi ones, so the lists aren't equivalent (`tables/template_distractor_pairs.csv`). The like-for-like comparison is English CoT: net +8.4 [6.7, 10.0] and +4.7 [3.6, 5.8]. en-CoT mentions the distractor more than English CoT does on the same list.

The OR claim needs softening too: 0.82 [0.59, 1.13] and 0.91 [0.58, 1.43] don't exclude a moderate harm, and English CoT's own time-related OR is 0.61 [0.39, 0.93].

### C.5 Agreement

Table C5's counts and φ are reproduced, but φ isn't fit for this claim:

- It is undefined in 11 of 45 cells for en-CoT. 17 of 45 cells have at most 2 English errors; the median is 5.
- Cross-distractor self-agreement, the same condition on the same questions, is itself only 0.103 and 0.068 for English CoT, and 0.061 and 0.102 for en-CoT (`tables/c5_self_ceiling.csv`). A cross-condition φ near 0.1 is therefore at the ceiling: within a cell, errors look close to noise. Low φ doesn't show "different questions".

Measures over all 45 cells (cluster bootstrap):

| Hindi condition vs English | Within-cell φ, all cells | MH OR, all cells | P(right given English wrong) | P(right given English right) | Same wrong answer, both wrong |
|---|---|---|---|---|---|
| Hindi direct vs English direct | 0.286 [0.254, 0.317] | 4.39 [3.79, 5.08] | 21.4 | 78.1 | 21.5% |
| Hindi CoT vs English CoT | 0.052 [0.028, 0.077] | 1.61 [1.28, 2.03] | 21.8 | 65.4 | 13.1% |
| CLP vs English CoT | 0.066 [0.034, 0.097] | 1.58 [1.28, 1.94] | 33.4 | 76.4 | 18.0% |
| en-CoT vs English CoT | 0.116 [0.079, 0.153] | 1.99 [1.62, 2.46] | 46.4 | 88.2 | 24.6% |

en-CoT is more aligned with English CoT than Hindi CoT is: within-cell φ difference CI [+0.021, +0.106]. Pooled P(right) columns are confounded by task; MH and within-cell φ are not. The largest per-task φ are time duration 0.254 and interval date 0.227 (`tables/c5_within_phi_by_task.csv`).

Off-by-one: the 52.3, 42.3, 21.2 and 26.9 figures reproduce, and the pattern survives task standardisation (49.1, 44.7, 23.5, 31.4). A weekday error is off by one by chance a third of the time, and day of week is 26 to 28% of errors in English CoT and en-CoT, so the task-standardised figures are the ones to quote.

### C.6 Backwards recurrences

Backwards rate over parsed recurrence answers (`tables/c6_recurrence_by_k.csv`, `tables/c6_k_error_types.csv`):

| k | English CoT | Hindi CoT | CLP | en-CoT | Hindi direct (first 50) | Thinking on, Hindi CoT |
|---|---|---|---|---|---|---|
| All | 0.4 (3/702) | 9.0 (67/746) | 8.1 (60/742) | 8.3 (58/698) [5.5, 11.5] | 7.5 (56/750) | 4.1 (5/121) |
| 1 | 3.5 (3/85) | 67.8 (59/87) | 69.0 (60/87) | 67.1 (55/82) | 63.2 (55/87) | 19.2 (5/26) |
| 2 | 0.0 | 1.7 | 0.0 | 0.8 (1/119) | 0.0 | 0.0 |
| 3 | 0.0 | 5.3 | 0.0 | 0.0 (0/56) | 1.8 | 0.0 |
| 4 | 0.0 | 0.0 | 0.0 | 1.9 (1/54) | 0.0 | 0.0 |
| 5 to 8 | 0.0 | 2.0 | 0.0 | 0.7 (1/138) | 0.0 | 0.0 |
| 9+ | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |

Note: on all 150 questions per cell, Hindi direct is 63.8% at k = 1, Hindi CoT 65.6%, English CoT 2.4%.

Test of "1वीं" against 2, 3, 4 and larger:

- **It's k = 1, not k = 1 and 2.** 55 of 58 en-CoT backwards answers are at k = 1. Within short, k = 1 vs k = 2 differs by +67.1 [56.3, 78.1] points. C.6's cross-reference is wrong. The full-grid `FINDINGS.md` line 116 says k = 1 only, and gives k = 2 as a separate first-step error.
- **Ungrammaticality isn't sufficient.** 2वीं, 3वीं and 4वीं are also non-standard (दूसरी, तीसरी, चौथी) and give essentially no backwards answers. All 82 answered en-CoT k = 1 traces hit an ordinal regex ("1st", "first" and similar), so the digit-plus-वीं form appears to be decoded. Mirror traces use "before" 87% and backward language 85%, against 12% and 8% in correct k = 1 traces. One read: "If today (2025-06-08) is excluded, I need to find when the 1st occurrence happened before today." The quote in C.6 is verbatim from one record (`short/date_recurrence_hi_IN/43/no_insertion/en-cot`).
- **A second error runs through every k.** Answers one step short (k − 1 intervals) occur at en-CoT 34.5% (k = 2), 10.7, 11.1, 8.0, 10.0, 18.5 (k = 17 to 32); Hindi CoT 47.5 down to 7.4; CLP 38 to 45 down to 22. English CoT is 0.0 up to k = 4, 0.7 at 5 to 8, then 5.2 and 6.7. Sampled traces (9 read, k = 2 and 3 only) count today as the first occurrence: "Since we exclude today (the 1st occurrence), the next occurrence (2nd occurrence) will be 5 days after today". It also occurs at k ≥ 5, where -वीं is acceptable. I did not read k ≥ 5 traces, and at large k some matches may be arithmetic coincidence.
- **Together:** backwards plus k − 1 answers account for 157 of 207 wrong en-CoT recurrence answers (76%), against 19 of 68 for English CoT (28%).
- **Working hypothesis (untested):** the exclusion clause "आज को छोड़कर" is misread, so today is taken as occurrence 1. At k = 1 that leaves nothing ahead and the model goes backwards. At k ≥ 2 it lands one step short. This fits both error families. It doesn't explain why k = 2 is so much worse than k = 3, and English direct also gives one step at k = 2 (88%), which looks like a direct-mode shortcut.
- **Template or comprehension?** Not separable with these data. For a template reading: the same model with the English carrier gives about 3% at k = 1, and the error appears under every Hindi prompting condition. For a capacity reading: thinking on reduces it to 19% (5/26), so the Hindi is interpretable. Note the English template is also non-standard ("the 1 occurrence", and TRD's own Table 2 prints "the 2 occurrence"), yet it does no harm. The decisive experiment is a rerun with corrected Hindi carriers (पहली, दूसरी; a future cue such as "आज के बाद"), which was not done.

**Template translation review (9 templates).** My reading, as an LLM, needs a native-speaker check before it is printed. One severe, four mild, four fine:

| Template | Text | Finding | Evidence of harm |
|---|---|---|---|
| Recurrence | "मेरे पास हर {n} दिनों पर एक पुनरावृत्ति है। आज को छोड़कर, {k}वीं आवृत्ति की तिथि क्या है?" | **Severe.** "मेरे पास ... पुनरावृत्ति है" is a calque of "I have a recurrence". Two nouns for one concept (पुनरावृत्ति, आवृत्ति; आवृत्ति also means frequency). -वीं is non-standard for k = 1 to 4. "हर 1 दिनों" is a plural with 1. No future cue. | Yes: 76% of en-CoT errors above. |
| Date addition | "{n} दिनों में तिथि क्या होगी?" | Mild. "1 दिनों में" is ungrammatical; "में" can read as "within". | None visible: en-CoT and Hindi CoT 100% at n = 1 on short. |
| Time addition | "अभी {HH:MM} बजे हैं, ..." | Mild. "बजे" with 24-hour clock is unusual. | Gap 3.3. |
| Time subtraction | "अभी {HH:MM} बजे हैं, ..." | Mild, same. | Gap 2.0. |
| Day of week | "{date} सप्ताह का कौन सा दिन (...) है?" | Mild. "को" after the date would be more natural. | See below. |
| Date subtraction | "{n} दिन पहले क्या तारीख थी?" | Fine. | Gap 1.2; so Hindi CoT's 66% is not a template problem. |
| Date duration | "{a} और {b} के बीच कितने दिन (...) बीत चुके हैं?" | Fine. | Gap 1.6. |
| Time duration | "अगर मैंने {a} पर घड़ी देखी और अब {b} है, ..." | Fine. | Gap 0.8. |
| Interval date | "अगले सप्ताह की शुरुआत और अंत की तिथियां क्या हैं, ..." | Fine. | Gap 6.6: −1.7 with no distractor, +10.2 time-related, +11.1 unrelated. Not a template signature. |

Residual gaps: recurrence 70.3 vs 90.3 is largely template-linked, but not entirely. Even at k ≥ 5 the gap is 7.4 [2.5, 12.1]. Day of week 52.5 vs 69.5 is **not** template-linked as far as I can tell. The question is an ISO date and one short phrase, en-CoT traces do compute weekdays, and verification is associated with much of the gap (see Missing findings). The Hindi distractors are also non-literal and often shorter than the English ones, for example "The last time I had a weekly commitment was in January" vs "आखिरी साप्ताहिक प्रतिबद्धता जनवरी में थी।" and "I always mix up dates ..." vs "... भूल जाता हूं" (forget). So English/Hindi distractor comparisons aren't strictly parallel.

Impact on the rest: removing k = 1 moves the overall gap only from 6.0 to 5.3 [4.3, 6.3], and removing k ≤ 2 to 4.6 [3.7, 5.7]; Hindi CoT goes 59.4 to 60.3. So it is a major limitation for recurrence and the short level, and a small one for pooled results. The en-CoT gain over Hindi CoT at k ≥ 5 is +67.4 [62.6, 72.3], which the ordinal form can't explain.

**Day of week.** Rates reproduce: one day late 24.0, 25.3, 16.2. Mechanism test on all traces: among one-day-late answers, the day-of-year number appears without day-of-year − 1 in 83.3% of English CoT and 77.8% of en-CoT traces, against 3.2% and 13.0% of correct answers. In correct answers day-of-year − 1 appears in 92.0% and 62.4%. Hand-read 12 late traces per condition (only the final part of each): 10 English and 11 en-CoT match inclusive counting, for example "Since January 1 is day 1 ... 255 ÷ 7 ... 3 days after Wednesday". Exceptions: an en-CoT Zeller result with the wrong weekday mapping, and two English traces I couldn't confirm. Anchors vary (1 January of the target year, 2000 or 2024), so "counts 1 January" holds better as "counts the anchor day". I don't rely on the anchor-weekday regex column. The mechanism is shared; the rate differs.

### Decomposition: reasoning language vs question language

Same 2,250 questions. Total = English question with English CoT − Hindi question with Hindi CoT. Reasoning part = en-CoT − Hindi CoT. Question part = English CoT − en-CoT.

| Cut | Total | Reasoning part | Question part | Reasoning share | Reasoning − question |
|---|---|---|---|---|---|
| Pooled, answered | 29.5 [28.1, 30.9] | 23.5 [22.1, 24.9] | 6.0 [5.0, 7.0] | 79.7% [76.5, 82.8] | 17.5 [15.5, 19.4] |
| Pooled, strict | 26.9 [25.6, 28.4] | 21.7 [20.4, 23.1] | 5.2 [4.2, 6.3] | 80.6% [77.1, 84.1] | 16.5 [14.6, 18.4] |
| None | 29.1 | 23.9 | 5.2 | 82.1% [76.8, 87.5] | 18.7 [15.5, 21.9] |
| Time-related | 29.2 | 22.0 | 7.2 | 75.4% [70.0, 80.9] | 14.9 [11.6, 18.2] |
| Unrelated | 30.1 | 24.5 | 5.6 | 81.4% [76.3, 86.7] | 18.9 [15.8, 22.1] |
| Short | 23.6 | 13.4 | 10.2 | 56.8% [47.9, 65.8] | 3.2 [−1.0, 7.4] |
| Medium | 26.2 | 19.6 | 6.7 | 74.6% [67.0, 82.3] | 12.9 [8.7, 17.1] |
| Long | 28.9 | 24.0 | 4.9 | 83.1% [77.1, 89.2] | 19.1 [15.3, 22.9] |
| Very long | 33.5 | 29.8 | 3.6 | 89.1% [82.9, 95.5] | 26.2 [21.8, 30.7] |
| Very very long | 35.0 | 30.7 | 4.3 | 87.6% [80.9, 94.2] | 26.3 [21.6, 31.0] |
| Date addition | 12.9 | 10.7 | 2.3 | 82.5% [67.7, 97.2] | 8.4 [4.4, 12.3] |
| Date subtraction | 29.2 | 28.0 | 1.2 | 95.8% [88.5, 103.3] | 26.8 [21.6, 32.1] |
| Date duration | 11.1 | 9.5 | 1.6 | 85.5% [73.6, 96.6] | 7.9 [4.7, 11.0] |
| Recurrence | 70.2 | 50.2 | 20.0 | 71.5% [65.6, 77.3] | 30.3 [21.8, 38.5] |
| Day of week | 48.5 | 31.5 | 17.0 | 64.9% [56.0, 74.3] | 14.5 [5.9, 23.2] |
| Interval date | 26.8 | 20.3 | 6.6 | 75.6% [61.4, 91.3] | 13.7 [6.3, 21.2] |
| Time addition | 22.5 | 19.2 | 3.3 | 85.3% [74.9, 95.0] | 15.8 [10.7, 21.0] |
| Time subtraction | 22.5 | 20.5 | 2.0 | 91.1% [82.8, 99.0] | 18.5 [13.8, 23.2] |
| Time duration | 18.9 | 18.1 | 0.8 | 95.8% [90.8, 100.6] | 17.2 [13.9, 20.7] |

The reasoning part exceeds the question part in every task and distractor condition, and at every level except short, where the interval includes zero. Triangulation: the direct-answer English − Hindi gap, with no reasoning at all, is 4.5 [3.2, 5.8] (none 4.6, time-related 5.0, unrelated 4.0), close to the 6.0 question part.

**What it identifies.** The change in accuracy from switching the instructed reasoning language with the Hindi question fixed, then the change from switching the question language (and the prompt's source-language sentence) with English reasoning fixed.

**What it doesn't identify.**
- The English question with Hindi CoT cell doesn't exist, so the split is one path and order-dependent. No Shapley or interaction term is possible.
- en-CoT differs from Hindi CoT in prompt wording as well ("The following question is written in Hindi").
- The reasoning part bundles language with style: 311 vs 212 median tokens, 74.2% vs 1.3% verification.
- Implicit translation: traces usually open by restating the question in English ("I need to find the date of the 1st occurrence"). Explicit "translat-" appears in only 0.5%, so reasoning in English may partly mean translating, as in EN-CoT's relation to TRANSLATE-EN. Comprehension failures show up in the question part, but a translation step may also rescue comprehension inside the reasoning part.
- Hindi question reading is measured through one template set; run-date differences apply (see Limitations).
- Answered-only and strict agree, but neither is causal at the level of mechanisms.

## Limitations

**Can't be concluded from this design**
- That Hindi comprehension as such, rather than the TRD Hindi carrier, causes C.6's error.
- A causal split of the gap into reasoning and question language.
- That verification causes accuracy; it is post-treatment, tied to length and possibly to confidence.
- Generalisation beyond Sarvam-105B, one prompt wording per condition, one English and one Hindi template set.

**Simply not run**
- Corrected Hindi carriers. This is the most valuable next experiment.
- English question with Hindi CoT.
- Paraphrased en-CoT prompts, and Hindi-question thinking-on with a token budget equal to 4,096.
- en-CoT on questions 50 to 149.
- Repeat calls at temperature 0.

**Threats the draft doesn't mention**
- **Run date.** en-CoT ran on 2026-10-28 and CLP on 2026-10-29; standard responses ran over 2026-09-29 to 2026-10-25 (a few later). The API's usage schema changed between 09-30 and 10-15 (`completion_tokens_details` absent, then present), so the server changed at some point. Batches are split mostly by task, so drift can't be separated from condition. Same-task overlap is thin (`tables/batch_effect.csv`; most intervals span 1). Part C treats all conditions as contemporaneous.
- **Answered-only selection.** It favours English CoT and en-CoT where cut-offs concentrate, and McNemar uses both-answered pairs only.
- **Multiplicity.** Holm covers nine tasks per contrast; Part C runs three contrasts plus many cuts. The big effects survive any correction; C.4's don't all.
- **Difficulty is not one thing.** Level changes k, interval and date range together, and only date range for day of week and interval date. k = 1 exists only at short.
- **Regex features.** Mention, verification and method flags are lexical. The verification regex misses "सत्यापन" and similar: widening it moves Hindi CoT from 1.3% to 3.5%, which doesn't change the conclusion.
- **Template review by an LLM.** Needs a native speaker.
- **Bootstrap.** Questions are the only unit resampled; templates and distractor sentences are fixed, so intervals understate uncertainty about other wordings.

**Subset representativeness.** The first 50 look like a fair slice for en-CoT comparisons. On the four standard conditions, none of 60 first-50 vs rest-100 differences (overall, by task, by level) has an interval excluding zero (`fig_data/new_subset_first50_vs_rest.csv`). The English − Hindi CoT gap is 29.5 vs 28.9. Across-level correlations in question values and outcomes are near zero. One imbalance matters: k = 1 is 58% of short recurrence in the first 50, against 46% in the rest (χ² p = 0.23). Reweighting to 50/50 moves en-CoT short recurrence from 44.8 to 47.0 and English CoT from 96.6 to 97.1, so the +10.2 short gap is slightly high (about 0.2 of a point). Being representative on these conditions doesn't prove en-CoT would behave the same on the rest. It also leaves distractor penalties underpowered, as noted.

## Design rationale from prior work

- **en-CoT.** EN-COT is defined by Shi et al. as predicting the chain of thought in English regardless of problem language. Our condition departs in several ways: theirs is few-shot (6 exemplars where possible) with GPT-3 and PaLM on MGSM math word problems; ours is zero-shot, instruction-only, on temporal reasoning with Sarvam-105B. MGSM's ten languages don't include Hindi. Their gain is small (Table 3, last block: 51.3 vs 48.1 averaged across languages; TRANSLATE-EN 55.0; check the row label), so our +23.5 isn't a replication. Cite it as "adapted from". `responses/INFO.txt` and C.1 imply more fidelity than that.
- **Reasoning language.** Yong et al. (2025) report mostly English traces with a quote-and-think pattern and advise letting English-centric models reason in high-resource languages. Qi et al. (2025) find that forcing reasoning into the user's language lowers accuracy. Both fit Part C and the thinking-mode data. Their models are reasoning models; en-CoT here is thinking-off.
- **Latent English.** Wendler et al. (2024) and Zhao et al. (2024) offer interpretability evidence for English-leaning intermediate processing. They motivate the hypothesis only. We have no activations from Sarvam-105B.
- **TRD.** Mazzia et al. (2026) state the carrier phrases were written and reviewed with native speakers for natural phrasing and grammatical correctness. "1वीं" doesn't fit that claim. They also disabled CoT, so our CoT conditions are new, and they find small negative insertion effects, which matches the scale here. Report the Hindi template line as our finding.
- **Statistics.** The question-cluster bootstrap fits three correlated responses per question. Report a single seed and larger B.

## Missing findings

All exploratory.

1. **Backwards answers are a k = 1 phenomenon across all Hindi prompting conditions.** n = 82 (en-CoT), 67.1%; CLP 69.0%, Hindi CoT 67.8%, English CoT 3.5%. Within short, k = 1 vs 2: +67.1 [56.3, 78.1].
2. **k − 1 errors persist at every k in Hindi conditions.** en-CoT n = 616 answered at k ≥ 2, 8 to 34.5% per bin. With backwards answers, 76% (157/207) of en-CoT recurrence errors. Accuracy gap at k ≥ 3: +8.5 [4.4, 12.6].
3. **On recurrence, the reasoning-language gain grows with k.** en-CoT − Hindi CoT: k = 1 +6.3 [−5.1, 17.8]; k = 2 +27.2 [15.7, 38.7]; k = 3, 4 +44.0 [31.2, 56.5]; k = 5 to 8 +63.3 [54.2, 72.0]; k = 9 to 16 +79.1 [71.8, 86.0]. Hindi CoT falls to 5.6% at k = 9 to 16 while en-CoT stays at 84.6% (144 responses per condition before excluding unanswered). So k = 1 is where reasoning language doesn't help and large k is where it helps most.
4. **Thinking mode nearly closes the gap on Hindi questions.** On questions 0 to 9, n = 1,350 per condition: thinking-on Hindi CoT 97.9 answered and 89.9 strict; en-CoT 83.8 and 81.9; Hindi CoT 60.3 and 59.9; thinking-on English CoT 98.8 and 92.7. Thinking Hindi − thinking English: −0.9 [−1.9, 0.0], strict −2.7 [−4.4, −1.2]. Thinking Hindi − en-CoT: +14.1 [11.6, 16.6], strict +8.1 [5.6, 10.4]. The reasoning channel is 79.4% English words pooled (mean 77.0%), 81.6% non-Devanagari letters; only 8.4% of Hindi CoT traces exceed 90% English. Visible output stays in Hindi (0.1% English words). Confounds: 16,000 tokens vs 4,096, thinking itself (English also gains +9.2 [7.1, 11.5]), the 10-question sample, and 107 cut-offs (7.9%; only 7 of 27 at k = 17 to 32 answered).
5. **More English inside a Hindi thinking trace doesn't track higher accuracy.** Question fixed effects, CoT, answered n = 1,240: whole trace −14.0 points per 100% English [−25.5, −2.5]; first 1,000 characters −6.4 [−13.4, +0.6]; first 3,000 −4.3 [−12.1, +3.4]. Whole-trace strict is −98 because long traces become almost all English and hit the budget (strict accuracy 40% and 19% in the two top share bins, median 15,999 reasoning tokens). So whole-trace share partly marks struggle. The between-condition evidence and this within-condition result don't conflict, but the second gives the candidate claim no extra support.
6. **Verification is associated with the residual day-of-week gap, not the en-CoT gain.** g-formula within task × level, 2,000 replicates. Hindi CoT to en-CoT: 0.2 [−1.4, +2.1] of 23.1 points, 1.0% [−6.3, 9.0], relying on en-CoT's outcome model since Hindi CoT verifies in 1.3%. en-CoT to English on day of week: verification rate 52.2% vs 98.3%, 10.6 [6.9, 14.4] of 16.7 points, 63.6% [39.8, 97.0]; all other tasks 0.0 [−0.2, +0.2]. Within-task MH OR: day of week 2.57 [1.87, 3.52], recurrence 0.34 [0.18, 0.66], others span 1. Among verifying day-of-week traces with a weekday before the check (crude, last weekday mentioned), changed-to-right vs changed-to-wrong are 71 vs 15 in en-CoT (n = 322) and 209 vs 11 in English (n = 610). The association may reflect selection. The draft's "usually checks its work" explanation for en-CoT beating CLP isn't supported beyond day of week.
7. **The time-related drop is largely two tasks.** See C.4 above. Interval date en-CoT: 13.3 [5.2, 21.7], n = 250 questions.

## Suggested claims for the paper

1. **Strong.** "On 2,250 Hindi questions, instructing Sarvam-105B to reason in English raised accuracy over Hindi CoT by 23.5 points [22.1, 24.9] (82.9% vs 59.4% of answered responses; 21.7 [20.4, 23.1] counting unanswered as wrong), and by 22.0 to 24.5 points in each distractor condition."
2. **Strong.** "Of the 29.5-point English-Hindi CoT gap [28.1, 30.9], 23.5 points are recovered by changing the reasoning language with the Hindi question fixed, and 6.0 [5.0, 7.0] remain between Hindi and English questions under English reasoning (79.7% [76.5, 82.8]; 75 to 82% in each distractor condition). This is a descriptive one-path decomposition: we did not run English questions with Hindi reasoning."
3. **Strong.** "Answers going backwards in time are confined to k = 1 of the Hindi recurrence template (en-CoT 67.1%, 55 of 82; Hindi CoT 67.8%; CLP 69.0%; English CoT 3.5%) and are almost absent at k = 2 to 4 (2 of 229 for en-CoT), although those ordinals are equally non-standard. Changing the reasoning language does not remove them, which points to the Hindi carrier phrase or its reading. We did not test a corrected template."
4. **Moderate.** "The en-CoT gap to English CoT narrows from 10.2 points at short to 4.3 at very very long (+5.9 [2.3, 9.5]), but this depends on recurrence: without the k ≤ 2 cells the change is +0.8 [−2.5, 4.1]. By contrast the Hindi CoT gap widens from 23.6 to 35.0."
5. **Moderate.** "The time-related distractor lowers en-CoT accuracy by 3.2 points [1.3, 5.0; Holm-adjusted p = 0.029 over 12 tests], concentrated in interval date (13.3 [5.2, 21.7]) and day of week (14.1 [4.8, 23.4]). The excess over direct answering is not significant (+2.0 [−0.5, +4.5])."
6. **Moderate.** "Over all 45 task-level cells, whether en-CoT is right is associated with whether English CoT is right (Mantel-Haenszel OR 1.99 [1.62, 2.46]; within-cell φ 0.116 [0.079, 0.153], against 0.052 for Hindi CoT), at about the level each condition agrees with itself across distractors (φ 0.06 to 0.10)."
7. **Moderate.** "One-day-late weekday answers are mostly inclusive counting in both conditions: the day-of-year number appears without day-of-year − 1 in 77.8% of late en-CoT traces and 83.3% of late English CoT traces, against 13.0% and 3.2% of correct ones."
8. **Suggestive.** "With thinking on, Hindi CoT reaches 97.9% of answered responses (89.9% strict) on questions 0 to 9, and its hidden reasoning is 79% English words, which fits the English-reasoning account. Larger token budgets and the thinking mode itself are confounded with this, and within Hindi traces a higher English share does not predict higher accuracy."
