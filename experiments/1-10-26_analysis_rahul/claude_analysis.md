# Analysis log (2026-10-01)

Working notes for the mid-submission analysis section. Everything here lives in `experiments/1-10-26_analysis_rahul/`.

## 1. Project in one paragraph

Netherite evaluates Sarvam (`sarvam-105b`) on the Temporal Reasoning Dataset (TRD), English (`en_US`) vs Hindi (`hi_IN`), comparing direct answers with chain-of-thought (CoT), with no / similar / dissimilar distractor sentences prepended to the question. Questions come from `Dataset/<difficulty>/<task>_<lang>.json` (150 questions per file, same question IDs in both languages). Each question was run 12 ways: 2 languages x 3 insertions x 2 modes (direct, cot).

## 2. State of the raw runs

| Difficulty | Run folder | Status |
|---|---|---|
| short | `experiments/29-9-2026_short_rahul` | 4 tasks complete; `day_of_week` almost; `interval_date` partial; `time_*` not run |
| medium | `experiments/29-9-26_med_rahul` | same as short |
| long | `experiments/2026-09-29-run-long-adi` | `date_addition` complete, `date_duration` 135/150 questions, `date_recurrence` 77/150, rest not run |
| very_long | `experiments/30-9-26_v_long_aayush` | all 9 tasks, a few `time_*` questions missing |
| very_very_long | not run | |

Runs stopped because the Sarvam API credit ran out (HTTP 402) and a few requests hit 429 after 6 retries. `reasoning_content` is null in every record, so the CoT text is in `content`.

## 3. Merged analysis dataset

`merged_results.json` (37,068 records, 3,089 questions, 85 MB) was built from `inputs/{short,medium,long,very_long}.json`, which are byte-identical copies of the four runs' `results.json`. It was built with a one-off inline command, so there is no script for it.

Selection rules:
- short and medium: `date_addition`, `date_subtraction`, `date_duration`, `date_recurrence`, `day_of_week`
- long: `date_addition`, `date_duration`
- very_long: all 9 tasks
- then every question that lacks all 12 results was dropped (61 questions, 431 records), so every kept question has exactly 12 records

Questions per task in the merged file:

| Task | short | medium | long | very_long |
|---|---|---|---|---|
| date_addition | 150 | 150 | 150 | 150 |
| date_subtraction | 150 | 150 | - | 150 |
| date_duration | 150 | 150 | 135 | 150 |
| date_recurrence | 150 | 150 | - | 150 |
| day_of_week | 146 | 149 | - | 150 |
| interval_date | - | - | - | 150 |
| time_addition | - | - | - | 149 |
| time_duration | - | - | - | 149 |
| time_subtraction | - | - | - | 111 |

A first version of a clean-set script (`build_clean_set.py`) was written, tested and then deleted at the user's request.

## 4. Code in this folder

- `metrics.py`: copy of the root `metrics.py`, unchanged. It cannot find the TRD package from this folder, so every script here puts `tools/temporal-reasoning-dataset/src` (two levels up) on `sys.path` before `import metrics`.
- `cot_delta.py`: accuracy for each (difficulty, task, language) under direct and CoT, and `cot_delta = cot - direct`. Fixed grouping, uses pandas. Output: `outputs/cot_delta.csv`. An interactive group-by version (ask y/n per field like `metrics.py`) was worked out and tested in a scratch copy but has not been applied to this file.
- `cot_insertion_deltas.py`: non-interactive, writes three CSVs (below).
- `temporal_answers.py`: shared helpers (answer parsing per task, distractor extraction, date/time/weekday mention extraction from the CoT). Not run on its own.
- `language_pair_check.py`: checks that the English and Hindi versions of each question are a valid pair. Writes `outputs/language_pair_check.json`.
- `cross_lingual_agreement.py`: per question, how often English and Hindi are both right / both wrong / split. Writes `outputs/cross_lingual_agreement.csv`.
- `error_types.py`: classifies every wrong, scored response. Writes `outputs/error_types.csv` and `outputs/error_types_per_response.csv`.
- `distractor_reuse.py`: whether wrong answers reuse a number, month or weekday from the distractor, against a no-insertion baseline. Writes `outputs/distractor_reuse.csv` and `outputs/distractor_reuse_per_response.csv`.
- `reasoning_faithfulness.py`: whether the CoT's final value matches the `Answer:` line. Writes `outputs/reasoning_faithfulness.csv` and `outputs/reasoning_faithfulness_per_response.csv`.

Run any of them as `python3 <script>.py` from this folder. None take arguments or need API access.

### Outputs (`outputs/`)

| File | Rows | Contents |
|---|---|---|
| `cot_delta.csv` | 42 | accuracy direct / cot / cot_delta per difficulty, task, language (insertions pooled) |
| `deltas_by_language.csv` | 42 | per difficulty, task, language: the 6 accuracies (direct/cot x none/similar/dissimilar); 3 CoT deltas (`cot_delta_*` = cot - direct at each insertion level); 3 CoT insertion drops (`cot_none_minus_similar`, `cot_none_minus_dissimilar`, `cot_similar_minus_dissimilar`); the same 3 drops for direct (`direct_*`); 3 `cot_drop_minus_direct_drop_*` columns; `min_scored` |
| `deltas_en_vs_hi.csv` | 21 | per difficulty, task: every delta above for English, for Hindi, and `en_minus_hi` |
| `cot_ratio.csv` | 126 | CoT responses only, per difficulty, task, language, insertion: response count, average and pooled target-language CoT ratio |

| `language_pair_check.json` | - | pass/fail counts for each pairing check (below) |
| `cross_lingual_agreement.csv` | 44 | per difficulty, task, condition (direct/cot), insertions pooled, plus `all` rows: `both_right`, `both_wrong`, `en_only`, `hi_only`, `split_rate`, `split_rate_if_independent`, `phi_correlation`, `en_only_vs_hi_only_p` (exact sign test) |
| `error_types.csv` | 83 | wrong scored responses per difficulty, task, language, condition, split by error type |
| `error_types_per_response.csv` | 11,537 | one row per wrong scored response: `error_type`, `signed_error` |
| `distractor_reuse.csv` | 24 | per task, language, condition, distractor type: wrong responses and reuse rate with the distractor inserted vs the same distractor tested against the no-insertion wrong answers (placebo) |
| `distractor_reuse_per_response.csv` | 3,719 | one row per (wrong response, distractor tested) |
| `reasoning_faithfulness.csv` | 42 | CoT only, per difficulty, task, language: match rates and counts (columns below) |
| `reasoning_faithfulness_per_response.csv` | 18,186 | one row per scored CoT response |

Conventions:
- Accuracy comes from `metrics.average_accuracy`, which drops responses with no `Answer:` line (mostly responses cut off at `max_tokens`).
- Insertion drops are `A - B` as named; positive means the distractor lowered accuracy.
- `cot_drop_minus_direct_drop_*` = CoT drop minus direct drop. Positive means CoT lost more accuracy to the distractor than direct answers did.
- Target-language CoT ratio = words in the response's own language / (Hindi words + English words). For Hindi questions that is Hindi / (Hindi + English); for English questions it is English / (English + Hindi). `metrics.target_words` already works this way.
- Cross-lingual agreement: a unit is one (question, insertion, condition) with both the English and the Hindi response scored; `pairs_scored` is how many survived. `split_rate_if_independent` is `p_en(1-p_hi) + p_hi(1-p_en)` from that row's accuracies; `phi_correlation` near 0 means English and Hindi correctness are unrelated within the task, so a split rate near the independent value means failures are language-specific rather than shared question difficulty. The `all` rows pool different tasks, so their phi is inflated by task difficulty.
- Error types (wrong, scored responses only): `off_by_one` (date or number off by 1, weekday +-1, interval start/end both within 1 day), `off_by_one_hour` (time tasks, `time_duration`: +-60 minutes), `wrong_direction` (answer is the mirror image of the gold around today/now, e.g. today - N instead of today + N; dates and clock times), `month_slip` (same year and day of month, different month), `year_slip` (same month and day, different year), `week_shift` (interval: both ends shifted by the same multiple of 7 days), `unit_confusion` (`time_duration`: answer is gold/60 or gold*60), `format_only` (parses to the gold value but is not the same string, e.g. `00:63`), `invalid_answer` (impossible date such as `2025-02-29`, or an unrecognised weekday), `other`. Checked in this order; `signed_error` is answer minus gold (days, minutes, or weekday offset in -3..3).
- Distractor reuse: a wrong answer reuses the distractor if any component (year, month, day of month, weekday, hour, minute, or the number itself) differs from the gold and equals a number, month name or weekday name in the distractor (hour also matches number+12, for "8 PM"). Only responses whose distractor contains at least one such number, month or weekday are counted; most dissimilar distractors have none, so those rows are tiny. The placebo is the no-insertion wrong answers tested against the distractor that would have been inserted for the same question, which gives the reuse rate expected by chance.
- Reasoning faithfulness: `last_value` is the last date / clock time / number / weekday mentioned in the CoT before its final `Answer:` line, ignoring values copied from the question (for dates and times) and ignoring numbers inside dates and times (for numbers). It is compared with the answer line (dates by month and day, and year when the CoT gives one). `has_verification` means the CoT contains a verification cue (verify, double-check, alternatively, सत्यापित, जांच, पुष्टि, ...), because the verification step restates other values after the conclusion. `answer_in_reasoning` means the answer value appears anywhere in the CoT (for intervals, both dates). `wrong_but_reasoning_ends_at_gold` counts wrong answers whose last CoT value was the correct one.
- `min_scored` is the smallest number of scored responses in any of the 6 accuracy cells of the row.

## 5. Results seen so far

These come from the CSVs above and a scratch run of the interactive grouping. They are pooled and descriptive, with no significance tests.

- CoT delta by language, all merged tasks pooled: English 0.632 -> 0.911 (+0.279); Hindi 0.577 -> 0.629 (+0.051). The task mix differs per difficulty, so do not read a trend across difficulties from pooled numbers.
- English CoT is never worse than direct in any (difficulty, task) cell. Large English gains: `date_recurrence`, `day_of_week`, the `time_*` tasks.
- Hindi CoT is sometimes worse than direct, e.g. `date_subtraction` very_long -0.31, `interval_date` very_long -0.17, `date_subtraction` medium -0.09. Where CoT helps in Hindi the gain is much smaller than in English.
- Worked example, short `date_recurrence`: drop from none to similar distractor with CoT is 0.068 (English) and 0.116 (Hindi); with direct it is 0.075 (English) and -0.067 (Hindi). CoT drop minus direct drop: English -0.007, Hindi +0.183. So in this cell CoT is more distractor-sensitive in Hindi but not in English. This needs a significance check.
- Target-language CoT ratio: English 1.000 everywhere; Hindi pooled between 0.918 and about 1.0, mean 0.989. No (difficulty, task, language, insertion) cell is below 0.9, so the model stays in Hindi when asked to.
- Hindi CoT responses are much shorter than English ones (mean completion tokens about 238 vs 630 over the earlier, smaller dataset). Compare in words or characters before relying on it.
- Earlier error samples: Hindi `date_recurrence` errors often read "excluding today, 1st occurrence" as going backwards (e.g. 2025-11-23 instead of 2025-12-01); Hindi `day_of_week` errors are often the correct day + 1.
- Pair validity (`language_pair_check.json`): all 3,089 questions have 12 records, 6 per language; the gold answer is identical across languages and across all 12 records (weekdays compared by day index, since Hindi golds are Hindi names); the numbers in the no-insertion question match across languages (ignoring order, because the "(e.g., 5, 9)" example sits elsewhere in the Hindi `date_duration` sentence); every prompt ends with its no-insertion question; direct and CoT prompts share the same question text; the numbers, months and weekdays in each distractor match across languages; each English distractor maps to exactly one Hindi distractor and back (35 similar, 43 dissimilar). So the paired English-Hindi analyses are valid.
- Cross-lingual agreement: under CoT, English is right and Hindi wrong far more often than the reverse (all tasks pooled: 2,585 vs 172 of 8,931 scored pairs). Within a task, the split rate under CoT is about what independence predicts (e.g. very_long `date_recurrence` 0.796 vs 0.793, phi -0.01), so the two languages fail on different questions. Under direct answers, phi is higher (0.2 to 0.5 in many cells), so shared question difficulty matters more there.
- Error types, CoT: English errors are mostly off by one (89% of `date_addition`, 100% of `date_duration`, 85% of `date_subtraction`, 80% of `day_of_week`). Hindi CoT has fewer off-by-one errors (34%, 87%, 23%, 45%) and more other types: `month_slip` 18% of `date_addition` errors, `wrong_direction` 16% of `date_recurrence` errors (6% in English). `time_*` errors are mostly neither off-by-one nor an hour slip. 61 wrong answers are impossible dates such as `2025-02-29`, mostly from direct answers.
- Distractor reuse: for Hindi direct answers, 12.1% of wrong answers (76 of 629) reuse something from the similar distractor, against 2.6% (16 of 607) for the same questions without it; Hindi direct `date_recurrence` is 17.8% vs 3.1%, almost all from "February" sentences pulling the answer into February. English direct is 4.9% vs 3.9% (no clear effect). Under CoT there is little reuse in either language (English 0 of 127, Hindi 4.8% vs 2.5%). No significance test has been run.
- Reasoning faithfulness: the answer line value appears in the CoT in 99.9% of English and 99.0% of Hindi CoTs. Only 1 English and 6 Hindi wrong answers had a CoT ending at the correct value (of 797 and 3,409 wrong answers), so wrong answers are almost never a copying error at the end. English CoTs contain a verification step 79% of the time (90 to 98% for the `time_*`, `date_duration`, `date_recurrence` tasks) against 1.5% for Hindi, which is why the plain last-value match is lower in English (0.950 vs 0.985). Among CoTs with no verification cue, it is 0.996 (English, 1,876 responses) and 0.986 (Hindi, 9,033).

## 6. Caveats to state in the report

- Not all tasks are present at all difficulties; only `date_addition` and `date_duration` appear at all four. `very_very_long` was never run.
- Per-insertion cells have about 150 questions, so differences within roughly 0.03 to 0.05 are noise. Use `min_scored`.
- Scored-only accuracy drops cut-off responses; more English CoT responses were cut off than Hindi ones, which slightly favours English.
- The data comes from one model, one seed, temperature 0.

## 7. Not done yet

- English-Hindi gap vs difficulty (line chart, direct and CoT).
- Confidence intervals / paired significance tests for the deltas and for the distractor effect.
- Strict accuracy that counts cut-off responses as wrong, as a robustness check.
- Whether the CoT mentions the distractor, and whether mentions go with wrong answers.
- Significance tests for the distractor reuse difference (inserted vs placebo) and for the per-task English-Hindi agreement.
- Whether verification steps in English CoTs change accuracy (they exist in 79% of English CoTs and 1.5% of Hindi ones).
- Share of Hindi CoT responses with ratio below 0.9 and their accuracy.
- Error types for the `other` bucket (`date_recurrence`, `time_*`, Hindi `date_subtraction`), which is still large.
- Move this folder to the `<YYYY-MM-DD>_<name>` naming from `CLAUDE.md`, and add a script that rebuilds `merged_results.json`.
- Re-running the missing requests (long `date_duration` / `date_recurrence`, a few `day_of_week` and `time_*` questions) and `very_very_long`, once API credit is available.
- Apply the interactive group-by version to `cot_delta.py`.

