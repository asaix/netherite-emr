# Consolidated analysis for the final report

This merges the seven audits into one account. Details, tables and sources are in each audit's `analysis.md`:

| Topic | Source document | Audit folder |
|---|---|---|
| Baseline (RQ1, RQ2) | `experiments/2026-10-27_full-grid-analysis/FINDINGS.md`, mid report | `audit/baseline/` |
| Hinglish | `docs/final/hinglish_report.pdf` | `audit/hinglish/` |
| CLP | `docs/final/netherite final analysis.pdf`, Part A | `audit/part_a_clp/` |
| en-CoT | same PDF, Part C | `audit/part_c_encot/` |
| Trace interventions | same PDF, Part B | `audit/part_b_interventions/` |
| Logistic regression | `docs/final/lr_report.pdf` | `audit/lr/` |
| Edit distance | `docs/final/ANALYSIS.md` | `tests/ed_audit/outputs/final_report_audit/` |

## Conventions used in the paper

- **Accuracy.** Answered-only is the primary number, because every team figure and the mid report use it. Strict (unanswered counts as wrong) sits beside every headline. Answered-only flatters English CoT by about 2.9 points, since 651 English CoT responses hit the token limit, so any conclusion that changes under strict scoring is flagged in the text.
- **Intervals.** `headline.py` recomputes all accuracy contrasts with one bootstrap (B = 2,000 over questions, seed 20261031), so Part A and Part C no longer print different intervals for the same quantity. Numbers from specialised analyses keep the audit's own interval.
- **Names.** "Drop" is accuracy without a distractor minus accuracy with one. "Penalty" is the CoT drop minus the direct drop.

## How much of the evidence stands

2,307 claims were checked across the documents: 2,059 reproduced, 133 overclaimed, 62 differ (mostly last-digit rounding), 30 unverifiable, 23 with a missing source. No number looks fabricated. Arithmetic is reliable. The problems are in wording and inference.

Data exists and matches the design: 81,000 standard responses over 6,750 questions, 6,750 CLP, 6,750 en-CoT, 13,500 Hinglish, 5,400 thinking-on, and 13,664 resampled continuations. All 13,500 gold answers were recomputed with `datetime` and match. An independent extractor agrees with the project's on all 80,172 graded standard responses.

**Missing from every local and remote ref, and needed for the code ZIP:** `experiments/2026-10-31_clp-analysis-rahul`, `experiments/2026-10-31_hinglish-analysis-aayush`, `report/make_report.py`, `sensitivity.py`, `noise_and_loops.py`, the script that built the Part A to C PDF, and `experiments/2026-10-30-LR-aayush/lr_out/*.csv` (git-ignored). All their numbers were recomputed from raw responses.

## Findings by research question

### RQ1. Does CoT help, by language and difficulty?

CoT helps English far more than Hindi, in every distractor condition.

| | Direct | CoT | Gain, answered | Gain, strict | None | Time-related | Unrelated |
|---|---|---|---|---|---|---|---|
| English | 59.0 | 88.5 | +29.5 [28.5, 30.6] | +26.8 [25.8, 27.8] | +28.8 | +29.1 | +30.7 |
| Hindi | 54.7 | 59.4 | +4.7 [3.6, 5.7] | +4.2 [3.2, 5.3] | +5.6 | +3.4 | +5.0 |

- The English-Hindi gap is +4.2 under direct answering and +29.1 under CoT, and +28.0, +29.7, +29.7 by distractor condition.
- **Answer to the evaluator's pooling criticism.** With no distractor, Hindi CoT lowers date subtraction by 19.9 [16.4, 23.4] and interval date by 23.3 [19.0, 27.7]; both stay significantly negative under each distractor. The mid report's inference from a pooled table did not support this, and the split now does.
- One task reverses by condition: the time duration gain gap is -5.2, +14.5, -2.2 (none, time-related, unrelated). Hindi CoT's harm at the short level is a distractor effect (-1.9 [-4.5, +0.7] with none, -6.2 and -4.7 with distractors).
- The CoT gap widens with difficulty in points (24.0 to 34.9; strict 23.0 to 31.1), but the logit trend is not significant (OR 0.97 per level, p = 0.21).

### RQ2. Does CoT make distractors more harmful?

Weaker than the mid report said. "Only in Hindi" should go.

- Hindi CoT drop with a time-related distractor is 2.6 [1.3, 3.8]. The Hindi penalty relative to direct is +2.2 [0.6, 3.8], stable when any one sentence is removed (1.8 to 2.6). **Part B's "+2.59 penalty" is the drop; both numbers are correct and measure different things.**
- Hindi minus English penalty, time-related: +2.6 [0.4, 4.7] answered, +1.4 [-0.7, 3.5] strict, and not significant on any logit specification except with recurrence removed.
- Across the 45 task-sentence units the Hindi time-related mean is +2.3 [-0.1, +4.6], so the result is about these sentences and may not generalise to new ones.
- **The largest effect is one sentence.** "The last time I had a weekly commitment was in January" sends 92 of 134 English CoT traces to the token limit (4 of 134 without it) and cuts strict English accuracy from 88.8 to 19.4. Hindi has no cut-offs but falls from 26.9 to 2.2. It is the largest loss among 90 sentences. The traces are non-repeating searches for a January start date, not verbatim loops (0 of 92), and the sentence competes with the premise, so it is not irrelevant in the GSM-IC sense. Removing it takes the Hindi recurrence penalty from +4.5 to +0.3.
- Hindi traces mention distractors more (25.0% vs 8.5% time-related on the cleaner measure), and mention goes with lower accuracy in both languages on that measure (OR 0.77, 0.57). Mention is not uptake: 10 of 15 sampled Hindi unrelated mentions dismiss the sentence.

### RQ3. Does the reasoning language matter? (central claim)

**The candidate claim survives as a descriptive statement.** On the same 2,250 questions:

| Condition | Question / reasoning | Answered | Strict |
|---|---|---|---|
| English CoT | English / English | 88.9 | 86.0 |
| en-CoT | Hindi / English | 82.9 | 80.8 |
| Hinglish, English questions | English / Hinglish | 70.9 | 70.3 |
| CLP | Hindi / English, two turns | 70.3 | 69.9 |
| Hindi CoT | Hindi / Hindi | 59.4 | 59.0 |
| Hinglish, Hindi questions | Hindi / mostly Devanagari | 59.4 | 59.1 |

- **Decomposition.** Of the 29.5-point gap [28.1, 30.9], 23.5 [22.1, 24.9] closes by changing the reasoning language with the Hindi question fixed, and 6.0 [5.0, 7.1] remains (79.7% [76.4, 82.9]; strict 21.7, 5.2, 80.7%). The reasoning part exceeds the question part in every task and distractor condition, and at every level except short, where the interval includes zero. The direct-answer gap, with no reasoning at all, is 4.5 [3.3, 5.8], close to the 6.0.
- **Convergent evidence from trace structure.** Edit distance tracks reasoning language: English vs Hindi CoT 0.852, en-CoT vs Hindi CoT 0.837, English CoT vs en-CoT 0.730, against 0.713 between English traces of one question with and without a distractor and 0.959 between English and Hindi CoT traces of different questions (values in `figures/data/distance.csv`). Verification also follows reasoning language: 86.1% English CoT, 74.2% en-CoT, 1.3% Hindi CoT.
- **What it does not identify.** There is no English-question, Hindi-reasoning arm, so the split is one path and order-dependent. en-CoT's prompt also differs in wording. "English reasoning" bundles language with style (311 vs 212 median tokens, verification), and may include implicit translation. Verification explains the day-of-week residual (63.6% [39.8, 97.0]) but not the en-CoT gain (1.0% [-6.3, 9.0]).
- **Thinking mode is suggestive only.** Thinking-on Hindi CoT reaches 97.9 answered and 89.9 strict on 450 questions, and hidden reasoning is 79% English words. But budget (16,000 vs 4,096) and thinking change together: at a simulated 4,096 limit, strict Hindi CoT would be 43.8, below thinking-off at 59.9. Within Hindi traces a higher English share does not predict higher accuracy.

**CLP.** +10.9 [9.6, 12.2] over Hindi CoT in every condition (+9.0, +10.4, +13.2), and +15.1 [13.5, 16.7] over Hindi direct, but significantly worse on interval date (35.3 vs 46.8). en-CoT beats it by +12.6 [11.4, 13.9], **reversing the order Qin et al. report for GPT-3.5 on MGSM**. On date tasks stage 2 is right 97.5% of the time when stage 1 ends at the gold date and 20.1% when it does not, and that persists within question (+62.5 [57.1, 68.0]); the same split on en-CoT differs by only about 7 points. Qin et al. did note stage 1 may provide answers, so the behaviour is known and the size of the anchoring is what we add. CLP was run at temperature 0 (theirs: higher) with an added language rule.

**Hinglish.** Prompting for Hinglish lowers English accuracy by 18.0 [16.8, 19.2] (strict 15.7), on all nine tasks and in every condition. Hindi's mean does not move (-0.0 [-1.3, 1.2]), so the gap closes only because English falls. Task effects cancel: date duration -5.5, date subtraction +5.1. **The loss can't all be attributed to Hindi words.** Traces with no Hindi function words still lose 10.3 [8.3, 12.3], and verification on those traces falls from 86.5% to 18.6%. Roman traces lose 11.3 [9.0, 13.6] more within task, level and distractor, but style is self-selected. On Hindi questions, 73.1% of traces have at least 10% Devanagari and 68.5% a Devanagari majority, so the Hindi arm mostly tests Devanagari code-mixing. Romanising gives no advantage (-2.8 [-5.2, -0.5]). One shared failure: English date subtraction crossing a month falls from 90.1 to 42.3 (Hindi CoT 36.2), while same-month stays at 97.4.

**Hindi template.** Backward answers on recurrence are confined to k = 1 (en-CoT 67.1%, Hindi CoT 67.8%, CLP 69.0%, English CoT 3.5%), do not respond to reasoning language, and are almost absent at k = 2 to 4 (2 of 229), though those ordinals are equally non-standard. A second error, one step short, runs through every k. Together they make 76% of en-CoT recurrence errors. It is a real limitation for recurrence and the short level, and a small one for pooled results (removing k = 1 moves the gap from 6.0 to 5.3). The en-CoT gain at k >= 5 is +67.4 [62.6, 72.3], which the ordinal form can't explain. We did not rerun a corrected template. **A Hindi speaker on the team should confirm the template reading before it is printed.**

**Claims dropped.** "Fails on different questions" (φ is undefined in 10 to 11 of 45 cells, and each CoT condition agrees with itself across distractors only about as well: MH OR 1.58 English with itself vs 1.58 CLP vs English, 1.99 en-CoT vs English). "The gap shrinks with difficulty" for en-CoT depends on recurrence (+5.9 [2.3, 9.5] pooled, +0.8 [-2.5, 4.1] without k <= 2). "Understanding turn absorbs the distractor" (two thirds of the fall in mentions also appears in single-turn en-CoT).

### RQ4. Does trace divergence track correctness?

**The LR report's headline does not stand as a statement about reasoning.** RDS contains final-answer tokens, and the outcome depends on the answers. Replacing only Hindi's answer values in 11,309 both-correct pairs raises mean RDS by 0.082, which is 68% of the 0.120 observed gap.

| Token view | OR per SD | Added AUC, out of fold | Within-question concordance |
|---|---|---|---|
| All tokens (as reported) | 6.47 [5.94, 7.05] | +0.099 [0.093, 0.105] | 0.752 [0.739, 0.764] |
| No answer tokens | 1.65 [1.58, 1.73] | +0.017 [0.013, 0.020] | 0.596 [0.582, 0.610] |
| Op types, no answer ops | 1.14 [1.09, 1.18] | +0.0007 [-0.0004, 0.0018] | 0.516 [0.501, 0.530] |

- Comparing final answers alone gives AUC 0.951 for this outcome, above the full model's 0.853.
- RDS is highest on both-wrong pairs (0.925), which count as agreement. It tracks whether any trace failed, not cross-lingual disagreement.
- Within question, op-type divergence keeps a slope only in date recurrence (OR per 0.1, 1.42 [1.25, 1.61]) and day of week (1.26 [1.11, 1.43]).
- The op-type view has little resolution: it separates a different question from the same question by only +0.012, and wrong and right Hindi traces on one question do differ by +0.030 [0.021, 0.039]. So the null does not show "same route".
- **Mode.** "Reasoning ON lowers odds by 90%" is not defensible. On 450 matched questions, counting unanswered as wrong, disagreement is 31.7% vs 10.9% (OR 0.23 [0.18, 0.30]), and thinking and budget change together.
- **Normalisation.** RDS is 58 to 61% length floor in standard and reasoning. The team's open question is settled here by reporting both parts: RDS = floor + (1 − floor) × floor-adjusted. Raw RDS does not separate reasoning mode from standard (+0.005 [-0.002, 0.011]); floor-adjusted does (+0.088 [0.072, 0.105]).
- **Parser.** Coverage is 95 to 96% of standard CoT segments and 86 to 88% of reasoning segments. Token precision had never been measured: 85% (op), 77% (full), from one LLM reader on 240 tokens, not validated by a human. Standard-content conclusions move by at most about 0.004 under bounds on unparsed segments.

### RQ5. Do distractor mentions cause errors?

Part B's numbers all reproduce, but several conclusions overreach.

- **Q − P.** Among 526 wrong Hindi traces mentioning the time-related distractor before answering, resampling from the first mention gives 45.2% without the distractor and 40.0% with it (+5.3 [3.2, 7.4], p < 0.001). Treating the 29 sentences as the sample, the interval is [-0.3, +9.4]. The excess fraction is 8.8% [5.5, 12.1]; it is a lower bound on necessity under selection, so "fixes one error in eleven" is too strong. One sentence supplies 58% of the effect; without it, +2.8 [0.4, 5.0].
- **M − P.** Keeping the first-mention sentence lowers Hindi accuracy by 3.3 [1.2, 5.4], p = 0.002. The primary test against an ordinary sentence is not significant (-4.6 [-9.6, +0.6], p = 0.09), so it can't be separated from one more step along a trace that ended wrong.
- **"Mainly through the question" is dropped.** The design can't separate the two, because free continuations mention the distractor in 57.8% of rollouts. In later-mention traces, rollouts with no mention match the no-distractor arm (+0.0 [-4.8, +4.7]), and those with a mention don't (+8.7 [3.7, 13.6]).
- **"Experiment 1's null was real" is dropped.** It had about 24% power for a 5-point effect.
- **"Pre-registered" is removed.** Experiment 2's first commit is about 24.5 hours after its last round. Experiment 1's plan is verifiably earlier.
- **Non-completion** rises from 5.7% to 10.0% in self-hosted Hindi rollouts but not on the API (0.81% to 0.89%), where the rise is in English (2.87% to 4.49%).
- **Calibration.** Self-hosted FP8 vs API is -2.2 [-13.3, 7.8] on 90 questions, which can't establish sameness. English FP8 scored 24.7 points below the API on 22 opening traces, so we make no causal claim for English.
- **No interventional data exist on originally correct traces.**

## Contradictions resolved

| Conflict | Resolution |
|---|---|
| Hindi penalty +2.2 (Part A, baseline) vs +2.59 (Part B) | Different quantities: penalty vs drop. Part B's code at `verify.py:308` confirms it. |
| Part A vs Part C intervals for the same contrast | Monte Carlo error. One seed in `headline.py`. |
| Part C "comes from reading the Hindi question" vs Hinglish "reasoning in either script" | Both overreach. Backward answers are specific to k = 1 of one template. Reasoning language matters more than question language, descriptively, and script is not crossed with language. |
| ANALYSIS.md "+0.005 on step types" vs LR's significant FE slope 1.07 | Same direction, different samples; both are near null and limited by the op view's resolution. |
| Verification 74.2 vs 74.8 for en-CoT | Regex vs parser CHECK/REVISE. The paper uses the regex. |
| Mid-report and FINDINGS: 4 starred Hindi tasks | Uncorrected intervals. Two survive Holm. |
| Note in my planning: "ED rests on an old parser" | Wrong. Stored parses are byte-identical to the current parser on the checked split. |

## Important limitations

1. One model, greedy decoding, one prompt per condition, one dataset seed, two languages. CIs cover question sampling only.
2. Runs span 29 Sep to 30 Oct, and the provider changed its usage schema in that time, so condition and date are partly confounded.
3. Reasoning language and prompt wording are confounded in every comparison across prompting conditions.
4. CLP, en-CoT and Hinglish use the first 50 questions per cell. That subset is effectively random for accuracy, but too small for distractor contrasts of 1 to 3 points (a penalty varies with SD 1.2 from subset choice alone).
5. Hindi distractors are not literal translations (0.81 of the English word count, three statements become questions). English-Hindi distractor comparisons aren't strictly parallel.
6. Distractor sentences are a fixed pool, assigned unevenly across tasks; the generator's seed reset makes levels share sentence mixes.
7. Mention, verification and trace style are lexical or self-selected, so they are observational.
8. All hand-labelled samples (parser precision, stage 1, mention precision, template review) were read by one LLM agent. None was validated by a person.
9. The interventions cover only wrong traces, only time-related distractors, on a quantised self-hosted model at temperature 0.8.
10. Thinking-mode data has 10 questions per cell and a fourfold token budget.

## Figures

All are built by `figures/make_figures.py` from audit `fig_data/` CSVs, with the same data and chart type as the originals. New figures are marked.

| File | Source | Placement |
|---|---|---|
| design example (TikZ) | new, real records | main |
| `by_level` | Part C, Fig. C1 | main |
| `decomposition` | new (Part C audit) | main |
| `distance` | new (ED audit) | main |
| `lr_forest` | new (LR audit) | main |
| `interventions` | Part B, Fig. B1 | main |
| `task_bars` | Part C, Fig. C2 | appendix |
| `hinglish_tasks`, `hinglish_style` | Hinglish, Figs. 1, 3 | appendix |
| `recurrence_k` | new (Part C audit) | appendix |
| `ed_task_difficulty`, `ed_outcome` | ANALYSIS.md, `newplot (2)`, `newplot (3)` | appendix |
| `lr_bins` | LR, Fig. 2 | appendix |
| `hinglish_level`, `hinglish_bytask`, `lr_hist`, `ed_task_set`, `ed_set_box`, `ed_insertion_difficulty` | remaining originals | repo only; two-page appendix limit |
