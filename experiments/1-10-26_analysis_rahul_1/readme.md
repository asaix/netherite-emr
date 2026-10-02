all the analysis in this folder is using metrics.py only. 


by_task.csv : 364 dicarded because they were cut off at max_tokens. day of the week is the worst performing task.

cot_ratio_avg computes the ratio per individual response first, then averages those ratios across all responses in the group. Each response counts equally, whether its CoT was 10 words or 500 words.
cot_ratio_pooled instead adds up all target-language words across every response in the group, and all total words across every response, then divides those two totals. This means longer responses have more influence on the result than short ones.

if they're close, response length doesn't matter much. If they diverge a lot, it tells you something like "a few very long responses are dragging the pooled number down/up" — a flag that the average alone might be misleading.

by_language.csv: 
english averaged across every difficulty, every task gets overall accuracy of 0.769, hindi gets 0.603. 
even for hindi the over all target language cot ratio is approx 1. Hence when asked to reason in hindi the model barely deviates.


by_condition.csv:
Cot of average increaes accuracy. Cot - 0.768 vs direct 0.605.


by_insertions.csv:
Overall insertions dont seem to be affecting the model output by much. 

insertion            | responses | scored | accuracy | cot_ratio_avg | cot_ratio_pooled
---------------------+-----------+--------+----------+---------------+-----------------
dissimilar_insertion |     12356 |  12265 |    0.684 |         0.996 |            0.996
no_insertion         |     12356 |  12235 |    0.694 |         0.994 |            0.991
similar_insertion    |     12356 |  12204 |    0.679 |         0.996 |            0.996

by_difficulty.csv:
not concrete as not all tasks have been completely run yet. skipping for now. 

overall.csv:
overall model accuracy across all, difficulties, languages, tasks is 0.686.

by_language_condition.csv:
Cot helps english massively, while helping hindi minimilly.  
accuracy of eng goes up by 0.911 - 0.632 
while accurace of hindi only goes up by 0.629 - 0.577 


by_task_condition.csv: 

without CoT model is just randomly guessing in the following tasks, 

condition | task             | responses | scored | accuracy | cot_ratio_avg | cot_ratio_pooled
----------+------------------+-----------+--------+----------+---------------+-----------------
direct    | date_recurrence  |      2700 |   2684 |    0.146 |             - |                -
direct    | day_of_week      |      2670 |   2670 |    0.149 |             - |                -


by_language_condition_insertion.csv:

"CoT makes distraction worse in general this claim is wrong." 

CoT makes distraction worse specifically in Hindi, not in English.

In english CoT is not more distractor sensitive, as the drop in accuracy by insertions of distractor is same in case of of both the condtions CoT and direct.


by_language_condition_task.csv:

interval_date and date_subtraction are the two tasks where CoT actively hurts accuracy in hindi, not just helps less.

task             | language | direct | cot   | cot delta
-----------------+----------+--------+-------+----------
interval_date    | en_US    | 0.298  | 0.431 |    +0.133
interval_date    | hi_IN    | 0.351  | 0.179 |    -0.172
date_subtraction | en_US    | 0.936  | 0.959 |    +0.023
date_subtraction | hi_IN    | 0.922  | 0.782 |    -0.140

both drops are significant (McNemar, Holm-corrected, see experiments/2026-10-02_mid-report-analysis). date_addition in hindi is also slightly negative (-0.012) but not significant. not caused by distractors, this is pooled across all insertions, so cot is just worse than direct here on its own for hindi. english cot is never worse than direct in any task.

also confirms the by_task_condition note above isn't the whole story: day_of_week and date_recurrence direct accuracy near chance in BOTH languages (day_of_week: en 0.141, hi 0.157; date_recurrence hi 0.048), but cot only rescues english (day_of_week cot: en 0.705, hi 0.218; date_recurrence cot: en 0.924, hi 0.260). so "cot fixes it" is mostly an english phenomenon.


by_difficulty_language_condition.csv:

required for the proposal (en-hi gap across difficulty levels), but same caveat as by_difficulty.csv: task mix is different per difficulty (long only has date_addition/date_duration, the easy tasks), so don't read accuracy going up with difficulty as a real trend.

what's still useful from it: the hindi cot drop vs direct (small gain) holds at every difficulty, it's not just one difficulty level driving the english/hindi cot asymmetry seen in by_language_condition.csv.

difficulty | lang  | direct | cot   | delta
-----------+-------+--------+-------+------
short      | en_US | 0.709  | 0.942 | +0.233
short      | hi_IN | 0.623  | 0.672 | +0.049
medium     | en_US | 0.624  | 0.935 | +0.310
medium     | hi_IN | 0.606  | 0.669 | +0.064
long       | en_US | 0.923  | 0.992 | +0.069
long       | hi_IN | 0.888  | 0.896 | +0.008
very_long  | en_US | 0.528  | 0.861 | +0.333
very_long  | hi_IN | 0.468  | 0.522 | +0.054


below: generated every remaining combination metrics.py can do (32 total, all of them now exist in outputs/). most are just here for completeness / for slicing later, only noting the ones that actually showed something.

by_difficulty_condition.csv:
cot delta pooled over both languages is ~0.14-0.19 at short/medium/very_long, but only +0.038 at long. not because cot "works less" there, long only has date_addition/date_duration (the easy tasks) so direct is already at 0.905, ceiling effect. explains why long looked like the outlier in the earlier difficulty table.

by_difficulty_insertion.csv:
distractor drop is small (~1-2 points) at every difficulty level, not just overall. so it's not that distractors matter more for harder questions, the effect (or lack of it) is flat across difficulty.

by_language_insertion.csv:
pooling direct+cot together, distractor effect looks small in both languages (en 0.766-0.775, hi 0.594-0.613). this hides the real story, you only see hindi-cot being distractor sensitive once you also split by condition (see by_language_condition_insertion.csv above). pooled-condition view is misleading here.

by_language_task.csv:
biggest en-hi accuracy gap (condition pooled) is date_recurrence: en 0.578 vs hi 0.154, a 42 point gap. bigger than day_of_week's 21 point gap (en 0.401 vs hi 0.187), even though day_of_week has the lower absolute numbers. date_recurrence is where the model's hindi reasoning falls apart the most.

by_insertion_task.csv:
date_recurrence is the task most knocked around by a distractor: no_insertion 0.383 -> similar 0.345 (-0.038), biggest relative drop of any task. day_of_week and date_duration barely move with any insertion type.

by_difficulty_task.csv:
this actually fixes the "don't trust by_difficulty.csv" caveat. holding the task fixed, accuracy declines monotonically with difficulty exactly like you'd expect: date_addition 0.98 -> 0.96 -> 0.93 -> 0.83, date_duration 0.94 -> 0.92 -> 0.92 -> 0.83, date_recurrence 0.45 -> 0.40 -> (not run) -> 0.24. so TRD's difficulty labels are doing their job, the earlier confusing by_difficulty.csv numbers were purely a task-mix artifact, not a problem with the difficulty levels themselves.

by_language_condition_insertion_task.csv:
exception to the "hindi cot is more distractor sensitive" rule from by_language_condition_insertion.csv: for date_recurrence specifically, english cot drops MORE on the similar distractor (0.955 -> 0.886, -0.069) than hindi cot does (0.294 -> 0.247, -0.047). so that rule is a general pattern, not universal, at least one task flips it.

by_difficulty_language_insertion.csv, by_difficulty_condition_insertion.csv, by_difficulty_insertion_task.csv, by_condition_insertion_task.csv, by_difficulty_language_task.csv, by_difficulty_condition_task.csv, by_language_insertion_task.csv:
generated, didn't find anything beyond what's already said above once you slice by one more field, mostly because the distractor effect is small everywhere to begin with. kept for reference / in case something needs to be double checked at that granularity.

by_difficulty_language_condition_insertion.csv, by_difficulty_language_condition_task.csv, by_difficulty_language_insertion_task.csv, by_difficulty_condition_insertion_task.csv, by_language_condition_insertion_task.csv, by_difficulty_language_condition_insertion_task.csv:
full breakdowns, cells get small (some combinations have well under 100 responses), too fine grained to eyeball row by row. generated and left for whenever a specific cell needs checking, not reading through all of these for patterns.


