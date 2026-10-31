# Figures

All CSVs are in `fig_data/` and are written by `verify.py`. Sample is answered pairs unless the row says otherwise.

| Figure | Status | Chart type | Encoding | CSV | Core or appendix |
|---|---|---|---|---|---|
| Report Figure 1: RDS by agreement | existing | step histogram, 25 bins on 0 to 1, dashed median lines | x `bin_lo` to `bin_hi`, y `density`, colour `disagree`, panel `mode`, median line `median` | `fig1_rds_distribution.csv` | Appendix. It shows the full-token RDS, so it should not appear without Figure 3 next to it. |
| Report Figure 2: rate by RDS bin | existing | line with points and error bars | x `mid`, y `rate`, error `wilson_lo`/`wilson_hi` (as printed) or `cluster_lo`/`cluster_hi` (recommended), colour `mode`, filter `shown_in_report` true | `fig2_rate_by_rds_bin.csv` | Appendix |
| New Figure 3: effect size by token view | new | forest plot | y `view` in the order full, noans, noansval, ops, opsnoans, opscore, prefix8, prefix8ops, precheck, precheckops; x `or_per_sd` on a log axis, interval `or_sd_lo`/`or_sd_hi`, reference line at 1, panel `model` | `fig3_or_by_token_view.csv` | Core. It carries the main correction. |
| New Figure 4: slope within each task | new | forest plot, small multiples | y `level`, x `or_per_0.1` on a log axis, interval `or_lo`/`or_hi`, colour `view` (full, noans, opsnoans), filter `by` = task, reference line at 1 | `fig4_task_slopes.csv` | Core. Use `by` = insertion for the distractor split in the appendix. |
| New Figure 5: added predictive value | new | dot plot with intervals | y `view`, x `delta_auc`, interval `lo`/`hi`, colour `baseline`, filter `sample` = all, reference line at 0; panels by `sample` for the distractor split | `fig5_cv_delta_auc.csv` | Core |
| New Figure 6: calibration by decile | new | line chart with points | x `x`, y `obs` (points), `lin` and `spl` (lines), panel `view` | `fig6_calibration.csv` | Appendix |
| New Figure 7: RDS by outcome | new | grouped bar | x `outcome`, y mean RDS, one group per column `full`, `noans`, `opsnoans` | `fig7_rds_by_outcome.csv` | Core. It shows both-wrong pairs have the highest RDS while counting as agreement. |
| New Figure 8: modes on the same 450 questions | new | grouped bar | x `mode`, y `disagree_answered` and `disagree_strict`, error on the answered bar `lo`/`hi` | `fig8_matched_modes.csv` | Appendix |
