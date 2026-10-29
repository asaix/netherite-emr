# Trace deletion results

234 complete traces (0 incomplete). Accuracy in % on originally wrong traces.

### By language

| group | n | A | B | C | B-C (95% CI) | only B / only C | McNemar p | A = original |
|---|---|---|---|---|---|---|---|---|
| en_US | 12 | 25.0 | 33.3 | 25.0 | 8.3 [0.0, 25.0] | 1 / 0 | 1 | 50.0 |
| hi_IN | 222 | 29.3 | 32.9 | 28.4 | 4.5 [-2.7, 11.7] | 37 / 27 | 0.26 | 20.3 |

### Hindi by task

| group | n | A | B | C | B-C (95% CI) | only B / only C | McNemar p | A = original |
|---|---|---|---|---|---|---|---|---|
| date_addition | 10 | 80.0 | 60.0 | 60.0 | 0.0 [-40.0, 40.0] | 2 / 2 | 1 | 0.0 |
| date_duration | 25 | 56.0 | 76.0 | 64.0 | 12.0 [-4.0, 28.0] | 4 / 1 | 0.375 | 28.0 |
| date_recurrence | 79 | 16.5 | 17.7 | 12.7 | 5.1 [-6.3, 16.5] | 13 / 9 | 0.523 | 12.7 |
| date_subtraction | 6 | 0.0 | 50.0 | 50.0 | 0.0 [-66.7, 66.7] | 2 / 2 | 1 | 16.7 |
| day_of_week | 18 | 38.9 | 33.3 | 16.7 | 16.7 [-11.1, 44.4] | 5 / 2 | 0.453 | 22.2 |
| interval_date | 51 | 15.7 | 13.7 | 13.7 | 0.0 [-13.7, 13.7] | 7 / 7 | 1 | 37.3 |
| time_addition | 11 | 45.5 | 72.7 | 72.7 | 0.0 [-36.4, 36.4] | 2 / 2 | 1 | 9.1 |
| time_duration | 20 | 45.0 | 50.0 | 50.0 | 0.0 [-20.0, 20.0] | 2 / 2 | 1 | 10.0 |
| time_subtraction | 2 | 50.0 | 0.0 | 0.0 | 0.0 [0.0, 0.0] | 0 / 0 | 1 | 50.0 |

### Hindi by difficulty

| group | n | A | B | C | B-C (95% CI) | only B / only C | McNemar p | A = original |
|---|---|---|---|---|---|---|---|---|
| long | 49 | 40.8 | 40.8 | 40.8 | 0.0 [-14.3, 14.3] | 6 / 6 | 1 | 16.3 |
| medium | 40 | 37.5 | 30.0 | 32.5 | -2.5 [-22.5, 17.5] | 7 / 8 | 1 | 15.0 |
| short | 42 | 28.6 | 35.7 | 28.6 | 7.1 [-9.5, 23.8] | 9 / 6 | 0.607 | 33.3 |
| very_long | 44 | 18.2 | 29.5 | 27.3 | 2.3 [-11.4, 15.9] | 5 / 4 | 1 | 25.0 |
| very_very_long | 47 | 21.3 | 27.7 | 12.8 | 14.9 [0.0, 27.7] | 10 / 3 | 0.0923 | 12.8 |

### Hindi by whether the deleted mention has digits

| group | n | A | B | C | B-C (95% CI) | only B / only C | McNemar p | A = original |
|---|---|---|---|---|---|---|---|---|
| False | 152 | 28.3 | 29.6 | 26.3 | 3.3 [-5.3, 11.8] | 24 / 19 | 0.542 | 21.1 |
| True | 70 | 31.4 | 40.0 | 32.9 | 7.1 [-5.7, 20.0] | 13 / 8 | 0.383 | 18.6 |

### Shared tasks (recurrence, interval, day of week)

| group | n | A | B | C | B-C (95% CI) | only B / only C | McNemar p | A = original |
|---|---|---|---|---|---|---|---|---|
| hi_IN | 148 | 18.9 | 18.2 | 13.5 | 4.7 [-4.1, 13.5] | 25 / 18 | 0.36 | 22.3 |
| en_US | 9 | 11.1 | 11.1 | 0.0 | 11.1 [0.0, 33.3] | 1 / 0 | 1 | 55.6 |

Repeatability: A run twice on 234 traces gives identical text in 4.3% and the same answer in 42.7%.

(B-C) Hindi minus English on shared tasks: -6.4 pts [-32.7, 11.3]

### Re-mention of the distractor in the continuation (%)

| language | A | B | C |
|---|---|---|---|
| en_US | 33.3 | 16.7 | 33.3 |
| hi_IN | 34.7 | 35.1 | 31.5 |

### Unanswered or cut off, deleted length

| language | unanswered A/B/C | mean deleted chars B / C |
|---|---|---|
| en_US | 1/1/1 | 105 / 60 |
| hi_IN | 16/10/11 | 67 / 52 |
