# Trace deletion: plan

Question: when Sarvam-105B writes the time-related distractor into its CoT before working out the answer, does that cause the error?
Method: take wrong traces, remove only the distractor sentence(s), let the same model continue from the edited prefix, and compare with removing length-matched neutral sentences.

## Data
- Runs: 2026-10-17_run-short-leftover-rahul, 2026-10-17_run-medium-leftover-rahul, 2026-10-16_finish-run-long-adi, 2026-10-18_run-very-long-leftover-aayush, 2026-10-18-very_very_long-aayush.
- CoT responses, `similar_insertion` (time-related distractor), en_US and hi_IN. Scored with the current root `metrics.py`.
- The no-insertion record of the same question gives the base question; distractor = question text minus base question.

## Eligibility (all must hold)
1. Has an answer line, finish_reason != length, answer wrong.
2. Mentions the distractor (stricter than the mid report, changed after the pilot check showed false positives such as "पता लगाना", "जानना", "9 अगस्त"): distractor content words = words of the distractor not in the base question (mid-report stoplist and tokeniser), minus month and weekday names. A sentence is a mention if it shares >= 2 of these words, or 1 word that is rare in clean traces (in < 2% of same-language no-insertion CoT traces). Neutral sentences must share no distractor word at all (loose rule) and have no digits.
3. First mention sentence k comes before the answer sentence (first sentence containing the final answer; whole-token match; if never found, the last sentence).
4. A neutral sentence exists before the answer sentence: no digits, no distractor words.

## Sampling
- Eligible after the stricter rule: 222 hi, 12 en wrong traces. English is descriptive only.
- Cells = language x task x difficulty. Each cell's eligible traces in a fixed seeded order (seed 26). Main run = first 10 per cell. Raising the cap later only appends; ids already done are skipped.
- Pilot = 20 traces (12 hi, 8 en) taken from the main selection, so pilot results count toward the main run.

## Splitting and editing
- Body = content before the last Answer line. Sentences = split on newlines, `।`, `?`, `!`, and `.` followed by whitespace or end. Keep character spans.
- k = first mention sentence. Neutral j: among neutral sentences before k, the one closest in length to k; if none, the first neutral after k (before the answer sentence).
- Window = sentences 0..max(k, j) (exact substring of the body, right-stripped).
- A = window. B = window minus all mention sentences in it. C = window minus the same number of neutral sentences in it, chosen closest in length to the deleted mention sentences. If not enough neutrals, or deleted lengths differ by more than 3x, the trace is not eligible.
- Sentence spans exclude leading whitespace; each kept sentence carries its trailing separator, so deletions leave clean spacing.
- Flag `mention_has_digits` when a deleted mention sentence contains digits.

## Calls
- messages = [original user message copied from record.request, {"role": "assistant", "content": prefix}] (plain prefill, tested 26 Oct).
- Same settings as the original request: sarvam-105b, temperature 0, top_p 1, reasoning_effort null, max_tokens 4096, non-streaming.
- id = original id + "/A" | "/B" | "/C". Two API keys: switch to key 2 when key 1 reports exhausted credit.

## Scoring
- Score the continuation only with metrics.extract_answer / is_correct and the original meta. No answer or cut off = wrong (counted).
- Re-mention: does the continuation contain distractor content words.
- Noise floor: A answer equals the original answer.

## Analysis
- Main: per language, accuracy after B vs after C on originally wrong traces; exact McNemar on the B/C pairs; bootstrap 95% CI for B - C (resample traces).
- Language comparison within the shared tasks (date_recurrence, interval_date, day_of_week); bootstrap CI of (B-C)_hi - (B-C)_en. English is low-powered.
- Secondary: A-original agreement, re-mention after B, per-task, mention_has_digits subgroup, count of mentions after the answer, deleted-length balance B vs C.

## Order
1. Build requests, print funnel. 2. Pilot (60 calls), read prefixes and continuations. 3. Main run. 4. Analysis.

## Self-hosted run (added 26 Oct, after the API pilot)

API pilot + diagnostic (outputs/diag/continuation_diag.json): the Sarvam API does not truly continue a partial assistant message (it opens a new reply; "The capital of France is Par" -> "The capital of France is Paris..."), and temperature 0 is not repeatable (0/8 identical repeats, answers differ). So single API continuations cannot isolate the edit.

Self-hosted design: Sarvam-105B FP8 weights (sarvamai/sarvam-105b-fp8) on 2 x H100 80 GB (Jarvislabs, IN2; H200 unavailable), vLLM 0.15.0 + Sarvam hot-patch (hotpatch_vllm.py is only in the bf16 repo sarvamai/sarvam-105b; it registers SarvamMLAForCausalLM, the FP8 checkpoint's architecture), TP 2, FP8 KV cache, bfloat16 activations, prefix caching off (A/B/C share prefixes; caching can change greedy outputs).
- Same selection rule, all eligible traces: 222 hi + 12 en = 234 traces (outputs/requests_cap1000.json), 702 continuations.
- True continuation: chat endpoint with continue_final_message=true, add_generation_prompt=false, chat_template_kwargs.enable_thinking=false (the template adds <|nothink|>, matching reasoning_effort null). Greedy: temperature 0, top_p 1, seed 0, max_tokens 4096.
- Sanity before the main run: split-word prefill continues; fresh answers have no <think> and an Answer line; English continuations do not restart; same request twice identical is reported but not blocking (the repeat run measures it on all 234 A prefixes).
- Repeat run of version A on all 234 traces to report repeatability.
- Analysis: analyze.py --output outputs/selfhost (same tests as above; A is the baseline; "A = original" compares with the API's original answer and is descriptive only).
- API pilot results stay in outputs/results.json and are reported as the motivation for self-hosting.
- Safety: gpu/preflight.py must pass before any VM is created; gpu/monitor.py (on the Mac) pauses the VM after 4 h or 25 min without progress; gpu/deadline.sh on the VM pauses it at 4.5 h as a backstop.

## Self-hosted attempt 1 and the fix (27 Oct)

- Attempt 1 sanity (outputs/selfhost/sanity_attempt1.json): continuation PASS ("Par" -> "us.", no English restarts); fresh answers returned only "<think>" because thinking-off replies are formatted as "<think></think>" + answer and the test did not pre-fill it (trace continuations already include it via the template); 8 requests sent together twice: 0/8 identical text (vLLM batching is not batch-invariant).
- Decision (user): run one request at a time (concurrency 1). Sanity now pre-fills "<think></think>" for fresh answers, checks continuations reach an Answer line, and measures one-at-a-time repeatability (identical text >= 7/8 -> MODE sequential, else MODE batched).
- Budget: main + repeat one at a time must project <= 120 min (continue.py --budget-minutes 120 stops itself otherwise); then option 2 = batched (concurrency 32) into outputs/selfhost_batched, with repeatability measured by the repeat run. Session cap 3 h after resume.
