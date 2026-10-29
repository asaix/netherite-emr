# Trace deletion results

234 complete traces (0 incomplete). Accuracy in % on originally wrong traces.

### By language

| group | n | A | B | C | B-C (95% CI) | only B / only C | McNemar p | A = original |
|---|---|---|---|---|---|---|---|---|
| en_US | 12 | 25.0 | 16.7 | 25.0 | -8.3 [-25.0, 0.0] | 0 / 1 | 1 | 50.0 |
| hi_IN | 222 | 33.3 | 33.8 | 33.8 | 0.0 [-6.8, 7.2] | 32 / 32 | 1 | 17.6 |

### Hindi by task

| group | n | A | B | C | B-C (95% CI) | only B / only C | McNemar p | A = original |
|---|---|---|---|---|---|---|---|---|
| date_addition | 10 | 60.0 | 50.0 | 70.0 | -20.0 [-60.0, 30.0] | 2 / 4 | 0.688 | 20.0 |
| date_duration | 25 | 64.0 | 68.0 | 72.0 | -4.0 [-20.0, 12.0] | 2 / 3 | 1 | 12.0 |
| date_recurrence | 79 | 17.7 | 20.3 | 15.2 | 5.1 [-6.3, 16.5] | 12 / 8 | 0.503 | 16.5 |
| date_subtraction | 6 | 66.7 | 33.3 | 66.7 | -33.3 [-66.7, 0.0] | 0 / 2 | 0.5 | 16.7 |
| day_of_week | 18 | 38.9 | 50.0 | 22.2 | 27.8 [-5.6, 55.6] | 7 / 2 | 0.18 | 0.0 |
| interval_date | 51 | 9.8 | 13.7 | 15.7 | -2.0 [-13.7, 9.8] | 4 / 5 | 1 | 33.3 |
| time_addition | 11 | 54.5 | 45.5 | 54.5 | -9.1 [-54.5, 36.4] | 3 / 4 | 1 | 18.2 |
| time_duration | 20 | 80.0 | 65.0 | 75.0 | -10.0 [-30.0, 15.0] | 2 / 4 | 0.688 | 5.0 |
| time_subtraction | 2 | 0.0 | 50.0 | 50.0 | 0.0 [0.0, 0.0] | 0 / 0 | 1 | 0.0 |

### Hindi by difficulty

| group | n | A | B | C | B-C (95% CI) | only B / only C | McNemar p | A = original |
|---|---|---|---|---|---|---|---|---|
| long | 49 | 36.7 | 40.8 | 38.8 | 2.0 [-12.2, 16.3] | 7 / 6 | 1 | 14.3 |
| medium | 40 | 30.0 | 40.0 | 37.5 | 2.5 [-15.0, 20.0] | 7 / 6 | 1 | 22.5 |
| short | 42 | 35.7 | 35.7 | 26.2 | 9.5 [-4.8, 23.8] | 7 / 3 | 0.344 | 16.7 |
| very_long | 44 | 34.1 | 29.5 | 40.9 | -11.4 [-27.3, 4.5] | 4 / 9 | 0.267 | 22.7 |
| very_very_long | 47 | 29.8 | 23.4 | 25.5 | -2.1 [-19.1, 12.8] | 7 / 8 | 1 | 12.8 |

### Hindi by whether the deleted mention has digits

| group | n | A | B | C | B-C (95% CI) | only B / only C | McNemar p | A = original |
|---|---|---|---|---|---|---|---|---|
| False | 152 | 28.9 | 30.3 | 29.6 | 0.7 [-7.2, 9.2] | 22 / 21 | 1 | 15.8 |
| True | 70 | 42.9 | 41.4 | 42.9 | -1.4 [-14.3, 11.4] | 10 / 11 | 1 | 21.4 |

### Shared tasks (recurrence, interval, day of week)

| group | n | A | B | C | B-C (95% CI) | only B / only C | McNemar p | A = original |
|---|---|---|---|---|---|---|---|---|
| hi_IN | 148 | 17.6 | 21.6 | 16.2 | 5.4 [-2.7, 12.8] | 23 / 15 | 0.256 | 20.3 |
| en_US | 9 | 0.0 | 11.1 | 11.1 | 0.0 [0.0, 0.0] | 0 / 0 | 1 | 66.7 |

Repeatability: A run twice on 234 traces gives identical text in 9.4% and the same answer in 52.6%.

(B-C) Hindi minus English on shared tasks: 5.4 pts [-2.7, 13.6]

### Re-mention of the distractor in the continuation (%)

| language | A | B | C |
|---|---|---|---|
| en_US | 16.7 | 16.7 | 16.7 |
| hi_IN | 32.4 | 31.5 | 25.2 |

### Unanswered or cut off, deleted length

| language | unanswered A/B/C | mean deleted chars B / C |
|---|---|---|
| en_US | 1/3/1 | 105 / 60 |
| hi_IN | 35/37/25 | 67 / 52 |
