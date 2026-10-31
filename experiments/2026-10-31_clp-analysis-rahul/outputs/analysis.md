# CLP analysis

## Data and unscored responses

| Condition | Responses | Questions | No Answer line | of which cut off |
|---|---|---|---|---|
| English direct | 6750 | 2250 | 7 | 7 |
| English CoT | 6750 | 2250 | 221 | 221 |
| Hindi direct | 6750 | 2250 | 0 | 0 |
| Hindi CoT | 6750 | 2250 | 43 | 43 |
| Hindi en-CoT | 6750 | 2250 | 174 | 174 |
| Hindi CLP | 6750 | 2250 | 39 | 39 |

CLP stage 1 was cut off at 4,096 tokens in 68 responses. Checks: CLP and en-CoT question texts and gold answers match the standard runs for every record (0 and 0 mismatches for CLP, 0 and 0 for en-CoT).

## Accuracy by task (% of answered responses)

| Task | English direct | English CoT | Hindi direct | Hindi CoT | Hindi en-CoT | Hindi CLP | CLP − Hindi CoT | CLP − Hindi direct | CLP − en-CoT |
|---|---|---|---|---|---|---|---|---|---|
| date addition | 85.6 | 98.0 | 82.8 | 85.1 | 95.7 | 92.7 | +7.6* | +9.9* | -3.1* |
| date subtraction | 86.0 | 95.2 | 84.8 | 66.0 | 94.0 | 86.9 | +20.9* | +2.1 | -7.1* |
| date duration | 84.0 | 99.3 | 78.9 | 88.3 | 97.7 | 92.7 | +4.4* | +13.7* | -5.1* |
| date recurrence | 22.1 | 90.3 | 2.8 | 20.1 | 70.3 | 27.0 | +6.8* | +24.2* | -43.4* |
| day of week | 14.9 | 69.5 | 15.2 | 21.0 | 52.5 | 31.8 | +10.8* | +16.6* | -20.7* |
| interval date | 43.2 | 50.7 | 46.8 | 23.9 | 44.1 | 35.3 | +11.4* | -11.5* | -8.8* |
| time addition | 70.5 | 95.9 | 75.6 | 73.5 | 92.6 | 88.2 | +14.7* | +12.6* | -4.4* |
| time subtraction | 64.7 | 97.7 | 64.9 | 75.2 | 95.7 | 90.1 | +14.9* | +25.2* | -5.6* |
| time duration | 65.7 | 98.9 | 44.7 | 80.1 | 98.1 | 86.7 | +6.6* | +42.0* | -11.5* |
| **All tasks** | 59.7 | 88.9 | 55.2 | 59.4 | 82.9 | 70.3 | +10.9* | +15.1* | -12.6* |

2,250 questions × 3 distractor conditions per cell. * exact McNemar p < 0.05 on paired responses, Holm-corrected over the 9 tasks within each comparison (the All row is uncorrected). Overall CIs (cluster bootstrap over questions): Hindi CLP − Hindi CoT +10.9 [+9.6, +12.2]; Hindi CLP − Hindi direct +15.1 [+13.6, +16.7]; Hindi CLP − Hindi en-CoT -12.6 [-13.9, -11.3]; English CoT − Hindi CLP +18.6 [+17.3, +19.9]. Counting unanswered responses as wrong: English direct 59.6, English CoT 86.0, Hindi direct 55.2, Hindi CoT 59.0, Hindi en-CoT 80.8, Hindi CLP 69.9.

## Paired comparisons, all tasks

| Comparison | Pairs | Only first right | Only second right | Δ (points) [95% CI] | p |
|---|---|---|---|---|---|
| Hindi CLP vs Hindi CoT | 6668 | 1297 | 562 | +10.9 [+9.6, +12.2] | <0.001 |
| Hindi CLP vs Hindi direct | 6711 | 1536 | 535 | +15.1 [+13.6, +16.7] | <0.001 |
| Hindi CLP vs Hindi en-CoT | 6540 | 400 | 1158 | -12.6 [-13.9, -11.3] | <0.001 |
| English CoT vs Hindi CLP | 6497 | 1366 | 240 | +18.6 [+17.3, +19.9] | <0.001 |

## Accuracy by difficulty (%)

| Level | English direct | English CoT | Hindi direct | Hindi CoT | Hindi en-CoT | Hindi CLP | Gap En CoT − Hi CoT | Gap En CoT − Hi CLP |
|---|---|---|---|---|---|---|---|---|
| short | 77.8 | 93.2 | 73.9 | 69.5 | 83.0 | 77.2 | +23.6 [+20.7, +27.0] | +16.0 [+13.0, +19.0] |
| medium | 69.6 | 91.6 | 65.3 | 65.4 | 84.9 | 75.7 | +26.2 [+23.3, +29.1] | +15.9 [+13.3, +18.7] |
| long | 61.2 | 89.3 | 57.9 | 60.4 | 84.4 | 71.3 | +28.9 [+25.7, +32.1] | +18.0 [+15.2, +20.7] |
| very long | 54.3 | 87.2 | 48.4 | 53.7 | 83.5 | 65.8 | +33.5 [+30.1, +36.8] | +21.4 [+18.4, +24.5] |
| very very long | 35.5 | 82.9 | 30.3 | 47.9 | 78.5 | 61.5 | +35.0 [+31.6, +38.5] | +21.4 [+18.1, +24.6] |

All nine tasks at every level (450 questions per level). Gaps in points with cluster-bootstrap 95% CIs.

## Distractors: accuracy (%) and drops (points)

| Condition | None | Time-related | Unrelated | Drop, time-related [95% CI] | Drop, unrelated [95% CI] |
|---|---|---|---|---|---|
| English direct | 60.6 | 59.9 | 58.6 | +0.7 [-1.0, +2.5] | +2.0 [+0.4, +3.7] |
| English CoT | 89.3 | 88.1 | 89.2 | +1.2 [-0.5, +2.7] | +0.2 [-1.4, +1.6] |
| Hindi direct | 56.0 | 54.9 | 54.6 | +1.2 [-0.5, +2.9] | +1.5 [-0.3, +3.2] |
| Hindi CoT | 60.2 | 58.9 | 59.1 | +1.3 [-0.8, +3.6] | +1.2 [-0.9, +3.2] |
| Hindi en-CoT | 84.1 | 81.0 | 83.6 | +3.2 [+1.3, +5.0] | +0.6 [-1.2, +2.4] |
| Hindi CLP | 69.3 | 69.3 | 72.3 | -0.1 [-2.1, +2.0] | -3.1 [-5.1, -1.1] |

Drop = accuracy without the distractor minus accuracy with it (positive: the distractor hurt).

## Distraction penalty relative to Hindi direct answers (points)

| Reasoning condition | Time-related [95% CI] | Unrelated [95% CI] |
|---|---|---|
| Hindi CoT | +0.2 [-2.6, +2.9] | -0.3 [-3.0, +2.4] |
| Hindi en-CoT | +2.0 [-0.6, +4.4] | -0.9 [-3.4, +1.5] |
| Hindi CLP | -1.2 [-4.1, +1.5] | -4.5 [-7.2, -1.9] |
| CLP drop − Hindi CoT drop | -1.4 [-4.4, +1.7] | -4.2 [-7.0, -1.3] |

Penalty = the condition's distractor drop minus the Hindi direct drop on the same questions (the mid report's CoT distraction penalty, with CLP or en-CoT in place of CoT).

## Wrong answers containing a number, month or weekday from the time-related distractor

| Condition | With distractor | Placebo (no distractor) | Fisher p |
|---|---|---|---|
| English direct | 4.9% (17/350) | 3.9% (14/359) | 0.58 |
| English CoT | 1.8% (2/114) | 0.0% (0/96) | 0.50 |
| Hindi direct | 12.6% (51/404) | 3.8% (15/390) | <0.001 |
| Hindi CoT | 3.2% (13/406) | 2.8% (11/387) | 0.84 |
| Hindi en-CoT | 2.0% (4/200) | 1.4% (2/148) | 1.00 |
| Hindi CLP | 2.6% (9/342) | 3.1% (10/325) | 0.82 |

Placebo: wrong answers to the same questions without the distractor, checked against the distractor that would have been inserted.

## Distractor mentions in the reasoning (% of answered responses; placebo in brackets) and odds ratio of a correct answer when mentioned

| Text | Time-related | Unrelated | OR, time-related | OR, unrelated |
|---|---|---|---|---|
| English CoT | 17.3 (8.9) | 11.0 (6.3) | 0.61 [0.39, 0.93] | 1.63 [0.90, 2.96] |
| Hindi CoT | 34.0 (10.3) | 28.7 (1.9) | 0.85 [0.68, 1.07] | 1.30 [1.00, 1.70] |
| Hindi en-CoT | 22.0 (9.3) | 17.0 (5.5) | 0.82 [0.59, 1.13] | 0.91 [0.58, 1.43] |
| Hindi CLP, stage 1 | 62.9 (9.4) | 83.7 (2.8) | 1.02 [0.79, 1.30] | 1.65 [1.19, 2.30] |
| Hindi CLP, stage 2 | 17.2 (9.7) | 8.7 (2.3) | 1.00 [0.72, 1.40] | 1.30 [0.81, 2.07] |

A text mentions the distractor if it contains a content word of the distractor that is not in the question (mid-report rule). For CLP and en-CoT, which reason in English about a Hindi question, the words of the matching English distractor also count. Placebo: the same check on responses to the same questions without the distractor. OR: Mantel–Haenszel odds ratio of a correct final answer for responses that mention the distractor versus those that do not, stratified by task and difficulty.

## Properties of the reasoning (answered responses)

|  | English CoT | Hindi CoT | Hindi en-CoT | CLP stage 2 | CLP stage 1 |
|---|---|---|---|---|---|
| Median words | 107 | 83 | 96 | 97 | 96 |
| Median completion tokens | 353 | 212 | 311 | 233 | 236 |
| Share of English words | 1.000 | 0.011 | 0.998 | 0.999 | 0.977 |
| Has a verification step (%) | 86.1 | 1.3 | 74.2 | 26.9 | 5.8 |
| Answer value appears in the reasoning (%) | 99.8 | 98.5 | 99.9 | 98.3 | – |
| Wrong answers whose reasoning ended at the gold value | 1 of 726 | 8 of 2,723 | 11 of 1,125 | 7 of 1,993 | – |

CLP uses a median of 487 completion tokens over both stages. Share of English words = English words / (English + Devanagari words), pooled over responses.

## From stage 1 to stage 2 (CLP, date-answer tasks)

|  | Stage 1 ends at the gold date | Stage 1 ends elsewhere | All |
|---|---|---|---|
| Responses | 1414 | 826 | 2240 |
| Stage 2 correct (%) | 97.5 | 20.1 | 69.0 |
| Stage 2 final answer = stage 1's last date (%) | 97.6 | 55.7 | 82.1 |

Date addition, date subtraction and date recurrence only (answers are dates, so stage 1's last date can be read reliably; checked by hand on 12 random responses). Stage 1 contains a date other than the question's in 98.6% of responses. Of 695 wrong stage-2 answers, 461 repeat stage 1's last date. On the same tasks, en-CoT is correct in 87.1%, Hindi CoT in 57.1% and English CoT in 94.6%.

## Stage 1 by task

| Task | Responses | Stage 1 ends at gold (%) | CLP correct (%) | en-CoT correct (%) |
|---|---|---|---|---|
| date addition | 750 | 86.3 | 92.7 | 95.7 |
| date subtraction | 748 | 83.8 | 86.9 | 94.0 |
| date recurrence | 742 | 18.9 | 27.0 | 70.3 |

## Does the Hindi condition fail on the same questions as English?

| Hindi condition (vs English) | Pairs | Both right | Both wrong | Only English right | Only Hindi right | Median φ within task × level [IQR] |
|---|---|---|---|---|---|---|
| Hindi direct (vs English direct) | 6743 | 3143 | 2138 | 881 | 581 | 0.28 [0.14, 0.42] |
| Hindi CoT (vs English CoT) | 6490 | 3778 | 557 | 2000 | 155 | 0.07 [-0.01, 0.12] |
| Hindi en-CoT (vs English CoT) | 6395 | 5033 | 370 | 672 | 320 | 0.02 [-0.03, 0.19] |
| Hindi CLP (vs English CoT) | 6497 | 4412 | 479 | 1366 | 240 | 0.10 [-0.03, 0.14] |

Pairs are the same question and distractor condition in both languages. φ is the correlation of right/wrong between the two, computed within each task × difficulty cell that has both right and wrong answers in both conditions (43, 35, 34, 35 of 45 cells, in table order), so that differences in difficulty between cells do not inflate it.

## Day of week: predicted minus correct weekday (% of answered)

| Condition | n | −3 | −2 | −1 | 0 (correct) | +1 | +2 | +3 |
|---|---|---|---|---|---|---|---|---|
| English direct | 750 | 13.9 | 13.3 | 12.8 | 14.9 | 15.5 | 13.6 | 16.0 |
| English CoT | 630 | 2.4 | 2.5 | 6.2 | 69.5 | 16.2 | 2.1 | 1.1 |
| Hindi direct | 750 | 11.9 | 16.1 | 15.6 | 15.2 | 12.9 | 12.4 | 15.9 |
| Hindi CoT | 722 | 8.9 | 10.7 | 10.4 | 21.1 | 25.3 | 11.2 | 12.5 |
| Hindi en-CoT | 659 | 4.1 | 5.2 | 5.9 | 52.5 | 24.0 | 4.9 | 3.5 |
| Hindi CLP | 723 | 8.9 | 9.7 | 10.0 | 32.1 | 22.4 | 7.6 | 9.4 |

## Date recurrence answer patterns (% of answered)

| Condition | n | Correct | First step only | Mirror (backwards) | Other |
|---|---|---|---|---|---|
| English direct | 741 | 22.1 | 21.3 | 0.9 | 55.6 |
| English CoT | 702 | 90.5 | 0.1 | 0.4 | 9.0 |
| Hindi direct | 750 | 2.8 | 21.5 | 7.5 | 68.3 |
| Hindi CoT | 746 | 20.1 | 8.7 | 9.0 | 62.2 |
| Hindi en-CoT | 698 | 70.3 | 5.9 | 8.3 | 15.5 |
| Hindi CLP | 742 | 27.1 | 6.3 | 8.1 | 58.5 |

First step only: today plus one interval, ignoring which occurrence was asked for. Mirror: the right number of days, counted backwards.

## Composition of wrong answers (%)

| Condition | Wrong answers | Off by one | Wrong direction | Month slip | Other |
|---|---|---|---|---|---|
| English CoT | 726 | 52.3 | 0.4 | 0.3 | 47.0 |
| Hindi CoT | 2723 | 21.2 | 2.8 | 1.1 | 75.0 |
| Hindi en-CoT | 1125 | 42.3 | 5.2 | 0.7 | 51.8 |
| Hindi CLP | 1993 | 26.9 | 3.1 | 0.9 | 69.1 |

Mid-report error classes; 'wrong direction' is the mirror image of the correct date or time around the one in the question.
