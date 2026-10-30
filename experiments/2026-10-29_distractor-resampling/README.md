# Distractor resampling (self-hosted Sarvam-105B)

When a wrong chain of thought (CoT) mentions the time-related distractor, did the distractor cause the error, and does the model's written mention of it matter? Measured separately for Hindi and English.

This follows `2026-10-27_trace-deletion-selfhost`. There, deleting the distractor sentence from a wrong trace (B) did no better than deleting a neutral sentence (C), and the model often wrote the distractor again. That matches Thought Branches (Macar et al., ICLR 2026): hand edits to a trace ("off-policy") have effects near zero and deleted content tends to come back. This experiment uses on-policy resampling instead (Thought Anchors, Bogdan et al. 2025): regenerate from a point in the trace several times and compare the answers.

## Design (fixed before the run)

- **Traces:** every originally wrong, finished API trace (`similar_insertion`, CoT) whose first distractor mention comes before the answer sentence. Same source runs and mention rule as the trace-deletion experiment, without the neutral-sentence and length filters. 563 traces: 526 Hindi, 37 English. All 234 trace-deletion traces are included. Built by `build_resample.py` (selection code copied unchanged in `build_requests.py`); counts in `outputs/build_summary.json`.
- **Arms** (k = index of the first sentence that mentions the distractor):

| arm | question | assistant prefix (API text) |
|---|---|---|
| Q | the dataset's `no_insertion` question (no distractor) | sentences before k |
| P | the `similar_insertion` question (with distractor) | sentences before k |
| M | with distractor | sentences up to and including k |
| P1 | with distractor | sentences before k - 1 (only when k >= 1; 263 traces) |

  An empty prefix (300 traces have k = 0: the first sentence already mentions the distractor) is sent as `<think></think>`, the form used and validated by calibration in the trace-deletion run.
- **Requests:** 1,952 per round (`outputs/requests_resample.json`).
- **Decoding:** temperature 0.8, top-p 0.95, max tokens 4,096 (`config/resample.cfg`); seed = round number.
- **Rounds:** one sample of every request per round. Rounds run until the GPU budget is used (`gpu/rounds.py`). Only complete rounds are analysed.
- **Scoring:** the Answer line of the continuation, root `metrics.py` rules; no Answer line or cut off counts as wrong. Per trace, the accuracy of each arm is averaged over rounds.
- **Distractor mention in a rollout:** a sentence of the continuation shares at least 2 strict distractor words, or 1 rare one, as in the selection rule. Q's rate is the detector's false-positive rate.

## Primary contrasts (per language)

| contrast | question it answers |
|---|---|
| Q - P | Does the distractor in the question make these errors more likely, with the same reasoning so far? |
| M - P | Does having written the mention change the outcome? |
| (M - P) - (P - P1) | Does the mention matter more than an ordinary sentence at the same place? (P - P1 is the effect of the sentence just before the mention.) |

Paired by trace; bootstrap 95% CI over traces; two-sided sign-flip permutation p. Hindi is the main test; English (37 traces) has low power. Everything else in `analysis.md` is exploratory: by task, by difficulty, whether the mention is the opening sentence, and accuracy of P rollouts that mention the distractor vs those that do not (answered rollouts only).

## Known limitations

- **Selection:** traces were chosen because one API sample was wrong. Resampled accuracy will be well above 0 in every arm, partly by regression to the mean. Arm comparisons are unaffected, since all arms share the selection.
- **API-written prefixes:** for k >= 1 the prefix was written by the API model under the distractor question, so it may already carry the distractor's influence. Q - P may therefore understate the distractor's effect for those traces, which is why the opening-sentence and later-mention groups are reported separately.
- **P1 and the empty-prefix form:** when k = 1, P1 is the empty-prefix form and P is not; the same holds for M vs P when k = 0. Rendering is checked by `gpu/template_check.py` before the run.
- **Model:** continuations come from `RedHatAI/sarvam-105b-FP8-dynamic`, which matched the API at these decoding settings in calibration (89/90 finished; 71.1% vs 73.3% overall; trace-deletion run).

## Files

| path | content |
|---|---|
| `build_resample.py`, `build_requests.py` | build the requests |
| `analyze_resample.py` | analysis (writes `analysis.md` and `analysis.json` into the output folder) |
| `config/resample.cfg` | decoding, rounds, analysis settings |
| `gpu/` | scripts as run on the VM (`rounds.py`, `continue.py`, `status.py`, `monitor.py`, `serve_rh.sh`, `bringup.py`, `deadline.sh`) and `template_check.py` (Mac, pre-boot) |
| `instruction_gpu.md` | instructions for the GPU session |
| `outputs/` | requests, build summary, and after the run: `resample/round_NN/results.json`, sanity, logs |
