# RDS and English/Hindi correctness disagreement: logistic regression

Observational analysis of existing Sarvam-105B outputs; no inference was rerun.

## Data

- Inputs: `edout/ron/*.csv` (reasoning ON) and `edout/standard/*.csv` (reasoning OFF); the pair table after the `question_id,...` header line is read, the aggregate block above it is ignored.
- Pairs loaded: 21600 (Reasoning OFF: 20250, Reasoning ON: 1350).
- Underlying question id `uid = difficulty|task|question_id` (question ids repeat across tasks and difficulties; the three insertion variants share a uid). Unique uids: 6750; present in both modes: 450.
- RDS = `content_norm_edit_distance`. disagree = 1 iff `en_correct != hi_correct`.

## Exclusions

- all: 938/21600 pairs excluded (4.3%): English answer unparseable 735, Hindi unparseable 256, RDS missing 0.
- on: 159/1350 pairs excluded (11.8%): English answer unparseable 84, Hindi unparseable 110, RDS missing 0.
- off: 779/20250 pairs excluded (3.8%): English answer unparseable 651, Hindi unparseable 146, RDS missing 0.

Missing correctness was never converted into a disagreement label. Both models use the identical sample.

## Descriptives (analysed sample)

- Paired observations: 20662; unique questions: 6739.

| mode | both correct | EN only | HI only | both wrong | disagreement rate |
|---|---|---|---|---|---|
| all | 12468 | 5967 | 516 | 1711 | 31.4% |
| on | 1159 | 20 | 11 | 1 | 2.6% |
| off | 11309 | 5947 | 505 | 1710 | 33.1% |

| mode | RDS mean | median | SD | min | max |
|---|---|---|---|---|---|
| all | 0.843 | 0.867 | 0.117 | 0.000 | 1.000 |
| off | 0.849 | 0.875 | 0.114 | 0.000 | 1.000 |
| on | 0.750 | 0.769 | 0.134 | 0.167 | 1.000 |

| mode | disagree | n | RDS mean | RDS median |
|---|---|---|---|---|
| all | 0 | 14179 | 0.809 | 0.828 |
| all | 1 | 6483 | 0.917 | 0.933 |
| off | 0 | 13019 | 0.814 | 0.833 |
| off | 1 | 6452 | 0.918 | 0.933 |
| on | 0 | 1160 | 0.746 | 0.769 |
| on | 1 | 31 | 0.909 | 0.923 |

Mann-Whitney U (RDS, disagree vs agree; unadjusted):

- all: median 0.933 vs 0.828, P(RDS_disagree > RDS_agree) = 0.798, p < 0.001.
- off: median 0.933 vs 0.833, P(RDS_disagree > RDS_agree) = 0.789, p < 0.001.
- on: median 0.923 vs 0.769, P(RDS_disagree > RDS_agree) = 0.860, p < 0.001.

## Models

Logit with standard errors clustered by uid. Reference levels: difficulty = `short`, task = `date_addition`, insertion = `no_insertion`, reasoning_mode = `off`.

| model | sample | n | events | RDS β | OR per 0.1 (95% CI) | p | AME per 0.1 (pp) | reliable |
|---|---|---|---|---|---|---|---|---|
| primary | pooled | 20662 | 6483 | 15.942 | 4.925 (4.578–5.297) | < 0.001 | 22.94 | yes |
| length_adjusted | pooled | 20662 | 6483 | 17.200 | 5.584 (5.176–6.025) | < 0.001 | 24.48 | yes |
| per_mode_off_adjusted | off | 19471 | 6452 | 15.833 | 4.871 (4.527–5.240) | < 0.001 | 23.96 | yes |
| per_mode_on_adjusted | on | 1191 | 31 | 24.668 | 11.785 (4.896–28.365) | < 0.001 | 4.60 | no: optimizer did not converge; ConvergenceWarning: Maximum Likelihood optimization failed to converge. Check mle_retvals; very large coefficient C(task)[T.time_duration] = -22.61 (scaled -22.61); zero cell (quasi-separation) for task = time_duration; events per parameter 2.1 < 10 |
| per_mode_off_rds_only | off | 19471 | 6452 | 13.918 | 4.022 (3.806–4.251) | < 0.001 | 24.02 | yes |
| per_mode_on_rds_only | on | 1191 | 31 | 20.462 | 7.739 (3.486–17.180) | < 0.001 | 4.64 | yes |

## Interpretation

**Primary model.** Holding difficulty, task, insertion condition and reasoning mode constant, higher RDS is associated with higher odds of English/Hindi correctness disagreement: β = 15.942 (SE 0.372, 95% CI 15.213 to 16.672, p < 0.001); OR per 0.1 RDS = 4.925 (95% CI 4.578 to 5.297); average marginal effect per 0.1 RDS = 22.94 pp (95% CI 22.15 to 23.72). The association is statistically significant at α = 0.05. On the odds scale, a 0.1 increase in RDS multiplies the odds of disagreement by 4.925. The AME is the average slope dP/dRDS scaled by 0.1, a local probability-scale summary; the adjusted prediction curves show the non-linear relationship over the observed RDS range.

**Length-adjusted model.** Adding `length_gap` = |len_en − len_hi| / max(len_en, len_hi) (0 when both are empty): β = 17.200 (SE 0.387, 95% CI 16.440 to 17.959, p < 0.001); OR per 0.1 RDS = 5.584 (95% CI 5.176 to 6.025); average marginal effect per 0.1 RDS = 24.48 pp (95% CI 23.68 to 25.28). The RDS coefficient changes by 7.9% relative to the primary model and is significant at α = 0.05; the association persists after accounting for relative trace-length differences. The `length_gap` coefficient itself is -1.190 (OR per 0.1 = 0.888, p < 0.001).

**Per-mode models (supplementary).** The pooled sample is dominated by reasoning-OFF pairs, so the RDS slope is also estimated within each mode:

- per_mode_off_adjusted (off): β = 15.833 (SE 0.373, 95% CI 15.101 to 16.564, p < 0.001); OR per 0.1 RDS = 4.871 (95% CI 4.527 to 5.240); average marginal effect per 0.1 RDS = 23.96 pp (95% CI 23.13 to 24.78).
- per_mode_on_adjusted (on): β = 24.668 (SE 4.481, 95% CI 15.885 to 33.451, p < 0.001); OR per 0.1 RDS = 11.785 (95% CI 4.896 to 28.365); average marginal effect per 0.1 RDS = 4.60 pp (95% CI 3.19 to 6.02). Not reliable: optimizer did not converge; ConvergenceWarning: Maximum Likelihood optimization failed to converge. Check mle_retvals; very large coefficient C(task)[T.time_duration] = -22.61 (scaled -22.61); zero cell (quasi-separation) for task = time_duration; events per parameter 2.1 < 10.
- per_mode_off_rds_only (off): β = 13.918 (SE 0.282, 95% CI 13.366 to 14.471, p < 0.001); OR per 0.1 RDS = 4.022 (95% CI 3.806 to 4.251); average marginal effect per 0.1 RDS = 24.02 pp (95% CI 23.38 to 24.66).
- per_mode_on_rds_only (on): β = 20.462 (SE 4.069, 95% CI 12.487 to 28.438, p < 0.001); OR per 0.1 RDS = 7.739 (95% CI 3.486 to 17.180); average marginal effect per 0.1 RDS = 4.64 pp (95% CI 2.91 to 6.36).

## Limitations

- Observational: RDS is measured on the same generations whose answers are scored, so the association cannot be read as reasoning divergence causing errors; both may reflect question-level difficulty not captured by the controls.
- Mode imbalance: reasoning ON contributes 1191 of 20662 pairs and few disagreements, so the pooled RDS slope mostly reflects reasoning OFF; the model assumes one common slope across modes.
- RDS depends on the step parser and the edit-distance cost scheme (`config/ed.yaml`); parsing errors add measurement error that would typically attenuate the coefficient.
- Pairs with an unparseable answer in either language are excluded, and exclusion is more common in some conditions, which can bias the sample toward cleaner generations.
- Clustered SEs account for repeated observations of a question (insertion variants, both modes) but assume independence across questions; a single generation per prompt means sampling noise in correctness is not separated from systematic effects.
- 92.0% of disagreements are English correct / Hindi wrong, so the outcome mostly captures Hindi-specific failures rather than symmetric disagreement.
- RDS is high for most pairs (see the RDS table), so the slope is estimated mainly from the upper part of the RDS range.
- Odds ratios are not percentage-point changes; use the AME column or the prediction curves for the probability scale.

## Files

- `analysis_dataset.csv`: cleaned combined dataset (all loaded pairs, with `included`).
- `desc_*.csv`: descriptive tables; `exclusions.csv`; `mann_whitney.csv`.
- `rds_results.csv`: RDS coefficient table for all models; `coef_<model>.csv`; `summary_<model>.txt`; `separation_<model>.csv`; `predicted_probability_primary.csv`.
- `*.png`: plots.

Reproduce: `python rds_regression.py` from this folder (requires pandas, numpy, scipy, statsmodels, matplotlib).
