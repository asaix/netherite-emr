# Hand-read judgements

Read by the auditing agent, not by a human annotator. Files: `sample_en_US.csv`, `sample_hi_IN.csv` (60 each), `mention_verification_sample.csv` (150). Row numbers refer to the CSV order.

## Answer extraction (120 responses)

Extraction was judged against the visible tail of each response. The first 260 characters kept from the end are in `tail`.

| Finding | Rows | Effect |
|---|---|---|
| Correct extraction | 112 of 120 | none |
| English response cut off at 4,096 tokens but scored, because an `Answer:` line was written mid-trace and the model kept going | en 0, 1, 2, 3 | scored correct although there is no final answer |
| Hindi direct, degenerate repeat of `Answer:` lines, cut off in the middle of a date, captured as `2019` | hi 15 | wrong either way |
| Hindi final line `उत्तर (Answer): मंगलवार` missed by both extractors because of the parenthesis | hi 22 | dropped from answered-only; wrong either way |
| My case-insensitive label matched lower-case `final answer:` mid-trace in cut-off English responses; the project extractor is right to leave these unscored | en 16, 17, 18 | my extractor's error, not counted in scoring |
| Value line disagrees with the `Answer:` line: `14:42` then `Answer: 02:42` (gold 14:42) | en 26 | scored wrong; scoring follows the prompt's final line |
| English weekday in a Hindi response after a Hindi `उत्तर:` line (`उत्तर: शनिवार` / `Answer: Saturday`) | hi 11 | handled by the weekday map; wrong either way |

Weekday names: no sampled or full-grid answer uses a Hindi synonym (`बृहस्पतिवार`, `इतवार`). Only two Hindi weekday answers are outside the seven canonical names plus English names (`<कोई परिणाम नहीं>`, `सैटर्न`).

12-hour times: of 8 + 8 sampled answers exactly 12 hours off, none used an AM/PM suffix. They are either arithmetic slips or a start time read as PM (hi 28: `01:26` treated as `13:26`). They are not a format problem.

## Distractor mention (60 per language in inserted traces, 10 per language placebo)

| Sample | Genuine reference to the distractor | False positive |
|---|---|---|
| English unrelated (15) | 6 | 9 (`need` 8, `can` 1) |
| English time-related (15) | 10 | 5 (`February` 3 as calendar months, `that`, `time`) |
| Hindi unrelated (15) | 15 | 0 |
| Hindi time-related (15) | 14 | 1 (`अगस्त` as the question's month) |

Of the 15 Hindi unrelated mentions, 10 explicitly dismiss the distractor as irrelevant, 3 restate the prompt verbatim at the start of the trace, and 2 work it into the reasoning. All 6 genuine English unrelated mentions dismiss it. The time-related Hindi mentions engage more often (9 of 14 treat it as part of the problem, for example answering whether the day will be sunny, or explaining decimal time).

Placebo hits are generic words: `need`, `can`, `when`, `actually`, month names, `उपयोग`, `सकते`, `होगा`, `हुए`, `पता`.

## Verification (15 per language)

English: 15 of 15 are real checks. Hindi: 13 of 15; the other two check a fact used in the calculation (a leap year, the length of a month), not the answer.
