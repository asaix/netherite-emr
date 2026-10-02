# Mid-report analysis: what is new, and how it was found

This folder builds the Analysis section of the mid-submission report (`report/analysis.tex`). It reuses `merged_results.json` from `experiments/1-10-26_analysis_rahul/` (3,089 questions x 12 responses = 37,068 responses) and does not call the API.

## How to rebuild

```bash
python build_responses.py   # one row per response -> outputs/data/responses.{pkl,csv}
python analysis.py          # statistics, LaTeX tables, PDF figures, macros -> outputs/
cp outputs/tables/*.tex report/tables/ && cp outputs/figures/*.pdf report/figures/
cd report && tectonic -X compile main.tex   # XeLaTeX; on Overleaf set the compiler to LuaLaTeX or XeLaTeX
```

Needs `pandas scipy statsmodels matplotlib numpy` and the TRD package in `tools/`. `metrics.py` is an unchanged copy of the root one. `temporal_answers.py` is a copy of the one in `1-10-26_analysis_rahul/`, changed only so it loads `merged_results.json` from that folder.

The report contains Devanagari, so it must be compiled with LuaLaTeX or XeLaTeX, not pdfLaTeX. `main.tex` follows ACL's official `acl_lualatex.tex` preamble (babel + Hindi, Lohit Devanagari font, falling back to Kohinoor Devanagari on macOS); copy its babel lines into the full paper. The odds-ratio analyses (distractor mentions, language drift, verification) are in `report/appendix.tex` (Appendix A), which goes after the references.

Every number in the text is a LaTeX macro from `outputs/tables/macros.tex` (232 macros), written by `analysis.py`. If the data changes, rerun the scripts and the text updates with it. `outputs/data/numbers.json` has every value with its confidence interval and more digits.

## Statistical methods (new; nothing before had significance tests)

- **Unit of resampling = question.** The 12 responses to a question are not independent, so CIs come from a cluster bootstrap: 2,000 resamples of the 3,089 questions with replacement, recomputing the statistic each time. 95% CI = 2.5th and 97.5th percentiles.
- **Direct vs CoT** uses the exact McNemar test on paired responses (same question, language and distractor), with Holm correction across the 18 task x language tests.
- **Property vs correctness** (does mentioning the distractor, drifting into English, or verifying go with correct answers?) uses Mantel–Haenszel odds ratios stratified by task x difficulty. I first tried logistic regression, but one model did not converge because some strata are separated. More importantly, the pooled comparisons are misleading twice in this data (Simpson's paradox, below).

## New findings, in detail

### 1. CoT deltas with significance (Table 1)
- English: 63.2% -> 91.1%, +27.9 points, 95% CI [+26.6, +29.3]. Significant in all 9 tasks.
- Hindi: 57.7% -> 62.9%, +5.1 points, CI [+3.8, +6.4]. Significant gain in 5 tasks, significant loss in 2:
  - date subtraction 92.2 -> 78.2 (-14.0)
  - interval date 35.1 -> 17.9 (-17.2)
- **Correction to my earlier readme note** (`1-10-26_analysis_rahul_1/readme.md`): I wrote that interval date is the only task where CoT hurts Hindi. Date subtraction also drops, by -14.0 points, and it is significant. The readme has been fixed.
- Time duration is the only task where Hindi gains more than English (+43.8 vs +40.9), because Hindi direct is very poor there (28.9%).
- Robustness: counting the 364 unscored (token-limit) responses as wrong gives CoT gains of +25.3 (English) and +4.7 (Hindi). Same conclusion.

### 2. Day of week: direct answers are pure guessing (Figure 1)
- For each direct answer I computed predicted weekday minus correct weekday (-3..+3). In both languages each of the 7 offsets gets 12.7–15.7% of answers. A uniform distribution is what you get when the answer is unrelated to the question; chance is 14.3%.
- Direct answers collapse onto one weekday: English answers "Friday" 35.4% of the time, and Hindi answers "Sunday" (ravivār) 63.4% of the time. The correct answers are spread roughly evenly over the week.
- English CoT gets 70.5% right. Its errors lean late (+1 day 17.4% vs -1 day 6.2%).
- Hindi CoT is more often exactly **one day late (25.7%) than correct (21.8%)**. This is a systematic off-by-one, not noise.

### 3. Date recurrence: a shortcut and a reversed direction
I parsed the interval N and occurrence k from each question and classified each answer relative to today:
- **First-step shortcut**: answer = today + N, ignoring k. This is 31.3% of direct answers in both languages. English CoT removes it (0.1%), but Hindi CoT keeps it in 16.6%.
- **Mirror**: answer = today - N*k, the correct distance but backwards in time. Hindi: 10.8% (direct), 11.8% (CoT). English: 1.1% and 0.5%.
- Possible cause (not tested): the Hindi template is "āj ko choṛkar, 1vīṃ āvṛtti kī tithi kyā hai?" ("excluding today, what is the date of the 1th occurrence?"). The ordinal suffix -vīṃ is non-standard for 1–4 (Hindi uses pahlī, dūsrī, ...), and "choṛkar" (leaving/excluding) may be misread. This could be a dataset (template) problem rather than a reasoning one. **Worth a small test**: rephrase the Hindi template and rerun ~50 questions once credit is back.

### 4. English–Hindi gap vs difficulty, controlled for task mix (Figure 2; required by the proposal)
`by_difficulty.csv` cannot answer this, because each level has different tasks. Holding the task set fixed:
- Date addition + date duration (the only tasks at all 4 levels): the gap grows 3.0 -> 7.1 points with direct answers and 6.6 -> 18.5 with CoT.
- Five date tasks at short/medium/very long: the CoT gap grows 27.0 -> 40.4 points, while the direct gap stays below 9.
- So the language gap is mostly a CoT gap, and it widens with more reasoning steps. At the short level, Hindi CoT (92.8%) is slightly below Hindi direct (94.0%) on the easy tasks.

### 5. CoT under distraction, with CIs (Table 2; proposal's main hypothesis)
Drop = accuracy without distractor - accuracy with it. DiD = CoT drop - direct drop.
- English similar-distractor DiD: +0.0, CI [-1.7, +1.8]. **No evidence for the hypothesis in English.**
- Hindi similar-distractor DiD: +5.2, CI [+2.9, +7.3]. Hindi dissimilar: +2.8, CI [+0.7, +4.9]. **The hypothesis holds in Hindi.** Hindi direct is unaffected (-0.7) while Hindi CoT drops 4.5.
- Hindi per task (similar distractor): date duration +10.3 [+5.3, +15.1], day of week +8.0 [+1.3, +14.2], time duration +22.1 [+8.3, +35.5]. Date recurrence is +5.8 [-0.0, +11.5], borderline. (My earlier readme note that English CoT drops more than Hindi CoT on recurrence compared raw CoT drops, which is true at 6.9 vs 4.7. The DiD view, which subtracts the direct drop, is the fairer comparison.)

### 6. Does the distractor enter the trace? (new; proposal item "check whether the model mentions the distractor")
- **Measure:** a CoT trace "mentions" the distractor if it contains a content word of the distractor that is not in the question. Function words (English and Hindi) and generic time words (day, month, time, din, mahīnā, samay, ...) are excluded. The stoplist is in `build_responses.py`.
- **Placebo:** the same test on the no-distractor trace of the same question, using the distractor that would have been inserted. This gives the rate of matches by chance.
- **Results (mention rate, with placebo in parentheses):**

  | Distractor | English | Hindi |
  |---|---|---|
  | Similar | 15.1% (10.4%) | 31.8% (8.3%) |
  | Dissimilar | 18.7% (8.5%) | 35.9% (1.4%) |

  Hindi takes the distractor into its reasoning about 3x as often, net of placebo.
- **Example** (short date_addition q5, dissimilar, correct): the Hindi trace ends "is tarah, bagīce meṃ nae phūl lagāne ke lie sahī tārīkh 2025-03-30 hai" ("Thus, the correct date for planting new flowers in the garden is 2025-03-30"). The distractor was "The garden needs new flowers." The model weaves the distractor into the story; this is the proposal's "motorcycle enters the reasoning", literally.
- **Mention vs correctness** (MH OR within task x difficulty):
  - Similar distractor: English 0.64 [0.44, 0.93], Hindi 0.77 [0.63, 0.95]. Mentioning it goes with **lower** accuracy.
  - Dissimilar distractor: English 1.33 (p=0.25), Hindi 1.11 (p=0.35). No association; the model mentions it and then ignores it.

### 7. Distractor reuse in wrong answers, with tests
Existing analysis, now with Fisher's exact test. In wrong Hindi direct answers, 12.1% (76/629) reuse a number, month or weekday from the similar distractor, against 2.6% (16/607) in the placebo (p<0.001). Hindi CoT: 4.8% vs 2.5% (p=0.04). English direct: 4.9% vs 3.9% (p=0.45). Interpretation: in Hindi direct answers the distractor changes *what* the wrong answer is, but not *how many* answers are wrong.

### 8. Hindi traces that drift into English are MORE accurate (Simpson's paradox)
- 224 Hindi CoT traces (2.4%) have target-language ratio < 0.9. Pooled, they look worse: 37.5% vs 63.5% accuracy.
- But 181 of them are day-of-week questions and 37 are recurrence questions, two of the hardest Hindi tasks. Within task they are **better**: day of week 34.3% vs 19.8%, recurrence 51.4% vs 25.3%. Stratified OR 1.94 [1.43, 2.64], p<0.001.
- This is consistent with MGSM (English intermediate steps help) and is direct motivation for the CLP condition.
- Caveat: this is observational. Drifting may be a symptom of the model "knowing" the answer, not a cause.

### 9. Verification steps don't explain the English advantage (Simpson's paradox again)
- 79.1% of English traces vs 1.5% of Hindi traces contain a verification cue.
- Pooled English accuracy: 89.5% with a verification step vs 97.4% without. This looks harmful, but verification is common in the hard tasks.
- Within task x difficulty: OR 1.33 [0.90, 1.95], p=0.13, not significant.

### 10. Trace length in words, not just tokens
The notes warned that the token comparison might mislead. Median length is 103 English vs 79 Hindi words, and 327 vs 198 completion tokens. Hindi traces are shorter in words too, though less dramatically than tokens suggest.

### 11. Cross-lingual agreement (re-derived)
Under CoT, English alone is right in 2,585 of 8,931 pairs and Hindi alone in 172. The median within-cell phi is 0.05 under CoT vs 0.31 under direct. With CoT, Hindi failures are nearly independent of which questions are hard in English.

## Things I noticed that you should fix or know

1. **Proposal says Sarvam-30B; all runs use `sarvam-105b`** (verified on all 37,068 request payloads: temperature 0, top_p 1, `reasoning_effort` null, max_tokens 4096). The report says 105B.
2. **Proposal reference for CLP has wrong pages.** It is EMNLP 2023 pp. 2695–2709, DOI 10.18653/v1/2023.emnlp-main.163, not 12332–12346. Fixed in `report/references.bib`.
3. **Sarvam blog** is now titled "Open-Sourcing Sarvam 30B and 105B" (6 March 2026), not "Introducing sarvam's sovereign models".
4. **Live API key** is hardcoded in `config/sarvam.yaml` on `main` and in every experiment copy (`experiments/*/config/sarvam.yaml`). Rotate it.
5. Proposal items **not yet done**, for the timeline section: the Hinglish condition, the CLP condition, and the RDS / edit-distance trace-structure analysis with the logistic model P(err) ~ RDS + difficulty + language.

## Verification done
- Accuracies in Tables 1–2 match `metrics.py` outputs in `1-10-26_analysis_rahul_1/outputs` (e.g. `by_language_condition_insertion.csv`, `by_language_condition_task.csv`) to every printed digit.
- Error-type count (11,537) and reuse rows (3,719) match the earlier scripts exactly.
- All references were checked against ACL Anthology, PMLR, NeurIPS proceedings, OpenReview, publisher DOI pages and JSTOR.
- Compiled PDF: A4 (595.28 x 841.89 pt), all fonts embedded (`pdffonts`), 0 overfull boxes, 0 undefined references or citations.

## Merged mid-submission report (report/main.tex)

The teammate's proposal-style draft (`report/Association_for_Computational_Linguistics__ACL__conference__2_.zip`, `acl_latex.tex`) was merged with the analysis into one paper:
Introduction, Problem Statement, Related Work, Experimental Setup, Progress So Far, Analysis, Timeline, Conclusion, Limitations, References, Appendix A (odds ratios) and Appendix B (error types).
The main text runs 8 pages; the appendix is about 0.93 of a page.

### Corrections to the teammate's text, checked against the code
- He said all answers are ISO 8601 and scored by exact string match. In fact durations are integers, intervals are "A to B", and weekdays are names scored by weekday identity (`metrics.is_correct`).
- He said the direct prompt is TRD's own template and the CoT prompt adds "Let's think step by step". In fact both use our own template in `config/prompt.yaml`, quoted in Section 4.
- He said thinking mode is off "in the direct condition". It is off in both conditions (`reasoning_effort: null` in all 37,068 request payloads).
- He presented CLP, Hinglish reasoning and RDS/step tagging as part of the setup. None is implemented yet; they are now marked as planned, including dashed boxes in Figure 1.
- He said the Sarvam documentation states the model accepts code-mixed input. The model card and blog mention native-script and romanized input only, so the claim was removed.
- He planned the "Only reason in Devanagari Hindi" instruction as future work. The CoT prompt already requires reasoning entirely in the question's language, so the sentence was removed.
- He described TRD's "five tasks". The code and our data have nine task types, which the paper groups into five core tasks; both are now stated.

### Reference fixes (all 39 entries checked against ACL Anthology, PMLR, NeurIPS, ICLR, OpenReview or arXiv)
- CLP pages: 2695–2709, not 12332–12346.
- Qi et al. 2025 title: "Controlling Thinking Language", not "Thinking Trace Language".
- Huang & Chang 2023: Findings of ACL 2023, not arXiv.
- Mirzadeh et al.: second author is Keivan Alizadeh-Vahid.
- Fatemi et al.: Seyed Mehran Kazemi.
- TRD booktitle: "System Technology", not "Systems".
- The Sarvam blog post's current title is used.
- DOIs or official URLs were added to every entry except Levenshtein (1966), for which none exists.
- Two literature claims were softened to what the sources support: Yong et al.'s "from about 3B parameters" (not in the paper's abstract), and "Mistral-7B" for mCoT (the paper says "7B model").
