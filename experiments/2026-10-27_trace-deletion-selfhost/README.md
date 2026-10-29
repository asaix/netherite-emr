# Trace deletion (self-hosted Sarvam-105B)

Does the model make an error because it wrote the time-related distractor into its chain of thought (CoT) before working out the answer?

Method: take CoT traces that ended with a wrong answer, delete only the distractor sentence(s) from the part of the trace written before the answer, and let the same model continue from the edited text. Compare with deleting the same number of length-matched neutral sentences.

This folder is the final, self-hosted run. It supersedes `2026-10-26_trace-deletion` (renamed to this folder). Everything made before the final run (API pilot, failed bring-up attempts, instructions of sessions 1 to 5, old scripts) is in `pre_final_run_archive/`.

## Design

- **Source traces:** the Sarvam API CoT runs (`similar_insertion`, en_US and hi_IN) from `2026-10-16_finish-run-long-adi`, `2026-10-17_run-short-leftover-rahul`, `2026-10-17_run-medium-leftover-rahul`, `2026-10-18_run-very-long-leftover-aayush` and `2026-10-18-very_very_long-aayush`.
- **Selection:** wrong answer, finished, and the distractor mentioned in the CoT before the answer sentence. 234 traces (222 Hindi, 12 English). Rules in `PLAN.md`; the selection funnel is in `outputs/funnel.json` and `outputs/eligible_counts.json`.
- **Three versions of each trace** (702 continuation requests, `outputs/requests_cap1000.json`):
  - **A:** the prefix as written.
  - **B:** the distractor sentence(s) removed.
  - **C:** neutral sentence(s) of similar length removed.
- **Continuation:** a true continuation of the assistant message (chat endpoint, `continue_final_message=true`, `add_generation_prompt=false`, `enable_thinking=false`). The Sarvam API cannot do this (it opens a new reply), which is why the model is self-hosted.
- **Scoring:** only the continuation's Answer line, with the root `metrics.py` rules. No Answer line or a cut-off output counts as wrong.
- **Repeat run:** version A of all 234 traces is run a second time to measure run-to-run noise.

## Setup of the final run

- **Model:** `RedHatAI/sarvam-105b-FP8-dynamic` (FP8 weights, dynamic FP8 activations, no KV-cache quantisation), a quantisation of Sarvam-105B. The traces being continued came from the API's `sarvam-105b`, so the continuations are from a different (quantised) deployment than the traces.
- **Server:** vLLM 0.31.0, tensor parallel 2 on 2 x H100 80 GB (Jarvislabs, IN2), `--kv-cache-dtype bfloat16 --moe-backend triton --attention-backend TRITON_MLA --block-size 64 --max-model-len 16384`, prefix caching off (`gpu/serve_rh.sh`).
- **Concurrency:** 16 requests at a time.
- **Decoding, both set per request, `max_tokens` 12,288 in both:**

| run | temperature | top-p | seed | folder |
|---|---|---|---|---|
| G (greedy) | 0 | 1 | 0 | `outputs/selfhost_G` |
| S (sampling, Sarvam model-card values) | 0.8 | 0.95 | 0 | `outputs/selfhost_S` |

- **Runaways:** a request that reaches the token limit without an Answer line is a runaway. It is counted as no answer and reported per arm. The run would stop if more than 30% of at least 50 outputs were runaways (it never came close).
- **Run order on one server:** G calibration, G sanity, G main, G repeat, S calibration, S main, S repeat. No step had to be repeated.
- **Cost:** 1.33 h on 2 x H100 (about 878 INR) for this run; all sessions including the failed attempts about 4.28 h (about 2,830 INR).

## Calibration: is the self-hosted model close to the API?

90 questions without a distractor (one per language x task x difficulty), answered by the server and compared with the API's answers to the same questions (`outputs/calibration_requests.json`, results in `outputs/selfhost/`). Information only in this run.

| | finished | overall | English | Hindi |
|---|---|---|---|---|
| Earlier attempt, greedy, 4,096 tokens (archive) | 82/90 | 63.3% | 66.7% | 60.0% |
| G greedy, 12,288 tokens | 81/90 | 67.8% | 73.3% | 62.2% |
| S sampling, 12,288 tokens | 89/90 | 71.1% | 82.2% | 60.0% |
| API | n/a | 73.3% | 84.4% | 62.2% |

S passes the pre-set gate (at least 95% finished, overall within 10 points of the API, each language within 15). G fails only the 95% finished check.

## Sanity check (G)

11 requests (`outputs/selfhost_G/sanity.json`, `outputs/logs/sanity_G.log`): PASS. 5 of 6 trace continuations reached an Answer line, the split-word continuation ("Par" to "us.") worked, and only 1 of 6 restarted its reasoning.

## Results

Accuracy in % on the originally wrong traces after continuing from each version. Full tables (by task, difficulty, digits, shared tasks, re-mention, unanswered) are in `outputs/analysis_G.md` and `outputs/analysis_S.md`.

| run | language | n | A | B (distractor removed) | C (neutral removed) | B - C (95% CI) | McNemar p |
|---|---|---|---|---|---|---|---|
| G | hi_IN | 222 | 33.3 | 33.8 | 33.8 | 0.0 [-6.8, 7.2] | 1 |
| G | en_US | 12 | 25.0 | 16.7 | 25.0 | -8.3 [-25.0, 0.0] | 1 |
| S | hi_IN | 222 | 29.3 | 32.9 | 28.4 | 4.5 [-2.7, 11.7] | 0.26 |
| S | en_US | 12 | 25.0 | 33.3 | 25.0 | 8.3 [0.0, 25.0] | 1 |

- **Main comparison (B vs C):** no significant difference in either run or language. All Hindi confidence intervals include 0. The English subset has 12 traces and is descriptive only.
- **Runaways:** G 99 of 702 (14.1%), S 37 of 702 (5.3%). Unanswered by arm (A/B/C): G hi 35/37/25, en 1/3/1; S hi 16/10/11, en 1/1/1.
- **Speed (wall time per request at 16 concurrent):** G 2.3 s for main, S 1.4 s.
- **Repeatability of version A** (`results_repeat.json`):
  - G greedy: identical text in 22/234 (9.4%), same answer in 123/234 (52.6%).
  - S sampling: identical text in 10/234 (4.3%), same answer in 100/234 (42.7%).

## Limitations

- **Greedy is not reproducible here.** With 16 requests batched, bf16 kernels are not bit-reproducible, so the greedy repeat gave identical text for only 9.4% of traces. G is one noisy sample, not a deterministic baseline.
- **Model mismatch.** Traces are from the API model; continuations are from the FP8-dynamic checkpoint. B, C and the A baseline are all continued by the same self-hosted model, so B vs C is a within-model comparison. The A-versus-original comparison in the analysis ("A = original") is descriptive only.
- **English gap under greedy.** G English calibration accuracy is 73.3% against 84.4% for the API; with sampling (S) it is 82.2%. The cause was not isolated; a BF16 run (about 210 GB, 4 x H100) would be needed.
- **Runaways count as wrong,** in all three arms.
- **`BAD OUTPUT` flags.** `continue.py` flags outputs under 20 characters. Five flags (G main requests 097 and 377, G repeat request 025, S main request 099, S repeat request 024) were valid Answer-only continuations such as `Answer: 0`, not server faults. Four are the same item (`short/date_duration_hi_IN/23`, version A). The run was not paused for them.
- **Small English sample** (12 traces).

## Layout

| path | content |
|---|---|
| `PLAN.md` | design and decision log (paths in it refer to the layout before this reorganisation) |
| `build_requests.py` | selects the 234 traces and builds the 702 requests |
| `build_calibration.py` | builds the 90 calibration questions |
| `analyze.py` | B vs C analysis |
| `config/run.cfg` | API settings of the pilot (keys redacted) |
| `gpu/` | scripts as run on the VM: `serve_rh.sh`, `bringup.py`, `calibrate_only.py`, `continue.py`, `status.py`, `monitor.py`, `deadline.sh`, `download_rh.sh`, `setup031.sh`, `preboot/`, `instance.json`, and `NOTES.md` (log of all GPU sessions) |
| `instruction_gpu_session6.md` | the instructions the final run followed |
| `outputs/requests_cap1000.json`, `outputs/calibration_requests.json` | inputs |
| `outputs/selfhost_G`, `outputs/selfhost_S` | `results.json` (702), `results_repeat.json` (234), `analysis.json`, `SUMMARY.md`; `sanity.json` for G |
| `outputs/selfhost` | calibration results for G and S |
| `outputs/logs` | bring-up, calibration, sanity, main and repeat logs, server log tail, deadline log |
| `outputs/analysis_G.md`, `outputs/analysis_S.md` | analysis output |
| `pre_final_run_archive/` | everything made before the final run: API pilot and diagnostics, sessions 1 to 5 instructions, old serve and setup scripts, failed bring-up and calibration outputs |

## Reproduce

Build inputs (Mac):

```
python3 build_requests.py
python3 build_calibration.py
```

On the VM (after `bringup.py redhat_v031_triton_mla` has started the server), run `continue.py` for each decoding:

```
python3 -u continue.py --mode sanity --temperature 0 --top-p 1 --max-tokens 12288 --concurrency 16 --out selfhost_G
python3 -u continue.py --mode main --temperature 0 --top-p 1 --max-tokens 12288 --concurrency 16 --budget-minutes 150 --out selfhost_G
python3 -u continue.py --mode repeat --temperature 0 --top-p 1 --max-tokens 12288 --concurrency 16 --out selfhost_G
python3 -u continue.py --mode main --temperature 0.8 --top-p 0.95 --max-tokens 12288 --concurrency 16 --budget-minutes 150 --out selfhost_S
python3 -u continue.py --mode repeat --temperature 0.8 --top-p 0.95 --max-tokens 12288 --concurrency 16 --out selfhost_S
```

Calibration uses `calibrate_only.py` with `TEMPERATURE`, `TOP_P`, `CAL_MAX_TOKENS`, `CAL_TAG` set in the environment. Analysis (Mac):

```
python3 analyze.py --output outputs/selfhost_G
python3 analyze.py --output outputs/selfhost_S
```
