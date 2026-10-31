# Figures

All CSVs are in `fig_data/`. Chart types for C1 and C2 follow `report.py` (`fig1_accuracy_by_difficulty.png`, `fig2_accuracy_by_task.png`). I did not visually inspect the PDF's page renderings of these two figures; I matched them by caption.

## Existing figures

| Figure | Chart | Encoding | CSV | Use |
|---|---|---|---|---|
| C1, accuracy by level | Line with error bars | x: level; y: accuracy; colour: condition; error bars: `lo`, `hi` | `figC1_accuracy_by_level.csv` (drop English direct to match the draft; `report.py` plots five series) | Core |
| C2, accuracy by task | Grouped bars | x: task; y: accuracy; colour: Hindi CoT, CLP, en-CoT, English CoT | `figC2_accuracy_by_task.csv` | Core |

CIs in `figC1_accuracy_by_level.csv` use B = 10,000, seed 20261031.

## Recommended figures

| Figure | Chart | Encoding | CSV | Use |
|---|---|---|---|---|
| Decomposition of the English-Hindi gap | Stacked horizontal bars | y: cut (pooled, distractor, level, task); x: points; colour: reasoning part, question part. Annotate share | `new_decomposition.csv` | Core |
| Recurrence error types by k | Small-multiple stacked bars | x: k bin; y: % of answers; colour: correct, backwards, k−1 steps, today, other; panel: `set` | `new_recurrence_error_types_by_k.csv` | Core |
| Backwards rate by k | Line or dot with intervals | x: k bin; y: `mirror%`; colour: `set`; error bars: `lo`, `hi` | `new_backwards_by_k.csv` | Appendix; covered by the figure above |
| Gap by task and level | Heatmap | x: level; y: task; colour: gap in points | `new_gap_task_level_heatmap.csv` | Core: shows the shrinking comes from recurrence |
| Distractor drops | Dot with intervals | x: drop; y: condition; panel: `ins` | `new_distractor_drops.csv` | Appendix |
| Mention rate by word list | Grouped bars | x: condition and `words`; y: mention, with placebo overlaid; panel: `ins` | `new_mentions_by_wordset.csv` | Appendix |
| Error overlap measures | Dot with intervals | x: `within-cell phi (all cells)` and CI; y: condition pair | `new_error_overlap.csv` | Appendix |
| Day-of-week mechanism | Grouped bars | x: `group`; y: `doy without doy-1`; colour: `cond` | `new_dow_mechanism.csv` | Appendix |
| Thinking mode on questions 0 to 9 | Dot with intervals | x: `acc`; y: `cond`; panel: `conv` | `new_think_q0_9.csv` | Core or appendix |
| Thinking accuracy by English share, whole trace | Bars | x: `bin`; y: `acc`; annotate `n`, `median_tok` | `new_think_accuracy_by_english_share.csv` | Appendix; shows the cut-off artefact |
| Thinking accuracy by English share, first 1,000 characters | Bars | x: `bin`; y: `acc_answered`, `acc_strict` | `new_think_accuracy_by_early_english_share.csv` | Appendix |
| First 50 vs rest | Dot with intervals | x: `first-rest`; y: `cut`; panel: `lang`, `cond` | `new_subset_first50_vs_rest.csv` | Appendix |
