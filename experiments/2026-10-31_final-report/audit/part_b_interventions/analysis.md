# Part B audit: distractor mentions and trace interventions

Saved by the main session from the audit agent's hand-back, because the harness refused the agent's own write of this file. Content is the agent's, unchanged.

Conventions: **strict** counts unanswered and cut-off outputs as wrong; **answered-only** drops them. Part B's arm tables and primary contrasts are strict. All Experiment 1 and 2 data are `similar_insertion` only, with Q the matching `no_insertion` question. No trace was resampled under `dissimilar_insertion`, so the split by distractor condition exists only for the API population (section 14).

Reused code: `verify.py` imports root `metrics.py` for scoring and reads the mid-report stoplist from `experiments/2026-10-02_mid-report-analysis/build_responses.py`. The tokeniser, sentence regex and mention rule are reimplemented from their written specification (the sentence regex is the same pattern). Statistics and loop detection are new.

## Verdict

| headline claim | verdict |
|---|---|
| Funnel, Tables B1 to B4, Figure B1 | **Hold.** The same 563 trace ids come back from the independent rule. `responses/standard` now has 6,750 Hindi responses, not 6,747 (3 more right; eligibility unaffected). |
| "Pre-registered", "fixed before the run" | **Remove "pre-registered". Unverifiable for Experiment 2.** Experiment 1's plan is verifiably earlier. |
| "One error in eleven", "one in four" | **Arithmetic holds; "fixes" and "due to" do not.** Excess fraction: Hindi 8.8% [5.5, 12.1], English 24.7% [13.6, 35.9]. |
| "Experiment 1's null was real" | **Overclaim.** 24% power for 5 points. |
| "Mainly through the question" | **Not identified; data lean the other way.** |
| "Only in the middle of the reasoning" | **Overclaim.** Later minus opening -3.7 [-7.8, +0.3]; largest at the second sentence. |
| "Part of the harm is not finishing" | **True of these rollouts only.** API Hindi 0.81% to 0.89%; the API rise is in English. |
| "Six primary tests, Bonferroni 0.0083" | **Count holds.** Correction is post hoc; under Holm, English M-P passes narrowly. |
| Self-hosted "matched" the API | **Overclaim.** Hindi -2.2 [-17.8, +15.6]; English FP8 24.7 points below the API on 22 questions. |
| Finding 5 | "Hindi writes it more" holds descriptively. "English is hurt more" is not defensible. |

## Data existence

| cited item | exists | records |
|---|---|---|
| `responses/standard/*.json` | yes | 81,000; 40,500 CoT |
| `selfhost_G`, `selfhost_S` `results.json` / `results_repeat.json` | yes | 702 / 234 each |
| `outputs/selfhost/calibration_*` | yes | 90 rows each |
| `resample/round_01..07/results.json` | yes | 1,952 each, 13,664 total, unique ids, seed = round |
| `resample/analysis.json` | yes | matches the PDF's tables |
| `sensitivity.py/.json`, `noise_and_loops.py/.json` | **no** | recomputed; all match (loop rule recovered, section 8) |
| "script that built this document" | **no** | unverifiable |
| `outputs/logs` (both experiments) | **no** | only summarised in `gpu/NOTES.md` |
| `outputs/diag/continuation_diag.json` | **no** | only PLAN.md text and `diag.py` remain |

Timeline (UTC): PLAN.md, `analyze.py`, `build_requests.py` committed 10-26 22:03 (1eb5b2a). Experiment 1 G 10-27 22:20 to 22:57, S 23:00 to 23:23. Experiment 1 committed 10-29 12:40. Experiment 2 rounds 10-29 14:16 to 17:11. Experiment 2 first commit ee32fd1 authored 10-30 17:43 (visible via `gh pr view 12`). Merge 63c7c6e 10-30 19:55. Working-tree mtimes are checkout times and say nothing.

## Corrected results

### 1. Were contrasts fixed before the run?

**Experiment 1: yes for the contrast.** PLAN.md's B vs C with exact McNemar is in 1eb5b2a, about 24 h before the final run, and `analyze.py` and `build_requests.py` at HEAD are identical to that commit. PLAN.md openly logs changes after earlier data existed: mention rule tightened after the pilot, token limit raised to 12,288, a failed gate overridden by user decision and made information-only, sampling added after greedy's problems.

**Experiment 2: unverifiable.** README, results and analysis first appear in one commit about 24.5 h after the last round. Internal evidence supports the claim (future-tense limitations, NOTES.md's pre-boot mock run of `analyze_resample.py`, MD5-matched requests), but no timestamp predates results. The design also followed Experiment 1 on 234 of the same traces. Not in the README's primary list: Bonferroni, answered-only, loop analysis, the 222-trace comparison, the "computation" reading.

**Wording:** "We specified the design and primary contrasts in an internal design document before the run, according to our run notes. It was first committed after the run, so version control cannot confirm this, and the study was not publicly registered. The design followed Experiment 1, which used 234 of the same traces."

### 2. Experiment 1

| run | language | n | A | B | C | B - C | only B / only C | p |
|---|---|---|---|---|---|---|---|---|
| G | Hindi | 222 | 33.3 | 33.8 | 33.8 | +0.0 [-6.8, +7.2] | 32 / 32 | 1.00 |
| S | Hindi | 222 | 29.3 | 32.9 | 28.4 | +4.5 [-2.7, +11.7] | 37 / 27 | 0.26 |
| G | English | 12 | 25.0 | 16.7 | 25.0 | -8.3 | 0 / 1 | 1.00 |
| S | English | 12 | 25.0 | 33.3 | 25.0 | +8.3 | 1 / 0 | 1.00 |

Drop the English intervals (one discordant pair). Table B1 uses 2,000 resamples, Table B4 5,000.

Method text corrections:
- "Cut before its answer sentence" misleads: the prefix stops at max(k, j), a median 8 sentences before the answer; only 13 of 234 stop right before it.
- B removes exactly one sentence in all 234.
- In 119 of 234 traces (115 Hindi) **A and M are the same string, and B and P are the same string**. In the other 107 Hindi traces (94 opening) B keeps text after the deleted sentence, so deleting and forcing are different there. The brief's "only addresses forcing, not deleting" is therefore right for those 107 but not for the 115.

Power (64 of 222 discordant, SE 3.6, exact McNemar, 4,000 simulations): 2 pts 7%, 3.3 pts 13%, 5 pts 24%, 7.5 pts 50%, 10 pts 78%, 15 pts 99%. MDE at 80% is about 10 points. The intervals rule out a benefit above about +7 (G) or +12 (S). Averaging G and S per trace: +2.3 [-3.2, +7.4].

Subset test: on the 115, M-P -1.6 [-6.1, +2.7]; Experiment 1 A-B -3.5 [-13.9, +7.0] (S), -5.2 [-13.9, +2.6] (G). Nothing in Experiment 2 corresponds to C. The 222 are unrepresentative: M-P -1.0 vs -5.0 in the other 304, difference +4.0 [+0.1, +8.1].

**Wording:** "Experiment 1 found no detectable benefit of deleting the mention (Hindi B - C +0.0 [-6.8, +7.2] greedy, +4.5 [-2.7, +11.7] sampling). With single continuations it had about 24% power for a 5-point effect, so it cannot distinguish no effect from the 3 to 5 point effects in Experiment 2. On the 115 Hindi traces where the deletion and forcing prefixes are identical, seven-run resampling also finds no clear difference (-1.6 [-6.1, +2.7])."

Flips (38, 53) and re-mention (35.1%, 34.7%) reproduce. "Wrote it back" needs care: the distractor stays in the question, and C, which kept the mention, re-mentions at 31.5%. Whole-text and sentence rules give identical rates here.

### 3. Arm accuracy and non-completion

| group | n | strict Q/P/M | answered Q/P/M | unanswered Q/P/M |
|---|---|---|---|---|
| Hindi, all | 526 | 45.2 / 40.0 / 36.7 | 47.9 / 44.4 / 41.1 | 5.7 / 10.0 / 10.8 |
| Hindi, opening | 278 | 56.0 / 50.7 / 49.1 | 58.0 / 54.4 / 53.5 | 3.5 / 6.9 / 8.1 |
| Hindi, later | 248 | 33.1 / 27.9 / 22.7 | 36.1 / 32.3 / 26.3 | 8.1 / 13.4 / 13.7 |
| English, all | 37 | 48.3 / 31.3 / 17.0 | 57.1 / 44.0 / 28.9 | 15.4 / 29.0 / 41.3 |
| English, opening | 22 | 61.7 / 37.0 / 16.2 | 72.5 / 62.6 / 43.9 | 14.9 / 40.9 / 63.0 |
| English, later | 15 | 28.6 / 22.9 / 18.1 | 34.1 / 25.8 / 20.0 | 16.2 / 11.4 / 9.5 |

### 4. Contrasts (independent bootstrap; differences from the PDF are Monte Carlo error)

| group | strict Q-P | answered Q-P | strict M-P | answered M-P | unanswered P-Q | unanswered M-P |
|---|---|---|---|---|---|---|
| Hindi, all | +5.3 [+3.2, +7.4] | +3.6 [+1.5, +5.7] | -3.3 [-5.3, -1.2] | -3.2 [-5.5, -0.9] | +4.3 [+3.0, +5.6] | +0.8 [-0.7, +2.1] |
| Hindi, opening | +5.3 [+2.5, +8.2] | +3.4 [+0.4, +6.3] | -1.5 [-4.3, +1.2] | -0.9 [-3.9, +1.9] | +3.4 [+2.1, +4.9] | +1.2 [-0.4, +2.8] |
| Hindi, later | +5.2 [+2.3, +8.0] | +3.8 [+0.7, +7.0] | -5.2 [-8.3, -2.2] | -5.7 [-9.2, -2.1] | +5.3 [+3.0, +7.7] | +0.3 [-2.1, +2.6] |
| English, all | +17.0 [+9.3, +25.1] | +13.4 [+3.8, +24.3] | -14.3 [-25.1, -3.9] | -16.4 [-31.6, -1.8] (n=33) | +13.5 [+5.4, +22.0] | +12.4 [+3.5, +21.2] |

Cluster bootstrap over distractor sentences: Hindi Q-P [-0.3, +9.4], M-P [-5.4, -1.3]; English Q-P [-2.9, +22.7], M-P [-25.2, +3.2].

"All conclusions hold" is too strong: answered English Q-P (p = 0.017) fails Bonferroni, and answered Q-P in the 304 Hindi traces outside the deletion set is +1.3 [-1.5, +4.2].

### 5. What Q-P identifies

For a selected wrong API trace with first mention k and pre-k text S, Q-P estimates E[Y(no distractor, S) - Y(distractor, S) | selected], where Y is a new FP8 continuation at temperature 0.8. It is the question's effect on everything generated **from k onward**, with S held at what was written under the distractor. So it is not the total effect for k > 0. For k = 0 (278 Hindi) it is the total effect on a fresh FP8 response, on questions where one API sample was wrong and mentioned the distractor. It always **includes** the path through mentions written in the continuation.

Regression to the mean:
1. *The test is safe.* Under a sharp null, Q and P are draws from one law given S, and selection used an earlier sample, so selection alone cannot produce a difference.
2. *The size is conditional.* Selecting on "wrong under the distractor" over-represents traces it hurts. Opening traces give +5.3 against an API population penalty of +2.6 [+1.4, +3.8]; recurrence +13.0 against +4.1. Deployments differ, so this shows direction only.
3. *"Arm comparisons are unaffected" is wrong for M-P and P-P1.* Those arms keep different amounts of a trace chosen for ending wrong. M-P mixes the mention with one more step along a wrong path. Rollouts repeating the original wrong answer rise with prefix length in later traces: Q 12.4%, P 14.1%, M 16.4%.

Arithmetic: (60.05 - 54.78) / 60.05 = 8.8%, 1 in 11.4 (1 in 8 to 1 in 18). English 24.7%, 1 in 4.0 (1 in 3 to 1 in 7). The denominator is errors in **new** continuations. Among original wrong traces, a new continuation is right 40.0% unchanged and 45.2% without the distractor: 45 right per 100, 40 of which would have come right anyway. The ratio is an excess-risk ratio, which Tian and Pearl call a lower bound on necessity without monotonicity. Monotonicity fails for some distractors ("22 तारीख ..." Q-P -4.6). Later 7.2% [3.2, 11.2], opening 10.8% [5.1, 16.3].

**Wording:** "Among wrong Hindi traces that mention the distractor before answering, a new continuation from the first mention is wrong 60.0% of the time with the distractor and 54.8% without it. The distractor accounts for a net 8.8% [5.5, 12.1] of errors arising from that point, a lower bound on how often it was necessary. Most such errors recur without the distractor." This covers 18.8% of Hindi wrong answers only.

### 6. "Mainly through the question"

Not comparable: (1) Q-P contains the mention path, as Q mentions 1.2% and P 57.8%. (2) M-P's control already mentions 57.8% (62.4% opening, 52.6% later). (3) M-P adds a wrong-path sentence. (4) Cut-offs fall on one side: unanswered P-Q +4.3, M-P +0.8. Answered-only the sizes match (+3.6, -3.2), and in later mentions the mention is larger (+3.8, -5.7). Answered-only conditions on a post-treatment outcome, so neither is clean.

| group | (Q-P)+(M-P) strict | answered | Q-P per unit mention | M-P per unit mention |
|---|---|---|---|---|
| Hindi, all | +2.0 [-1.5, +5.4] | +0.5 [-3.3, +4.4] | +9.3 [+5.7, +12.8] | -7.8 [-12.7, -3.1] |
| Hindi, later | -0.1 [-5.1, +5.0] | -1.9 [-7.8, +4.1] | +10.2 [+4.6, +16.1] | -11.1 [-17.5, -4.5] |
| Hindi, opening | +3.8 [-1.0, +8.5] | +2.5 [-2.5, +7.5] | +8.7 [+4.0, +13.3] | -4.1 [-11.6, +3.0] |

Per-unit columns assume the arm acts only through mention, which is not credible alone.

Observational, post-treatment: Q minus P rollouts without / with a mention: all (328 traces) +1.1 [-2.2, +4.5] / +6.0 [+2.6, +9.4]; opening (177) +2.1 [-2.7, +6.8] / +3.8 [-0.9, +8.4]; later (151) +0.0 [-4.8, +4.7] / +8.7 [+3.7, +13.6]. Within-trace mention minus no mention: strict -4.9 [-8.7, -1.2], answered -2.3 [-6.2, +1.6]; later -8.7 [-14.0, -3.5], -7.7 [-13.4, -2.2]. Rollouts going badly may write the distractor more, and long rollouts have more chances to trigger the detector.

Not run: a question x mention 2 x 2, or P rollouts filtered to no mention (Macar's counterfactual++).

**Wording:** "Removing the distractor from the question and keeping the model's first mention change Hindi accuracy by similar amounts (+5.3 and -3.3 points; on answered outputs +3.6 and -3.2). Our design cannot separate the two, because free continuations mention the distractor 57.8% of the time."

### 7. "Only in the middle"

- Later minus opening: -3.7 [-7.8, +0.3].
- Largest at k = 1, the second sentence: -8.0 [-12.8, -3.4], n=104; k >= 2: -3.3 [-7.3, +0.8], n=144. Second difference -9.5 [-17.9, -1.5] and -1.0 [-7.7, +5.5]. P1 is empty-prefix at k = 1, so format may contribute.
- Stable across tasks: later M-P -4.9 [-8.5, -1.4] recurrence, -5.5 [-10.3, -0.7] others. This is the most robust Part B result.
- "Typically builds it into computation" is unsupported. Hand-coded random 30 later Hindi mentions (one coder, the audit agent): 12 used, 14 restated, 2 dismissed, 1 incidental, 1 false positive (40%, Wilson about 25 to 58%). 54% have digits; M-P is -5.3 with and -5.1 without.
- "Usually a remark": 14 of 20 sampled Hindi opening mentions, 5 interpret it, 1 false positive. English opening mentions (22/22) are problem framings instead.

### 8. Not finishing

Numbers reproduce: 9.4% to 11.9% per round; 1,205 and 232 cut-offs; p99 3,124 tokens; 0.7% above 3,500; 5.7% to 10.0%.

"About a third": (5.27 - 3.62) / 5.27 = 31%; midpoint decomposition 38% [24, 61]; 24% in the 222, 60% in the other 304; English 40%, 71% in opening traces.

Scoring cut-offs as wrong is sound: in Experiment 1 S, 52 of 702 passed 4,096 tokens, 40 never finished, 12 did, 2 were right (at most 0.3 points).

API, 6,750 pairs:

| | none | similar | diff | dissimilar | diff |
|---|---|---|---|---|---|
| Hindi | 0.81% | 0.89% | +0.07 [-0.22, +0.39] | 0.46% | -0.36 [-0.62, -0.09] |
| English | 2.87% | 4.49% | +1.62 [+1.02, +2.18] | 2.34% | -0.53 [-1.05, -0.06] |

FP8 no-distractor opening rollouts fail to answer 3.5% vs 0.7% for the API on the same questions, so "nearly doubles" belongs to FP8 at temperature 0.8 on selected traces.

**Loop rule recovered:** the last 60 characters occur at least 3 times in the output. It reproduces 554/1,205, 93/232, 80/102, 34/40 exactly. It is not adjacent repetition. A periodic-suffix test gives: at least 2 repeats 536, 45, 70, 31; at least 3 repeats with 100+ characters 441, 30, 70, 31; at least 10 repeats 226, 7, 64, 24. For English, over half of flagged outputs are not adjacent loops; sampled tails show re-solving and hedging. Say "repeat long stretches of text" and state the rule.

### 9. Multiplicity

Six matches the README (3 x 2). The README states no correction.

| test | p | Bonferroni | Holm threshold | Holm |
|---|---|---|---|---|
| Hindi Q-P | 5e-05 | yes | 0.0083 | yes |
| English Q-P | 0.0003 | yes | 0.0100 | yes |
| Hindi M-P | 0.0019 | yes | 0.0125 | yes |
| English M-P | 0.0159 (4M permutations) | no | 0.0167 | narrowly yes |
| Hindi second difference | 0.084 to 0.092 | no | 0.0250 | no |
| English second difference | 1.00 | no | 0.0500 | no |

Build no claim on English M-P either way.

### 10. Self-hosted vs API

| decoding | language | self | API | diff [95% CI] | discordant | equivalence margin (90%) |
|---|---|---|---|---|---|---|
| S | all | 71.1 | 73.3 | -2.2 [-13.3, +7.8] | 11/13 | 11.2 |
| S | English | 82.2 | 84.4 | -2.2 [-15.6, +11.1] | 4/5 | 13.3 |
| S | Hindi | 60.0 | 62.2 | -2.2 [-17.8, +15.6] | 7/8 | 16.5 |
| G | all | 67.8 | 73.3 | -5.6 [-16.7, +4.4] | 9/14 | 14.3 |
| G | English | 73.3 | 84.4 | -11.1 [-24.4, +0.0] | 2/7 | 21.9 |
| G | Hindi | 62.2 | 62.2 | +0.0 [-15.6, +15.6] | 7/7 | 13.8 |

90 questions cannot establish sameness. Calibration has no distractor or prefix, one sample each, mixes quantisation with temperature, and ran at 12,288 rather than 4,096 tokens (the 3 outputs over 4,096 were English and wrong, so scores do not change).

Larger check: on opening traces, Q vs API `no_insertion` on the same question. Hindi n=278: 50.4 vs 56.0, +5.7 [+0.5, +10.8], unanswered 0.7% vs 3.5%. English n=22: 86.4 vs 61.7, -24.7 [-42.9, -5.2], unanswered 0% vs 14.9%.

Greedy failed the gate on finishing only (81/90); its English gap passes the 15-point rule (p = 0.18). It repeats identical text in 9.4% of traces, so it is not deterministic. Present it as a Hindi robustness check only, not independent replication, and drop the G English row.

### 11. Prompt, prefill, exclusions

Verified: user message identical to the API's in all 1,952 requests (Q uses the `no_insertion` record); prefix is a substring of the API text in all 1,952; no system prompt on either side (template adds none; 40,500 API CoT requests have one user message); null `reasoning_content` on both; uniform decoding apart from seed. By the agent's reading of the template, non-empty prefixes render as `\n<think></think>\n` plus prefix, and empty ones start with a generated newline like API outputs. The template-check log is not kept. Round 1 restarts: 0 of 1,099 Hindi continuations with a usable prefix; English M 5 of 37.

Differences: unprefilled sanity outputs open with `<think>` despite `enable_thinking=false`, so thinking-off is enforced by prefill; the API's server side is unobservable; 89 rollouts contain a think tag. Traces were written at temperature 0 and continued at 0.8 on a quantised model, so "on-policy" is approximate, and Q is off-policy by construction.

Exclusions: opening traces are kept in Q-P and M-P and in Experiment 1 (94 of 222). They cannot enter the third primary contrast, which therefore covers 47% of Hindi and 41% of English traces.

### 12. English

Experiment 1 (n=12): nothing can be claimed. Q-P on the 37: a within-sample sign test only. Later (15): nothing. "English is hurt more": no. Gap -11.7 [-20.3, -3.4], but 17 of 37 use one distractor (+25.2; without it +10.0), Hindi reweighted to the English task mix is +9.1, later rows match (+5.7, +5.2), the whole gap is 22 opening traces of which 71% is non-completion, FP8 is 24.7 below the API there, selection is harder (4.7% vs 18.8%), and API penalties match (2.59, 2.30).

"Hindi writes the distractor more": 18.8% vs 4.7% of wrong answers, 17.9% vs 5.8% of answered traces, strong as description, with one lexical detector. 73% of Hindi mentions restate at least 80% of the distractor's tokens, against 46% in English.

### 13. Wrong-only selection

**No interventional data exist on originally correct traces.** 673 Hindi and 338 English correct traces mention the distractor before answering; none were continued. Whether a mention turns right answers wrong is not tested. Paper text: "We did not test whether mentions harm traces that would otherwise be correct."

### 14. API population by distractor condition (exploratory)

| language | condition | strict | answered | strict penalty | both-answered penalty | excess fraction |
|---|---|---|---|---|---|---|
| Hindi | none | 60.33 | 60.82 | - | - | - |
| Hindi | similar | 57.73 | 58.25 | +2.59 [+1.38, +3.84] | +2.47 [+1.27, +3.78] | 6.1% [3.2, 9.0] |
| Hindi | dissimilar | 58.86 | 59.13 | +1.47 [+0.25, +2.77] | +1.56 [+0.23, +2.78] | 3.6% [0.6, 6.5] |
| English | none | 86.25 | 88.80 | - | - | - |
| English | similar | 83.96 | 87.90 | +2.30 [+1.36, +3.21] | +0.91 [+0.05, +1.79] | 14.3% [8.8, 19.9] |
| English | dissimilar | 86.73 | 88.80 | -0.47 [-1.41, +0.46] | -0.26 [-1.14, +0.64] | -3.6% [-10.7, +3.4] |

Pre-answer mention vs wrong, Mantel-Haenszel over task x difficulty: Hindi similar OR 1.39 [1.19, 1.63], dissimilar 0.94 [0.79, 1.12]; English similar 2.04 [1.33, 3.12] (crude reverses: 9.9% vs 12.2%), dissimilar 0.67 [0.06, 7.17], n=14.

The PDF's editing note gives +2.2 [+0.6, +3.8] for the Hindi penalty, which this audit does not reproduce on either convention. It is outside Part B; flagged for the Part A auditor.

## Limitations

**Cannot be concluded:** effect on correct traces; share of all errors caused (81% of Hindi wrong answers have no detected mention, and Turpin et al. show that does not clear the distractor); whether the effect runs through the mention; generality over distractors; Hindi vs English effect sizes; that Experiment 1 shows no effect; that results describe the API model.

**Threats the document omits:**
- One sentence, "आखिरी साप्ताहिक प्रतिबद्धता जनवरी में थी" (n=106, +15.2), supplies 58% of summed Hindi Q-P, and the recurrence task 63%. Excluding that sentence: +2.8 [+0.4, +5.0]. Excluding the task: +2.6 [+0.3, +4.9].
- Later-mention Q-P outside recurrence is -0.5 [-4.1, +3.0].
- The detector excludes month and weekday names: 191 Hindi and 63 English wrong traces contain such a word with no detected mention. These words appear before k in 2.4% of later Hindi traces.
- No false-negative estimate exists.
- One seed per round; batched inference is not reproducible.
- Seven runs vs Bogdan's 100. Second-difference MDE is about 7 points.
- P-P1 is not matched to the mention, and 104 of 248 have an empty-prefix P1.
- Experiment 1's neutral filter selects traces.
- Missing logs and scripts.
- The hand coding has one coder and no second rater.

**Not run:** interventions on correct or `dissimilar_insertion` traces; question x mention factorial; filtered resampling; calibration with prefixes and distractors at 4,096 tokens; a BF16 comparison.

## Design rationale from prior work (quotes in `citations.md`)

| choice | defensible? | basis and departure |
|---|---|---|
| Intervening on the trace | Yes | Lanham et al.; their Adding Mistakes regenerates after an edit but inserts rather than deletes. |
| Hand deletion to resampling | Yes as a method | Macar and Bogdan. Their off-policy result is from decision tasks and insertion, and Macar's MATH appendix finds strong local effects from handwritten edits. So our null cannot be explained away by citing them. |
| "Hand edits get repaired" | Partly | Macar supports regeneration and error correction. Yang et al. find models keep following injected thoughts. Cite both. |
| Q arm | Yes | Macar's transplantation. Their hint effects are diffuse and cumulative, so it is a partial effect for k > 0. |
| M vs P as mention effect | Weak | Bogdan filters similar resamples; Macar keeps content absent. We do neither. |
| 7 rollouts | For pooled means only | Bogdan uses 100. |
| Wrong traces only | Limits the question | Bogdan uses correct and incorrect. |
| Excess fraction | If worded correctly | Tian and Pearl. |
| Distractor premise | Yes | Shi et al.; our API penalties (1.5 to 2.6 points) are far smaller than "dramatically decreased". |
| Unmentioned influence | Out of scope | Turpin et al. |

Bibliography: all five [verify] entries are real. Add "Findings of EMNLP 2025" to Yang. ICLR 2026 for Macar is confirmed through the ICLR poster page, not arXiv; authors are Macar, Bogdan, Rajamanoharan, Nanda. Turpin and Shi 2023a are cited but missing from the list.

## Missing findings (all exploratory)

| # | finding | n | effect | interval |
|---|---|---|---|---|
| 1 | Over distractors, Hindi Q-P includes 0, M-P does not | 526, 29 sentences | +5.3; -3.3 | [-0.3, +9.4]; [-5.4, -1.3] |
| 2 | Q-P outside recurrence | 391 | +2.6 | [+0.3, +4.9] |
| 3 | Later Q-P only in recurrence; M-P stable | 111; 137 | +12.2, -0.5; -4.9, -5.5 | [+7.9, +16.9], [-4.1, +3.0]; [-8.5, -1.4], [-10.3, -0.7] |
| 4 | P rollouts without a mention match Q (later) | 151 | +0.0 vs +8.7 | [-4.8, +4.7]; [+3.7, +13.6] |
| 5 | M vs P rollouts without a mention | 385; 195; 190 | -6.3; -10.2; -2.3 | [-9.4, -3.1]; [-14.9, -5.8]; [-6.8, +2.2] |
| 6 | Later effect at the second sentence | 104; 144 | -8.0; -3.3 | [-12.8, -3.4]; [-7.3, +0.8] |
| 7 | API non-termination: Hindi flat, English up | 6,750 each | +0.07; +1.62 | [-0.22, +0.39]; [+1.02, +2.18] |
| 8 | API excess fraction, similar | 6,750 each | 6.1%; 14.3% | [3.2, 9.0]; [8.8, 19.9] |
| 9 | Unrelated distractor penalty | 6,750 each | +1.47; -0.47 | [+0.25, +2.77]; [-1.41, +0.46] |
| 10 | Mention-error association, similar only | 1,199; 1,124 | OR 1.39; 0.94 | [1.19, 1.63]; [0.79, 1.12] |
| 11 | Larger FP8 calibration | 278; 22 | +5.7; -24.7 | [+0.5, +10.8]; [-42.9, -5.2] |
| 12 | Experiment 1 traces differ | 222 vs 304 | +4.0 | [+0.1, +8.1] |
| 13 | Identical prefixes across experiments | 115 | -3.5, -5.2, -1.6 | [-13.9, +7.0], [-13.9, +2.6], [-6.1, +2.7] |
| 14 | Cut-off scoring cost | 702 | at most 0.3 points | count |

## Suggested claims for the paper

1. **strong.** "On the API's own responses, adding a time-related distractor lowers strict accuracy by 2.6 points in Hindi (60.3% to 57.7%; +2.59 [+1.38, +3.84], 6,750 questions) and 2.3 points in English (86.3% to 84.0%; +2.30 [+1.36, +3.21]); an unrelated distractor costs 1.5 points in Hindi (+1.47 [+0.25, +2.77]) and nothing detectable in English (-0.47 [-1.41, +0.46])."
2. **moderate.** "Among 526 wrong Hindi traces that mention the time-related distractor before answering, resampling from the first mention gives 45.2% correct without the distractor and 40.0% with it (+5.3 [+3.2, +7.4], p < 0.001; [-0.3, +9.4] when resampling over the 29 distractor sentences), so the distractor accounts for a net 8.8% [5.5, 12.1] of errors from that point and most errors recur without it; the effect is concentrated in the recurrence task (+13.0, against +2.6 [+0.3, +4.9] elsewhere)."
3. **moderate.** "Keeping the sentence containing the model's first mention lowers Hindi accuracy by 3.3 points (-3.3 [-5.4, -1.2], p = 0.002; answered outputs -3.2 [-5.5, -0.9]), but the test against the preceding ordinary sentence is not significant (-4.6 [-9.6, +0.6], p = 0.09), so we cannot attribute this to the mention rather than to one more step along a trace that ended wrong."
4. **suggestive.** "This effect appears for mentions after the first sentence (-5.2 [-8.3, -2.2], n = 248) and not clearly for opening mentions (-1.5 [-4.2, +1.2], n = 278), though the difference is not significant (-3.7 [-7.8, +0.3]) and the split was exploratory."
5. **moderate.** "Experiment 1 found no detectable benefit from deleting the mention (Hindi B - C +0.0 [-6.8, +7.2] greedy, +4.5 [-2.7, +11.7] sampling), but it had about 24% power for a 5-point effect, so it does not show that deletion has no effect."
6. **suggestive.** "Our design does not separate the distractor in the question from the act of writing it: free continuations mention it in 57.8% of Hindi rollouts, against 1.2% without the distractor, and in later-mention traces rollouts without a mention match the no-distractor arm (+0.0 [-4.8, +4.7]) while those with a mention do not (+8.7 [+3.7, +13.6])."
7. **moderate.** "In self-hosted continuations the distractor raises unanswered Hindi rollouts from 5.7% to 10.0% (+4.3 [+3.0, +5.6]), about a third of the Q - P effect (38% [24, 61]); this does not hold on the API, where Hindi moves from 0.81% to 0.89% (+0.07 [-0.22, +0.39]) and the rise is in English (2.87% to 4.49%, +1.62 [+1.02, +2.18])."
8. **strong.** "All interventions used originally wrong traces with the time-related distractor, on a quantised self-hosted model at temperature 0.8 whose calibration difference from the API was -2.2 points [-13.3, +7.8] on 90 questions; we did not test originally correct traces, and we make no causal claim for English, where only 37 traces qualify, 17 from one distractor sentence, and the self-hosted model scored 24.7 points below the API [-42.9, -5.2] on 22 of these questions."

B.4 replacements: Finding 1 becomes claim 2. Delete Finding 2 and use claim 6. Finding 3 becomes claims 3 and 4. Finding 4 becomes claim 7. Finding 5 keeps only "Hindi writes the distractor more often (18.8% vs 4.7% of wrong answers)".
