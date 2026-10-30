# English-Hindi reasoning divergence: five comparisons across three selections

Source: `experiments/2026-10-29_ed-analysis/edout/cube.html`. The bar values in every table were recalculated from the data embedded in that page and match what Plotly drew (268 bars, largest difference below 1e-14).

## Main findings

1. Most of the ron vs standard gap in the content plots comes from comparing different channels. On matched pairs, ron's visible reply scores 0.751 and standard scores 0.844. Ron's reasoning channel scores 0.849 and standard scores 0.854, so raw ED barely moves once reasoning is compared with reasoning.
2. Pairs can have high ED with right answers. In the reasoning channel, every task has at least 93% Hindi accuracy and at least 97% English accuracy, and task means still run from 0.810 to 0.904.
3. ED rises with difficulty in all three selections. In content, the length floor rises and accuracy falls along with it. In reasoning, the floor falls and accuracy stays flat, and ED still rises from 0.825 to 0.874.
4. Answer tokens account for most of the failure gap in content. "Both correct" sits about 0.13 below every failure outcome, and when Hindi flips on the same question the gap is +0.085 on full tokens and +0.005 on step types.
5. Distractors barely move mean ED: similar-distractor means rise by 0.011 in standard content and 0.002 in reasoning. The means do hide one large effect in date recurrence, where a single distractor sentence sent 69% of its English traces into the 4,096-token limit.
6. The "both" selection can't be used as an estimate, because it averages two different kinds of text for ron and changes nothing for standard. It works as a sensitivity check.

## What each selection contains

| Selection | Plots | Standard pairs | Ron pairs | Total |
|---|---|---|---|---|
| `content` | `newplot*.png` in this folder | 20,250 | 1,197 | 21,447 |
| `reasoning_content` | `reasoning/` | 0 | 1,350 | 1,350 |
| Both fields | `both/` | 20,250 | 2,547 | 22,797 |

- Normalized ED is Levenshtein distance over parsed op tokens (ops, operands and answer tokens), divided by the longer sequence. A substitution that differs only by a partial vs full date costs 0.5. A score of 1 means every aligned position differs.
- The length floor is |hi − en| / max(hi, en), the lowest normalized ED a pair's lengths allow.
- Standard has no reasoning channel, so its numbers are the same in `content` and `both`.
- Ron ran with `reasoning_effort: low`, `max_tokens` 16,000 instead of 4,096, and 10 questions per task and difficulty cell. Its comparison with standard is observational.
- Ron content is a filtered sample. 153 of the 1,350 ron pairs have no parsed content on at least one side, nearly always because reasoning used the whole token budget. These are the hard pairs: their reasoning ED is 0.917, against 0.840 for the rest.
- Accuracy columns exclude unanswered records, as the cube's table does, which flatters ron. Counting unanswered as wrong on the same 450 questions, English goes from 87.3% in standard to 92.7% in ron, and Hindi from 59.9% to 89.9%.

## 1. Task by set

| Content | Reasoning | Both |
|---|---|---|
| ![Mean ED by task and set, content](<newplot.png>) | ![Mean ED by task, reasoning](<reasoning/task_by_set.png>) | ![Mean ED by task and set, both fields](<both/task_by_set.png>) |

Mean normalized ED ± the cube's 95% CI:

| Task | Standard | Ron content (n) | Ron reasoning (n = 150) | Ron both (n) |
|---|---|---|---|---|
| date_addition | 0.7721 ± 0.0048 | 0.7026 ± 0.0207 (150) | 0.8096 ± 0.0122 | 0.7561 ± 0.0134 (300) |
| date_duration | 0.8380 ± 0.0035 | 0.7718 ± 0.0152 (148) | 0.8475 ± 0.0084 | 0.8099 ± 0.0097 (298) |
| date_recurrence | 0.8688 ± 0.0037 | 0.7279 ± 0.0270 (112) | 0.8658 ± 0.0081 | 0.8069 ± 0.0149 (262) |
| date_subtraction | 0.8160 ± 0.0053 | 0.7127 ± 0.0234 (150) | 0.8188 ± 0.0122 | 0.7657 ± 0.0145 (300) |
| day_of_week | 0.9377 ± 0.0026 | 0.8570 ± 0.0166 (103) | 0.9044 ± 0.0042 | 0.8851 ± 0.0077 (253) |
| interval_date | 0.9436 ± 0.0020 | 0.8449 ± 0.0162 (99) | 0.9024 ± 0.0049 | 0.8795 ± 0.0079 (249) |
| time_addition | 0.8039 ± 0.0052 | 0.7044 ± 0.0218 (141) | 0.8196 ± 0.0139 | 0.7638 ± 0.0143 (291) |
| time_duration | 0.8650 ± 0.0039 | 0.7993 ± 0.0185 (146) | 0.8353 ± 0.0108 | 0.8176 ± 0.0108 (296) |
| time_subtraction | 0.8343 ± 0.0048 | 0.6948 ± 0.0218 (148) | 0.8365 ± 0.0089 | 0.7661 ± 0.0142 (298) |

Same-pair differences and mean token lengths. Standard lengths are over all 2,250 pairs per task:

| Task | Standard − ron content | Standard − ron reasoning | Standard en / hi | Ron content en / hi | Ron reasoning en / hi | Standard en / hi accuracy | Ron reasoning en / hi accuracy |
|---|---|---|---|---|---|---|---|
| date_addition | +0.075 | −0.032 | 17.5 / 11.7 | 11.3 / 10.4 | 96.8 / 236.5 | 97.1 / 85.2 | 99.3 / 100 |
| date_duration | +0.071 | −0.005 | 32.2 / 10.9 | 14.2 / 11.1 | 197.6 / 352.8 | 99.2 / 87.4 | 97.3 / 96.6 |
| date_recurrence | +0.124 | +0.003 | 80.0 / 24.8 | 20.0 / 17.3 | 460.2 / 570.0 | 88.8 / 21.1 | 98.4 / 93.4 |
| date_subtraction | +0.109 | +0.003 | 23.7 / 11.1 | 13.2 / 11.1 | 137.8 / 258.2 | 94.3 / 67.0 | 98.7 / 100 |
| day_of_week | +0.072 | +0.028 | 175.4 / 40.5 | 35.6 / 30.5 | 788.9 / 1042.5 | 69.1 / 21.8 | 99.2 / 98.2 |
| interval_date | +0.087 | +0.035 | 100.9 / 19.3 | 29.4 / 21.2 | 681.8 / 874.2 | 51.4 / 22.8 | 97.6 / 94.8 |
| time_addition | +0.087 | −0.023 | 31.3 / 13.1 | 11.5 / 11.0 | 143.5 / 239.4 | 96.0 / 74.4 | 99.3 / 98.0 |
| time_duration | +0.065 | +0.029 | 24.2 / 14.7 | 14.8 / 14.5 | 94.8 / 247.9 | 99.2 / 77.7 | 100 / 100 |
| time_subtraction | +0.145 | +0.004 | 27.0 / 13.8 | 12.6 / 12.8 | 121.6 / 274.8 | 97.3 / 75.6 | 99.3 / 98.7 |
| **All matched pairs** | **+0.093** (1,197) | **+0.005** (1,350) | 56.9 / 17.8 | 16.9 / 14.7 | 302.6 / 455.2 | 88.5 / 59.4 | 98.8 / 97.9 |

In the content plot, ron is lower on all nine tasks, by 0.065 to 0.145 on the same pairs. Most of that comes from English getting shorter: on matched pairs, English falls from 44.3 to 16.9 tokens and Hindi only from 16.5 to 14.7. Ron's visible reply is a short write-up of reasoning done elsewhere, so this plot compares a summary with a full chain of thought.

In the reasoning channel the gap closes to +0.005 overall, with tasks ranging from −0.032 (date_addition) to +0.035 (interval_date). The length pattern also reverses. Hindi is longer than English here (455 vs 303 tokens), while in standard English is about three times longer than Hindi. Hindi traces in this channel are only 21% Devanagari letters, so most of this reasoning isn't written in Hindi.

In the both plot, ron bars fall between the other two because they average them. The ron-standard gap in this plot (0.016 to 0.068) doesn't correspond to any actual text.

Task ordering is fairly stable across selections. The Spearman correlation with standard is 0.917 for ron reasoning and 0.833 for ron content, and day_of_week and interval_date rank in the top two everywhere. Length likely contributes, since those two have the longest English traces in every channel.

Accuracy alone doesn't explain task means. In standard, task ED and Hindi accuracy correlate at r = −0.81 (Spearman −0.57, n = 9), but day_of_week scores 0.904 in reasoning with 99% and 98% accuracy.

Raw ED understates the change in reasoning mode. An earlier audit compared English-Hindi ED with the distance between same-language versions of a question, with and without a distractor. The excess over that baseline falls from +0.130 in standard to +0.042 in ron content and +0.032 in ron reasoning, so the language-specific part shrank even though raw reasoning ED looks like standard.

## 2. Set by insertion (distribution)

| Content | Reasoning | Both |
|---|---|---|
| ![ED distribution by set and insertion, content](<newplot (1).png>) | ![ED distribution by insertion, reasoning](<reasoning/set_by_insertion.png>) | ![ED distribution by set and insertion, both fields](<both/set_by_insertion.png>) |

The whiskers show the minimum and maximum, not 1.5 × IQR, because the cube draws these boxes with `boxpoints: false`.

| Selection | Set | Insertion | n | Mean | Median | Q1 | Q3 | Min | Max | En acc. | Hi acc. |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Content | ron | dissimilar | 398 | 0.7443 | 0.7610 | 0.6667 | 0.8421 | 0.2000 | 1 | 0.990 | 0.990 |
| Content | ron | none | 404 | 0.7442 | 0.7647 | 0.6667 | 0.8507 | 0.2500 | 1 | 0.988 | 0.975 |
| Content | ron | similar | 395 | 0.7643 | 0.7857 | 0.6978 | 0.8492 | 0.1667 | 1 | 0.992 | 0.982 |
| Content, both | standard | dissimilar | 6,750 | 0.8525 | 0.8750 | 0.7917 | 0.9412 | 0.2222 | 1 | 0.888 | 0.591 |
| Content, both | standard | none | 6,750 | 0.8480 | 0.8750 | 0.7857 | 0.9389 | 0 | 1 | 0.888 | 0.608 |
| Content, both | standard | similar | 6,750 | 0.8593 | 0.8824 | 0.8000 | 0.9448 | 0.1250 | 1 | 0.879 | 0.583 |
| Reasoning | ron | dissimilar | 450 | 0.8496 | 0.8606 | 0.8089 | 0.9051 | 0.5781 | 0.9916 | 0.991 | 0.986 |
| Reasoning | ron | none | 450 | 0.8473 | 0.8626 | 0.8086 | 0.9012 | 0.4706 | 0.9816 | 0.988 | 0.976 |
| Reasoning | ron | similar | 450 | 0.8497 | 0.8590 | 0.8081 | 0.8970 | 0.6406 | 0.9646 | 0.986 | 0.976 |
| Both | ron | dissimilar | 848 | 0.8002 | 0.8258 | 0.7410 | 0.8871 | 0.2000 | 1 | 0.990 | 0.988 |
| Both | ron | none | 854 | 0.7985 | 0.8278 | 0.7368 | 0.8856 | 0.2500 | 1 | 0.988 | 0.975 |
| Both | ron | similar | 845 | 0.8098 | 0.8333 | 0.7619 | 0.8846 | 0.1667 | 1 | 0.989 | 0.979 |

Same-question differences, which are the valid way to compare insertions:

| Selection | Similar − none | Dissimilar − none | Similar − dissimilar |
|---|---|---|---|
| Standard content (n = 6,750) | +0.0113 ± 0.0029 | +0.0045 ± 0.0029 | +0.0068 ± 0.0029 |
| Ron content (n ≈ 375) | +0.0212 ± 0.0175 | +0.0029 ± 0.0166 | +0.0179 ± 0.0170 |
| Ron reasoning (n = 450) | +0.0024 ± 0.0071 | +0.0023 ± 0.0077 | +0.0001 ± 0.0064 |

All three selections are left-skewed and pressed against the ceiling, so means sit below medians. Standard content has 42.8% of pairs at or above 0.9, and 1.9% at exactly 1. Ron content has only 11.6% at or above 0.9 and the widest spread (IQR about 0.15 to 0.18). Ron reasoning has about half that spread (IQR about 0.09), and no pair reaches 1. Long traces always share some tokens and rarely align well, so their scores bunch together.

The long lower whiskers are single pairs. The 0 in standard is one pair out of 20,250 (date_subtraction, short, question 11, no distractor, 8 tokens on each side), and the next lowest is 0.125.

Standard shows a small, clear ordering of similar > dissimilar > none. The similar effect in ron content is larger but only just clears zero. Reasoning shows no detectable effect, with similar and dissimilar both at +0.002.

In the both plot, the ron boxes span two different distributions, so their medians and quartiles don't describe either channel. The standard boxes are unchanged.

## 3. Task by difficulty

| Content | Reasoning | Both |
|---|---|---|
| ![Mean ED by task and difficulty, content](<newplot (2).png>) | ![Mean ED by task and difficulty, reasoning](<reasoning/task_by_difficulty.png>) | ![Mean ED by task and difficulty, both fields](<both/task_by_difficulty.png>) |

Content, as plotted (standard and ron pooled; each cell n ≈ 480, CI ±0.004 to ±0.013):

| Task | Short | Medium | Long | Very long | Very very long | Rise | Hindi acc. short → v.v. long | English acc. short → v.v. long |
|---|---|---|---|---|---|---|---|---|
| date_addition | 0.6788 | 0.7656 | 0.7836 | 0.7980 | 0.8127 | +0.134 | 0.981 → 0.745 | 1.000 → 0.919 |
| date_duration | 0.7779 | 0.8292 | 0.8399 | 0.8506 | 0.8717 | +0.094 | 0.877 → 0.881 | 0.988 → 0.994 |
| date_recurrence | 0.8156 | 0.8147 | 0.8764 | 0.8872 | 0.9202 | +0.105 | 0.315 → 0.032 | 0.963 → 0.728 |
| date_subtraction | 0.6822 | 0.7810 | 0.8079 | 0.8688 | 0.9080 | +0.226 | 0.975 → 0.294 | 0.988 → 0.881 |
| day_of_week | 0.9202 | 0.9290 | 0.9368 | 0.9415 | 0.9437 | +0.024 | 0.263 → 0.257 | 0.774 → 0.678 |
| interval_date | 0.9255 | 0.9378 | 0.9433 | 0.9454 | 0.9455 | +0.020 | 0.438 → 0.162 | 0.745 → 0.379 |
| time_addition | 0.7700 | 0.7674 | 0.7960 | 0.8186 | 0.8386 | +0.069 | 0.776 → 0.747 | 0.952 → 0.961 |
| time_duration | 0.8023 | 0.8697 | 0.8793 | 0.8680 | 0.8857 | +0.083 | 0.885 → 0.656 | 1.000 → 0.964 |
| time_subtraction | 0.8059 | 0.7980 | 0.8224 | 0.8431 | 0.8589 | +0.053 | 0.820 → 0.688 | 0.973 → 0.936 |

Reasoning (n = 30 per cell, CI ±0.007 to ±0.035), with the rise from the other two selections for comparison:

| Task | Short | Medium | Long | Very long | Very very long | Rise, reasoning | Rise, content | Rise, both |
|---|---|---|---|---|---|---|---|---|
| date_addition | 0.7603 | 0.8004 | 0.8041 | 0.8265 | 0.8567 | +0.096 | +0.134 | +0.132 |
| date_duration | 0.8259 | 0.8406 | 0.8471 | 0.8605 | 0.8632 | +0.037 | +0.094 | +0.091 |
| date_recurrence | 0.8239 | 0.8370 | 0.8641 | 0.8819 | 0.9223 | +0.098 | +0.105 | +0.104 |
| date_subtraction | 0.7609 | 0.7778 | 0.8152 | 0.8659 | 0.8740 | +0.113 | +0.226 | +0.219 |
| day_of_week | 0.8986 | 0.9050 | 0.9067 | 0.9061 | 0.9058 | +0.007 | +0.024 | +0.023 |
| interval_date | 0.8908 | 0.8996 | 0.9117 | 0.8947 | 0.9151 | +0.024 | +0.020 | +0.020 |
| time_addition | 0.8108 | 0.8004 | 0.8133 | 0.8383 | 0.8353 | +0.025 | +0.069 | +0.066 |
| time_duration | 0.8149 | 0.8140 | 0.8480 | 0.8542 | 0.8456 | +0.031 | +0.083 | +0.080 |
| time_subtraction | 0.8355 | 0.8305 | 0.8309 | 0.8389 | 0.8468 | +0.011 | +0.053 | +0.051 |

Profile across all tasks:

| Difficulty | Content ED | Content floor | Content en / hi median tokens | Content en / hi acc. | Reasoning ED | Reasoning floor | Reasoning en / hi mean tokens | Reasoning en / hi acc. | Both ED |
|---|---|---|---|---|---|---|---|---|---|
| short | 0.7975 | 0.405 | 16 / 11 | 0.933 / 0.705 | 0.8246 | 0.559 | 198 / 351 | 0.989 / 0.958 | 0.7991 |
| medium | 0.8320 | 0.441 | 19 / 12 | 0.915 / 0.685 | 0.8339 | 0.537 | 253 / 403 | 0.989 / 0.984 | 0.8321 |
| long | 0.8535 | 0.492 | 24 / 13 | 0.898 / 0.631 | 0.8490 | 0.516 | 272 / 440 | 0.992 / 0.992 | 0.8533 |
| very_long | 0.8686 | 0.528 | 31 / 14 | 0.871 / 0.552 | 0.8630 | 0.505 | 353 / 494 | 0.984 / 0.984 | 0.8683 |
| very_very_long | 0.8867 | 0.567 | 41 / 15 | 0.836 / 0.503 | 0.8739 | 0.467 | 437 / 588 | 0.987 / 0.978 | 0.8859 |

In content, failure and divergence rise together on some tasks. Date subtraction is the clearest case: ED rises by 0.226 while Hindi accuracy falls from 97.5% to 29.4%. The within-task correlation between ED and the en-hi accuracy gap is above 0.9 for date and time subtraction (5 points per task, so descriptive only).

ED also rises without failure. Date duration rises by 0.094 with Hindi accuracy flat at 88%, and time addition by 0.069 with Hindi accuracy almost flat. Restricting to pairs where both languages are right still leaves rises of 0.016 to 0.167 by task, though date recurrence has only 10 such pairs at very very long, so its figure is weak.

The top two tasks are saturated. Day of week and interval date start at 0.92 and rise by 0.024 or less. Interval date's English accuracy halves from 74.5% to 37.9% with almost no ED change, because scores near the ceiling have little room to move. ED can't track difficulty on these tasks.

Date recurrence (short vs medium), time addition and time subtraction (short vs medium) and time duration (long vs very long) all reverse slightly, but each of those differences sits within overlapping CIs.

Reasoning has the same shape, with rises smaller on eight of nine tasks. They rank in nearly the same order as standard content (Spearman 0.90): date subtraction, date recurrence and date addition lead, and day of week stays flat. With n = 30 per cell, time-task reversals here are noise.

Across all tasks in reasoning, ED climbs by 0.049 while the floor falls by 0.092 and accuracy stays above 95% in both languages. Length asymmetry and wrong answers can't explain that rise. It points to harder problems producing more differently ordered or differently valued steps, though these plots can't separate the two.

The both plot is almost identical to content, with a largest cell shift of 0.005, because ron is only 11% of the pooled pairs.

## 4. Outcome by insertion

| Content | Reasoning | Both |
|---|---|---|
| ![Mean ED by outcome and insertion, content](<newplot (3).png>) | ![Mean ED by outcome and insertion, reasoning](<reasoning/outcome_by_insertion.png>) | ![Mean ED by outcome and insertion, both fields](<both/outcome_by_insertion.png>) |

Mean ED for each insertion, listed as dissimilar / none / similar:

| Outcome | Content | Content n | Reasoning | Reasoning n | Both |
|---|---|---|---|---|---|
| both correct | 0.7915 / 0.7873 / 0.7999 | 4,155 / 4,244 / 4,069 | 0.8403 / 0.8364 / 0.8395 | 389 / 388 / 382 | 0.7957 / 0.7914 / 0.8033 |
| en only | 0.9165 / 0.9158 / 0.9185 | 2,070 / 1,945 / 1,952 | 0.8730 / 0.8726 / 0.8771 | 4 / 9 / 7 | 0.9164 / 0.9156 / 0.9184 |
| hi only | 0.9292 / 0.9232 / 0.9187 | 172 / 178 / 166 | 0.8634 / 0.9179 / 0.9044 | 4 / 4 / 3 | 0.9277 / 0.9231 / 0.9185 |
| both wrong | 0.9265 / 0.9235 / 0.9241 | 564 / 544 / 603 | — / 0.8338 / — | 0 / 1 / 0 | 0.9265 / 0.9233 / 0.9241 |
| unanswered | 0.9743 / 0.9685 / 0.9709 | 187 / 243 / 355 | 0.9154 / 0.9252 / 0.9113 | 53 / 48 / 58 | 0.9613 / 0.9614 / 0.9625 |

Pooled over insertion:

| Outcome | Standard n | Standard ED | Standard floor | Ron content n | Ron content ED | Ron reasoning n | Ron reasoning ED | Ron reasoning floor |
|---|---|---|---|---|---|---|---|---|
| both correct | 11,309 | 0.7977 | 0.413 | 1,159 | 0.7458 | 1,159 | 0.8387 | 0.530 |
| en only | 5,947 | 0.9169 | 0.555 | 20 | 0.9258 | 20 | 0.8743 | 0.559 |
| hi only | 505 | 0.9247 | 0.581 | 11 | 0.8788 | 11 | 0.8944 | 0.610 |
| both wrong | 1,710 | 0.9248 | 0.678 | 1 | 0.8000 | 1 | 0.8338 | 0.586 |
| unanswered | 779 | 0.9715 | 0.853 | 6 | 0.8998 | 159 | 0.9169 | 0.405 |

In content, any failure adds about 0.13. The step from both correct (0.79) to en only, hi only or both wrong (0.92) is the largest in these plots, and the three failure outcomes are nearly equal. Task mix doesn't explain it: within task and difficulty, en only sits above both correct in 45 of 45 standard cells, by 0.094 on average and at least 0.014.

The gap alone doesn't show that failing traces took a different route. A wrong answer can't match the other language's answer tokens, and failures also tend to be longer. Take questions where English is right throughout and Hindi is right under one distractor condition but wrong under another (2,356 questions). The wrong-minus-right difference is:

| Token view | Wrong − right | 95% CI |
|---|---|---|
| Full tokens | +0.085 | [0.081, 0.089] |
| Answer tokens removed | +0.027 | [0.023, 0.031] |
| Step types only | +0.005 | [−0.000, 0.011] |

Date recurrence is the one clear exception, at +0.062 [0.048, 0.076] on step types. Interval date and time subtraction are slightly negative (−0.017 and −0.019), and the remaining six tasks' intervals include zero.

En only, hi only and both wrong are within 0.01 of each other, so the direction of failure makes little difference. Both-wrong pairs also rarely agree: only 323 of 1,710 end on the same answer token, and those score 0.873 against 0.937 for the rest.

Unanswered means something different in each channel:

- In standard it means the token limit. 651 of 651 English no-answer records and 145 of 146 Hindi ones stopped at 4,096 tokens. Median lengths are 334 (English) vs 30 (Hindi), and the floor of 0.85 accounts for most of the score.
- In ron reasoning it covers 159 pairs, 153 of which have no visible content. The pairs average 974 and 1,130 tokens, so both sides tend to be long and the floor is only 0.405, which means the 0.917 score isn't a length artefact in the same way.

Most of the outcome bars in reasoning are too small to read. Only both correct and unanswered have usable counts. The wide error bars on en only and hi only come from n = 3 to 9, and the lone both-wrong bar is a single pair. Pooled, the 31 disagreements sit at 0.874 and 0.894 against 0.839 for both correct, a smaller gap than in content.

The only visible change in the both plot is the unanswered bars, down by up to 0.013, because reasoning's lower-scoring unanswered pairs enter the pool.

The bars also don't show how many pairs are unanswered. Bar heights look alike across insertions, but the counts are 187 / 243 / 355, and almost all of the similar-distractor increase comes from one task. In standard date recurrence, unanswered pairs go 23 / 23 / 130 (dissimilar / none / similar):

- On the same questions, similar adds +14.3 points of unanswered pairs (± 2.9, n = 750). Dissimilar adds 0.0 (± 1.7).
- English cut-offs account for it: 20 / 19 / 118.
- One distractor sentence causes most of it: "The last time I had a weekly commitment was in January." It appears in 134 similar-distractor questions, and 92 of those (69%) hit the token limit in English. The other four sentences cause 26 cut-offs across 616 questions (4%).
- 91 of the 118 cut-off traces mention "weekly", against 39 of the 632 other traces. The questions say the event recurs every 13 days, so the distractor conflicts with them. The one trace I read in full keeps revisiting how to interpret the setup until it runs out of tokens, but that mechanism comes from one trace and hasn't been measured.
- Ron reasoning shows no comparable jump in date recurrence (13 / 12 / 17 unanswered), on 50 questions per condition and a 16,000-token budget. Results for that sentence alone were not checked.

Day of week moves the other way, with fewer unanswered pairs under distractors in standard (117 / 166 / 138).

## 5. Insertion by difficulty

| Content | Reasoning | Both |
|---|---|---|
| ![Mean ED by insertion and difficulty, content](<newplot (4).png>) | ![Mean ED by insertion and difficulty, reasoning](<reasoning/insertion_by_difficulty.png>) | ![Mean ED by insertion and difficulty, both fields](<both/insertion_by_difficulty.png>) |

Mean ED for each insertion, listed as dissimilar / none / similar:

| Difficulty | Content (n ≈ 1,430 per bar) | Reasoning (n = 90 per bar) | Both (n ≈ 1,520 per bar) |
|---|---|---|---|
| short | 0.7970 / 0.7879 / 0.8077 | 0.8332 / 0.8188 / 0.8219 | 0.7991 / 0.7897 / 0.8085 |
| medium | 0.8327 / 0.8249 / 0.8383 | 0.8352 / 0.8369 / 0.8296 | 0.8329 / 0.8256 / 0.8378 |
| long | 0.8512 / 0.8489 / 0.8605 | 0.8455 / 0.8459 / 0.8555 | 0.8508 / 0.8487 / 0.8602 |
| very_long | 0.8663 / 0.8650 / 0.8746 | 0.8651 / 0.8588 / 0.8651 | 0.8663 / 0.8646 / 0.8740 |
| very_very_long | 0.8858 / 0.8844 / 0.8899 | 0.8689 / 0.8761 / 0.8766 | 0.8848 / 0.8839 / 0.8891 |

Same-question differences from no distractor:

| Difficulty | Content, similar | Content, dissimilar | Reasoning, similar | Reasoning, dissimilar |
|---|---|---|---|---|
| short | **+0.0199 ± 0.0075** | **+0.0092 ± 0.0073** | +0.0031 ± 0.0197 | +0.0144 ± 0.0211 |
| medium | **+0.0134 ± 0.0070** | **+0.0077 ± 0.0072** | −0.0073 ± 0.0175 | −0.0017 ± 0.0181 |
| long | **+0.0115 ± 0.0062** | +0.0023 ± 0.0063 | +0.0096 ± 0.0154 | −0.0004 ± 0.0174 |
| very_long | **+0.0090 ± 0.0057** | +0.0017 ± 0.0060 | +0.0063 ± 0.0130 | +0.0063 ± 0.0144 |
| very_very_long | +0.0053 ± 0.0054 | +0.0010 ± 0.0054 | +0.0006 ± 0.0132 | −0.0071 ± 0.0147 |

Bold marks intervals that exclude zero. None are corrected for multiple comparisons.

Difficulty has the larger effect. Within any insertion condition, short to very very long adds about 0.08 to 0.10 in content, while the largest insertion effect at any difficulty is 0.020. In reasoning, short to very very long adds 0.036 to 0.057.

In content, similar > dissimilar > none holds at all five difficulties, and the similar effect shrinks from +0.020 to +0.005 as questions get longer. That fits one added sentence mattering less in a longer trace, but the ceiling is also closer at high difficulty, and these plots can't separate the two. Dissimilar is only detectable at short and medium.

In reasoning, no interval excludes zero and the ordering isn't consistent across difficulties, so there's no detectable distractor effect at this sample size. These intervals are 2 to 3 times wider than in content, so an effect the size of content's can't be ruled out at any single difficulty. Pooled over difficulty, the interval (±0.007) does exclude a similar-distractor effect as large as ron content's +0.021.

The both plot is close to content again, with a largest shift of 0.002.

ED picks up distractors poorly. The earlier audit found that similar and dissimilar distractors lower Hindi accuracy by 2.5 and 1.6 points, while ED moves by only 0.011 and 0.004. On date duration, Hindi loses 7.0 points with ED up 0.004. The date recurrence cut-offs in section 4 are another case, where a large change in behaviour becomes a small shift in the insertion means.

## Which selection to use for what

| Question | Use | Reason |
|---|---|---|
| English-Hindi divergence in ordinary CoT | Standard content | Full reasoning is in the visible reply, with the most data |
| Whether reasoning mode changes divergence | Ron reasoning vs standard content, on matched pairs, with the self-distance control | Compares reasoning with reasoning, and includes the hard pairs |
| How much the visible reply differs | Ron content | It answers this specific question, but drops 153 hard pairs, and it is not comparable to standard CoT |
| Distractor effects | Paired differences, not the plotted means | Removes between-question variance |
| Checking results don't depend on the channel | Both | Only as a sensitivity check; it should not be quoted as an estimate |

## Limits

- CIs in the plots are too narrow for some comparisons. The cube treats each pair as independent, but the three insertion versions of a question are related. In `both`, ron's two channels for the same question are counted separately as well. The paired tables above avoid the first problem.
- The content plots pool ron into standard. With the `set` filter left at both sets, sections 3 to 5 include ron. The largest shift from standard-only is 0.0115 (date recurrence, very long), and it is at most 0.0073 for the other two views.
- Ron bars in content cover a smaller, easier sample. Bars for date recurrence, day of week and interval date exclude 25% to 34% of pairs.
- Reasoning cells are small. Task by difficulty has n = 30 per cell, on 10 questions per condition.
- Some numbers come from an earlier audit in `tests/ed_audit/outputs/cube_findings/`, not from the cube page: the self-distance excess, step-type differences, Devanagari share, accuracy with unanswered counted as wrong, and distractor accuracy effects. I recomputed the +0.085 full-token result from the cube page and it matches (+0.0849 ± 0.0039).
- Everything here comes from one model and one decoding setup (greedy). These are descriptive comparisons, and no causal claims follow from them.
- Parser error can hide step-type effects. Date recurrence shows the step-type view can detect an effect, but it does not bound how much the view misses on other tasks.

## Figures

The content plots are the original exports, unchanged. `newplot.png` and `newplot (2).png` clip the `time_subtraction` label, and `newplot (2).png` has its axis title overlapping the legend.

The reasoning and both plots were rendered through the cube page's own drawing code, with the selection named in each title. They differ from the original exports in size, in having a fixed y-axis of 0 to 1.05, and in the label fixes. Versions of the content plots in the same format are in `tests/ed_audit/outputs/final_plots/content_rendered/`.

## Regenerate

```bash
python3 tests/ed_audit/final_plots_render.py
.venv/bin/python tests/ed_audit/final_plots.py
```

The first needs Chrome and network access for the Plotly CDN. The second writes every table above to `tests/ed_audit/outputs/final_plots/` (`log.txt` and one CSV per view).
