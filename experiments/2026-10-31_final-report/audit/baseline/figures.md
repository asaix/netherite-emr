# Figures

All CSVs are in `fig_data/`. Chart types follow the source figure where one exists. Filter `scoring` to `answered` unless stated, and show `strict` beside it for headline panels. No draft PNGs were made.

## Figures in the documents

| Figure | Chart type | Encoding | CSV | Use |
|---|---|---|---|---|
| Difficulty (`full/plots/difficulty.pdf`, panel c; mid report Fig. 3) | Line with error bars | x level; y accuracy (`direct`, `cot`); colour language; line style condition. CIs for accuracy are not in this file, only for `delta` | `fig_difficulty.csv` (`split = pooled`) | core, facet by `split` |
| Day of week (mid report Fig. 2) | Grouped bars | x offset; y share; colour language; fill condition; chance line at 14.3 | `fig_dow_offsets.csv` | appendix |
| Error types (`error_types.pdf`; mid report Fig. 4) | Stacked horizontal bars in source | This audit only recomputed off-by-one share: x task, y share, colour language. Wrong direction and month slip were not recomputed; use `outputs/full/numbers.json` for those | `fig_error_off_by_one.csv` | appendix |
| CoT delta by task x level (`extra/plots/cot_delta_task_level.pdf`) | Heatmap | x level; y task; colour `delta`; panel language; star where the interval excludes 0 | `fig_cot_delta_heatmap.csv` (`split = pooled`) | core |
| Penalty by difficulty (`extra/plots/did_by_difficulty.pdf`) | Points with error bars | x level; y penalty; colour language; panel distractor | `fig_penalty_by_difficulty.csv` | appendix |
| Thinking on vs off (`reasoning_on/plots`) | Paired bars | x language and condition; y accuracy (`off`, `on`) | `fig_thinking_budget.csv`, `ron_by_task.csv`, `ron_by_level.csv` | appendix |

## New figures recommended

| Figure | Chart type | Encoding | CSV | Use |
|---|---|---|---|---|
| N1. CoT delta split by distractor | Dot plot with error bars | x `delta`; y task; colour `split`; panel language | `fig_cot_delta_task_split.csv` | core; answers the evaluator |
| N2. English-Hindi gap by distractor | Grouped bars with error bars | x `split`; y `v`; colour `cond`; panel `scoring`; `scope = all` | `rq1_gap_by_scope_split.csv` | core |
| N3. Penalty and interaction forest | Forest plot | x `penalty`; y `scope`; colour `lang` including `hi_minus_en`; panel `ins`, `scoring` | `fig_penalty_forest.csv` | core |
| N4. Sentence-level penalty | Sorted dot plot with error bars | x `sent_penalty`; y sentence within task; colour `lang`; marker size `cot_cutoffs` | `fig_sentence_penalty.csv` | core |
| N5. Leave-one-sentence-out | Dot plot with error bars | x `loo_all_tasks`; y sentence; panel `lang`, `ins` | `rq2_loso.csv` | appendix |
| N6. Thinking at equal budget | Grouped bars | x language and condition; y strict accuracy; colour off, on at 16k, on at 4,096. `delta` for `cap4k_strict` is the budget contrast | `fig_thinking_budget.csv` | core |
| N7. Recurrence pattern by k | Stacked bars | x k; y share (`correct`, `first_step`, `mirror`, `other`); panel language and condition. Filter k <= 4 for legibility | `recurrence_by_k.csv` | appendix |
| N8. Mention rate, two measures | Grouped bars | x language and distractor; y rate with placebo marker; colour `measure` | `fig_mention.csv` | appendix |
| N9. φ by cell | Strip plot | x `cond`; y `phi`; reference line at `phi_max` | `phi_by_cell.csv` | appendix |
| N10. TRD comparison | Table or slope chart | task by model and language | `trd_comparison_medium_direct.csv` | appendix |

## Other data files

Tables, not figures: `distractor_pool.csv`, `gold_spotcheck_30_per_task.csv`, `interval_error_kinds.csv`, `direct_compliance_by_task.csv`, `run_date_drift_check.csv`, `recurrence_by_level_k.csv`, `dow_accuracy_by_year.csv`, `trd_reasoning_memorization_by_level.csv`, `rq1_cot_delta_by_scope_split.csv`, `rq1_cot_delta_task_level.csv`, `rq1_gain_gap_by_scope_split.csv`, `rq2_penalty_by_scope.csv`, `rq2_penalty_task_level.csv`.
