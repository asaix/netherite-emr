# Baseline audit: FINDINGS.md and the mid-report RQ1/RQ2 results on the full grid

All numbers come from `verify.py`, which reads `responses/standard/`, `responses/ron/`, `dataset/` and the run folders. Accuracy differences are percentage points. "Answered" drops responses with no answer line. "Strict" counts them as wrong. Brackets are 95% cluster-bootstrap intervals over questions (B = 2000, my own seed, so bounds can differ from `numbers.json` by a few tenths). Stars mark Holm-corrected p < 0.05 over the nine tasks in a language, from a question-level paired t-test, not from McNemar.

## Verdict

| Mid-report or FINDINGS claim | Verdict on the full grid |
|---|---|
| CoT helps English far more than Hindi (+27.9 vs +5.1) | **Stands.** +29.5 vs +4.7 answered, +26.8 vs +4.2 strict, and true in all three distractor conditions. |
| CoT significantly hurts Hindi date subtraction and interval date | **Stands, and now shown directly.** With no distractor: -19.9 and -23.3. The mid-report's inference from a pooled table did not support this; the split does. |
| The gap under CoT widens with difficulty | **Stands.** 24.0 to 34.9 points over five levels. Its logit trend is not significant (OR 0.97 per level, p = 0.21), so the widening is on the points scale and depends on direct accuracy collapsing. |
| Time duration is the only task where Hindi gains at least as much as English | **Reverses when pooled** (English +35.3, Hindi +33.0). True with no distractor or an unrelated one; strongly false with a time-related one. |
| Distractors make CoT more fragile only in Hindi | **Weakens to not supported as a language difference.** The Hindi effect is small and fragile; the Hindi-minus-English interaction for time-related distractors is significant only on answered-only points. |
| Hindi recurrence problem is "one template cell" | **Overclaimed.** Mirror answers do sit at k = 1, but 75.6% of Hindi CoT recurrence errors are at k >= 3. |
| Whether Hindi CoT is right has almost nothing to do with whether English is right | **Weakens.** Median φ 0.06 reproduces, but failures do overlap (within-cell OR 0.64 [0.57, 0.73]). |
| Thinking mode removes the Hindi deficit | **Holds only at the 16k budget.** At a 4,096-token budget, strict accuracy for thinking on would be below thinking off in Hindi (43.8 vs 59.9, CoT). |
| Answer extraction | **Sound.** My independent extractor agrees on every graded response. The reverted parser bug changes 5 extracted strings and no score. |

## Data existence

| Item | Exists | Count | Matches design |
|---|---|---|---|
| `responses/standard/{5 levels}.json` | yes | 16,200 each, 81,000 total | yes; 6,750 questions, 12 records each |
| The 5 completed run folders in FINDINGS | yes | 16,200 each | identical to `responses/standard/` on every record compared (`integrity.json`) |
| Early runs (`2026-09-29_*`, `2026-09-30_*`) | yes | 9,895, 9,475, 4,885, 15,989 | every record is unchanged in the final data |
| `2026-10-01_analysis-rahul/merged_results.json` | yes | 37,068 over 3,089 questions | exact subset, so the claim that mid-report data are unchanged holds |
| `responses/ron/`, `2026-10-25_test-reasoning-on` | yes | 5,400 over 450 questions (q0-9) | identical record by record; the `short` file is byte-identical |
| `dataset/` | yes | 150 per level x task x language | yes; no duplicate questions within a cell |
| `outputs/*/numbers.json`, `extra/tables/logit.tex` | yes | | |
| `outputs/data/*.pkl` | **no** | | Git-ignored and rebuildable; FINDINGS' rebuild steps depend on it |
| `2026-10-26_trace-deletion` | **no** | | The folder present is `2026-10-27_trace-deletion-selfhost`; the "still running" note is stale |

**The 5 filled-in questions.** Commit `d7e7bfe` added 5 responses, not 60: one Hindi response each in `very_very_long/time_addition/84`, `time_duration/73`, `time_duration/149`, `time_subtraction/2` and `time_subtraction/27`, all dated 29 Oct. Dropping the whole questions explains the earlier 80,940 count.

**Settings.** All 81,000 standard records have temperature 0, 4,096 max tokens, `reasoning_effort` null and an empty `reasoning_content`. No `<think` text appears.

**Run dates.** Responses span 29 Sep to 29 Oct, so model version is not controlled. Questions in the mid-report set were all run first, so "mid vs new" is confounded with run date as well as task and level. In the 8 language x condition cells that straddle two dates with at least 20 questions each, the mean difference is -0.6 and the mean absolute difference 3.8 points (`fig_data/run_date_drift_check.csv`). That shows no systematic drift, on thin evidence.

## Corrected results

### Answer extraction

I wrote a separate extractor and a typed comparison that accepts other date formats, 12-hour suffixes, units and Hindi weekday synonyms (`common.py`), then compared it with the project's regex on all 81,000 responses. I copied the three regex versions into `build_frame.py` so they could be compared without importing project code.

- **Agreement.** On all 80,172 graded responses the two give the same score. No correct answer is being lost to strict string matching.
- **Format compliance.** Only 2 of 80,172 extracted answers break the expected format. No answer uses `बृहस्पतिवार` or `इतवार`, so the Hindi weekday-synonym risk does not arise.
- **Hand reading.** I read 60 mismatch or edge cases per language (`hand_review/judgements.md`). This was done by the auditing agent, not a human annotator. 112 of 120 were plainly correct and the other 8 are covered below; none changes a conclusion.
- **Five scored cut-offs.** 832 responses hit the token limit. 827 have no answer line, and 5 have an `Answer:` line written before the cut-off and are graded (4 count as correct, all English CoT). One further response finished normally with `उत्तर (Answer): मंगलवार`, which both extractors miss; it is wrong anyway. So "828 cut off" is really 827 cut off plus 1 missed, and `cutoff_all_length` is false in `numbers.json`. The effect is at most 5 of 20,250 responses in a cell.
- **12-hour times.** 185 time answers are exactly 12 hours off. None has an AM/PM suffix, and hand reading shows arithmetic slips or start times read as PM. Accepting them would add 0.3 to 1.5 points per cell (`results_secondary.json`, `twelve_hour`).

**The reverted parser bug.** The 25 Oct regex let `\s*` after `उत्तर है:` cross a newline, so `उत्तर है:\nAnswer: सोमवार` was captured as the string `Answer: सोमवार`, which then fails the comparison. I confirm it changes the extracted text of exactly 5 Hindi CoT responses, 1 of which the mid-report parser also misread. All 5 are wrong under the fixed parser too, because the model's actual answer differs from gold, so **no score changes**. The paper does not depend on an unfixed bug affecting results. The fix should still be restored on root: the bug would silently lose a correct answer on any new run where the model writes that pattern, including the other conditions, which I did not check.

### RQ1: does CoT help, by language and difficulty?

{{T_OVERALL}}

Per task, answered-only, split by distractor (`fig_data/fig_cot_delta_task_split.csv`; strict values are in the same file):

{{T_TASK}}

Per level, answered-only:

{{T_LEVEL}}

Hindi CoT is significantly below direct in 15 of 45 task x level cells when pooled and 12 of 45 with no distractor; English in none (`fig_data/fig_cot_delta_heatmap.csv`). These are uncorrected bootstrap intervals over 45 cells.

Answered-only flatters English: excluding 651 English CoT cut-offs raises its CoT accuracy by 2.9 points. McNemar treats the 3 responses per question as independent. Question-level tests agree on every headline, but McNemar's p-values are too small and should not be quoted as exact for the pooled rows.

**Direct is not fully direct.** 4.1% of English and 7.2% of Hindi direct responses have over 12 words, reaching 28% in Hindi interval date and 24% in English recurrence. Against compliant direct responses alone, the deltas barely move (+29.6 and +4.3), so this does not change RQ1.

### The evaluator's pooling criticism

The mid-report sentence "this happens without any distractor, since the table pools all three distractor conditions" does not follow: a pooled table cannot show what happens in one condition. The correct statement, on the full grid:

> With no distractor, Hindi CoT lowers accuracy on date subtraction (-19.9 [-23.5, -16.3]) and interval date (-23.3 [-27.5, -19.0]); both remain significantly negative with a time-related and an unrelated distractor.

The earlier merged-data split of Hindi CoT gain, +7.8/+2.6/+5.0, becomes **+5.6 / +3.4 / +5.0** (none, time-related, unrelated). Strict: +5.1 / +2.9 / +4.7.

English-Hindi gap, all tasks:

{{T_GAP}}

The gap under CoT holds in every condition (28.0, 29.7, 29.7 points), so the pooled statement is not an artefact.

Difference in CoT gain (English gain minus Hindi gain), answered-only:

{{T_GAIN}}

**Which conclusions change sign or significance:**

- **Time duration gain gap changes sign:** -5.2 none, +14.5 time-related, -2.2 unrelated. This is the one task-level conclusion that reverses. Pooled, it is +2.3 and not significant.
- **Hindi time addition** changes sign (+0.4, -0.1, +1.1), but it is null in all three.
- **Hindi date addition** is significant only when pooled; no single condition survives Holm.
- **Hindi day of week** loses Holm significance with a time-related distractor (+4.7, Holm p = 0.07).
- **English interval date** ranges from +4.0 (n.s.) to +17.0. Under strict scoring with no distractor it is not significant after Holm (+5.1, Holm p = 0.06).
- **Hindi at the short level:** the headline "CoT starts significantly harmful at short" (-4.3) is **not significant with no distractor** (-1.9 [-4.5, +0.8]). It comes from -6.2 and -4.7 in the distractor conditions.
- **Hindi date duration at short and medium** reverses in the cells: +6.7 and +8.7 with no distractor, against -12.0 and -6.0 time-related and -7.3 and -9.3 unrelated. The pooled "date duration short is significantly negative" in FINDINGS is a distractor effect.
- At task x level, 8 Hindi and 2 English cells change sign across conditions. Only one has significant effects in opposite directions (Hindi date duration, medium).

### RQ2: does CoT make distractors more harmful?

{{T_PEN_ALL}}

Penalty by level:

{{T_PEN_LEVEL}}

Time-related penalty by task, answered-only (a positive drop means the distractor hurt):

{{T_TASK_PEN}}

**Does "more fragile only in Hindi" hold? No, not as stated.**

| Test of Hindi minus English, time-related | Estimate | Result |
|---|---|---|
| Points, answered, question bootstrap | +2.6 [+0.5, +4.7], p = 0.022 | significant |
| Points, strict | +1.4 [-0.7, +3.6], p = 0.19 | not significant |
| Logit ratio, task + level FE, answered | 0.92 [0.79, 1.08], p = 0.33 | not significant |
| Logit ratio, cell FE, answered | 0.89 [0.75, 1.06], p = 0.18 | not significant |
| Logit ratio, cell FE, strict | 1.02 [0.86, 1.20], p = 0.85 | not significant |
| Logit ratio, cell FE, answered, recurrence removed | 0.81 [0.67, 0.97], p = 0.020 | significant |
| Treating the 45 task-sentence units as the sample, strict | +1.4 [-2.1, +4.9] | not significant |

So the Hindi penalty is significant and the English one is not, but the difference between them depends on the scale and on how cut-offs and recurrence are handled. Significant in one language and not the other does not establish an interaction. Under strict logit, English is significant too (OR 0.85 [0.75, 0.97]), which removes "only in Hindi". My regression reproduces `extra/tables/logit.tex` to two decimals. Its answered-only values are 0.87 [0.78, 0.97] in Hindi and 0.98 [0.85, 1.12] in English (cell FE).

**Unrelated distractor.** Hindi minus English is +2.6 answered and +2.8 [+0.7, +5.0] strict, p = 0.007, with logit ratios of 0.81 to 0.84 (p = 0.009 to 0.052). It also holds across sentences (+2.8 [+0.4, +5.3]). This is the more robust interaction, but its source is the opposite of the hypothesis: English direct falls about 2 points while English CoT does not, and the Hindi penalty is null (+0.7, +0.4 strict).

**The penalty is partly a direct-answer effect.** It is a difference of drops, so changes in direct answers count too. In time duration, Hindi direct **rises** 7.3 points with a time-related distractor and English direct falls 7.3. So 7.3 of the Hindi +11.5 and 7.3 of the English -8.1 ("CoT protects") come from direct answers. Only Hindi date duration (+8.8, direct -1.7, CoT +7.1) is a clear CoT-side effect among the Holm survivors. Only 2 Hindi tasks survive Holm (date duration, time duration), against FINDINGS' 4 starred, which use uncorrected intervals.

**Simpson's paradox.** There is no reversal in the penalty. The grid is balanced, so the pooled value is close to the mean of cells (Hindi +2.2 vs a cell mean of +2.2; 29 of 45 cells positive, 15 negative). The issue is heterogeneity: Hindi task values run from -4.5 to +11.5. True Simpson reversals do exist elsewhere, and the mid-report is right about them: Hindi drift (36.7% vs 59.9% pooled, OR 2.08 within cell) and English verification (87.5% vs 95.2% pooled, OR 1.28 within cell). The odds ratio is not collapsible, which Simpson's example also turns on according to a secondary source (`citations.md`), so ORs and points need not agree when English sits near ceiling.

**Leave-one-sentence-out (`fig_data/rq2_loso.csv`).**

| Quantity | Full | Range over dropping any one of 45 sentences | Worst CI |
|---|---|---|---|
| Hindi, time-related, answered | +2.2 | +1.8 to +2.6 | excludes 0 throughout; lowest bound +0.11 |
| Hindi, time-related, strict | +2.2 | +1.8 to +2.6 | excludes 0 throughout; lowest bound +0.17 |
| English, time-related, answered | -0.3 | -0.9 to +0.1 | includes 0 throughout |
| English, time-related, strict | +0.8 | -0.4 to +1.2 | includes 0 throughout |
| Hindi, unrelated, answered | +0.7 | +0.4 to +1.0 | includes 0 throughout |
| English, unrelated, answered | -1.9 | -2.3 to -1.3 | excludes 0 throughout |

No single sentence decides the pooled sign. But **the Hindi recurrence penalty is one sentence**: without "The last time I had a weekly commitment was in January" it falls from +4.5 to +0.3 [-4.6, +4.9].

That sentence is also the cut-off phenomenon, confirmed: 92 of 134 English CoT responses hit the limit (91 ungraded), against 0 of 134 in Hindi. Reading the traces, the model tries to reconcile "weekly" with "every N days", so the sentence competes with the question's premise and is not irrelevant in the GSM-IC sense. English recurrence penalty goes from +8.4 answered to +18.8 strict because of it, and even without it stays +8.5 and +9.9. "Dates in February always confuse me a bit" gives English +20.1 [+11.3, +28.5].

Treating sentences as the sample matters for generalising. Across 45 task-sentence units the Hindi time-related mean is +2.3 [-0.1, +4.6], t-test p = 0.07, so the result is about these sentences and may not extend to new ones.

### Mention, reuse, drift, verification, lengths and failure overlap

All FINDINGS values reproduce: mention 17.4% (placebo 9.9), 33.8% (10.1), 11.5% (5.9), 30.4% (1.9); MH ORs 0.92, 0.84, 1.12, 1.13 and my own MH implementation matches statsmodels. Question-clustered intervals are close to the standard ones (Hindi time-related 0.84 [0.73, 0.96]).

**The mention measure has an English false-positive problem.** In a hand-read sample, 9 of 15 English unrelated hits were `need` or `can` ("I need to find..." against "Solar panels need sunlight"), so English precision was 6 of 15, against 15 of 15 in Hindi. Restricting to distractor words with under 2% placebo hits gives near-zero placebos and these rates (exploratory):

| | Rate | Placebo | OR, correct given mention |
|---|---|---|---|
| English, time-related | 8.5% | 0.2% | **0.57 [0.38, 0.85]** |
| English, unrelated | 5.7% | 0.1% | 1.30 [0.62, 2.70] |
| Hindi, time-related | 25.0% | 0.2% | 0.77 [0.67, 0.89] |
| Hindi, unrelated | 29.6% | 0.0% | 1.15 [1.00, 1.33] |

This undercuts "The mid-report English result was most likely noise": on the cleaner measure English time-related mention goes with lower accuracy, as in the mid report (0.64). The Hindi-English contrast in uptake gets larger, not smaller.

**Mention is not uptake.** Of 15 hand-read Hindi unrelated mentions, 10 dismiss the distractor as irrelevant, 3 restate the prompt and 2 use it. The mid-report's "often build the distractor into the narrative" is true of some traces but not the typical one for unrelated sentences. Hindi time-related mentions engage more often: a rough cue-word split puts 11% of them as dismissals, against 58% for unrelated. That split is not validated.

**Reuse.** 11.3% vs 4.1% in Hindi direct (p < 0.001) and 6.1% vs 3.4% in English direct (p = 0.004) reproduce, so "In English the two rates do not differ" no longer holds. 78% of Hindi direct reuse comes from three date-recurrence sentences naming February or January, so this is a recurrence-with-month effect. Fisher's test ignores the clustering of responses within questions.

**Drift.** TLR 0.988, 2.14% below 0.9 (431 traces), OR 2.08 [1.66, 2.60], cluster CI [1.69, 2.61]. 82.8% of drifting traces are day of week, and only that task and recurrence have enough cases (OR 2.36, 1.49). The result is observational: a trace that drifts may differ in other ways. It holds in each distractor condition (OR 2.39, 1.67, 2.10).

**Verification and length.** 86.8% vs 1.48%; a broader Hindi cue list only raises Hindi to 3.5%, so missed phrasing does not explain the gap. English OR 1.28 [1.01, 1.62] is borderline, p = 0.037, and not significant on new questions alone (1.26, p = 0.13). Medians of 107 and 83 words, 356 and 213 tokens reproduce.

**φ.** Median 0.28 (direct) and 0.06 (CoT) reproduce, but φ is capped by the marginals when English is near 90%. φ/φmax is 0.36 vs 0.16. Within-cell, English being wrong lowers the odds of Hindi being right (OR 0.64 [0.57, 0.73] under CoT, 0.23 under direct). Pooled, Hindi is wrong 77.2% of the time when English is wrong and 34.5% when English is right. Question-level correlation is 0.11, positive in 30 of 42 cells. Correct wording: failure overlap is much weaker under CoT than direct, and most Hindi CoT failures occur where English is right (5,947 of 7,657), but it isn't zero.

### Recurrence by k

Values reproduce (`fig_data/recurrence_by_k.csv`): k = 1 mirror 64% and 66% in Hindi, 6% and 2% in English; k = 2 first-step 86% and 54% in Hindi, 92% and 0.3% in English. 90% of Hindi CoT mirror answers are at k = 1.

The heading "one template cell" and the sentence "pins the wording concern to the ordinals" go too far:

- It is at least two different patterns, and k = 2 first-step under **direct** is equally common in English (92%), so that cell isn't a Hindi template effect.
- Only 24% of Hindi CoT recurrence errors are at k = 1 or 2. Hindi CoT accuracy at k >= 3 is 18.1% against 85.6% in English, so most of the deficit lies outside those cells.
- `{occurrence}वीं` is used at every k, and English has its own non-ordinal "the 1 occurrence". The mid-report timeline planned a rewording test. I did not check whether it was run elsewhere, and nothing in FINDINGS tests it, so the cause remains untested here.

External support: TRD's Tables 6 and 7 show Hindi recurrence at 0.00 to 0.36 for every model listed, against up to 0.82 in English for the same model, consistent with a template problem.

### Thinking on vs off

Matched on 450 questions and 5,400 pairs (`results_ron.json`, `fig_data/fig_thinking_budget.csv`).

| | Off, answered | On, answered | On - off | Off, strict | On, strict | On at 4,096 tokens, strict |
|---|---|---|---|---|---|---|
| English direct | 64.2 | 97.9 | +33.7 [+30.1, +37.6] | 63.1 | 95.3 | 77.1 |
| English CoT | 91.4 | 98.9 | +7.5 [+5.6, +9.6] | 87.3 | 92.7 | 68.3 |
| Hindi direct | 59.2 | 94.9 | +35.7 [+32.0, +39.9] | 57.9 | 90.9 | 33.6 |
| Hindi CoT | 64.1 | 97.9 | +33.8 [+30.4, +37.4] | 59.9 | 89.9 | 43.8 |

**The token budget is a large confound.** Thinking-on had 16,000 tokens against 4,096. 65% of Hindi direct and 56% of Hindi CoT responses used more than 4,096, against 22% and 31% in English. Treating those as failures, thinking on would be 24 points **below** thinking off in Hindi direct and 16 below in Hindi CoT. The simulation assumes deterministic output up to the limit, and it is a lower bound on a real 4k run only in that sense. Median completion tokens: 5,206 on vs 25 off (Hindi direct).

**Script share.** Hidden Hindi traces have 3.6% to 4% Devanagari words (direct) and 21% to 27% (CoT), depending on pooling and denominator; FINDINGS' 25% and 27% differ for that reason. Visible Hindi CoT stays 99.9% Hindi.

**What can be stated safely:** on a 10-per-cell pilot with `reasoning_effort: low` and a 16k budget, thinking on raises Hindi CoT from 64.1% to 97.9% and closes the CoT gap from 27.3 to 1.0 points answered-only (strict: 27.4 to 2.7), and the hidden trace is mostly English. **Not safe:** that thinking removes the deficit at equal cost, that English reasoning is the cause (language and thinking were not varied separately), or that distractor penalties vanish (intervals of about ±4 points, and the matching thinking-off subset also lacks the full-grid penalty). The q0-9 subset runs about 1 to 4 points above q10-149 in thinking-off accuracy.

### Distractor pool

- **Size.** 35 unique time-related and 43 unique unrelated sentence pairs (mid-report value confirmed), five per task. Addition and subtraction share time-related lists for both dates and times; two unrelated sentences recur across tasks. English and Hindi sentences map one-to-one, and each question uses the same index in both languages (verified on all 6,750).
- **Assignment.** `random.choice` per question, one draw of each type per question. It is **not balanced**: task x time-related sentence counts range from 116 to 191 of 750 (χ² p < 0.001); unrelated from 127 to 177 (p = 0.003). Sim x unrelated index is also not independent (p < 0.001). The generator resets the seed at each level, and the time tasks get nearly the same sentence mix at every level (time subtraction is close to [39, 25, 32, 32, 22] at four of five levels), so more levels add little independent sentence sampling. Within a level, the two tests I ran (task x time-related sentence, time-related x unrelated index) show no imbalance (p > 0.17). I did not find the cause of the pooled sim x unrelated dependence; the repeated seed is the likely one.
- **Hindi equivalence.** Not equivalent. Hindi time-related sentences average 0.81 of the English word count and often drop content: "My scheduling app keeps crashing when I try to set this up" becomes "My scheduling app crashes"; "I wonder if counting backwards with dates is harder than forwards" becomes the direct question `क्या उल्टा गिनना कठिन है?`. Three English statements become Hindi questions, which plausibly invites an answer (hand-read Hindi traces do answer "will it be sunny?"). This is a threat to any English-Hindi penalty comparison and was not back-translated by a human.
- **"Unrelated" is not always unrelated.** "The museum opens at nine", "The library closes at 8 PM", "Sunflowers grew tall this year" and "The sky looks blue today" carry time content (`fig_data/distractor_pool.csv`).

### Dataset validity

- **Gold answers.** I computed every gold answer in both languages with Python `datetime` from the parsed question: **13,500 of 13,500 match**, including the requested 30 per task (`fig_data/gold_spotcheck_30_per_task.csv`). Dates reach 2039 and leap days are correct. Only 4 questions involve 29 February.
- **Parallelism.** Parameters and gold agree across English and Hindi on all 6,750.
- **Difficulty differs from TRD's Table 5 for time tasks.** The paper says hours 1-4 at short through 32-64 at very very long, but the code draws `randint(0, hours_max)`. So hour offsets start near 0 at every level (h = 0 in 18% of short and 7% of long time-addition questions) and levels overlap heavily. For day of week and interval date, difficulty only widens the year range. Wrap-around grows with level (time addition 12% to 85%), so "difficulty" also means midnight crossing. Date ranges otherwise match Table 5.
- **Carrier phrases differ from the paper's Table 2** for duration and interval (the repo says "assuming Monday is the first day of the week", which removes the week-start ambiguity). Answers one day early (Sunday start) are still 14.5% of English CoT and 7.7% of Hindi CoT interval answers, and are correctly scored wrong under the stated convention.
- **Compared with TRD's results.** Its medium direct results are not directly comparable because of different models and prompts (`fig_data/trd_comparison_medium_direct.csv`). Sarvam direct at medium is 12% / 17% on day of week and 11% / 6% on recurrence (English / Hindi), far below Claude 3.5 Sonnet (100/94, 82/36) and close to the low-capacity models on recurrence. TRD's reasoning-accuracy decline with level also appears here (English 88 to 42, Hindi 80 to 37). TRD says memorisation stays stable across difficulty; here it **declines** (English 44 to 19, Hindi 45 to 19), so this departs from TRD. The decline comes from interval date, since day of week is near chance at every level.
- **TRD format convention.** TRD counts format errors as incorrect, so strict scoring is closer to the source than answered-only.

## Limitations

**Cannot be concluded from this design:**

- Anything causal about language. Hindi differs in script, tokenisation, template wording, sentence wording and training data together, and only Hindi and English are compared.
- Any general claim about CoT. There is one model, one prompt template, one seed, greedy decoding and no repeated runs.
- That sentences generalise. The 78 sentences are a fixed pool and treating them as fixed effects overstates certainty.
- That a trace reflects the computation behind the answer. Mention, drift and verification are observational and were assigned by the model itself, not by us.
- That the Hindi penalty is caused by CoT reasoning rather than wording. The Hindi sentences are shorter, three are questions, and direct-arm shifts contribute.

**Simply not run:**

- Rewording the Hindi recurrence template, a thinking-on run at a matched budget, repeat runs for model drift, human annotation of mention and verification, and human back-translation of the sentences.
- The trace-faithfulness measures in the mid report ("answers follow the trace") and `error_types` other than off-by-one were not fully recomputed in this audit (`claims.csv` marks them).

**Threats the documents do not mention:**

- The answered-only and strict columns can give different RQ2 conclusions, and FINDINGS' "distraction-penalty conclusions are unchanged" contradicts its own section 2.
- Runs span a month, confounded with the mid/new split.
- Sentence assignment is imbalanced and correlated across levels because of the seed reset.
- Multiple testing: FINDINGS' task and cell asterisks are uncorrected, and many analyses were chosen after seeing mid-report results.
- The refined mention filter here is data-driven and exploratory, and my hand-reading is one reader's judgement, not validated annotation.
- The McNemar and Fisher tests treat responses within a question as independent.

**Audit limits.** The Mantel-Haenszel, McNemar, Simpson and Holm full texts could not be read here (`citations.md`). `secondary.py` peaked at 4.5 GB, above the 3 GB guideline in the brief, and one earlier run of it died without output, most likely for memory reasons.

## Design rationale from prior work

Quotes and URLs are in `citations.md`.

| Design choice | Basis | Where we depart |
|---|---|---|
| Zero-shot CoT prompt | Kojima et al. 2022: no examples, only a trigger phrase | No "Let's think step by step", a language instruction instead, and a format line in one prompt rather than Kojima's two-stage extraction |
| Direct vs CoT contrast | Sprague et al. 2025: CoT mainly helps math and symbolic tasks, so date arithmetic should benefit. English fits; Hindi date subtraction does not | One model and language-specific; our direct prompt allows a value line and an answer line |
| CoT can hurt | Liu et al. 2025: in three of six human-inspired tasks CoT lowers performance | Different mechanism and tasks. The mid report's "models degrade in the same way" on six tasks overstates: the source says three, with mixed effects otherwise |
| One irrelevant sentence, related or unrelated | Shi et al. 2023a GSM-IC: one sentence that must not affect the solution; in-topic vs off-topic | We use TRD's sentences, without role-name or number-range factors. Some do affect interpretation ("weekly commitment"), breaking GSM-IC's rule, and placement is before the whole question |
| Resampling and distractor robustness | Mirzadeh et al. 2025: variance across instantiations, seemingly relevant clauses cost up to 65% | They do not contrast CoT on and off. Our sentence-level analysis follows their concern with variance, but each question has only one sentence draw |
| Paired tests | McNemar 1947 for correlated proportions; Dror et al. 2018 list it for paired binary outcomes | Assumes independent pairs, while we have 3 per question. Report question-level tests alongside |
| Cluster bootstrap | Berg-Kirkpatrick et al. 2012 use a paired bootstrap and caution about i.i.d. assumptions | They resample test items with b = 10^6; we resample questions as clusters with B = 2000. The cluster extension is ours |
| Stratified odds ratios | Mantel and Haenszel 1959 for stratified summary measures | Applied to observational trace features, not exposures; standard CIs ignore clustering, though a cluster bootstrap agrees here |
| Simpson check | Simpson 1951 | Full text not read; only metadata and a secondary description |
| Benchmark and scoring | TRD (Mazzia et al. 2026): "leaving the exploration of CoT's impact ... for future research"; format errors count as incorrect | Generator code differs from Table 5 on hours; answered-only departs from TRD's scoring, so report strict as well |

## Missing findings

All exploratory.

1. **One sentence drives a task-level result.** "The last time I had a weekly commitment was in January", date recurrence, n = 134 questions: English CoT cut-off 92 of 134 vs Hindi 0. Hindi penalty +23.1 [+15.7, +31.2] for this sentence; without it the Hindi task penalty is +0.3 [-4.6, +4.9].
2. **Time duration's direct-answer reversal.** n = 750 questions: Hindi direct +7.3 points and English direct -7.3 with a time-related distractor, Hindi minus English penalty +19.7 [+12.6, +26.9], the only time-related interaction surviving Holm under both scorings (English-driven recurrence also survives under strict only, -14.1 [-20.1, -8.0]).
3. **Short-level Hindi harm depends on distractors.** n = 1,350 questions: -1.9 [-4.5, +0.8] with no distractor, -6.2 [-8.8, -3.8] time-related.
4. **Token budget reverses thinking in Hindi.** n = 1,350 pairs per cell: Hindi CoT strict 59.9 off vs 43.8 on at 4,096 tokens, -16.1 [-19.3, -12.7].
5. **Cleaner mention measure.** n = 6,451 English traces: OR 0.57 [0.38, 0.85], CI not clustered, filter chosen after seeing the data.
6. **Sentence-level uncertainty.** k = 45 units: Hindi time-related +2.3 [-0.1, +4.6]; Hindi minus English unrelated +2.8 [+0.4, +5.3].
7. **Memorisation declines with level for this model**, departing from TRD: Hindi direct, no distractor, 45.3 to 19.3 over five levels, 150 questions per task and level (`fig_data/trd_reasoning_memorization_by_level.csv`).
8. **Interval errors in Hindi CoT are often malformed.** 16.0% of answers do not span seven days vs 2.9% in English, and 2.5% in Hindi direct (n about 2,250 per cell, no interval computed). This may help explain why CoT hurts Hindi there.

## Suggested claims for the paper

1. **Strong.** "Over 6,750 questions, CoT raised Sarvam-105B's accuracy by 29.5 points in English (58.99% to 88.51%, 95% CI [28.5, 30.5]) but only 4.7 in Hindi (54.74% to 59.40%, [3.6, 5.6]); counting unanswered responses as wrong gives +26.8 and +4.2."
2. **Strong.** "With no distractor, CoT lowered Hindi accuracy on date subtraction by 19.9 points [16.3, 23.5] and on interval date by 23.3 [19.0, 27.5], and both effects remained significant with either distractor type; English CoT was never significantly below direct in any task or task-by-level cell."
3. **Strong.** "The CoT gain gap holds in each distractor condition: English minus Hindi CoT accuracy is 28.0 points with no distractor, 29.7 with a time-related and 29.7 with an unrelated sentence, against 4.0 to 4.9 under direct answering."
4. **Moderate.** "A time-related distractor cost Hindi CoT 2.2 points more than Hindi direct answering [0.6, 3.9], robust to removing any single sentence (range 1.8 to 2.6), but the difference from English was not reliably significant (+2.6 [0.5, 4.7] answered-only, +1.4 [-0.7, 3.6] strict; odds-ratio ratio 0.89 to 1.02)."
5. **Moderate.** "Distractor effects were concentrated in particular tasks and sentences: after Holm correction only date duration (+8.8) and time duration (+11.5) showed a Hindi penalty, the latter mostly because Hindi direct accuracy rose, and removing one sentence eliminated the recurrence penalty (+4.5 to +0.3)."
6. **Moderate.** "Under CoT, Hindi and English failures overlapped far less than under direct answering (median within-cell φ 0.06 vs 0.28), and in 5,947 of 7,657 pairs where Hindi was wrong English was right, though overlap remained above chance (OR 0.64 [0.57, 0.73])."
7. **Suggestive.** "Hindi traces that drifted into English were more often correct within task and level (OR 2.08 [1.66, 2.60], n = 431 drifting traces, 83% on day of week), an observational association."
8. **Suggestive.** "In a pilot of 450 questions with thinking enabled and a 16,000-token limit, Hindi CoT accuracy rose from 64.1% to 97.9% with hidden reasoning that was mostly in English; 56% of those responses exceeded the 4,096-token limit used elsewhere, so the comparison does not hold cost constant."
