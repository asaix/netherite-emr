# Data check for the final slides

Checked against raw `responses/`, the audit tables and the report as it stood at 19:13 on 2026-10-31. Run the scripts in `verify/` with `.venv/bin/python`.

## Fixed from the old deck

| Old slide | Problem | Now |
|---|---|---|
| 13 | −19.9 and −23.3 were labelled as the full study. They are the no-distractor split. Pooled, the falls are −17.6 and −21.8. | Labelled no distractor |
| 13, 14 | Chart values come from 2,250 questions, the quoted numbers from 6,750, with no label | Both labelled |
| 12, 17 | The gap is 29.1 on 6,750 questions and 29.5 on 2,250. 29.5 is also the English gain. None of this was labelled. | Sample stated |
| 19 | "Similar question" compared identical Hindi questions | Removed |
| 21 | 86.5% to 18.6% applies only to the 1,838 traces with no Hindi function words | Labelled |
| 22 | Hindi day-of-week cell was blank | 31% of 1,696 (526 late), computed from the audit data; not in the report |
| 24 | Answer-token caveat had no size | 5 / 6 on a real pair; +0.082 on 11,309 pairs |
| 26 | Title said "predicts" for an in-sample association | Reworded |
| 29 | Title said resampling helps. Removing the distractor is what helps. | Reworded |
| 8, 11, 14, 23, 25, 26, 30, 32 | Cropped figures and captions, rule through titles | Redrawn |

## Open in the report

- **OR 4.93 should be 4.92.** Refit gives 4.925, and `audit/lr/analysis.md` line 163 calls 4.93 double rounding. The slides use 4.92 and the report still says 4.93. The upper bound 6.03 has the same problem (6.025).
- **"90 sentences" in the report** are 90 task-sentence units (45 per kind). There are 78 distinct sentences: 35 time-related and 43 unrelated. The slides say units.
- **RQ5 length sentence.** The report says length differences alone do not appear to explain the link. `audit/lr/analysis.md` line 14 calls the negative length coefficient an artefact of RDS having a length floor.
- **Bootstrap intervals differ by 0.1 between runs.** Date subtraction is [16.4, 23.4] in the report and [16.3, 23.4] in `audit/baseline`. The M − P interval is [1.2, 5.4] in the report and [1.25, 5.32] in the figure data.
- **English date subtraction across a month under Hinglish** is 42.3 on 362 pairs and 42.15 on all 363. The slides use the paired 42.3, as the report does.
- **January cut-offs.** 92 traces have finish reason `length`. 91 of them have no answer line, so one cut-off trace still has one.

## Open in `docs/error-trends.pdf`

Slides 54 to 58 use this PDF, recomputed with `verify/recompute_errors.py`.

- **Day-of-week direct wrong answers:** the PDF says 3,869. The data gives 3,839 of 4,500.
- **The 5,170-word trace:** the PDF says 630 steps. The parsed trace has 636.
- **Hindi CoT answering 00:00:** the PDF says 19 times with a similar distractor and 5 with none. `audit/error_trends/verified.json` has 2 and 2. Not used.
- **130 wrong time answers discussing the distractor (105 Hindi CoT):** not found in the verify scripts. Not used.
- **Next-week categories:** the slide uses mutually exclusive ones, so shares differ from the PDF. Saturday to Friday is 34% against 25% for English direct. One day off is 18% against 23% for Hindi CoT. "This week" is 22% for English direct, matching the report; the PDF has 23%. Not 7 days matches.
- **Hindi direct dates off by 10, 20 or 30 days:** 380 of 1,246 is 30%. The PDF prints 31%.
- **Small scorer differences:** month-end and midnight counts differ by up to 7 between my scorer and the PDF. The slide's boundary chart uses mine. Whole-hour time shares use the PDF, which matches the report.

## Reproduced from raw responses

`verify/recompute.py` uses its own answer scorer and matches the report at the printed precision:

- answered and strict accuracy for all sets
- all 36 task cells on 2,250 questions
- both no-distractor Hindi falls
- CoT gap by level, 24.04 to 34.94
- time-related drops
- January sentence: 134 questions, 88.81 to 19.40 in English, 26.87 to 2.24 in Hindi

`verify/recompute_lr.py` refits the regression from `audit/lr/pairs.csv.gz`:

- 20,662 pairs, 19,471 with thinking off
- 31.38% disagree
- mean RDS 0.917 and 0.809
- outcomes 12,468, 5,967, 516 and 1,711
- OR 4.925 [4.578, 5.297], 5.584 with the length gap
- 1.678 with no answer tokens, 1.100 on op types without answers

`verify/recompute_traces.py` gives verification of 86.1, 74.2 and 1.3 on answered traces, and the 58% and 31% one-day-late shares.

`verify/check_deck.py` checks the worked RDS example with root `ed.py` (3 and 5 edits) and looks up each number on the slides in the report, audits and data. What it can't match is retry codes, a parser example date, the worked 0.50 and values its regex misreads in comma-joined CSV rows.

## Not recomputed

These are copied from audit outputs: mention rates and ORs, interventions (no GPU here), thinking-on figures, CLP stage shares, error pattern shares and the FORMAT counts.

The report was being edited during this check, so reread it before presenting. Footers cite report sections by name because page and section numbers were changing.
