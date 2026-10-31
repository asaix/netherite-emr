# Figures

Plotted values are in `fig_data/`. Accuracy is answered-only unless the `convention` column or a `_strict` column says otherwise. Keep the chart types; styling is central.

## Figures in the document

| Figure | Chart type | Encoding | CSV | Use |
|---|---|---|---|---|
| Fig. 1 | Dumbbell with three markers per task, two panels | y task, x accuracy, colour condition (`direct`, `std`, `hing`), panel `language`; last row `all` | `fig1_accuracy_by_task.csv` | core |
| Fig. 2 | Line with 95% bands, two panels | x `difficulty`, y `accuracy`, band `lo`/`hi`, colour `condition`, panel `language`; filter `convention=answered` | `fig2_accuracy_by_level.csv` | core |
| Fig. 3 | Horizontal stacked bar | y `language`, x `pct_of_traces`, colour `style` | `fig3_style_shares.csv` | core |
| Fig. 4 | Horizontal grouped bar | y `task`, x `roman_diff` and `plain_diff`, colour style | `fig4_style_by_task.csv` | core |

Table 3's figure-like values are in `results/table3.csv`; Table 2's are in `table2_gaps.csv`, `table2_penalties.csv` and `numbers.json` (`gains`). Fig. 3's Roman share uses the Devanagari-under-10% rule that Table 3 actually uses. Fig. 2's y-axis in the report does not start at zero; keep that visible.

## Recommended new figures

| ID | Chart type | Encoding | CSV | Use |
|---|---|---|---|---|
| N1 | Forest plot, two panels | y `task`, x `diff_pairs`, interval `lo`/`hi`, panel `language`. Replaces the claim "every task" and shows Hindi's two moving tasks | `new_task_hing_minus_std.csv` | core |
| N2 | Grouped bar | x `style`, y `hing` and `encot`, on Hindi questions | `takeaway2_encot_by_style.csv` | core |
| N3 | Grouped bar | x `group`, y `acc_cross_month` and `acc_same_month` | `new_subtraction_month_cross.csv` | core |
| N4 | Grouped bar | x `condition_language`, y `orig` and `ext`; the zero-function-word result (18.61 vs 86.51) goes in the caption from `numbers.json` | `new_verification_rates.csv` | core |
| N5 | Small multiples of grouped bars | x `language`, y `std`, `hing`, panel `insertion`; filter `convention=answered` | `new_split_headline.csv` | core, answers the evaluator's pooling criticism |
| N6 | Heatmap | x `fn_thr`, y `deva_thr`, colour `en_did_cellfe` | `threshold_sensitivity.csv` | appendix |
| N7 | Line | x `token_bin`, y `acc`, colour `group` | `length_bins_english.csv` | appendix |
| N8 | Bar with n labels | x `fn_share_bin`, y `loss` | `dose_response_english.csv` | appendix |
| N9 | Point with interval | x `insertion`, y `roman_pct`, interval `lo`/`hi` | `new_roman_share_by_distractor.csv` | appendix |
| N10 | Grouped bar | y `task`, x `roman_loss`, `plain_loss`, panel `insertion` | `fig4_by_distractor.csv` | appendix |
| N11 | Stacked bar | x `condition`/`language`, stack `correct`, `plus1`, `minus1`, `other` | `dow_offsets.csv` | appendix |
| N12 | Stacked bar | x `condition`/`language`, stack error types | `subtraction_error_types.csv` | appendix |
| N13 | Coefficient plot | y `model`, x `b`, interval `lo`/`hi`, filter `term` to `hinglish`, `roman_h`, `plain_h` | `new_length_verification_models.csv` | appendix |
| N14 | Grouped bar | x `style`, y `hing`, `encot`, panel `insertion` | `takeaway2_encot_by_style_distractor.csv` | appendix |

Supporting tables with no figure: `failure_agreement.csv`, `wordlist_sensitivity.csv`, `takeaway2_script_by_task.csv`, `subtraction_month_cross_by_style.csv`, `level_by_distractor_english.csv`.
