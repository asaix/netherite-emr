# Audit: Reasoning in Hinglish report

Document: `docs/final/hinglish_report.pdf`. Every number is recomputed by `verify.py` (feature extraction in `features.py`, claim table in `claims.py`) from `responses/` and `dataset/`. Run from the repo root with `.venv/bin/python experiments/2026-10-31_final-report/audit/hinglish/verify.py`. All values are in `numbers.json`, `results/` and `fig_data/`.

Reused code: I did not import any analysis script. The answer regex and the verification regex are copied in text from `experiments/2026-10-27_full-grid-analysis/` (`metrics.py`, `temporal_answers.py`) because the convention being audited depends on them. Definitions of the bootstrap and penalty follow `analysis.py` in that folder. Everything else is new.

Conventions: **answered-only** drops responses with no answer line. **Strict** counts them wrong. **Paired** uses only pairs where both responses answered. The report uses answered-only for Tables 1 and 2 and paired for Table 3, without saying so for Table 3.

## Verdict

262 claims checked: 236 reproduced, 13 overclaimed, 8 differ, 3 source missing, 2 unverifiable. No number looks fabricated. Tables 1 and 2 reproduce in full, including all 18 significance marks and every CI once the question order is matched. The problems are in the wording.

| Headline claim | Verdict |
|---|---|
| Hinglish CoT hurts English (88.9 to 70.9) | **Holds.** Strict: 86.0 to 70.3. Paired: -16.95 [-18.22, -15.68]. Holds in all distractor conditions. |
| Does worse than English CoT on every task | **Holds.** 9 of 9, Holm p<0.001. All 27 task-by-distractor cells are negative; 25 survive Holm. |
| Hindi unchanged (59.4 vs 59.4) | **Holds in aggregate.** Paired +0.06 [-1.12, +1.34]. |
| "Every task-level change is within noise" | **False.** Date duration -5.48 (Holm p=0.028), date subtraction +5.08 (Holm p=0.045). |
| Gap closes only because English gets worse | **Holds.** |
| "Hinglish hurts English" as a language effect | **Not separable from the prompt.** Traces with no Hindi lose -9.45. The Roman excess is -11.32. |
| Roman group is "not just the harder questions" | **Argument insufficient; conclusion survives** stronger controls. It remains self-selected. |
| Ordering in all nine tasks | **Holds**, in all distractor conditions and all 48 threshold pairs. |
| Cost grows with difficulty | **Holds.** -3.92 per level [-4.83, -3.00]; strict -3.21. |
| Cost grows with how much Hindi | **Two-group contrast only.** No established gradient. |
| "In either script" limits CoT | **Suggestive only.** Direction supported, wording too strong. |
| 73% "mostly Devanagari" | **Overclaimed.** 73.1% reach 10%; 68.5% have a majority. |
| Verification fall is mostly a regex miss | **Contradicted.** 18.6% vs 86.5% on traces where the regex applies fully. |

## Data existence

| Cited item | Exists | Records | Matches design |
|---|---|---|---|
| `experiments/2026-10-31_hinglish-analysis-aayush/` (FINDINGS.md) | **No**, in no local or remote ref | n/a | `source_missing` |
| `report/make_report.py` | **No**, in no local or remote ref | n/a | `source_missing` |
| `responses/hinglish/` | Yes | 13,500 (2,700 per level) | Yes |
| `experiments/2026-10-30-hinglish-aayush/output/results.json` | Yes, `errors.json` is empty | run folder, same data | Yes |
| `responses/standard/` | Yes | 81,000; 27,000 on these questions | Yes |
| `responses/en-cot/` | Yes | 6,750, Hindi questions only | Yes |
| `dataset/` | Yes | First 50 IDs match; 2,250 unique question texts | Yes |

Checks: 0 question-text differences and 0 gold differences across Hinglish, standard and en-CoT. Model, temperature, top_p, max tokens and reasoning effort are identical. All unanswered responses are `finish_reason=length`. The first 50 are representative: pooled CoT is 88.88 vs 88.51 (English) and 59.40 vs 59.40 (Hindi) against the full grid (`results/first50_vs_full_grid.csv`).

Differences the report does not state:
- **The prompts differ by more than the language named.** Hinglish drops "Write your entire response in {language}" and the "do not switch to another language" lock. The en-CoT prompt adds "The following question is written in Hindi". The report's quotation also cuts the final parenthetical without an ellipsis.
- **Run dates differ.** Standard ran 29 Sep to 29 Oct, en-CoT on 28 Oct, Hinglish on 29 to 30 Oct.
- **The function-word list is lost.** The report prints five words. A 60-word reconstruction (`features.py`) reproduces every accuracy and all discordant counts, and the English n to within 3 of 6,483.
- **The printed Roman rule is not the rule used.** "No Devanagari" gives n=1,571 on Hindi questions. Table 3's n=1,631 needs "Devanagari share under 10%", so 61 traces in that row contain Devanagari.

## Corrected results

### Headline by distractor condition

Accuracy in %, 2,250 questions, paired CIs from a cluster bootstrap (B=2000).

| Questions | Distractor | Direct | Std | Hinglish | Hing - Std answered | Hing - Std strict | Gain answered |
|---|---|---|---|---|---|---|---|
| English | None | 60.6 | 89.3 | 70.6 | -18.7 [-20.6, -16.8] | -16.4 [-18.3, -14.4] | +10.0 [+7.7, +12.3] |
| English | Similar | 59.9 | 88.2 | 69.7 | -18.4 [-20.4, -16.4] | -14.9 [-17.0, -12.8] | +9.9 [+7.5, +12.2] |
| English | Dissimilar | 58.6 | 89.2 | 72.4 | -16.8 [-18.6, -14.9] | -15.7 [-17.5, -13.8] | +13.8 [+11.4, +16.1] |
| English | Pooled | 59.7 | 88.9 | 70.9 | -18.0 [-19.3, -16.7] | -15.7 [-16.9, -14.4] | +11.2 [+9.6, +12.8] |
| Hindi | None | 56.0 | 60.2 | 61.0 | +0.8 [-1.3, +3.1] | +0.9 [-1.1, +3.2] | +5.0 [+2.7, +7.3] |
| Hindi | Similar | 54.9 | 58.9 | 59.1 | +0.2 [-1.9, +2.4] | +0.3 [-1.8, +2.6] | +4.2 [+1.8, +6.6] |
| Hindi | Dissimilar | 54.6 | 59.1 | 58.0 | -1.1 [-3.2, +1.1] | -1.0 [-3.1, +1.2] | +3.4 [+1.2, +5.8] |
| Hindi | Pooled | 55.2 | 59.4 | 59.4 | -0.0 [-1.2, +1.2] | +0.1 [-1.1, +1.4] | +4.2 [+2.5, +5.9] |

All headline conclusions hold in each condition. Answered-only overstates the English loss by 2.3 points, because standard CoT is cut off on 3.3% of responses (Hinglish 0.8%). The strict gain figures are in `fig_data/new_split_headline.csv`.

Gap on five date tasks, answered-only (`results/split_gap.csv`):

| Distractor | Short, Std | Short, Hing | Very long, Std | Very long, Hing |
|---|---|---|---|---|
| None | 27.3 [21.8, 33.2] | 15.6 [9.8, 21.6] | 43.2 [36.5, 49.6] | 6.6 [-0.0, 13.2] |
| Similar | 28.6 [23.0, 34.6] | 17.3 [11.2, 23.8] | 39.5 [32.4, 46.8] | 8.2 [0.2, 15.6] |
| Dissimilar | 28.7 [22.8, 34.9] | 19.5 [14.2, 25.6] | 39.0 [32.3, 45.5] | 10.1 [2.7, 17.3] |

Pooled very-long strict values are 36.5 (standard) and 8.0 (Hinglish). With no distractor the Hinglish very-long interval touches zero.

### Paired tests, Hinglish minus standard

Paired on responses where both answered. Sign-flip is at question level with Holm over nine tasks in that language. Source: `fig_data/new_task_hing_minus_std.csv`.

| Task | English diff [CI] | Hing / Std only | Strict | Hindi diff [CI] | Hing / Std only | McNemar Holm | Flip Holm |
|---|---|---|---|---|---|---|---|
| Date addition | -10.67 [-13.45, -8.20] | 11 / 91 | -10.67 | +0.80 [-2.60, +4.14] | 89 / 83 | 1.0 | 1.0 |
| Date subtraction | -24.43 [-28.68, -20.37] | 17 / 200 | -24.40 | **+5.08 [+1.73, +8.66]** | 109 / 71 | **0.045** | 0.055 |
| Date duration | -6.41 [-8.33, -4.63] | 4 / 52 | -6.27 | **-5.48 [-8.70, -2.34]** | 72 / 113 | **0.028** | **0.015** |
| Date recurrence | -34.78 [-39.21, -29.91] | 17 / 258 | -32.00 | -1.22 [-4.83, +2.51] | 95 / 104 | 1.0 | 1.0 |
| Day of week | -34.94 [-40.36, -29.64] | 59 / 269 | -25.20 | +2.83 [-1.21, +6.98] | 125 / 105 | 1.0 | 1.0 |
| Interval date | -11.70 [-16.20, -6.92] | 101 / 185 | -10.27 | -0.27 [-4.20, +3.61] | 121 / 123 | 1.0 | 1.0 |
| Time addition | -12.91 [-16.01, -10.07] | 16 / 111 | -11.60 | -1.20 [-4.78, +2.50] | 113 / 122 | 1.0 | 1.0 |
| Time subtraction | -12.47 [-15.33, -9.38] | 14 / 106 | -11.87 | -0.67 [-4.69, +3.25] | 128 / 133 | 1.0 | 1.0 |
| Time duration | -8.81 [-11.24, -6.59] | 2 / 68 | -8.80 | +0.80 [-2.75, +4.21] | 97 / 91 | 1.0 | 1.0 |

- **"Does worse on every task":** all nine English tasks have McNemar Holm p<0.001 and flip Holm p≤0.001, and all are significant under strict scoring.
- **"Every task-level change is within noise":** false. Date duration survives every test. Date subtraction is borderline: McNemar yes, sign-flip p=0.055. Seven tasks are null. In the split by distractor only date duration with no distractor survives (-8.8, Holm p=0.038), so this is not a robust task story either, and the corrected wording should be modest.
- **Hindi aggregate:** 949 vs 945 pairs flip, so 28% of pairs change outcome while the mean holds still. "Unchanged" describes the mean only.
- **Table 1 marks:** a question-level sign-flip with Holm gives the same 18 decisions as McNemar.
- **Task significance varies by distractor** (`results/split_by_distractor_task.csv`). Date subtraction (both languages) and Hindi interval date stay significantly below direct in all three. Hindi time subtraction's gain over direct is significant only with the similar distractor, Hindi day of week not with the dissimilar one, English date duration not with the similar one, and English time addition not with no distractor.

### Script classification

| Measure | Value |
|---|---|
| English: Roman / plain / any Devanagari | 63.08% / 36.92% / 0 of 6,750 |
| Hindi: Devanagari mix (at least 10%) / Roman / plain | 73.07% / 24.39% / 2.55% |
| Hindi: no Devanagari at all | 25.50% |
| Hindi: Devanagari majority (at least 50%) | **68.46%** |
| Hindi: at least 75% Devanagari | 37.76% |
| Median Devanagari share, all Hindi traces / mix traces only | 67.65% / 75.61% |

Sensitivity across 48 threshold pairs (Devanagari 1 to 50%, function word 1 to 20%; `fig_data/threshold_sensitivity.csv`): English Roman share 61.3 to 69.1, Hindi Devanagari share 68.5 to 74.3, adjusted Roman-minus-plain difference -8.4 to -12.0, and the nine-task ordering 9 of 9 every time. Word lists (`wordlist_sensitivity.csv`): 5 words n=3,935, Roman accuracy 67.7; 60 words n=4,112, 68.0. **Conclusions do not depend on the thresholds**, because the distribution is close to two groups: 28.4% of paired English traces have zero function words, 59.9% have 25% or more, and only 1.1% lie between 3% and 15%.

Style shares move with the distractor. English Roman share: none 65.2 [63.2, 67.1], similar 68.8 [66.9, 70.7], dissimilar 55.2 [53.1, 57.2]. Hindi Devanagari share: 71.4, 74.4, 73.3.

### Self-selection

English questions, n=6,483 pairs, cluster-robust SE. Roman minus plain.

| Comparison | Standard CoT | Hinglish CoT | Loss difference |
|---|---|---|---|
| Raw | +0.81 | -11.02 | -11.83 |
| Within task x level x distractor (135 cells) | +0.32 [-1.08, +1.73] | -10.99 [-12.92, -9.06] | **-11.32 [-13.61, -9.03]** |
| Plus standard-CoT correctness | | -11.03 [-12.95, -9.11] | |
| Plus length, number density, verification | | -10.20 [-12.20, -8.19] | |
| Question fixed effects | | -10.90 [-13.18, -8.63] | |

- Mantel-Haenszel OR for Hinglish correct, Roman vs plain, 135 strata: 0.44 [0.38, 0.51].
- Within standard-right items: 72.4 vs 84.4 (-11.34). Within standard-wrong items: 31.4 vs 37.7 (-8.14).
- By distractor, cell-adjusted loss difference: none -10.56 [-14.59, -6.52], similar -12.77 [-16.87, -8.67], dissimilar -10.73 [-14.41, -7.04].

**Is Table 3's argument sufficient? No.** A marginal match on standard accuracy does not rule out different task mixes that happen to balance, and it says nothing about trace-level selection. Style mix does vary by task (date subtraction 75% Roman, date duration 41%). Controls do not move the estimate, so the group difference is not explained by item hardness. But style is measured after the model has started answering. If the model tends to write Hinglish on the runs where it is also less careful, no item-level control can detect that. The result should be described as an association among self-selected traces.

Quasi-experimental check (exploratory): unrelated distractors reduce Roman share by -11.68 [-14.03, -9.12] within question. The reduced-form effect on the Hinglish-minus-standard difference is +1.03 [-1.10, +3.11], giving a Wald estimate of -8.86 [-27.06, +10.16]. This agrees in size with -11.32 but cannot confirm it, and it assumes the distractor affects accuracy only through style.

### Is it Hindi, the instruction, or shorter traces?

The prompt is one fixed wording, so these cannot be fully separated. What the data can say, English questions, n=6,483 pairs:

| Group | n | Hinglish | Std same items | Loss | Tokens H / S | Verif. regex H / S |
|---|---|---|---|---|---|---|
| Roman | 4,112 | 68.02 | 89.30 | -21.28 [-22.92, -19.64] | 222 / 344 | 4.2 / 84.7 |
| Plain | 2,371 | 79.04 | 88.49 | -9.45 [-11.14, -7.70] | 252 / 373 | 31.8 / 88.2 |
| Zero function words | 1,838 | 78.35 | 88.63 | -10.28 [-12.28, -8.32] | 227 / 340 | 18.6 / 86.5 |

- **Instruction effect, upper-bound reading.** Traces with no Hindi still lose about 10 points. That is 44% of the Roman loss and is not attributable to Hindi words in the trace. Self-selection could push it either way.
- **Verification fell for real.** The report's caveat is contradicted. On zero-function-word traces the regex works and the fall is -67.9 points [-70.3, -65.4]. A regex extended with romanised terms lifts Hinglish only from 14.6% to 20.4%. A script-independent measure agrees: the share of the trace after the answer first appears drops from 0.358 to 0.187. Hand check (`results/manual_verif_sample.json`): 0 of 30 Roman traces with no regex match had a check step in their last 420 characters, and of 15 extended-regex-only matches at least 6 were real checks, 4 were false positives, and 5 could not be judged from the tail, so 11.75% for Roman is likely an upper bound.
- **Controlling for length does not remove the loss.** Matched on task, level and token decile: -16.73 overall (raw -16.95), Roman -20.94, plain -8.39. At 200 to 300 tokens the accuracies are 97.9 (standard), 84.9 (plain), 65.8 (Roman).
- **Controlling for length and verification together reduces it but does not remove it.** Pair fixed effects (`new_length_verification_models.csv`):

| Model | Hinglish term | | Style model | Roman | Plain |
|---|---|---|---|---|---|
| None | -16.95 [-18.21, -15.69] | | None | -21.28 | -9.45 |
| log tokens | -12.22 [-13.56, -10.89] | | | | |
| verification | -10.31 [-12.05, -8.57] | | | | |
| log tokens, verification, post-answer share | -8.48 [-10.16, -6.80] | | All three | -13.43 [-15.55, -11.31] | -3.35 [-5.29, -1.41] |

These controls are post-treatment, and the two length adjustments disagree because long traces also mark hard items. Within-condition evidence is mixed: verification is associated with +8.0 [+5.65, +10.36] inside Hinglish and +0.42 [-1.74, +2.58] inside standard CoT, where almost every trace verifies. **Fair summary:** terser traces with less checking go with most of the plain-English loss (-9.45 to -3.35), while Roman traces still lose about 13 points to standard CoT after these controls. Neither is shown to be causal.

### Takeaway 2: "in either script"

Same questions and answered pairs. Hindi questions:

| Trace style | n | Hinglish | en-CoT | en-CoT advantage [CI] | None / Sim. / Dis. |
|---|---|---|---|---|---|
| Devanagari mix | 4,778 | 58.48 | 81.39 | +22.92 [+21.34, +24.58] | 24.0 / 19.5 / 25.3 |
| Roman | 1,605 | 64.74 | 87.79 | +23.05 [+20.56, +25.48] | 20.4 / 24.5 / 24.7 |
| Plain | 168 | 67.86 | 82.74 | +14.88 [+7.59, +21.92] | 9.8 / 18.4 / 15.7 |
| All | 6,551 | 60.25 | 82.99 | +22.74 [+21.37, +24.13] | |

Other contrasts (answered-only):

| Contrast | Diff [CI] |
|---|---|
| Reading cost: English Q std vs Hindi Q en-CoT | +5.99 [+5.00, +6.98]; strict +5.21 |
| Reasoning cost on Hindi Q: en-CoT vs Hindi CoT | +23.49 [+22.12, +24.90]; strict +21.73 |
| Hindi Q en-CoT vs English Q Hinglish | +12.00 [+10.66, +13.36]; strict +10.46 |
| Gap recovered by en-CoT | 29.48 to 5.99, 79.7%; strict 26.95 to 5.21 |
| Roman vs Devanagari on Hindi Q, within cell | -2.84 [-5.15, -0.52] |
| Roman vs Devanagari on Hindi Q, question fixed effects | -2.30 [-5.02, +0.42] |
| Plain vs Devanagari on Hindi Q, within cell | +8.18 [+2.74, +13.62] |
| Roman on both languages, same item | English 71.91, Hindi 65.07; 169 vs 102, n=979, p<0.001 |

What this supports:
- Reasoning language matters more than question language: 23 vs 6 points. Hindi questions with English reasoning beat English questions under the Hinglish prompt by 12 points.
- Romanising does not rescue Hindi reasoning. The raw Table 3 gap in favour of Roman on Hindi questions (64.1 vs 57.8) comes from easier items selecting Roman (standard 66.9 vs 57.1) and is gone or slightly reversed after controls.
- Within the same prompt, traces without Hindi beat traces with Hindi by a similar amount on both question languages: 11.0 points on English (plain vs Roman, n=6,483) and 8.2 on Hindi (plain vs Devanagari, n=6,513 with only about 168 plain). This is the strongest evidence for the claim, and it is self-selected.

What it does not support:
- **"What limits CoT" as a sole cause.** en-CoT and Hinglish prompts differ in more than language, and plain traces under the Hinglish prompt still lose 14.88 to en-CoT on Hindi questions. So part of the 23 points belongs to the prompt.
- **"In either script" as a tested factor.** Script is chosen by the model and no English question gets Devanagari reasoning, so language and script are not crossed.
- **Reading is not cost-free.** With the trace style held at Roman, English questions still beat Hindi by 6.8 points.

Suggested wording: "Together with en-CoT, this suggests that reasoning language matters more than question language; on Hindi questions, Roman traces do no better than Devanagari traces."

### Gradient and shared failure

- **Difficulty:** slope -3.92 per level [-4.83, -3.00], strict -3.21 [-4.14, -2.30]; none -3.72, similar -4.33, dissimilar -3.72, each excluding zero. Holds.
- **Amount of Hindi:** Bins at 15 to 25% and at 25% or more lose -20.11 and -21.57. Within Roman traces the raw loss falls across quartiles (-24.85, -21.61, -21.18, -18.38) because high-share traces cluster on easy items, while the cell-adjusted slope is -4.24 per 10 points [-6.59, -1.90]. Sign depends on adjustment, and the range is narrow. Claim the two-group contrast, not a gradient.
- **Date subtraction shares Hindi CoT's failure: supported.** See the first missing finding. Error mix: English Hinglish 26.4% off-by-one and 56.4% other; Hindi CoT 19.6% and 65.5%; English CoT 91.7% off-by-one. Item overlap with Hindi failures is phi 0.40, vs 0.14 for English CoT.
- **Day of week: not supported.** Overlap phi 0.016. In English Hinglish the correct answer stays most common (34.7 vs 19.7 for one day late), whereas in Hindi CoT one day late is most common (25.3 vs 21.0). The two examples quoted in the report are accurate but are a selection.

### Distractor penalties

All twelve cells reproduce. The -3.8 is called "most likely chance", which was not tested. It equals a direct drop of 2.05 plus a Hinglish gain of 1.75, and at the no-distractor style mix it would be -2.81, so about one point is style composition. The direct drop is shared with the standard-CoT penalty, which is also negative and under strict scoring excludes zero: -2.76 [-5.16, -0.49]. So English unrelated penalties are not independent results. Better wording: "probably reflects the lower direct baseline and a shift to plain-English traces under unrelated distractors."

### Scoring

Fourteen Hindi day-of-week responses give romanised weekday names ("Shanivar") and score wrong, while "Saturday" scores right. Lenient scoring moves that cell from 23.47 to 25.38. No mark changes. Report or fix it.

## Limitations

**Cannot be concluded from this data**
- Any causal effect of trace style, Hindi words or script. Style is post-treatment and self-selected.
- That Hindi rather than the instruction causes the English loss. There is one wording and no control arm.
- That shorter traces or less verification mediate the loss. Both are post-treatment, and the adjustments disagree.
- Anything about Hinglish **input**. Questions stay in English or Hindi, so the report's motivation, how users write, does not match its manipulation.
- Anything beyond Sarvam-105B, greedy decoding, TRD templates, thinking off.
- Whether results depend on model changes between runs. Hinglish ran up to a month after much of the standard data, and no overlapping rerun exists.

**Threats the report does not mention**
- Prompt differences beyond the named language.
- Answered-only scoring favours standard CoT, especially day of week: -34.9 paired, -25.2 strict, because 16% of standard day-of-week responses are cut off.
- The CIs cover question sampling only. The prompt is fixed, so there is no prompt-to-prompt variance, and temperature 0 gives no sampling variance. Intervals are too narrow for claims about "Hinglish prompts".
- McNemar counts three distractor variants of a question as independent. Here it matters only for Hindi date subtraction.
- The classifier is a word list, not the word-level language identification planned in the mid report, and there is no hand-labelled validation of style. The reconstructed list is not the original.
- Hinglish-vs-standard tests are absent from Table 1, though the prose depends on them.
- Many tests were run in this audit and in the report without a global correction. Treat anything near p=0.05 as weak.
- The verification hand check is small, by one reader, using only trace tails.

**Not run but could be** (needs new API runs): an English CoT prompt without the language lock; a terse English prompt to measure length alone; a verification-suppressed prompt; prefilled Roman, Devanagari or English openings to randomise style; several Hinglish paraphrases; a Hinglish prompt with an explicit "entire response" lock; romanised questions. **Possible offline, no API:** word-level language identification, hand-labelled style and error samples, and a cross-check that keeps the original word list if it can be recovered from Aayush.

## Design rationale from prior work

Sources and quotes are in `citations.md`.

| Choice | Rationale | Departure or weakness |
|---|---|---|
| Test reasoning language as a factor | Shi et al. introduced EN-CoT and found it competitive or better than native CoT. Tam et al. and Qi et al. report accuracy costs from imposing a reasoning language. | Our en-CoT advantage (+23) is far above Shi's 3 to 5 points. Those works use other models and data. Qi's trade-off implies the imposed instruction alone may cost accuracy, which supports the prompt-effect reading. |
| Hinglish as a mixed condition | Hindi-English is an established code-switching pair (GLUECoS, LinCE). | These benchmarks test code-mixed input and tagging or classification tasks, not generated reasoning. |
| Expect mixing might help | Shankar et al. show code-mixed few-shot examples improve some tasks. | Theirs is few-shot input on alignment tasks. Ours is zero-shot output on arithmetic. Our negative result does not contradict theirs. The mid-report's "add to CoT gains" is not supported by the fetched abstract. |
| Expect Roman script might help | RomanSetu reports romanised text matches or beats native script after pretraining on it. | Ours is not a romanised-trained setup, and we find Roman no better than Devanagari on Hindi questions. Script Gap reports romanised input costs 5 to 12 F1 points on triage. |
| Report instruction compliance | Marchisio et al. treat wrong-language output as a failure to measure. Winata et al. report Devanagari in generated Hindi-English. Indi-RomCoM reports models reverting to English and that this rises with mixing. | Our compliance failure follows the question's language on both sides: Devanagari on Hindi questions, plain English on 37% of English ones. This is a measured pattern and fits this work, but we measure script and a function-word proxy, not language at word level. |
| Single fixed prompt | Keeps comparison with standard runs simple. | Weakest design choice. Prevents separating instruction, register and language. |
| Same questions, paired tests | Exact McNemar, Holm, cluster bootstrap as the team convention. Pairing removes item difficulty for condition comparisons. | It does not help style comparisons, which are observational. |
| Distractor conditions | Shi et al. 2023 show irrelevant context can hurt. | Only metadata read for that paper. Pooling hides that distractors shift trace style. |

We found no study measuring accuracy with CoT traces written in Hinglish, so the condition is new as far as one search session shows. Indi-RomCoM is the nearest work, and it is a recent preprint.

## Missing findings

All exploratory.

1. **Date subtraction loss is almost entirely month-crossing.** English, crossing a month, n=362 pairs: 90.06 to 42.27, **-47.79 [-54.11, -41.53]**. Same month, n=387: 100.0 to 97.42, -2.58 [-4.49, -1.09]. Roman 35.0 (n=277) and plain 65.1 (n=86) under Hinglish, close to Hindi CoT at 36.2. en-CoT on Hindi questions recovers to 88.1. Hindi same-month CoT 93.8. This names the shared failure.
2. **Traces with no Hindi still lose about ten points.** n=1,838, 78.35 vs 88.63, **-10.28 [-12.28, -8.32]**; none 78.36 vs 90.10, similar 77.60 vs 85.85, dissimilar 78.85 vs 89.36.
3. **Verification collapses on these same traces.** n=1,838, 18.61% vs 86.51%, **-67.9 [-70.3, -65.4]**.
4. **Roman excess after adjustment.** n=6,483, **-11.32 [-13.61, -9.03]**, holding across thresholds at -8.4 to -12.0 and across distractors at -10.56 to -12.77.
5. **Romanising gives no advantage on Hindi questions.** n=6,513, Roman vs Devanagari **-2.84 [-5.15, -0.52]**; question fixed effects -2.30 [-5.02, +0.42]; the raw gap of +6.3 disappears.
6. **Hindi questions with English reasoning beat English questions with the Hinglish prompt.** n=6,750 per arm before dropping unanswered, 82.89 vs 70.89, **+12.00 [+10.66, +13.36]**; strict +10.46 [+9.14, +11.81].
7. **Unrelated distractors change the style the model picks.** n=6,750 per condition set, Roman share 55.2 [53.1, 57.2] vs 65.2 [63.2, 67.1] with none and 68.8 [66.9, 70.7] with similar. A one-sentence change moves language choice by up to 14 points. Mechanism unknown.
8. **A large hidden churn on Hindi.** n=6,679 pairs, 28.4% change correctness, 949 vs 945, net +0.06 [-1.12, +1.34]. The Devanagari-mix group has 29.25% discordance and only 48.57% identical answers.
9. **Hindi date subtraction rises by similar amounts on both sides of the month boundary.** Crossing n=361, +6.37 [-0.25, +12.95], interval includes zero; same month n=387, +3.88 [+1.02, +6.94].

## Suggested claims for the paper

1. **Strong.** "Prompting for Hinglish reasoning lowered accuracy on English questions from 88.9% to 70.9% (strict 86.0% to 70.3%; paired difference -17.0 points, 95% CI [-18.2, -15.7]), with a significant loss on all nine tasks and in every distractor condition (-18.7, -18.4, -16.8)."
2. **Strong.** "On Hindi questions, mean accuracy did not change (59.4% in both; paired +0.1, [-1.1, +1.3]), so the English-Hindi gap fell from 29.5 to 11.5 points only because English accuracy fell. Task effects cancelled: date duration fell by 5.5 points ([-8.7, -2.3], Holm p=0.03) while date subtraction rose by 5.1 ([+1.7, +8.7], Holm p=0.045, not robust to question-level testing)."
3. **Strong.** "The model largely ignored the Roman-script instruction on Hindi questions: 73.1% of traces had at least 10% Devanagari words and 68.5% a Devanagari majority, and only 25.5% had none. On English questions it used no Devanagari, and 36.9% of traces were plain English."
4. **Moderate.** "Traces with Hindi function words lost more than plain-English traces on all nine tasks (-21.3 vs -9.5 points; -11.3 [-13.6, -9.0] within task, level and distractor, and -8.4 to -12.0 across all thresholds). Because the model chooses the style, this is an association. Plain-English traces under the same prompt still lost 9.5 points, so the prompt itself probably accounts for part of the loss."
5. **Moderate.** "The prompt changed behaviour as well as language: on traces with no listed Hindi function words, verification phrases fell from 86.5% to 18.6% (n=1,838) and median length from 340 to 227 tokens. Matching on task, level and length left the loss almost unchanged (-16.7 points), so length alone does not explain it."
6. **Moderate.** "English reasoning on Hindi questions reached 82.9% against 59.4% for Hindi reasoning and 88.9% for English questions, recovering 80% of the gap. This suggests reasoning language matters more than question language (23.5 vs 6.0 points), though the two prompts differ in more than language."
7. **Suggestive.** "Romanisation did not help on Hindi questions: Roman traces were no better than Devanagari traces after controls (-2.8 points, [-5.2, -0.5]; -2.3 [-5.0, +0.4] with question fixed effects), and both lost about 23 points to en-CoT on the same questions. Script was self-selected."
8. **Suggestive.** "Hinglish reproduced one specific Hindi failure: on English date subtraction crossing a month boundary, accuracy fell from 90.1% to 42.3% (Hindi CoT 36.2%) while same-month accuracy stayed at 97.4%, and failures overlapped with Hindi CoT's on the same questions (phi 0.40 vs 0.14 for English CoT). Day of week shows no such overlap (phi 0.02)."
