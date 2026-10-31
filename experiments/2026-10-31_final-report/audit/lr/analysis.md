# Audit of `docs/final/lr_report.pdf`: RDS and English/Hindi correctness disagreement

Saved by the main session from the audit agent's hand-back, because the harness refused the agent's own write of this file. Content is the agent's, unchanged.

Conventions: "answered" drops pairs where either language has no answer line, which is the report's convention. "Strict" counts no answer as wrong. Odds ratios (OR) come from logits with SEs clustered by question unless stated. Rates use the cluster bootstrap over questions (B = 2000). All tables are in `tables/`; the table for the paper is `corrected_regression_table.csv`.

## Verdict

| Headline claim | Verdict |
|---|---|
| Table 1, Table 2, 31.4%, 92%, 0.809 and 0.917, 80% | The numbers reproduce from raw data. Four table values differ by 0.01 from double rounding, and the printed CI is unclustered. |
| "A 0.1 increase in RDS multiplies the odds by 4.93" | The number holds, but most of it is built in. RDS contains the answer tokens and the outcome depends on the answers. Without answer tokens the OR per 0.1 is 1.68; on op types without answers it is 1.10. |
| "RDS is a useful signal" | Not supported. On op types without answers it adds 0.0007 AUC [-0.0004, 0.0018] out of fold. Comparing the two final answers alone gives AUC 0.951. |
| "Length differences do not explain the association" | Not supported. The negative coefficient comes from RDS being bounded below by the length gap, and it disappears once answer tokens are removed. |
| "Reasoning ON lowers the odds by about 90% (OR 0.10)" | The number holds, but the wording does not. It conditions on a post-treatment variable, drops 11.8% of ON pairs, and bundles reasoning with a fourfold token budget. Strict and matched, the OR is 0.23 [0.18, 0.30]. |
| "Reliable" column | Correct as a check that the optimiser worked, and misleading as a label. |

**Strongest defensible statement.** In Sarvam-105B with thinking off, pairs where exactly one language is correct have more dissimilar reasoning tokens than other pairs, but the raw RDS gap mostly restates that the final answers differ. With answer tokens removed, a 1 SD rise in RDS goes with 1.65 times the odds of disagreement [1.58, 1.73], and it adds 0.017 AUC [0.013, 0.020] beyond task, difficulty, distractor and mode. Those remaining tokens still carry values downstream of an error. Comparing op types alone, with no answer tokens, the OR per SD is 1.14 [1.09, 1.18], added AUC is indistinguishable from zero, and within-question concordance is 0.516 [0.501, 0.530]. Only date recurrence and day of week keep a within-question op-type slope after Holm correction. We find little evidence that a different sequence of reasoning operations marks cross-lingual disagreement outside those two tasks.

## Data existence

| Item | Exists | Check |
|---|---|---|
| `experiments/2026-10-29_ed-analysis/parsed/{standard,ron}/*.p.json` | yes | 8,100 CoT records per difficulty in standard, 540 in ron. 20,250 and 1,350 pairs, matching the design (6,750 and 450 questions times 3 distractors). |
| `experiments/2026-10-29_ed-analysis/edout/{standard,ron}/*.csv` | yes | My rebuild matches on all 21,600 rows: RDS max abs diff 0, reasoning RDS max abs diff 0, 0 correctness mismatches. |
| `experiments/2026-10-30-LR-aayush/rds_regression.py` | yes | It reads `ROOT/edout`, which is not in that folder, so it cannot run as committed. Its inputs must have been equivalent to the 10-29 CSVs, since every table value reproduces. |
| `lr_out/` figures, `findings.md`, 6 `summary_*.txt` | yes | Used for comparison. |
| `lr_out/` CSVs listed in `findings.md` (`analysis_dataset.csv`, `rds_results.csv`, `coef_*`, `desc_*`, `exclusions.csv`, `mann_whitney.csv`, `separation_*`, `predicted_probability_primary.csv`) | **missing** | `*.csv` is git-ignored and they are not on disk. Recomputed here. |
| LR copy of `ed.py` | yes, differs from root | It handles empty token lists differently. `findings.md` reports "RDS missing 0", whereas the current CSVs have 153 missing (all ON, all among excluded pairs). No effect on the fitted sample: all 20,662 answered pairs have RDS. |

`verify.py` and `build_pairs.py` do not import the report's code. The answer regex, the weekday rule and the partial-date cost are retyped from the definitions in `metrics.py` and `ed.py`, because they define the quantity. The token classes follow `tests/ed_audit/cube_variants.py`. Tokens come from the stored `parser.py` output in `parsed/`, per the brief.

## Corrected results

### 1. Leakage

RDS is computed over tokens that include `ANSWER` and `SPITANSWER`. Those are 2.6 to 12.9% of an English trace and 8.8 to 20.7% of a Hindi trace, depending on task (`t8_answer_token_share_by_task.csv`). A wrong answer changes them by construction.

A direct test: on the 11,309 both-correct OFF pairs, I replaced only the values in Hindi's answer tokens. Mean RDS rose from 0.798 to 0.879, or +0.082. The observed gap between disagreeing and both-correct pairs is 0.120, so this one edit, with no change to the reasoning, reproduces 68% of it.

Table: 20,648 answered pairs with every token view non-empty (6,482 disagreements). Primary is `disagree ~ view + difficulty + task + insertion + mode`; length-adjusted adds that view's length gap. The fixed-effect (FE) columns are conditional logits on OFF only, 3,172 questions with varying outcome, with insertion dummies and bootstrap CIs. ORs per 0.1 are not comparable across views because their SDs differ, so use the per-SD column.

| Token view | Model | OR per SD | OR per 0.1 | AME pp per 0.1 | AUC full model | AUC view alone | Out-of-fold (CV) added AUC | FE OR per 0.1 | Within-q concordance |
|---|---|---|---|---|---|---|---|---|---|
| Full (report) | primary | 6.47 [5.94, 7.05] | 4.92 [4.58, 5.30] | 22.9 | 0.853 | 0.798 | +0.099 [0.093, 0.105] | 4.32 [3.87, 4.85] | 0.752 [0.739, 0.764] |
| | length-adj. | 7.49 [6.86, 8.19] | 5.58 [5.17, 6.02] | 24.5 | 0.856 | | | | |
| (a) No answer tokens | primary | 1.65 [1.58, 1.73] | 1.68 [1.60, 1.76] | 9.0 | 0.771 | 0.630 | +0.017 [0.013, 0.020] | 1.58 [1.47, 1.69] | 0.596 [0.582, 0.610] |
| | length-adj. | 1.64 [1.57, 1.72] | 1.67 [1.59, 1.75] | 8.9 | 0.771 | | | | |
| (a+) Also no answer-valued tokens | primary | 1.52 [1.45, 1.58] | 1.51 [1.45, 1.58] | 7.2 | 0.767 | 0.620 | +0.013 [0.010, 0.016] | 1.40 [1.32, 1.50] | 0.572 [0.559, 0.587] |
| | length-adj. | 1.51 [1.44, 1.58] | 1.50 [1.44, 1.57] | 7.1 | 0.767 | | | | |
| (b) Op types | primary | 1.21 [1.16, 1.26] | 1.14 [1.11, 1.18] | 2.4 | 0.756 | 0.624 | +0.002 [0.000, 0.003] | 1.07 [1.03, 1.12] | 0.522 [0.508, 0.536] |
| | length-adj. | 1.16 [1.10, 1.22] | 1.11 [1.07, 1.15] | 1.8 | 0.756 | | | | |
| (b+) Op types, no answer ops | primary | 1.14 [1.09, 1.18] | 1.10 [1.07, 1.13] | 1.7 | 0.755 | 0.594 | +0.001 [-0.000, 0.002] | 1.07 [1.02, 1.11] | 0.516 [0.501, 0.530] |
| | length-adj. | 1.08 [1.03, 1.14] | 1.06 [1.02, 1.10] | 1.1 | 0.755 | | | | |
| First 8 op types | primary | 1.07 [1.03, 1.10] | 1.04 [1.02, 1.06] | 0.7 | 0.755 | 0.555 | +0.001 [-0.000, 0.001] | 1.04 [1.01, 1.08] | 0.516 [0.504, 0.529] |
| | length-adj. | 1.03 [0.99, 1.07] | 1.02 [1.00, 1.04] | 0.3 | 0.766 | | | | |

Controls alone give in-sample AUC 0.755, so most of the "full model" AUC in the lower rows comes from the controls.

The no-answer view still leaks. An error changes later operands, and removing tokens that hold the final value lowers the OR per SD only to 1.52. That residual can't separate "a different route" from "the same route with a wrong number".

Within-question, restricted to English right and Hindi flipping (2,356 questions, `t8_flip_types.csv`): RDS +0.087 [0.083, 0.091], no-answer +0.027 [0.023, 0.031], op types without answers +0.005 [-0.000, 0.011]. This agrees with `tests/ed_audit/outputs/cube_findings/FINDINGS.md`.

**By distractor** (primary, pooled, OR per 0.1): full 5.37, 4.60, 4.95 for none, similar, dissimilar; no answers 1.78, 1.62, 1.65; op types without answers 1.13, 1.08, 1.09. The RDS by distractor interaction is not significant except at the margin on op types (OFF: full p = 0.64, no answers p = 0.40, ops p = 0.050, op types without answers p = 0.20). The conclusion holds in each condition. Within-question concordance by distractor contrast is in `t8_within_question_by_insertion_contrast.csv`.

### 2. Added predictive value

10-fold cross-validation with folds grouped by question (`t10_cv_delta.csv`, `t10_cv_auc.csv`). Baseline is task + difficulty + insertion + mode, AUC 0.753. With task by difficulty, AUC is 0.771. Interval is a question bootstrap on the out-of-fold predictions.

| Added to baseline | All | None | Similar | Dissimilar |
|---|---|---|---|---|
| Full RDS | +0.099 [0.093, 0.105] | +0.101 | +0.103 | +0.096 |
| No answer tokens | +0.017 [0.013, 0.020] | +0.018 | +0.018 | +0.016 |
| Op types, no answers | +0.0007 [-0.0004, 0.0018] | +0.0018 [0.0001, 0.0039] | +0.0014 [-0.0005, 0.0035] | +0.0005 [-0.0014, 0.0024] |
| Same, richer baseline | +0.0019 [0.0009, 0.0030] | +0.0034 | +0.0012 | +0.0025 |

The two trace lengths alone reach AUC 0.769, about the same as no-answer RDS (0.770). Adding op-type RDS to the lengths gives 0.769, so nothing more.

The full-RDS gain is not a useful signal, because the question it answers is available more cheaply. A disagreement implies differing answers, so the rule "the two final answers differ" has recall 1.00, precision 0.82 and AUC 0.951 on all 20,662 pairs, above the full model's 0.853.

RDS also doesn't track disagreement specifically. In OFF, both-wrong pairs have the highest RDS and count as agreement (`t9_rds_by_outcome.csv`):

| Outcome | n | Full | No answers | Op types, no answers |
|---|---|---|---|---|
| Both correct | 11,309 | 0.798 | 0.862 | 0.712 |
| English only | 5,947 | 0.917 | 0.910 | 0.763 |
| Hindi only | 505 | 0.925 | 0.920 | 0.779 |
| Both wrong | 1,710 | 0.925 | 0.927 | 0.816 |

RDS separates "both correct" from everything else (AUC 0.847 for any wrong, 0.789 for disagree). Against both-wrong pairs, disagreement has lower raw RDS (AUC 0.434). Adjusted for task and difficulty the sign turns positive (OR 1.54 [1.38, 1.72]).

### 3. Mode

Same 450 questions, OFF vs ON (`t11_*.csv`):

| | OFF | ON |
|---|---|---|
| Pairs missing an answer in at least one language | 3.4% | 11.8% |
| Disagreement, answered | 31.5% [28.4, 34.8] | 2.6% [1.7, 3.6] |
| Disagreement, strict | 31.7% | 10.9% |
| English accuracy, strict | 87.3% | 92.7% |
| Hindi accuracy, strict | 59.9% | 89.9% |
| Mean content RDS | 0.849 | 0.750 |
| Mean content tokens EN / HI | 55 / 18 | 17 / 14 |

Strict OFF and ON by distractor: none 30.9 and 11.6, similar 31.6 and 10.9, dissimilar 32.7 and 10.2. All three hold.

| Mode OR, ON vs OFF | OR [95% CI] |
|---|---|
| Report: all questions, conditioning on content RDS | 0.098 [0.066, 0.144] |
| All questions, no RDS | 0.046 [0.031, 0.068] |
| Matched 450, conditioning on content RDS | 0.106 [0.067, 0.167] |
| Matched 450, no RDS | 0.049 [0.032, 0.077] |
| Matched 450, strict, no RDS | 0.214 [0.165, 0.278] |
| Same prompt, exact McNemar, answered (337 vs 19) | 0.056 [0.034, 0.089] |
| Same prompt, exact McNemar, strict (367 vs 86) | 0.234 [0.183, 0.297] |

The 90% figure comes from one specification and is not defensible as an effect of reasoning. RDS sits downstream of the mode and is measured on a different kind of text, so conditioning on it is wrong. The strict figure is about a 77 to 79% reduction in odds.

The budget matters too. In ON, 31% of English and 56% of Hindi responses used more than 4,096 tokens. Had those stopped there with no answer, strict ON disagreement would be 30.2% against 31.7% for OFF (`t11_budget_sensitivity.csv`). That is an arithmetic bound rather than a rerun, since a model given 4,096 tokens may behave differently, but it shows that mode and budget can't be separated with this data.

Suggested wording: "On the same 450 questions, a thinking-on run (`reasoning_effort: low`, 16,000 tokens) disagreed on 10.9% of pairs against 31.7% for the standard run (4,096 tokens), counting unanswered as wrong (matched OR 0.23 [0.18, 0.30]). The two runs differ in both thinking and budget, so the comparison does not isolate either."

ON slopes with Firth fits, 31 events in 29 questions (`t12_on_firth.csv`, `t12_on_auc.csv`):

| Channel and view | Firth OR per 0.1, profile CI | AUC [cluster CI] |
|---|---|---|
| Content, full | 7.46 [4.21, 14.32] | 0.860 [0.793, 0.920] |
| Content, no answers | 1.69 [1.17, 2.56] | 0.644 [0.533, 0.741] |
| Content, op types no answers | 1.31 [1.01, 1.74] | 0.599 [0.500, 0.706] |
| `reasoning_content`, full | 3.43 [1.73, 7.34] | 0.702 [0.621, 0.783] |
| `reasoning_content`, no answers | 2.76 [1.46, 5.60] | 0.681 [0.596, 0.766] |
| `reasoning_content`, op types no answers | 1.86 [1.20, 2.89] | 0.631 [0.538, 0.721] |

The visible content is a short summary, so answer tokens weigh more in it and the content slope is inflated. The reasoning channel keeps a weak positive association, with wide intervals. On the same 450 questions in OFF, ORs per 0.1 are 4.10 [3.15, 5.34], 1.50 [1.25, 1.81], and 1.06 [0.95, 1.19] on op types without answers. ORs across these samples are not directly comparable (Mood 2010).

### 4. Exclusions

The 938 dropped pairs are informative (`t13_*.csv`). Of 991 missing answers, 987 stopped at the token limit, so "could not be parsed" misdescribes them. Exclusion depends strongly on task (Wald chi-squared 819, 8 df) and difficulty (151, 4 df), with AUC 0.887 for the exclusion model. It reaches 19.6% in day_of_week, 9.1% in date_recurrence and 6.5% in interval_date, against under 2% in the others. By distractor it is 4.0%, 5.7% and 3.3%. In OFF, when English has no answer, Hindi is right only 20.2% of the time, against 60.7% overall. Excluded OFF pairs have RDS 0.972, against 0.849 for included pairs.

| Scenario (`t14_exclusion_sensitivity.csv`) | n | Rate | OR per 0.1 |
|---|---|---|---|
| Answered (report) | 20,662 | 31.4% | 4.92 [4.58, 5.30] |
| Strict, RDS defined | 21,447 | 31.3% | 4.13 [3.87, 4.41] |
| Strict, undefined RDS set to 1 | 21,600 | 31.6% | 4.23 [3.96, 4.52] |
| Bound: excluded counted as agreement | 21,447 | 30.2% | 3.82 [3.58, 4.07] |
| Bound: excluded counted as disagreement | 21,447 | 33.9% | 5.29 [4.91, 5.69] |
| Strict, no answer tokens | 21,446 | 31.3% | 1.56 [1.49, 1.63] |
| Strict, op types no answers | 21,446 | 31.3% | 1.05 [1.02, 1.08] |

The slope's sign survives every scenario. Within question on strict outcomes, op types without answers are null: 1.02 [0.98, 1.06]. The main damage is to mode: ON disagreement moves from 2.6% to 10.9%, while OFF barely moves (33.1% to 32.9%). The English share of disagreements goes from 92.0% to 89.9% overall, and in ON it is 62.6%.

### 5. Length

Collinearity is moderate rather than severe: r = 0.49, Spearman 0.52, VIF 1.55 (RDS) and 1.65 (gap), with no floor violations (`t15_length_collinearity.csv`). The floor equals 56% of mean RDS. So the problem with the report's inference is its logic, not unstable estimates.

The gap coefficient is +0.62 [0.46, 0.78] on its own and -1.19 [-1.36, -1.02] once RDS is in the model. RDS = gap + excess, so the same model can be written with floor +16.01 and excess +17.20, with identical likelihood. The negative sign says only that a unit of floor counts slightly less than a unit of excess. It is not evidence that length plays no part. It also goes away when answer tokens are removed: +0.07 [-0.09, 0.22] with no-answer RDS, +0.29 [0.10, 0.49] with op types without answers.

Length also does explain part of the op-type association: OR per SD falls from 1.14 to 1.08 with the gap added. Within length-gap bands in OFF, full RDS stays strong in every band (5.98, 5.02, 6.85, 8.24, 13.58), no-answer RDS also (1.46 to 2.92), and op types without answers include 1 in all five bands (1.01, 1.04, 1.08, 0.99, 1.08). Median English length runs 18, 41, 58, 79 tokens for both correct, English only, Hindi only, both wrong; Hindi runs 11, 15, 15, 19.

### 6. Table values and scaling

All Table 1 and Table 2 values reproduce, except four differing by 0.01 from rounding an already rounded value: OR 4.93 (4.9246), CI 6.03 (6.0250), OR 11.79 (11.7847), CI 28.37 (28.3647). The correct values are 4.92, 6.02 or 6.03, 11.78 and 28.36.

- **24.0 and 4.6.** They are not copies: 23.96 and 24.02, 4.60 and 4.64. They round alike because AMEs change little when controls are added, which is the property Mood (2010) describes.
- **AME scaling.** The column is the derivative times 0.1, so 22.9 = 15.94 x 0.1439 x 10. A step of +0.1 actually gives 23.9 uncapped or 19.8 capped at RDS 1, and 37.5% of pairs sit above 0.9. It is plausible against a 31.4% base rate only as an average tangent. Observed OFF bin steps are +6.6, +18.5 and +29.5 pp, so a flat "23 points per 0.1" fits nowhere in particular. In ON, 4.6 pp exceeds the 2.6% base rate; +0.1 capped gives 7.9 to 8.3.
- **80%.** U share is 0.798, counting ties as half. Strictly greater is 0.796. Cluster CI [0.792, 0.805]. OFF 0.789. By distractor in OFF 0.794, 0.784, 0.788.
- **31.4% CI.** The printed [30.7, 32.0] is Wilson (30.747, 32.013), which ignores clustering. Clustered is [30.6, 32.2]. Strict is 31.6% [30.8, 32.3].
- **Figures.** Figures 1 and 2 match the recomputed values. The text cites Figure 2 for "predicted" disagreement, though it shows observed rates. Observed rates below 0.7 are 0 to 2.7%, and the rise starts near 0.75 rather than above 0.8. Adjusted predictions are in `t5_adjusted_predictions.csv`.
- **Bin rates** (OFF): 0, 0, 2.7, 2.6, 9.2, 27.7, 57.2%. ON: 0, 0, 0, 1.2, 2.9, 13.8%. Clustered CIs are in `fig2_rate_by_rds_bin.csv`.
- **Distractors.** "Almost no effect" holds. Paired in OFF against no distractor: similar +1.1 pp [-0.3, 2.4], dissimilar +1.5 pp [0.1, 2.9]; strict +0.2 [-1.1, 1.5] and +1.7 [0.2, 3.0].
- **Difficulty.** "Rises" is loose: 26.7, 26.4, 29.3, 36.2, 38.6.

### 7. Convergence and separation

"No" for ON adjusted is correct: not converged, time_duration coefficient -22.6, 0 of 146 disagreements, 2.1 events per parameter. "Yes" for ON RDS-only is defensible numerically. The fit converges, the MLE is finite, leave-one-question-out beta runs 19.4 to 22.9, and Firth gives 7.46 against 7.74. But statsmodels prints a quasi-separation note because 40.5% of agreeing pairs lie below the lowest RDS of any disagreement (0.733). The script's check doesn't react to that note. A Firth fit makes the adjusted model estimable: 9.73 with profile CI [5.17, 19.55] and cluster bootstrap [1.60, 24.74]. The gap between those intervals shows how little 31 events can support, and 2.1 events per parameter remains far below the range Peduzzi et al. (1996) found safe. Advice to read only the unadjusted model removes all controls, and it inherits the leakage. "Reliable" should be renamed "Converged".

### 8. Linear logit

The linear form ranks and calibrates acceptably for full RDS, with deciles within about 2 points (`t16_calibration.csv`), but a single OR misdescribes it. Piecewise OR per 0.1 is 2.36 below 0.7, 4.54 from 0.7 to 0.9, 6.44 above 0.9 (cluster Wald chi-squared 28.6, 2 df, p < 0.001). A 5 df spline lowers AIC by 70 and BIC by 46, with AUC 0.854 against 0.853. For no-answer RDS, the relation is not monotone at the top: the last two deciles are 52.8% and 36.4%, while the linear fit gives 41.7% in the last. For op types without answers, the pattern reverses: 1.20 below 0.7, 1.03 and 0.96 above. Report the spline curve or the bin rates, with any single OR labelled as an average.

### 9. Splits by task

OFF, OR per 0.1 with difficulty and distractor controls, Holm within view (`t17_splits.csv`), and FE within question (`t17_splits_within_question.csv`):

| Task | Full | No answers | Op types, no answers | FE op types, no answers |
|---|---|---|---|---|
| date_addition | 6.99 | 1.45 | 0.97 [0.87, 1.09] | 0.96 [0.83, 1.11] |
| date_duration | 16.06 | 2.18 | 1.10 [0.96, 1.25] | 1.05 [0.90, 1.23] |
| date_recurrence | 4.02 | 2.33 | **1.49 [1.34, 1.64]** | **1.42 [1.25, 1.61]** |
| date_subtraction | 8.44 | 1.54 | 0.97 [0.89, 1.05] | 1.03 [0.91, 1.15] |
| day_of_week | 1.83 | 1.43 | **1.22 [1.11, 1.34]** | **1.26 [1.11, 1.43]** |
| interval_date | 2.40 | 1.49 | 0.98 [0.89, 1.08] | 1.08 [0.96, 1.21] |
| time_addition | 4.46 | 1.46 | **1.11 [1.03, 1.19]** | 0.98 [0.88, 1.08] |
| time_duration | 10.40 | 2.41 | **1.18 [1.06, 1.31]** | 1.10 [0.95, 1.27] |
| time_subtraction | 5.32 | 1.38 | 1.02 [0.94, 1.11] | 0.87 [0.77, 0.98] |

Bold survives Holm. Full and no-answer slopes are positive in all nine tasks, but they vary widely (task interaction Wald 308 on full, 8 df). Full-RDS slopes are smallest where answer tokens are the smallest share of the trace (day_of_week, interval_date). On op types without answers, the slope exists in four of nine tasks across questions and two of nine within question. time_subtraction runs the other way within question (nominal p = 0.025, Holm 0.18). With English right and Hindi flipping, date_recurrence is the only clear positive (concordance 0.656 [0.608, 0.701]); day_of_week is 0.558 [0.497, 0.618], and interval_date (0.427) and time_subtraction (0.445) reverse (`t8_hindi_flip_by_task.csv`). By difficulty, op types without answers survive Holm only at short and very_very_long, with no clear trend (`t17_splits.csv`).

## Limitations

**Threats the report doesn't mention:**

- The outcome is partly built into the predictor. This is the main defect.
- Removing answer tokens does not end the leakage, since errors propagate to later operands. Op types are the only view free of values, and they can miss a real difference in route, because two routes can share op names.
- Op-type RDS is affected by a structural asymmetry: CHECK/REVISE appears in 88% of English traces and 3.7% of Hindi traces (prior audit). The pre-CHECK views partly address this.
- Parser coverage differs by language (94% vs 89% on ron short content), which can attenuate the op-type slope. Date recurrence shows the measure can detect an effect, but the null elsewhere is only as good as the parser.
- The trace may not be the computation (Turpin et al. 2023; Lanham et al. 2023).
- ON "reasoning" in the report is the visible summary.
- ON and OFF differ in thinking, token budget and question count together.
- Exclusion depends on task and outcome.
- Both-wrong pairs count as agreement although their answers usually differ (1,388 of 1,710).

**Not run here:** repeated sampling per prompt, trace interventions (swapping, truncation, error injection), a thinking-on run at 4,096 tokens or a thinking-off run at 16,000, and other models. One model at temperature 0 gives one generation per prompt, so generation noise can't be separated from systematic effects.

**Cannot be concluded from this design:** that divergence causes errors, that errors cause divergence beyond the mechanical part, that thinking itself narrows the gap, or anything about other models.

**Choices of mine that affect these numbers:** the prefix length of 8 is arbitrary. Fold assignment uses one seed. Bootstrap counts below convention: B = 1000 for added AUC, 300 in distractor splits and task AUCs, 500 for Firth and ON AUCs. Holm is applied within view, with no correction across the many views. The corrected table uses 20,648 pairs so that all views share a sample, so its full-RDS row differs from the report's 20,662 in the third decimal.

## Design rationale from prior work

- **Normalised edit distance** extends Levenshtein's measure to parsed op tokens. Dai et al. (2024) apply minimum edit distance to CoT pairs, but to locate pivotal steps, not as a predictor. That is a defensible use of the metric, with two departures of ours: partial-date cost, and normalising by the longer length, which creates the length floor.
- **Separating answer from step scores.** FinChain's ChainEval scores final answers and step consistency as separate components, and process-mining work scores structural deviation. RDS merges them. The corrected table separates them.
- **Cross-lingual trace comparison.** Zhao et al. (2025) test consistency by swapping traces between languages and test faithfulness by perturbation. Our design is observational and cheaper, and it can only support association. Lanham et al. (2023) intervene on the CoT for the same reason.
- **Clustered logit.** Clustering by question follows Cameron and Miller (2015), and 6,739 clusters is ample in the pooled model. ON has 430 clusters but only 29 with an event, so the asymptotics are weak there, which is why I use the Firth profile and the cluster bootstrap together.
- **Conditional logit.** Chamberlain (1980) gives the right tool for removing question effects, and it uses only questions whose outcome varies (3,172 of 6,739). It answers a narrower question, about what changes across distractor variants of the same question.
- **AMEs and per-SD effects.** Mood (2010) warns against comparing ORs across models and samples, which is what a side-by-side table tempts. Per-SD and AME columns reduce the problem without removing it.
- **Firth and events per variable.** Firth's method gives finite estimates under separation (Ogawa and Tomo 2023, secondary source). Peduzzi et al. (1996) is the reference for events per variable. Heinze and Schemper (2002), Firth (1993) and Liang and Zeger (1986) are `UNVERIFIED`; see `citations.md`.

## Missing findings

All exploratory. OFF unless stated.

1. **Answer-token edit alone reproduces most of the gap.** n = 11,309 both-correct pairs, +0.082 RDS, 68% of the 0.120 observed gap. No interval computed; the estimate is a mean over the full stratum.
2. **Final-answer comparison beats RDS for this outcome.** n = 20,662, AUC 0.951, recall 1.00, precision 0.82, against model AUC 0.853. No interval computed.
3. **RDS is highest on both-wrong pairs.** n = 1,710, RDS 0.925, against 0.917 English-only. AUC for disagree vs both-wrong 0.434, adjusted OR per 0.1 1.54 [1.38, 1.72].
4. **Early divergence hardly matters.** First 8 op types, n = 19,467 within OFF, 3,172 FE questions: FE OR per 0.1 1.04 [1.01, 1.08], concordance 0.516 [0.504, 0.529].
5. **Recurrence and day of week are the exceptions.** FE ORs 1.42 [1.25, 1.61] (418 questions) and 1.26 [1.11, 1.43] (416 questions). These two tasks also have the highest disagreement (68.2% and 58.2%), and day_of_week the most exclusions.
6. **Token budget accounts for the arithmetic of the mode gap.** n = 1,350 ON pairs. Cap at 4,096 used tokens gives strict disagreement 30.2% (no interval; a bound, not a rerun) against 31.7% in OFF.
7. **The ON reasoning channel keeps a weak op-type association.** n = 1,191, 31 events, Firth OR per 0.1 1.86 [1.20, 2.89], AUC 0.631 [0.538, 0.721].

## Suggested claims for the paper

1. **Strong.** "RDS as first defined includes final-answer tokens, so it rises by construction when one language is wrong: replacing only Hindi's answer values in 11,309 both-correct pairs raises mean RDS by 0.082, which is 68% of the observed gap of 0.120."
2. **Strong.** "Adjusting for task, difficulty, distractor and mode, the odds ratio per SD of RDS falls from 6.47 [5.94, 7.05] with answer tokens to 1.65 [1.58, 1.73] without them and 1.14 [1.09, 1.18] on operation types alone. The pattern holds in each distractor condition."
3. **Strong.** "Operation-type divergence adds no measurable out-of-fold discrimination beyond those controls (added AUC 0.0007 [-0.0004, 0.0018], question-grouped cross-validation), and within a question it barely separates disagreeing from agreeing variants (concordance 0.516 [0.501, 0.530])."
4. **Moderate.** "Within a question, an association between operation-type divergence and disagreement appears only in date recurrence (OR per 0.1, 1.42 [1.25, 1.61]) and day of week (1.26 [1.11, 1.43]) after Holm correction."
5. **Strong.** "RDS is highest on pairs where both languages are wrong (0.925), which count as agreement, so it tracks whether any trace failed rather than cross-lingual disagreement."
6. **Moderate.** "On the same 450 questions, a thinking-on run at a 16,000-token budget disagreed on 10.9% of pairs against 31.7% for the standard run at 4,096 tokens, counting unanswered as wrong (matched OR 0.23 [0.18, 0.30]). Thinking and budget change together, so this does not isolate either."
7. **Moderate.** "Excluding 938 unanswered pairs is not neutral: nearly all are token-limit cut-offs concentrated in day of week (19.6%) and date recurrence (9.1%). Counting them as wrong leaves the OFF disagreement rate near 33% but raises the ON rate from 2.6% to 10.9%."
8. **Suggestive.** "In the thinking-on reasoning channel, operation-type divergence is weakly associated with disagreement (Firth OR per 0.1, 1.86 [1.20, 2.89]), based on only 31 disagreements."
