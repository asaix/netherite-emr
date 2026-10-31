# Figures for Part B

All CSVs are in `fig_data/` and are written by `verify.py`. Percentages and points are on a 0 to 100 scale. Nothing is plotted here; a later step restyles figures centrally.

## In the document

| figure | chart type | encoding | CSV | placement |
|---|---|---|---|---|
| Figure B1 | Forest plot, three panels | x: difference in points with 95% bootstrap CI (`mean_pts`, `ci_low`, `ci_high`). y: `group`. Panel: `panel` (a Q-P, b M-P, c P-P1). Colour and marker: language | `fig_b1_contrasts.csv` | core |

Notes on Figure B1:

- The values here are the audit's own bootstrap, so intervals can differ from the PDF by Monte Carlo error of up to about 0.5 points. Exact printed values are in `experiments/2026-10-29_distractor-resampling/outputs/resample/analysis.json`.
- Panel (c) has only the "later" rows. "All" and "later" are the same traces for P-P1.
- Keep the chart type. Add a caption line saying the data are `similar_insertion` only, unanswered counts as wrong, and traces were selected for being wrong.

## Recommended new figures

| id | chart type | encoding | CSV | placement |
|---|---|---|---|---|
| N1 | Grouped forest plot | x: `mean_pts` with `ci_low`, `ci_high`. y: `group`. Colour: `metric` (`answered_only_Q-P`, `answered_only_M-P`, `unanswered_P-Q`, `unanswered_M-P`) | `new_answered_only_and_unanswered.csv` | core |
| N2 | Dot plot sorted by effect, dot size by traces | x: `Q-P` in points. y: `distractor`, labelled with `task`. Size: `n`. Separate panel per language | `new_by_distractor_hi_IN.csv`, `new_by_distractor_en_US.csv` | core |
| N3 | Line chart | x: `effect_pts`. y: `power`. Colour: `run` (G and S are identical because both have 64 discordant pairs, so one line is enough). Add reference lines at 3.3 and 5.2 points, the Experiment 2 Hindi M-P estimates | `new_exp1_power_curve.csv` | core |
| N4 | Grouped bars | x: `group`. y: `accuracy_pct`. Colour: `series` (Q arm, P rollouts without a mention, P rollouts with a mention, M arm). Annotate `n_rollouts` | `new_p_rollouts_by_mention.csv` | appendix, labelled exploratory |
| N5 | Grouped bars | x: `language`. y: `strict_excess_fraction_pct` with `ef_low`, `ef_high`. Colour: `condition` | `new_api_population_attribution.csv` | core |
| N6 | Grouped bars | x: `group`. y: `unanswered_pct`. Colour: `arm` | `new_unanswered_by_arm.csv` | appendix |
| N7 | Forest plot | x: `diff` with `ci_low`, `ci_high`. y: `language`. Panel: `run` | `new_calibration_ci.csv` | appendix |
| N8 | Stacked bar, one bar per group | y: `total_Q_P`, split into `completion_part_midpoint` and `quality_part_midpoint` | `new_decomposition_completion_quality.csv` | appendix |
| N9 | Forest plot | x: `excess_fraction_pct` with `ci_low`, `ci_high`. y: `group` | `new_excess_fraction.csv` | appendix |

## Tables backed by CSV

| table | CSV |
|---|---|
| Table B3 arm accuracies | `table_b3_arm_accuracy.csv` |
| API penalties by distractor condition | `new_api_population_penalty.csv` |
| Share of rollouts repeating the original wrong answer | `new_repeat_original_answer.csv` |

## What the figures should show

- **N1:** the distractor effect in Hindi is partly non-completion, while the written-mention effect is not.
- **N2:** the Hindi Q-P average rests on a few distractor sentences, especially the "weekly commitment" one. This is the reason the cluster interval includes 0.
- **N3:** Experiment 1 could not see effects of the size Experiment 2 found.
- **N5:** the clean population result, free of wrong-trace selection, and the only Part B-related figure that splits by distractor condition.
