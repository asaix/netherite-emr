# Part A audit: cross-lingual prompting (RQ4)

Saved by the main session from the audit agent's hand-back, because the harness refused the agent's own write of this file. Content is the agent's, unchanged.

Conventions. "Answered" is accuracy over responses with an Answer line, as in the document. "Strict" counts unanswered as wrong. CIs are 95% cluster bootstraps over questions (B = 2,000) unless stated. Printed CI endpoints within 0.4 of ours are marked `reproduced`, because the document's seed is unknown and 2,000-draw percentile endpoints move by about 0.1 to 0.3 between seeds. Part A prints −3.1 [−5.1, −1.1] where Part C prints [−5.1, −1.2] for the same quantity; that is the same Monte Carlo noise.

Code reuse. `build_rows.py` is our own extraction and scoring, but it copies these operational definitions verbatim from `experiments/2026-10-27_full-grid-analysis`: the verification regex, the stoplist, the token pattern and the month list. They define the measures, so a rewrite would test something else. `verify.py` imports `temporal_answers.py` only for a differential check of answer extraction. TRD's `DAY_NAMES` is imported from `tools/`.

## Verdict

| Headline claim | Verdict |
|---|---|
| CLP beats Hindi CoT by +10.9 | **Holds** in every distractor condition and under both scoring conventions. |
| CLP beats Hindi direct by +15.1 "on every task" | **Number holds, "every task" is false.** Interval date is significantly worse (−11.5), date subtraction is not significant (+2.1). |
| English CoT stays +18.6 ahead | **Holds**, but +16.1 under strict scoring. |
| "The gap still widens with difficulty" | **Not robust.** +5.4 [+0.9, +9.8] answered, +2.2 [−2.2, +6.4] strict, and it reverses on the log-odds scale. |
| Stage 2 mostly follows stage 1 (97.5 vs 20.1) | **Holds and gets stronger.** It survives task, difficulty and question fixed effects (+62.5 [+57.1, +68.0]). |
| Distractors do not hurt CLP | **Weaken to "no drop detected".** Time-related drop −0.1, 90% CI [−1.8, +1.6]. |
| Unrelated distractor gain (−3.1) | **Not noise, but post hoc** and led by date recurrence. A stage-1 mode shift explains about a third of it (exploratory). |
| Understanding turn "absorbs" the distractor | **Overclaimed.** Most of the fall in mentions also appears in single-turn en-CoT. |
| Wrong answers "stop borrowing" | **Overclaimed.** Hindi CoT already shows no borrowing (3.2 vs 2.8, p = 0.84). |
| CLP "fails on different questions" from English, failures "unrelated" | **Not supported.** The association excludes zero and matches each CoT condition's agreement with itself across distractor versions. |
| The subset has a "smaller" penalty | **Misleading.** The subset is effectively random. +0.2 is a low draw of the same quantity (p = 0.08), not a subset property. |
| Full-grid Hindi penalty +2.2 [+0.6, +3.8] | **Reproduces** as Hindi CoT drop minus Hindi direct drop. See below for the Part B discrepancy. |

All 352 rows in `claims.csv`: 329 reproduced, 17 overclaimed, 1 differs, 3 unverifiable, 2 source missing. The arithmetic is very reliable. The problems are in wording and inference.

## Data existence

| Cited item | Exists | Count | Matches design |
|---|---|---|---|
| `experiments/2026-10-31_clp-analysis-rahul` (`numbers.json`, `analysis.md`) | **No**, absent from the tree and all refs (`git log --all` empty) | n/a | `source_missing`; everything recomputed |
| Script that built the document; "independent script" of A.1 | **No** | n/a | `unverifiable`; `verify.py` here is a separate reproduction, which does not verify the claim that another script existed |
| `responses/clp/*.json` | Yes | 1,350 per level, 6,750 | Yes; byte-identical to `experiments/2026-10-29_clp/outputs/*/results.json`; `errors.json` empty |
| `responses/standard/*.json` | Yes | 16,200 per level, 81,000; 27,000 on the subset | Yes |
| `responses/en-cot/*.json`, `responses/hinglish/*.json` | Yes | 6,750; 13,500 | Yes |
| `dataset/` | Yes | 150 per task, level, language | Regenerated equal in 45 of 45 cells with `config/generator.cfg` (English files compared; Hindi replays the same draws) |
| Full-grid pipeline and `FINDINGS.md` | Yes | `outputs/data` pickles absent | "+2.2 [+0.6, +3.8]" confirmed from raw data and `outputs/full/numbers.json` |
| Question text and gold match | Yes | 6,750 of 6,750 CLP, 81,000 of 81,000 standard | Yes |
| Settings | Yes | 13,500 CLP requests: `sarvam-105b`, temperature 0, top_p 1, 4,096 tokens, reasoning off | Yes |

Answer extraction agrees with the pipeline on 40,499 of 40,500 responses. The one mismatch is a cut-off stage 2 that quotes the prompt; both versions score it wrong.

Run dates differ. In the two levels checked (short, very very long), standard responses span 2026-09-29 to 10-29, en-CoT is 10-28 and CLP is 10-29. The document does not mention this.

## Corrected results

### Accuracy (%) by distractor condition (`fig_data/new_headline_by_distractor.csv`)

| Condition | Pooled answered / strict | None | Time-related | Unrelated |
|---|---|---|---|---|
| English direct | 59.7 / 59.6 | 60.6 / 60.6 | 59.9 / 59.7 | 58.6 / 58.5 |
| English CoT | 88.9 / 86.0 | 89.3 / 86.6 | 88.1 / 84.0 | 89.2 / 87.3 |
| Hindi direct | 55.2 / 55.2 | 56.0 / 56.0 | 54.9 / 54.9 | 54.6 / 54.6 |
| Hindi CoT | 59.4 / 59.0 | 60.2 / 59.8 | 58.9 / 58.5 | 59.1 / 58.8 |
| Hindi CLP | 70.3 / 69.9 | 69.3 / 68.9 | 69.3 / 68.7 | 72.3 / 72.1 |
| Hindi en-CoT | 82.9 / 80.8 | 84.1 / 82.2 | 81.0 / 78.2 | 83.6 / 81.8 |

Unanswered responses: English CoT 221 (68, 107, 46 by none, time, unrelated), en-CoT 174, Hindi CoT 43, CLP 39 (12, 20, 7), English direct 7, Hindi direct 0. All are cut-offs.

### Contrasts (points)

| Contrast | Distractor | Answered [CI] | Strict [CI] | Discordant pairs | Tasks passing Holm |
|---|---|---|---|---|---|
| CLP − Hindi CoT | Pooled | +10.9 [+9.6, +12.3] | +10.9 [+9.5, +12.2] | 1,297 vs 562 | 9 up |
| | None | +9.0 [+6.8, +11.3] | +9.1 [+6.8, +11.3] | 416 vs 210 | 5 up |
| | Time-related | +10.4 [+8.3, +12.6] | +10.2 [+8.2, +12.4] | 422 vs 192 | 7 up |
| | Unrelated | +13.3 [+11.2, +15.4] | +13.3 [+11.2, +15.4] | 459 vs 160 | 6 up |
| CLP − Hindi direct | Pooled | +15.1 [+13.6, +16.7] | +14.7 [+13.2, +16.3] | 1,536 vs 535 | 7 up, 1 down |
| | None | +13.2 [+11.0, +15.4] | +12.8 [+10.7, +15.0] | 490 vs 198 | 7 up, 1 down |
| | Time-related | +14.4 [+12.3, +16.7] | +13.8 [+11.7, +16.0] | 500 vs 188 | 7 up, 1 down |
| | Unrelated | +17.7 [+15.6, +19.9] | +17.5 [+15.4, +19.6] | 546 vs 149 | 8 up |
| English CoT − CLP | Pooled | +18.6 [+17.2, +19.9] | +16.1 [+14.7, +17.4] | 1,366 vs 240 | 9 up |
| | None | +20.1 [+18.0, +22.1] | +17.7 [+15.7, +19.7] | 486 vs 72 | 9 up |
| | Time-related | +18.8 [+16.8, +20.8] | +15.2 [+13.2, +17.3] | 441 vs 77 | 8 up |
| | Unrelated | +16.8 [+14.8, +18.8] | +15.2 [+13.2, +17.2] | 439 vs 91 | 8 up |

The pair counts 1,297 and 562 are exact, over 6,668 pairs where both answered. CIs barely change with a bootstrap stratified by task and level ([+9.7, +12.2]) or clustered on task and question ID across levels ([+9.6, +12.3]). Same-numbered questions across levels are not duplicates: mean correlation of outcomes is 0.00 to 0.02, and anchors are never the same at all five levels.

"Better on all nine tasks" is a pooled result. The direction is positive in all conditions, but in any one distractor condition only 5 to 7 tasks pass Holm. That loss is power, not a reversal.

### The gap across difficulty

| Change, short to very very long | Answered | Strict | Log-odds gap (answered) |
|---|---|---|---|
| English CoT − CLP | +5.4 [+0.9, +9.8] | +2.2 [−2.2, +6.4] | 1.39 → 1.11, change −0.28 [−0.60, +0.01] |
| English CoT − Hindi CoT | +11.4 [+6.8, +16.2] | +7.9 [+3.5, +12.6] | 1.79 → 1.66, change −0.13 [−0.44, +0.17] |
| CLP − Hindi CoT | +6.0 [+1.8, +10.2] | +5.8 [+1.6, +10.0] | 0.39 → 0.55, change +0.16 [−0.03, +0.34] |

By distractor, English CoT − CLP changes by +4.8 [−1.8, +11.2] (none), +3.2 [−3.1, +9.5] (time-related) and +8.3 [+2.1, +14.4] (unrelated). Say that the CLP gain over Hindi CoT grows in points with difficulty. Do not say the distance to English grows without giving the scale. The answered-only figure also drops English CoT's 221 cut-offs, which is why it exceeds the strict one.

### Stage 1 and stage 2 (date tasks, `fig_data/table_a3_stage1_stage2.csv`)

Table A3 reproduces exactly: 1,414 / 826 / 2,240; 97.5 / 20.1 / 69.0; 97.6 / 55.7 / 82.1; 461 of 695.

**Our read of 40 random stage-1 texts** (`sample_stage1.py`, seed 20261031; labels in `hand_check_stage1.csv`; one reader, not blinded):

- The last date equals the date stage 1 concludes in 38 of 40: **95.0% [83.5, 98.6]** (Wilson). Both misses are trailing notes.
- The gold / not-gold bin is right in 39 of 40: 97.5% [87.1, 99.6]. The one wrong bin (`very_long/date_addition/33`) moves a true gold conclusion into "other", which inflates "recovery".
- 40 of 40 state a conclusion: 100% [91.2, 100].
- Blind spots seen in extra samples: `DD-MM-YYYY` is not read, and a month-length rhyme produced "30 September".

The document's "correct in all 12" cannot be checked because the 12 are not identified. Our estimate is a little lower, and the error does not threaten the table.

**Sensitivity of 20.1%.** Treating the 43 responses with gold written but not last as gold gives 17.9%. Of 20 sampled recoveries, 18 are genuine ([69.9, 97.2]): stage 1 concludes a wrong date and stage 2 recomputes it. The 31 responses with no stage-1 date are 77.4% correct; of 12 we read, 9 are plain restatements.

**Control for shared difficulty** (`numbers.json`, `A3_controlled`):

| Measure | Stage 2 given stage 1 gold vs not | Negative control: en-CoT on same question and distractor |
|---|---|---|
| Raw risk difference | +77.4 | +19.9 (94.2 vs 74.3) |
| Mantel-Haenszel, task × level | +62.3; OR 64.8 [41.6, 100.9] | +7.2; OR 1.86 [1.31, 2.64] |
| Within question (fixed effects, 253 questions whose stage 1 varies across distractors) | +62.5 [+57.1, +68.0]; 95.5 vs 29.4 | 86.7 vs 79.8 |

Difficulty explains about 7 points of task-adjusted dependence. English CoT shows +2.1 and Hindi CoT +6.4 on the same adjustment. Stage 1 correctness and stage 2 correctness do share difficulty, but that does not explain the table. It remains observational: within a question, the distractor changes both stages.

By task: stage 2 given gold vs other is 99.5 / 49.5 (addition), 96.5 / 37.2 (subtraction), 92.9 / 11.6 (recurrence). By distractor: 96.3 / 22.1, 98.7 / 16.3, 97.6 / 22.2. The pattern holds in each.

The same pattern appears on tasks the document excludes, using a cruder "gold string appears in stage 1" test (`fig_data/new_gold_in_stage1_by_task.csv`): time addition 93.5 vs 53.1, time subtraction 95.4 vs 51.6, time duration 94.4 vs 48.4, date duration 94.8 vs 56.1, interval date 86.2 vs 4.3.

### Distractors under CLP

Table A4 reproduces. Additions:

- **Time-related:** CLP drop −0.07, 95% [−2.09, +1.87], 90% [−1.77, +1.62]. Strict +0.18 [−1.87, +2.13]. By task, none passes Holm, with the two hardest highest: recurrence +4.4 [−2.0, +10.7], day of week +5.4 [−3.2, +14.0] (`fig_data/new_clp_time_drop_by_task.csv`).
- **"Neither English CoT nor Hindi CoT shows a significant drop"** is answered-only. Strict English CoT is +2.67 [+1.07, +4.22], from more cut-offs. Strict Hindi CoT is +1.29 [−0.84, +3.47].
- **Difference in time-related drop:** CLP − Hindi CoT −1.4 [−4.6, +1.6]. CLP − en-CoT −3.2 [−6.0, −0.6]. The data support "no more vulnerable than Hindi CoT", not "less".

**Unrelated gain.** CLP goes from 69.3 to 72.3; flips are 294 wrong-to-right vs 224 right-to-wrong (p = 0.0024).

| Test | Result |
|---|---|
| Holm over Table A4's ten drops | p = 0.024; the only one of the ten to pass |
| Bootstrap over the 45 task-sentence clusters | +3.14 [+1.27, +5.16] |
| Sign-flip by sentence | p = 0.003; 32 of 43 non-zero sentences up |
| Single sentence after Holm | none of 45 pass |
| By task after Holm | only recurrence, +11.7 [+3.9, +19.1], 65 vs 36, p_holm = 0.046 |
| Leaving recurrence out | +2.0 [−0.0, +4.1]; other removals give +2.6 to +3.8 |
| Accuracy change, other conditions | en-CoT −0.6, English CoT −0.2, Hindi CoT −1.2, Hinglish −0.6 (65.8 → 65.2) |

It survives multiplicity and sentence clustering, so it is unlikely to be noise in this sample. It is also post hoc, one model and prompt, and cannot be re-tested on the other 100 questions without new runs. Report it as exploratory.

**Candidate explanation.** The gain arises in stage 1. On date tasks stage 1's last-date accuracy rises from 60.5 to 67.3 and stage 2 from 67.1 to 73.1; on recurrence stage 1 goes from 11.6 to 30.0. Stage 1 also changes style: it quotes Devanagari or says "translate" in 13.1% without a distractor, 21.1% with a time-related one and 47.1% with an unrelated one, and it dismisses the sentence explicitly in 0.8%, 9.2% and 33.3%. Median stage-1 tokens are 190, 249 and 281. Within question, this analysis mode is linked to +3.2 [+0.1, +6.4] points and reduces the gain from +3.14 to +2.03 [−0.31, +4.37], about 35% mediated. Time-related sentences raise the mode less, and our reading shows they also draw conversational replies ("The dates in February can indeed be confusing"), which may offset any benefit. This is observational and the mode was defined after looking at the data.

**Table A5 and net of chance.** All values reproduce, with one denominator mismatch: stage-1 rates and ORs reproduce only over all 2,250 responses (with unanswered as wrong for the OR), while the caption says answered responses. The difference is at most 0.1 point on rates and 0.01 on ORs.

Is subtraction valid for CLP given the both-language rule? Largely yes (`fig_data/table_a5_mentions_by_rule.csv`):

| Reasoning | Rate / placebo time-related | Paired net [CI] | Excluding every placebo word | Rate / placebo unrelated | Paired net [CI] | Excluding every placebo word |
|---|---|---|---|---|---|---|
| English CoT | 17.3 / 8.9 | +9.3 [+7.8, +10.8] | 9.1 | 11.0 / 6.3 | +4.9 [+3.9, +6.0] | 5.1 |
| Hindi CoT | 34.0 / 10.3 | +23.9 [+21.9, +25.5] | 24.2 | 28.7 / 1.9 | +26.9 [+25.1, +28.9] | 27.9 |
| CLP stage 1 | 62.8 / 9.3 | +53.4 [+51.3, +55.7] | 53.1 | 83.7 / 2.7 | +81.0 [+79.4, +82.6] | 83.4 |
| CLP stage 2 | 17.2 / 9.7 | +7.4 [+5.8, +8.6] | 7.9 | 8.7 / 2.3 | +6.5 [+5.2, +7.7] | 6.8 |
| en-CoT | 22.0 / 9.3 | +13.1 [+11.5, +14.8] | 14.1 | 17.0 / 5.5 | +11.6 [+10.6, +13.2] | 12.2 |

The paired-net CIs use 300 of the bootstrap draws, so their endpoints are a little noisier than the others.

- Hindi words have 0.0% placebo in CLP stage 2 and add at most 0.1 point to it, so counting both languages does not inflate CLP's rate. Hindi CoT is unchanged by adding English words (34.0 either way).
- Placebo hits are ordinary words in both arms: `february`, `calendar`, `break`, `number`, `need`, `can`. They fire about equally with and without the sentence (`fig_data/new_mention_top_words.csv`). The stoplist is asymmetric: `चाहिए` is stopped but `need` is not, which raises English unrelated placebos (6.3 vs 1.9).
- Hand check of 30 stage-2 matches: precision 8 of 15 time-related (53% [30, 75]), 12 of 15 unrelated (80% [55, 93]). That implies roughly 9.2 and 7.0 true mentions, consistent with the net rates.
- Under independence the adjusted excess is slightly larger: 8.3 and 6.6.

The caveat is causal. Paired net mention for stage 2 versus en-CoT differs by −5.9 [−8.0, −3.7] (time-related) and −5.4 [−7.3, −3.5] (unrelated). en-CoT versus Hindi CoT differs by −10.5 and −15.3. So about two thirds of the fall from Hindi CoT to stage 2 needs no understanding turn.

The confirmed stage-2 mentions differ by type. Of the 12 unrelated ones we read, about two thirds dismiss the sentence as irrelevant. Of the 8 time-related ones, most engage with it: two answer it as a side question, and two use it as a premise (`22nd` as a weekday anchor, the kitchen clock as a time). This is a small sample, but it means "stage 2 seldom uses it" is less safe for time-related sentences. Raw accuracy with a time-related mention is 54.6 vs 72.4 without, and that gap vanishes within task and level (OR 1.00), because matches concentrate in recurrence and day of week.

**Reuse.** Hindi direct 12.6 vs 3.8 and CLP 2.6 vs 3.1 (p = 0.82) reproduce. Hindi CoT is 3.2 vs 2.8 (p = 0.84), English direct 4.9 vs 3.9, en-CoT 2.0 vs 1.4. Borrowing belongs to Hindi direct answering.

### Does CLP fail like English?

Table A6 reproduces. The problems are in the measure. φ is undefined in 10 of 45 cells, all with English CoT at 100%, mostly easy date addition and duration cells. The median then runs over a selected set, and φ is capped by unequal marginals. Measures over all cells (`fig_data/table_a6_agreement_all_cells.csv`, `fig_data/new_agreement_vs_self.csv`):

| Pair | Median φ | MH OR, task × level [CI] | Within-cell r [CI] | Both wrong, observed / expected under independence [CI] |
|---|---|---|---|---|
| Hindi direct, English direct | 0.28 | 4.39 [3.74, 5.15] | 0.286 [0.25, 0.32] | 2,138 / 1,864 = 1.15 [1.13, 1.16] |
| Hindi CoT, English CoT | 0.07 | 1.61 [1.27, 2.03] | 0.052 [0.03, 0.08] | 557 / 522 = 1.07 [1.03, 1.10] |
| CLP, English CoT | 0.10 | 1.58 [1.26, 1.96] | 0.066 [0.03, 0.10] | 479 / 439 = 1.09 [1.05, 1.14] |
| en-CoT, English CoT | 0.02 | 1.99 [1.63, 2.45] | 0.116 [0.08, 0.15] | 370 / 310 = 1.19 [1.13, 1.25] |

**Reliability ceiling.** Compare each condition with itself across distractor versions of the same question (`fig_data/new_self_agreement.csv`):

| Condition | MH OR [CI] | Within-cell r [CI] |
|---|---|---|
| English CoT | 1.58 [1.23, 2.03] | 0.080 [0.03, 0.13] |
| Hindi CoT | 1.74 [1.46, 2.00] | 0.104 [0.07, 0.13] |
| CLP | 1.63 [1.36, 1.90] | 0.085 [0.05, 0.11] |
| en-CoT | 1.48 [1.20, 1.79] | 0.076 [0.03, 0.11] |
| English direct | 6.34 [5.18, 7.39] | 0.383 [0.34, 0.41] |
| Hindi direct | 5.83 [4.76, 6.77] | 0.355 [0.31, 0.39] |

CLP agrees with English CoT (OR 1.58) as much as English CoT agrees with itself after one irrelevant sentence is added (OR 1.58). Disattenuated r is 0.80 for CLP, 0.57 for Hindi CoT and 0.78 for direct.

So "fails on different questions" fails as a claim about language. What the data show is that, within a task and level, which CoT response fails depends very little on the question: a small prompt change at temperature 0 reshuffles failures about as much as switching condition. Direct answers are more question-determined, and that explains the 0.28 vs 0.10 contrast. The association holds in each distractor condition (CLP vs English within-cell r 0.082, 0.091, 0.037), though we did not compute CIs for these splits.

**Error profile.**

- Off-by-one reproduces: 26.9 / 21.2 / 52.3. With equal task weights it is 31.4 / 23.5 / 49.1 (en-CoT 44.7). CLP lies between Hindi CoT and English CoT, closer to Hindi.
- By task (CLP / Hindi CoT / English CoT): date addition 56.4 / 34.8 / 93.3, subtraction 50.0 / 19.6 / 91.7, day of week 47.1 / 45.2 / 73.4, interval date 30.2 / 23.4 / 45.4, recurrence 4.1 / 3.2 / 38.2. On addition and subtraction CLP is close to the midpoint (`fig_data/new_off_by_one_by_task.csv`).
- It is stable across distractors: 27.6, 26.9, 26.2.
- When both are wrong, CLP gives the same wrong answer as English CoT in 23.3% (110 of 473) and as Hindi CoT in 22.6% (313 of 1,388). Not more Hindi-like on this measure.

**Task-specific failures.**

- Day after the right weekday: CLP 22.4 vs Hindi CoT 25.3, p = 0.20. en-CoT 24.0, English CoT 16.2.
- Backward recurrence: CLP 8.1 vs Hindi CoT 9.0, p = 0.58. en-CoT 8.3, English CoT 0.4.

"Shrink" is not established. Backward recurrence persists at the same rate under en-CoT, so it follows the Hindi question and not the reasoning language, as the mid report suspected about the template.

### The subset (first 50 of 150)

**Is it a random draw?** Effectively yes.

- `custom-generator.py` reseeds once per level (seed 9) and draws sequentially, discarding duplicates. Question IDs are acceptance order.
- Re-running the generator reproduces all 45 cells. Only 175 draws were rejected, 19 before question 50, concentrated in short `interval_date` (51) and short `day_of_week` (42). Those are the cells where later questions are most constrained by earlier ones.
- Parameters: 0 of 25 offset KS tests and 2 of 45 anchor-date KS tests have p < 0.05. One passes Bonferroni in its family (`very_long/date_recurrence`, median anchor 2030 vs 2028, p = 0.0005).
- Distractor sentences: 1 and 2 of 45 chi-square tests at p < 0.05.

**Accuracy, first 50 vs remaining 100** (`fig_data/new_subset_vs_rest_by_cell.csv`):

| Condition | First 50 | Full | First − rest [CI] | Random 50-per-cell draws, 95% | p |
|---|---|---|---|---|---|
| English direct | 59.68 | 58.99 | +1.03 [−1.05, +3.11] | 57.98 to 59.98 | 0.17 |
| English CoT | 88.88 | 88.51 | +0.56 [−0.58, +1.79] | 87.91 to 89.12 | 0.21 |
| Hindi direct | 55.17 | 54.74 | +0.65 [−1.59, +2.77] | 53.78 to 55.69 | 0.38 |
| Hindi CoT | 59.40 | 59.40 | 0.00 [−1.92, +1.90] | 58.60 to 60.27 | 1.00 |

- Across 180 task × level × condition cells: 5 at p < 0.05 (9 expected), 0 after Benjamini-Hochberg. Largest differences are −13.7 (Hindi direct, long time subtraction) and +13.0 (English direct, medium time duration). With 50 vs 100 questions, such gaps are expected.
- By task and level, the first − rest CIs we inspected include zero; `by_task` and `by_level` in `numbers.json` have all of them. English CoT date addition is closest to the edge (+1.33 [−0.02, +2.77]).
- Position trend per 100 questions: |z| ≤ 1.17 in every condition.

**The penalty** (`fig_data/new_subset_penalty.csv`, `fig_data/new_subset_random_draw_null.csv`):

| Hindi CoT penalty, time-related | Value [CI] |
|---|---|
| First 50 | +0.17 [−2.71, +3.02] |
| Remaining 100 | +3.24 [+1.36, +5.23] |
| Full grid | +2.21 [+0.60, +3.82] |
| First − rest | −3.07 [−6.57, +0.42] |
| Random 50-per-cell draws | mean +2.23, SD 1.18, 95% −0.05 to +4.57; first 50 at p = 0.08 |

The penalty's two parts move in opposite directions: Hindi CoT's drop is 1.33 vs 2.57 full grid (draw p = 0.18), and Hindi direct's is 1.16 vs 0.36. By task it ranges from −6.4 to +8.1 on the subset.

**The +2.2 figure and the Part B discrepancy** (`penalty_check.py`, `penalty_check.json`). The PDF's +2.2 is a difference-in-differences: Hindi CoT drop minus Hindi direct drop. It reproduces from raw data under each convention:

| Convention | Hindi CoT drop [CI] | Hindi direct drop [CI] | Penalty [CI] |
|---|---|---|---|
| Answered | +2.57 [+1.31, +3.82] | +0.36 [−0.65, +1.38] | +2.21 [+0.48, +3.84] |
| Strict | +2.59 [+1.38, +3.81] | +0.36 [−0.65, +1.38] | +2.24 [+0.52, +3.85] |
| Both answered | +2.47 [+1.24, +3.70] | +0.36 [−0.65, +1.38] | +2.12 [+0.39, +3.72] |

Part B's +2.59 [+1.38, +3.84] strict and +2.47 both-answered match the middle-left column, the Hindi CoT drop alone, to two decimals. So they most likely measure a different quantity, and neither figure is wrong as computed. This is inferred from the match, since we did not see Part B's code. Part B should check this. The paper should name which quantity it reports: "Hindi CoT loses 2.6 points" and "2.2 points more than direct answers" are both correct. The pipeline's own value is 2.21 [0.58, 3.83]. The lower bound ranges from about 0.4 to 0.6 across conventions and seeds, so print it as "about +0.5" or fix one seed and convention.

**Implications.**

1. Between-condition accuracy comparisons on the subset generalise well. Nothing suggests the 2,250 questions are easier or harder.
2. Distractor contrasts of 1 to 3 points do not. A difference-in-differences varies with SD 1.2 from subset choice alone, and +0.2, −1.2 and −0.1 are all compatible with a true Hindi CoT penalty of +2.2. The CLP penalty's interval [−4.0, +1.5] also carries this.
3. "Smaller on the subset" should be dropped. Write that the subset is too small to detect an effect of that size.
4. The full-grid penalty is itself modest: its lower bound is about +0.5, and it varies widely in sign across tasks.

### Stage-1 cut-offs and length, and CLP vs en-CoT (added analysis)

**Cut-offs.** Stage 1 hit 4,096 tokens in 68 of 6,750 (1.0%); by distractor 13, 20, 35; day of week has 25. In those, CLP is 55.0% answered (48.5% strict), 10 stage 2s are also cut off (vs 34 of the other 6,682), en-CoT is 66.2% and Hindi CoT 29.4%. Dropping them moves the CLP − Hindi CoT gain from +11.02 to +10.93 in the pairs used. Cut-offs do not drive the gain.

**Length.** Within task and level (`fig_data/new_gain_by_stage1_length.csv`):

| Stage-1 length tertile | Median tokens | CLP | Hindi CoT | en-CoT | CLP − Hindi CoT | CLP − en-CoT |
|---|---|---|---|---|---|---|
| Short | 128 | 69.6 | 62.2 | 83.0 | +7.7 | −12.5 |
| Middle | 231 | 69.0 | 56.9 | 83.1 | +12.2 | −13.0 |
| Long | 458 | 72.3 | 59.1 | 82.5 | +13.1 | −9.2 |

The within-cell slope is +3.27 points per log token [+1.73, +4.82] against Hindi CoT and +2.37 [+1.01, +3.88] against en-CoT. Length is an outcome of the response and rises with distractors, so this is description. The gain is not confined to long stage 1s.

**Stage 2 vs en-CoT, same questions** (`fig_data/new_stage2_vs_encot_by_task.csv`).

| Task | Median tokens stage 1 / stage 2 / en-CoT | Verification stage 2 / en-CoT | CLP / en-CoT accuracy |
|---|---|---|---|
| Date recurrence | 300 / 315 / 643 | 28.8 / 90.4 | 27.0 / 70.3 |
| Day of week | 352 / 454 / 718 | 28.0 / 58.0 | 31.8 / 52.5 |
| Interval date | 285 / 279 / 724 | 12.4 / 88.5 | 35.3 / 44.1 |
| Date addition | 199 / 223 / 247 | 39.2 / 58.8 | 92.7 / 95.7 |
| Time duration | 223 / 198 / 255 | 22.5 / 85.1 | 86.7 / 98.1 |
| All | 237 / 234 / 318 | 27.3 / 74.8 | 70.3 / 82.9 |

Stage 2 is shorter and checks itself far less than en-CoT. The largest accuracy gaps are on recurrence and day of week, where en-CoT writes long derivations. Interval date also has a long en-CoT derivation but a smaller gap.

On date tasks, conditioning on stage 1 (`fig_data/new_date_tasks_clp_vs_encot_by_stage1.csv`; n = 2,186): if stage 1 is right, CLP 97.6 vs en-CoT 94.2; if not, CLP 20.8 vs en-CoT 74.3. The total gap of +16.8 splits into +19.0 from stage-1-wrong responses and −2.2 from stage-1-right ones. Those questions are not hopeless, since en-CoT solves three quarters. Conditioning on a CLP outcome is not a clean counterfactual, but the size is hard to explain otherwise.

## Limitations

**What cannot be concluded from these data**

- Why stage 2 follows stage 1. There is no randomised stage-1 content; within a question, the distractor changes both stages.
- That the understanding turn removes distractor influence. No arm has the turn without English reasoning.
- That CLP is robust to distractors in general. The bound is about ±2 points, on one subset, with no power at task level (CIs of ±4 to ±9).
- That errors are language-specific or English-like. Agreement measures are limited by low self-agreement in every CoT condition.
- Any mechanism in the model. Wendler et al. and Zhao et al. study other models and internal states; we have only outputs.

**What was simply not run**

- CLP on the other 100 questions per cell, which would settle the penalty and retest the unrelated gain.
- A stage-1 arm that forbids solving, or a translation-only arm.
- Temperatures above 0, as in Qin et al., and CLSP voting.
- Repeated identical prompts, to separate API nondeterminism from prompt sensitivity. Until this exists, the reliability reading above cannot separate the two.
- CLP without our added language rule.
- CLP on English questions (a two-stage baseline), or other target languages.

**Threats the document does not mention**

- The source analysis and build script are missing, so provenance rests on this recomputation.
- Conditions were run on different dates. A provider-side model update cannot be ruled out, and the records hold no model snapshot beyond the name `sarvam-105b`.
- Answered-only accuracy compares different response sets. English CoT loses 3.3% of responses, and more under the time-related distractor. This raises English in gaps and hides its strict drop.
- CIs treat the distractor sentences as fixed. Only about 45 task-sentence combinations exist, so inference to new sentences is weaker. The one test we ran (cluster by sentence) barely changed the unrelated gain.
- Multiplicity is handled within tasks only. Nothing corrects across the many contrasts in Part A; Holm over Table A4 is our addition. The findings in this audit are also uncorrected unless stated.
- Stage-1 text has style leaks: about 21% echo the language rule, and some contain planning or loops ("Wait, I think I am overthinking this"), even with thinking off. These lengthen stage 1 and could affect stage 2.
- Stage 1's date reading is limited to date tasks, and it misses `DD-MM-YYYY`. Our hand checks had one reader, were not blinded, and used small samples.
- The Hindi template's ordinals ("1वीं") are a known oddity and may contribute to recurrence errors in all Hindi-question conditions. en-CoT recurrence is 44.8 at short and 63.4 at very very long, the reverse of the usual pattern, against 96.6 and 77.1 for English CoT.
- Exact string scoring barely matters: lenient parsing finds at most 5 format-only errors per condition (`format_only_wrong` in `numbers.json`).

## Design rationale from prior work

Full quotes and URLs are in `citations.md`.

**CLP as a condition.** Qin et al. designed CLP for this exact case: a non-English question, English reasoning, zero-shot. Using it is defensible. On GPT-3.5 and MGSM they report CLP 70.6 vs Native-CoT 51.0, En-CoT 57.8 and Translate-En 68.4. Our +10.9 over native CoT has the same sign and about half the size. **Our result reverses their ordering of CLP and En-CoT:** they have CLP +12.8 above En-CoT, we have en-CoT +12.6 above CLP. Model, task and settings all differ, so we cannot say which caused it. Any paper text should state this as a non-replication of ordering, and note that MGSM has no Hindi.

**Faithfulness to Qin et al.**

| Element | Qin et al. | Ours | Assessment |
|---|---|---|---|
| Stage 1 | "Please act as an expert in multi-lingual understanding in [Source Language Ls]. Request: [Given sentence X] Let's understand the task in [Target Language Lt] step-by-step!" | Same, plus "Write your entire response in English." | **Departure** not mentioned in A.8 |
| Stage 2 | "After understanding, you should act as an expert in [Target Task T] in [Target Language Lt]. Let's resolve the task you understand above step-by-step!" "Finally, you should format your answer as 'Answer: [num]'." | Same opening, plus an English-only rule and a task-specific format | Format change is necessary; the language rule is another departure |
| Conversation | Two turns | Two turns, verified in all records | Faithful |
| Shots | Zero-shot | Zero-shot | Faithful |
| Temperature | Paper: stage 1 selected from [0, 2], stage 2 from [0, 1], top-p 1. Code: stage 1 temperature 1, stage 2 temperature 0.2 | 0 and 0 | **Departure** |
| Target languages | CLP single target; CLSP votes across several | English only, no CLSP | Faithful to CLP; says nothing about CLSP's +6.1 |
| Model and task | GPT-3.5, MGSM arithmetic | Sarvam-105B, TRD temporal | Generalisation test, not a replication |

**Greedy decoding.** Temperature 0 matches TRD's stated setting ("Temperature was fixed at 0.0 to enforce deterministic behavior") and our main study, so it serves within-study comparison, and that is the right priority. The cost is that it departs from Qin et al.'s higher stage-1 temperature, which could yield more varied alignment. We cannot say how much that matters.

**Did Qin et al. intend stage 1 to solve?** Not as its purpose, but they saw it and did not treat it as failure. They say alignment prompting is "used to align representations between different languages". Yet they annotate 200 samples and list "Preliminary Solution" among seven strategies: "CLP starts preliminary mathematical operations based on comprehension. It may even provide answers during the alignment phase. However, the model's second stage may modify this answer, so it is not the final solution." It covers 54.0% of their samples, with CLP accuracy 61.11 vs Native-CoT 54.63. Our run differs in degree: 40 of 40 sampled date-task texts conclude, and only about 20% of stage-1-wrong answers end up correct. A.4's reading should cite this. The behaviour is known; the size of the anchoring is what we add. Our added "entire response" rule may push stage 1 toward a finished answer; this is untested.

**English reasoning.** Shi et al. find "intermediate reasoning steps in English consistently lead to competitive or better results than those written in the native language of the question". This supports en-CoT as a comparison and is consistent with both English-reasoning conditions beating Hindi CoT here.

**Cross-lingual prompting more broadly.** Huang et al. report that XLT "brings over 10 points of average improvement in arithmetic reasoning and open-domain question-answering tasks". Our +10.9 is of a similar size, on a different model and method.

**Why English helps.** Wendler et al. find that the "concept space" in Llama-2 "lies closer to English than to other languages"; Zhao et al. hypothesise that models convert inputs into English for task-solving. These motivate the question but are mechanistic results on other models. They do not show Sarvam-105B works this way. Use them as motivation only.

**Distractors.** TRD says "LLMs show varied responses to both similar and dissimilar insertions", and it disables CoT. So a gain with one insertion type in one condition is not out of line with its findings, and our CoT-distractor results extend what it measured rather than repeat it.

**Statistics.** Paired McNemar and Holm suit a paired design. φ is the weak choice: replace or supplement it with all-cell measures and a reliability baseline.

## Missing findings

All labelled **exploratory**.

1. **Stage-1 errors are costly compared with the same model without stage 1.** Date tasks, stage 1 not at gold, n = 775: CLP 20.8 vs en-CoT 74.3, gap 53.5 points. Within question, stage-1 correctness is linked to +62.5 [+57.1, +68.0] (n = 756 responses over 253 questions). en-CoT negative control: +6.9 points (no interval computed).
2. **CoT failures are prompt-sensitive.** Same condition across distractor versions: CLP MH OR 1.63 [1.36, 1.90], English CoT 1.58 [1.23, 2.03], against English direct 6.34 [5.18, 7.39] (n = 2,250 questions × 3 pairs). This reframes A.6.
3. **The unrelated gain is partly a stage-1 style shift.** Analysis mode 13.1% → 47.1% (n = 2,250 questions); gain +3.14 [+1.26, +5.09] falls to +2.03 [−0.31, +4.37], about 35% mediated, mode effect +3.24 [+0.12, +6.37].
4. **CLP is less affected than en-CoT by the time-related distractor.** Difference in drops −3.2 [−6.0, −0.6], n = 2,250 questions per arm; uncorrected. en-CoT strict drop +4.0 [+2.2, +5.8].
5. **Backward recurrence follows the Hindi question.** CLP 8.1 (n = 742), Hindi CoT 9.0 (n = 746), en-CoT 8.3 (n = 698), English CoT 0.4 (n = 702). CLP vs en-CoT: p = 0.92.
6. **Restatement-style stage 1 looks like what Qin et al. intended and does well.** No date in stage 1, n = 31: CLP 77.4, en-CoT 80.0, Hindi CoT 45.2, recurrence 70.6 (n = 17); no intervals computed. Very small and selected, but it is a cheap pointer to a no-solve arm.
7. **English CoT's distractor sensitivity is visible only under strict scoring.** Time-related drop +2.67 [+1.07, +4.22] vs +1.17 [−0.36, +2.62] answered; cut-offs 68 → 107, n = 2,250 per arm.
8. **The carry-over extends beyond date tasks.** Gold string in stage 1 vs not: time subtraction 95.4 vs 51.6 (n not = 91), time duration 94.4 vs 48.4 (n not = 126). Cruder measure, no CI.

## Suggested claims for the paper

1. **Strong.** On 2,250 Hindi questions, two-stage cross-lingual prompting scores 70.3% against 59.4% for Hindi CoT (+10.9 [+9.6, +12.3], McNemar 1,297 vs 562), and the gain holds without a distractor (+9.0 [+6.8, +11.3]), with time-related (+10.4 [+8.3, +12.6]) and unrelated ones (+13.3 [+11.2, +15.4]), and under strict scoring (+10.9).
2. **Strong.** CLP beats Hindi direct answers overall (+15.1 [+13.6, +16.7]) and on seven of nine tasks, but it is significantly worse on interval date (35.3 vs 46.8), with no significant difference on date subtraction.
3. **Strong.** English CoT stays ahead of CLP by +18.6 [+17.2, +19.9] answered and +16.1 [+14.7, +17.4] strict, and a single-turn English-reasoning prompt on the same Hindi questions beats CLP by +12.6 [+11.3, +13.9], reversing the order Qin et al. report for GPT-3.5 on MGSM.
4. **Strong.** On date tasks, stage 2 is right in 97.5% of responses when stage 1 ends at the gold date and 20.1% when it does not (n = 1,414, 826), and the association persists within the same question (+62.5 [+57.1, +68.0]) while en-CoT on those questions differs by about 7 points; the design remains observational.
5. **Moderate.** We detect no drop for CLP with a time-related distractor (−0.1, 90% CI [−1.8, +1.6]), and it is no more affected than Hindi CoT (difference −1.4 [−4.6, +1.6]), but the subset cannot resolve effects below about 2 points, including Hindi CoT's full-grid penalty relative to direct answers of +2.2 [+0.6, +3.8].
6. **Moderate.** CLP's stage-2 traces mention the distractor less than Hindi CoT traces net of placebo (+7.4 vs +23.9 time-related, +6.5 vs +26.9 unrelated), but about two thirds of that fall also appears in single-turn en-CoT (+13.1, +11.6), so it mainly reflects reasoning in English.
7. **Suggestive.** Which question a CoT response fails depends weakly on the question within a task and level: CLP and English CoT agree (MH OR 1.58 [1.26, 1.96]) about as much as English CoT agrees with itself across distractor versions (1.58 [1.23, 2.03]), against 6.34 for English direct answers.
8. **Suggestive.** CLP is more accurate with an unrelated distractor (+3.1 [+1.1, +5.1], Holm p = 0.024 over ten drops), led by date recurrence (+11.7 [+3.9, +19.1]) and partly accompanied by a shift to explicit translation in stage 1 (13.1% → 47.1%); this was found post hoc.
