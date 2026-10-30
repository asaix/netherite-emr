# Distractor resampling results

Rounds used: 7 (complete rounds only). Each trace has one sample per arm per round. Accuracy in %, averaged per trace over rounds, then over traces.

Primary contrasts (fixed before the run): Q - P, M - P and (M - P) - (P - P1), for Hindi and for English. Everything else is exploratory.

## Accuracy by arm

| group | traces | Q (no distractor) | P (before mention) | M (after mention) | P1 (one sentence earlier) |
|---|---|---|---|---|---|
| hi_IN | 526 | 45.2 | 40.0 | 36.7 | 28.6 |
| en_US | 37 | 48.3 | 31.3 | 17.0 | 27.6 |
| hi_IN, mention in opening sentence | 278 | 56.0 | 50.7 | 49.1 | – |
| hi_IN, mention later | 248 | 33.1 | 27.9 | 22.7 | 28.6 |
| en_US, mention in opening sentence | 22 | 61.7 | 37.0 | 16.2 | – |
| en_US, mention later | 15 | 28.6 | 22.9 | 18.1 | 27.6 |
| hi_IN, in trace-deletion set (234) | 222 | 43.6 | 36.0 | 35.1 | 27.1 |
| hi_IN, task date_addition (exploratory) | 15 | 83.8 | 86.7 | 76.2 | 80.0 |
| hi_IN, task date_duration (exploratory) | 42 | 83.3 | 77.9 | 78.6 | 14.3 |
| hi_IN, task date_recurrence (exploratory) | 135 | 32.3 | 19.3 | 14.6 | 22.1 |
| hi_IN, task date_subtraction (exploratory) | 31 | 36.4 | 34.1 | 34.6 | 35.7 |
| hi_IN, task day_of_week (exploratory) | 93 | 19.7 | 23.3 | 19.7 | 19.7 |
| hi_IN, task interval_date (exploratory) | 65 | 29.0 | 20.2 | 20.9 | 10.5 |
| hi_IN, task time_addition (exploratory) | 43 | 78.1 | 68.4 | 60.1 | 63.4 |
| hi_IN, task time_duration (exploratory) | 65 | 66.2 | 65.7 | 61.5 | 66.3 |
| hi_IN, task time_subtraction (exploratory) | 37 | 58.7 | 56.4 | 54.8 | 42.9 |
| hi_IN, difficulty long (exploratory) | 97 | 47.0 | 42.6 | 39.2 | 35.7 |
| hi_IN, difficulty medium (exploratory) | 97 | 48.5 | 44.0 | 39.8 | 39.8 |
| hi_IN, difficulty short (exploratory) | 105 | 54.1 | 44.4 | 38.2 | 26.5 |
| hi_IN, difficulty very_long (exploratory) | 105 | 43.4 | 37.7 | 36.2 | 23.8 |
| hi_IN, difficulty very_very_long (exploratory) | 122 | 35.1 | 32.8 | 31.3 | 20.6 |

## Contrasts (percentage points, paired by trace, bootstrap 95% CI, sign-flip permutation p)

| group | Q - P: distractor in the question | M - P: the written mention | P - P1: an ordinary sentence (baseline) | (M - P) - (P - P1): mention beyond an ordinary sentence |
|---|---|---|---|---|
| hi_IN | +5.3 [+3.2, +7.4], p=5e-05 (n=526) | -3.3 [-5.4, -1.2], p=0.0019 (n=526) | -0.7 [-3.5, +2.1], p=0.662 (n=248) | -4.6 [-9.6, +0.6], p=0.0918 (n=248) |
| en_US | +17.0 [+8.9, +25.5], p=0.0003 (n=37) | -14.3 [-25.1, -4.2], p=0.0167 (n=37) | -4.8 [-13.3, +3.8], p=0.43 (n=15) | +0.0 [-22.9, +23.8], p=1 (n=15) |
| hi_IN, mention in opening sentence | +5.3 [+2.4, +8.2], p=0.00025 (n=278) | -1.5 [-4.2, +1.2], p=0.288 (n=278) | – | – |
| hi_IN, mention later | +5.2 [+2.4, +8.1], p=0.00065 (n=248) | -5.2 [-8.3, -2.2], p=0.0011 (n=248) | -0.7 [-3.5, +2.2], p=0.663 (n=248) | -4.6 [-9.6, +0.5], p=0.0882 (n=248) |
| en_US, mention in opening sentence | +24.7 [+14.3, +35.1], p=0.0004 (n=22) | -20.8 [-33.8, -7.8], p=0.00565 (n=22) | – | – |
| en_US, mention later | +5.7 [-2.9, +16.2], p=0.361 (n=15) | -4.8 [-22.9, +11.4], p=0.717 (n=15) | -4.8 [-13.3, +2.9], p=0.43 (n=15) | +0.0 [-21.9, +21.9], p=1 (n=15) |
| hi_IN, in trace-deletion set (234) | +7.6 [+4.6, +10.6], p=5e-05 (n=222) | -1.0 [-3.9, +1.9], p=0.537 (n=222) | -0.8 [-4.2, +2.8], p=0.709 (n=128) | -1.8 [-8.5, +5.0], p=0.616 (n=128) |
| hi_IN, task date_addition (exploratory) | -2.9 [-12.4, +5.7], p=0.753 (n=15) | -10.5 [-17.1, -4.7], p=0.0154 (n=15) | +8.6 [-5.7, +20.0], p=0.5 (n=5) | -28.6 [-40.0, -17.1], p=0.0658 (n=5) |
| hi_IN, task date_duration (exploratory) | +5.4 [-0.3, +11.6], p=0.106 (n=42) | +0.7 [-5.1, +6.8], p=0.912 (n=42) | – | – |
| hi_IN, task date_recurrence (exploratory) | +13.0 [+9.0, +17.2], p=5e-05 (n=135) | -4.7 [-7.9, -1.5], p=0.0081 (n=135) | -2.8 [-6.6, +0.9], p=0.166 (n=111) | -2.1 [-8.2, +4.0], p=0.54 (n=111) |
| hi_IN, task date_subtraction (exploratory) | +2.3 [-5.5, +10.1], p=0.654 (n=31) | +0.5 [-9.7, +11.1], p=1 (n=31) | +0.0 [-12.2, +13.3], p=1 (n=14) | -2.0 [-26.5, +23.5], p=0.946 (n=14) |
| hi_IN, task day_of_week (exploratory) | -3.7 [-8.3, +0.9], p=0.134 (n=93) | -3.7 [-8.6, +1.1], p=0.158 (n=93) | +4.5 [-1.4, +10.9], p=0.188 (n=63) | -11.6 [-23.4, -1.1], p=0.051 (n=63) |
| hi_IN, task interval_date (exploratory) | +8.8 [+3.3, +14.5], p=0.0047 (n=65) | +0.7 [-4.0, +5.5], p=0.856 (n=65) | -1.0 [-9.5, +7.6], p=1 (n=15) | +0.0 [-18.1, +21.9], p=1 (n=15) |
| hi_IN, task time_addition (exploratory) | +9.6 [+0.3, +17.9], p=0.0391 (n=43) | -8.3 [-16.9, +1.0], p=0.099 (n=43) | -8.0 [-19.6, +2.7], p=0.267 (n=16) | +8.9 [-15.2, +35.7], p=0.559 (n=16) |
| hi_IN, task time_duration (exploratory) | +0.4 [-5.1, +5.9], p=0.935 (n=65) | -4.2 [-11.0, +2.4], p=0.259 (n=65) | +1.0 [-13.3, +17.3], p=1 (n=14) | -7.1 [-37.8, +19.4], p=0.702 (n=14) |
| hi_IN, task time_subtraction (exploratory) | +2.3 [-5.8, +10.0], p=0.639 (n=37) | -1.5 [-12.0, +8.9], p=0.831 (n=37) | -4.8 [-14.3, +4.8], p=0.56 (n=9) | -6.3 [-38.1, +25.4], p=0.797 (n=9) |
| hi_IN, difficulty long (exploratory) | +4.4 [-0.3, +9.0], p=0.0802 (n=97) | -3.4 [-8.5, +1.5], p=0.21 (n=97) | -2.6 [-8.9, +3.7], p=0.48 (n=50) | -3.4 [-14.6, +7.7], p=0.573 (n=50) |
| hi_IN, difficulty medium (exploratory) | +4.4 [-0.3, +9.1], p=0.079 (n=97) | -4.3 [-8.2, -0.3], p=0.0522 (n=97) | -4.8 [-11.6, +2.4], p=0.22 (n=42) | -0.0 [-11.2, +11.2], p=1 (n=42) |
| hi_IN, difficulty short (exploratory) | +9.8 [+4.1, +15.2], p=0.0009 (n=105) | -6.1 [-11.0, -1.2], p=0.0192 (n=105) | +1.8 [-4.8, +8.6], p=0.668 (n=48) | -11.9 [-24.4, +0.0], p=0.0797 (n=48) |
| hi_IN, difficulty very_long (exploratory) | +5.7 [+1.6, +9.8], p=0.00825 (n=105) | -1.5 [-6.3, +3.3], p=0.582 (n=105) | -0.3 [-7.0, +6.3], p=1 (n=45) | -3.8 [-16.2, +8.9], p=0.603 (n=45) |
| hi_IN, difficulty very_very_long (exploratory) | +2.3 [-1.8, +6.1], p=0.267 (n=122) | -1.5 [-5.6, +2.5], p=0.498 (n=122) | +1.4 [-3.9, +6.8], p=0.696 (n=63) | -3.4 [-14.1, +7.0], p=0.562 (n=63) |

## Distractor mentioned in the continuation (% of rollouts)

Q's question has no distractor, so Q's rate is the detector's false-positive rate.

| group | Q | P | M | P1 | P, answered rollouts: accuracy when mentioning / not (n) | P, answered: within-trace difference |
|---|---|---|---|---|---|---|
| hi_IN | 1.2 | 57.8 | 38.2 | 61.2 | 41.1 (1829) / 48.4 (1485) | -2.3 [-6.1, +1.6] (n=317) |
| en_US | 4.6 | 56.8 | 63.3 | 4.8 | 53.1 (81) / 36.9 (103) | -27.8 [-48.6, -7.1] (n=13) |
| hi_IN, mention in opening sentence | 0.9 | 62.4 | 32.3 | – | 50.2 (1102) / 61.1 (709) | +2.2 [-3.1, +7.3] (n=175) |
| hi_IN, mention later | 1.6 | 52.6 | 44.9 | 61.2 | 27.4 (727) / 36.9 (776) | -7.7 [-13.3, -2.0] (n=142) |
| en_US, mention in opening sentence | 4.5 | 87.7 | 94.8 | – | 55.6 (72) / 89.5 (19) | -27.9 [-63.6, +7.1] (n=7) |
| en_US, mention later | 4.8 | 11.4 | 17.1 | 4.8 | 33.3 (9) / 25.0 (84) | -27.8 [-47.2, -8.3] (n=6) |
| hi_IN, in trace-deletion set (234) | 0.7 | 57.4 | 33.8 | 63.4 | 32.4 (772) / 48.6 (638) | -8.7 [-14.0, -3.4] (n=138) |
| hi_IN, task date_addition (exploratory) | 0.0 | 21.9 | 21.0 | 28.6 | 91.3 (23) / 85.4 (82) | +3.6 [-15.8, +19.4] (n=12) |
| hi_IN, task date_duration (exploratory) | 0.0 | 29.3 | 2.4 | 0.0 | 74.1 (85) / 80.2 (207) | -7.3 [-18.9, +4.4] (n=35) |
| hi_IN, task date_recurrence (exploratory) | 0.2 | 62.3 | 54.5 | 70.4 | 20.8 (461) / 25.3 (340) | -8.1 [-15.4, -0.7] (n=82) |
| hi_IN, task date_subtraction (exploratory) | 0.5 | 19.4 | 17.1 | 10.2 | 45.0 (40) / 34.4 (163) | +3.1 [-11.6, +18.1] (n=18) |
| hi_IN, task day_of_week (exploratory) | 3.8 | 56.5 | 37.3 | 66.4 | 22.1 (290) / 35.5 (248) | -8.1 [-17.8, +1.4] (n=61) |
| hi_IN, task interval_date (exploratory) | 0.0 | 76.5 | 4.2 | 58.1 | 22.6 (340) / 14.3 (105) | +2.4 [-7.6, +13.3] (n=29) |
| hi_IN, task time_addition (exploratory) | 0.3 | 71.1 | 56.5 | 72.3 | 75.7 (185) / 75.9 (87) | -0.6 [-14.3, +13.7] (n=23) |
| hi_IN, task time_duration (exploratory) | 1.8 | 57.1 | 56.3 | 27.6 | 67.5 (246) / 69.3 (192) | +14.3 [+4.4, +24.2] (n=41) |
| hi_IN, task time_subtraction (exploratory) | 3.1 | 76.4 | 53.7 | 54.0 | 67.3 (159) / 63.9 (61) | -2.6 [-23.4, +19.8] (n=16) |
| hi_IN, difficulty long (exploratory) | 1.2 | 54.1 | 41.5 | 58.3 | 40.1 (334) / 51.8 (299) | -11.9 [-21.4, -2.3] (n=60) |
| hi_IN, difficulty medium (exploratory) | 1.5 | 64.2 | 35.9 | 66.0 | 44.7 (389) / 53.2 (235) | +2.1 [-7.4, +11.5] (n=55) |
| hi_IN, difficulty short (exploratory) | 1.5 | 63.0 | 36.6 | 69.0 | 47.5 (413) / 49.4 (263) | -0.7 [-8.7, +7.1] (n=68) |
| hi_IN, difficulty very_long (exploratory) | 0.7 | 55.2 | 38.6 | 58.7 | 37.3 (332) / 48.9 (313) | -2.3 [-11.3, +6.6] (n=66) |
| hi_IN, difficulty very_very_long (exploratory) | 1.3 | 53.4 | 38.5 | 56.2 | 34.3 (361) / 41.6 (375) | +1.2 [-6.3, +8.3] (n=68) |

## Unanswered or cut off (% of rollouts) and noise in P

| group | Q | P | M | P1 | P traces always right / always wrong / mixed |
|---|---|---|---|---|---|
| hi_IN | 5.7 | 10.0 | 10.8 | 13.8 | 40 / 114 / 372 |
| en_US | 15.4 | 29.0 | 41.3 | 9.5 | 3 / 11 / 23 |
| hi_IN, mention in opening sentence | 3.5 | 6.9 | 8.1 | – | 29 / 37 / 212 |
| hi_IN, mention later | 8.1 | 13.4 | 13.7 | 13.8 | 11 / 77 / 160 |
| en_US, mention in opening sentence | 14.9 | 40.9 | 63.0 | – | 2 / 7 / 13 |
| en_US, mention later | 16.2 | 11.4 | 9.5 | 9.5 | 1 / 4 / 10 |
| hi_IN, in trace-deletion set (234) | 5.1 | 9.3 | 10.1 | 14.6 | 14 / 59 / 149 |
| hi_IN, task date_addition (exploratory) | 1.9 | 0.0 | 1.9 | 0.0 | 5 / 0 / 10 |
| hi_IN, task date_duration (exploratory) | 1.0 | 0.7 | 0.3 | 0.0 | 9 / 1 / 32 |
| hi_IN, task date_recurrence (exploratory) | 4.6 | 15.2 | 17.1 | 17.8 | 1 / 54 / 80 |
| hi_IN, task date_subtraction (exploratory) | 4.6 | 6.5 | 9.2 | 7.1 | 1 / 6 / 24 |
| hi_IN, task day_of_week (exploratory) | 17.7 | 17.4 | 16.6 | 16.1 | 1 / 20 / 72 |
| hi_IN, task interval_date (exploratory) | 2.4 | 2.2 | 1.8 | 4.8 | 0 / 25 / 40 |
| hi_IN, task time_addition (exploratory) | 0.3 | 9.6 | 8.3 | 7.1 | 8 / 1 / 34 |
| hi_IN, task time_duration (exploratory) | 3.5 | 3.7 | 7.0 | 6.1 | 12 / 4 / 49 |
| hi_IN, task time_subtraction (exploratory) | 3.1 | 15.1 | 14.7 | 6.3 | 3 / 3 / 31 |
| hi_IN, difficulty long (exploratory) | 5.0 | 6.8 | 10.0 | 8.9 | 9 / 15 / 73 |
| hi_IN, difficulty medium (exploratory) | 5.3 | 8.1 | 8.4 | 12.2 | 9 / 13 / 75 |
| hi_IN, difficulty short (exploratory) | 3.7 | 8.0 | 10.1 | 14.9 | 12 / 18 / 75 |
| hi_IN, difficulty very_long (exploratory) | 6.4 | 12.2 | 11.2 | 15.6 | 6 / 29 / 70 |
| hi_IN, difficulty very_very_long (exploratory) | 7.6 | 13.8 | 13.5 | 16.6 | 4 / 39 / 79 |

## Rounds

| round | results | complete |
|---|---|---|
| round_01 | 1952 | True |
| round_02 | 1952 | True |
| round_03 | 1952 | True |
| round_04 | 1952 | True |
| round_05 | 1952 | True |
| round_06 | 1952 | True |
| round_07 | 1952 | True |
