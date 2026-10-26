# Trace deletion results

20 complete traces (0 incomplete). Accuracy in % on originally wrong traces.

### By language

| group | n | A | B | C | B-C (95% CI) | only B / only C | McNemar p | A = original |
|---|---|---|---|---|---|---|---|---|
| en_US | 8 | 25.0 | 75.0 | 50.0 | 25.0 [0.0, 50.0] | 2 / 0 | 0.5 | 50.0 |
| hi_IN | 12 | 58.3 | 50.0 | 41.7 | 8.3 [-33.3, 50.0] | 4 / 3 | 1 | 16.7 |

### Hindi by task

| group | n | A | B | C | B-C (95% CI) | only B / only C | McNemar p | A = original |
|---|---|---|---|---|---|---|---|---|
| date_addition | 1 | 100.0 | 100.0 | 0.0 | 100.0 [100.0, 100.0] | 1 / 0 | 1 | 0.0 |
| date_duration | 2 | 100.0 | 0.0 | 100.0 | -100.0 [-100.0, -100.0] | 0 / 2 | 0.5 | 0.0 |
| date_recurrence | 1 | 100.0 | 0.0 | 100.0 | -100.0 [-100.0, -100.0] | 0 / 1 | 1 | 0.0 |
| day_of_week | 2 | 50.0 | 50.0 | 0.0 | 50.0 [0.0, 100.0] | 1 / 0 | 1 | 0.0 |
| interval_date | 1 | 0.0 | 0.0 | 0.0 | 0.0 [0.0, 0.0] | 0 / 0 | 1 | 0.0 |
| time_addition | 2 | 0.0 | 100.0 | 0.0 | 100.0 [100.0, 100.0] | 2 / 0 | 0.5 | 50.0 |
| time_duration | 3 | 66.7 | 66.7 | 66.7 | 0.0 [0.0, 0.0] | 0 / 0 | 1 | 33.3 |

### Hindi by difficulty

| group | n | A | B | C | B-C (95% CI) | only B / only C | McNemar p | A = original |
|---|---|---|---|---|---|---|---|---|
| long | 2 | 0.0 | 100.0 | 0.0 | 100.0 [100.0, 100.0] | 2 / 0 | 0.5 | 50.0 |
| medium | 1 | 100.0 | 100.0 | 100.0 | 0.0 [0.0, 0.0] | 0 / 0 | 1 | 0.0 |
| short | 4 | 75.0 | 50.0 | 75.0 | -25.0 [-100.0, 50.0] | 1 / 2 | 1 | 0.0 |
| very_long | 4 | 75.0 | 25.0 | 25.0 | 0.0 [-75.0, 75.0] | 1 / 1 | 1 | 25.0 |
| very_very_long | 1 | 0.0 | 0.0 | 0.0 | 0.0 [0.0, 0.0] | 0 / 0 | 1 | 0.0 |

### Hindi by whether the deleted mention has digits

| group | n | A | B | C | B-C (95% CI) | only B / only C | McNemar p | A = original |
|---|---|---|---|---|---|---|---|---|
| False | 3 | 66.7 | 66.7 | 66.7 | 0.0 [-100.0, 100.0] | 1 / 1 | 1 | 0.0 |
| True | 9 | 55.6 | 44.4 | 33.3 | 11.1 [-44.4, 55.6] | 3 / 2 | 1 | 22.2 |

### Shared tasks (recurrence, interval, day of week)

| group | n | A | B | C | B-C (95% CI) | only B / only C | McNemar p | A = original |
|---|---|---|---|---|---|---|---|---|
| hi_IN | 4 | 50.0 | 25.0 | 25.0 | 0.0 [-75.0, 75.0] | 1 / 1 | 1 | 0.0 |
| en_US | 5 | 0.0 | 60.0 | 20.0 | 40.0 [0.0, 80.0] | 2 / 0 | 0.5 | 80.0 |

(B-C) Hindi minus English on shared tasks: -40.0 pts [-125.0, 55.0]

### Re-mention of the distractor in the continuation (%)

| language | A | B | C |
|---|---|---|---|
| en_US | 75.0 | 25.0 | 50.0 |
| hi_IN | 25.0 | 33.3 | 25.0 |

### Unanswered or cut off, deleted length

| language | unanswered A/B/C | mean deleted chars B / C |
|---|---|---|
| en_US | 1/1/1 | 104 / 64 |
| hi_IN | 0/0/0 | 71 / 56 |
