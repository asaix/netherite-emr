# Figures for Part A

All CSVs are in `fig_data/`. Values are percent or percentage points unless noted.

## Existing figure

| Figure | Chart type | Encoding | CSV | Use |
|---|---|---|---|---|
| A1, accuracy by difficulty | Line with 95% CI error bars | x: level (short to very very long, ordinal). y: accuracy. Colour and line style: condition (English CoT, Hindi CLP, Hindi CoT, Hindi direct). Direct labels at line ends. English direct is in the CSV but omitted from the plot | `figure_a1_accuracy_by_level.csv` (columns `<cond>`, `<cond>_lo`, `<cond>_hi`; `encot` also present) | Core |

## Recommended new figures

| Figure | Chart type | Encoding | CSV | Use |
|---|---|---|---|---|
| N1, headline gains by distractor | Forest plot | y: contrast (`clp-hi_cot`, `clp-hi_direct`, `en_cot-clp`, `encot-clp`). x: `diff_answered` with `lo`, `hi`. Colour: `distractor`. Second marker: `diff_strict` with `strict_lo`, `strict_hi` | `new_headline_by_distractor.csv` | Core; answers the evaluator's pooling criticism |
| N2, CLP vs en-CoT by stage-1 outcome | Grouped bar | x: `stage1_ends_at_gold`. y: `clp_acc`, `encot_acc`, `hi_cot_acc`. Colour: condition. Annotate `n` | `new_date_tasks_clp_vs_encot_by_stage1.csv` | Core; best single picture of carry-over |
| N3, agreement vs self-agreement | Dot plot with CI | y: `pair`. x: `mh_or` with `mh_lo`, `mh_hi` (log scale). Colour: `comparison` (cross vs self across distractor) | `new_agreement_vs_self.csv` | Core if A.6 stays |
| N4, subset null for the penalty | Histogram with marker | x: `hi_time` (5,000 random 50-per-cell draws). y: count. Vertical lines: first 50 (+0.17), full grid (+2.21) | `new_subset_random_draw_null.csv`; values in `new_subset_penalty.csv` | Appendix |
| N5, unrelated gain by task | Forest plot | y: `task`. x: `gain` with `lo`, `hi`. Side markers: `gain_encot`, `gain_hi_cot` | `new_unrelated_gain_by_task.csv` | Appendix |
| N6, time-related drop by task | Forest plot | y: `task`. x: `drop` with `lo`, `hi` | `new_clp_time_drop_by_task.csv` | Appendix |
| N7, stage-1 style by distractor | Grouped bar | x: `feature`. y: rate. Colour: distractor columns `no_insertion`, `similar_insertion`, `dissimilar_insertion` | `new_stage1_mode_rates.csv` | Appendix |
| N8, net mention by rule | Grouped bar | x: `reasoning`. y: `net_paired`. Colour: `kind`. Facet: `rule` (use `doc` for core) | `table_a5_mentions_by_rule.csv` | Appendix |
| N9, off-by-one by task | Grouped bar | x: `task`. y: `off_by_one`. Colour: `cond` | `new_off_by_one_by_task.csv` | Appendix |
| N10, stage 2 vs en-CoT length | Grouped bar | x: `task`. y: `median_s1`, `median_s2`, `median_encot`. Colour: measure | `new_stage2_vs_encot_by_task.csv` | Appendix |
| N11, gain by stage-1 length | Grouped bar | x: `tertile`. y: `gain_vs_hi_cot`, `gain_vs_encot`. Colour: contrast | `new_gain_by_stage1_length.csv` | Appendix |

## Data files without a planned figure

Tables and supporting data: `table_a1_accuracy_by_task.csv`, `table_a3_stage1_stage2.csv` (response level), `table_a4_drops.csv`, `table_a6_agreement_all_cells.csv`, `new_subset_vs_rest_by_cell.csv`, `new_generator_draws_by_cell.csv`, `new_phi_cells_*.csv`, `new_self_agreement.csv`, `new_mention_top_words.csv`, `new_dismissal_phrase_rates.csv`, `new_weekday_offsets.csv`, `new_gold_in_stage1_by_task.csv`, `new_unrelated_gain_by_sentence.csv`, `new_subset_penalty.csv`.
