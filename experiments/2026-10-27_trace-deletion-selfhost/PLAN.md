# Trace deletion: plan

Paths in this file refer to the folder layout before 2026-10-27 (`outputs/selfhost`, `outputs/selfhost_s4` and so on). Final results are in `outputs/selfhost_G` and `outputs/selfhost_S`; everything from before the final run is in `pre_final_run_archive/`. See `README.md`.

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

## Session 2 failure and the fix (27 Oct)

- Session 2 sanity (outputs/selfhost/sanity.json, renamed sanity_attempt2.json in session 3): every generation gave one correct token (prefill, FlashAttention) and then 4,095 invisible tokens until max_tokens. Cause: --kv-cache-dtype fp8 with no KV-cache scale tensors in the checkpoint (only weight_scale/input_scale; Sarvam's sarvam.py loads none), so vLLM used scale 1.0; MLA cache values beyond the FP8 e4m3 range become NaN, and NaN logits make greedy decoding emit token 0 (<pad>). With FP8 KV only FlashMLA was eligible (vLLM 0.15.0: FLASH_ATTN_MLA and TRITON_MLA accept only bf16 KV). Session 1's "<think>" outputs were the same failure.
- Fix: bf16 KV cache (--kv-cache-dtype auto). gpu/bringup.py tries bf16+FlashMLA, bf16+FLASH_ATTN_MLA, bf16+TRITON_MLA, TRITON_MLA+--enforce-eager, and keeps the first that passes smoke tests (real text, Answer line, finish=stop, no special tokens). continue.py stops on degenerate output (exit 4). Fresh-answer tests are informational (the experiment only uses continuations).
- Pre-boot: gpu/template_check.py renders the exact prompts with Sarvam's real tokenizer on the Mac (user turn ends <|nothink|>; assistant part '\n<think></think>\n' + prefix; no end-of-turn after it; one [@BOS@]).

## Session 3 result and the final attempt (27 Oct)

- Session 3: with `--kv-cache-dtype auto`, vLLM 0.15 still used FP8 (auto follows the checkpoint's kv_cache_quant_algo: FP8; resolve_kv_cache_dtype_string) and gave the same <pad> output; explicit `bfloat16` crashed in concat_and_cache_mla ("Unsupported data type of kv cache: bfloat16"; 0.15's DISPATCH_BY_KV_CACHE_DTYPE accepts only auto/fp8/fp8_e4m3/fp8_e5m2).
- Final attempt (instruction_gpu_session4.md): vLLM 0.31.0 in /home/venv031 (native Sarvam support; get_fp8_kv_cache_data_type maps "bfloat16" to an unquantized cache; Python 3.10 supported; installed from a pinned lock file resolved for the VM's platform), `--kv-cache-dtype bfloat16 --moe-backend triton`, plus a loader patch that drops unused KV-scale tensors and extra layers. Fallback: vLLM 0.15 with the KV FP8 tag removed from the model's config.json/hf_quant_config.json (backups kept) so auto gives bf16.
- Bring-up smoke test now uses long prompts (longest trace prefix), long Hindi output, logprobs, and fails on <pad>/special tokens, NaN log-probabilities, a token repeated > 20 times, missing Answer lines or error responses.
- If bring-up fails, GPU work stops; trace deletion is reported from the design, the API pilot and diagnostics, with self-hosted continuation as future work.

## Session 4 result and session 5 plan (27 Oct)

- Session 4: bf16 KV on vLLM 0.31 removed the <pad> garbage, but Sarvam's FP8 checkpoint degraded on long reasoning (wrong months, absurd sums, loops to 4096 tokens; kernel-dependent). Suspected cause: static per-expert input scales collapsed to the per-layer maximum by vLLM.
- Session 5: RedHatAI/sarvam-105b-FP8-dynamic (per-channel FP8 weights, per-token dynamic FP8 activations, no KV quantization; validated by Red Hat on vLLM, 99-101% recovery). Served with vLLM 0.31 (already installed), bf16 KV, Triton MoE (supports channel-weight + per-token-dynamic FP8), no --quantization flag.
- Calibration gate (new): 90 no-distractor questions from the API runs (one per language x task x difficulty; outputs/calibration_requests.json; API accuracy 73.3%: en 84.4%, hi 62.2%). Accept a setting only if >= 95% finish, overall accuracy >= API - 10 points, and each language >= API - 15 points. Scoring reproduces metrics.is_correct on 90/90 API answers.
- Download on the cheapest machine that can resume the VM disk, pause, then resume on 2 x H100.
- The paper must say the experiment used Red Hat's FP8-dynamic checkpoint, justified by the calibration result.

## Session 5 result and session 6 plan (28 Oct)

- **Session 5:**
  - Red Hat FP8-dynamic on vLLM 0.31 with TRITON_MLA passed every smoke test; the default backend looped.
  - **Calibration gate FAILED, on English only:**
    - English: self 66.7% vs API 84.4% (1 vs 9 discordant, exact McNemar p = 0.02).
    - Hindi: 60.0% vs 62.2% (8 vs 9, p = 1.0).
    - Overall: 63.3% vs 73.3% (p = 0.12).
    - Finished: 82/90. The 8 unfinished ran to 4,096 tokens; the API answered the same questions in 355–2,042 tokens.
- **Deviation from the pre-set gate (user decision):** proceed anyway.
  - 666 of 702 requests are Hindi, where the self-hosted model matches the API.
  - B vs C is a within-model comparison: B, C and the A baseline are all continued by the same self-hosted model.
  - English (36 requests) is reported descriptively, with the calibration gap stated.
  - Write-up limitation: the traces came from the API (sarvam-105b), the continuations from the FP8-dynamic self-hosted model.
- **Likely causes of the English gap,** not separable without a BF16 run (about 210 GB, needs 4 x H100):
  - runaway generations under strict greedy decoding;
  - FP8 rounding compounding over long day-counting chains.
- **Session 6:**
  - max_tokens 12,288 for every path (was 4,096). Runaways are counted as no answer and reported per arm; they stop the run only above 30%.
  - Decoding is chosen by the user: Sarvam model-card sampling (temperature 0.8, top-p 0.95, seed 0), or greedy.
  - With sampling, the 90-question calibration is rerun first as information, and the A repeat run measures sample-to-sample noise.
  - No smoke test; batched at 16.
- **Update (user decision, 28 Oct):** run both, on one server, G first then S.
  - Each run gets its own 90-question calibration at its own decoding (12,288 tokens), information only.
  - Outputs go to `selfhost_G` and `selfhost_S`.
  - Analyze each separately. If the B vs C result holds under both decodings, report it as a robustness check.
