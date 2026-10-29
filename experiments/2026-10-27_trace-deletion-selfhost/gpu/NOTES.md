# Self-hosted run notes

## Instance

{"machine_id": "548505", "started_at": "2026-10-26T19:11:29+00:00", "work": "/home/trace-deletion"}

- Created with `jl create --gpu H100 --num-gpus 2 --vm --storage 250 --region IN2 --name netherite-trace --yes --json`.
- Changed from the command in `instruction_gpu.md` (approved by the user):
  - `--vm` added and `--template pytorch` dropped: 2 x H100 in IN2 had 0 free containers and 7 free VMs; `--template` applies to containers only.
  - `--region IN2` added: the rules allow only IN2, and the written command did not pin a region.
- Result: on-demand (`is_spot: false`, `billing_frequency: hour`, no reservation), 2 x H100, 48 cores, 400 GB RAM, 250 GB SSD, user `ubuntu`.

- Boot: the VM reported `Running` at 19:11:52Z but SSH (port 22) only answered at 19:21:09Z, about 10 minutes later. That time is billed.

## Session 2 (instruction_gpu_resume.md)

- Resumed with `jl resume 548505 --yes --json` at 2026-10-26T20:05:03Z. New machine id **548606** (same IP 151.185.52.24, 2 x H100, IN2, on-demand, hourly).
- `instance.json`: `{"machine_id": "548606", "started_at": "2026-10-26T20:05:03+00:00", "work": "/home/trace-deletion", "previous_hours": 0.65}`.
- Budget: at most 3 h from the resume; deadline guard at resume + 11700 s; monitor `--max-hours 3`.
- SSH answered at 20:06:22Z (about 1 minute). Checks: 2 x H100 80GB HBM3, 23 shards, vllm 0.15.0. The resumed machine has new SSH host keys on the same IP (expected after the id changed); `known_hosts` left unchanged.
- Deadline guard: `deadline guard active: pausing 548606 at Mon Oct 26 23:20:03 UTC 2026` (session 1 log kept as `deadline_session1.log`).
- Uploaded the new `continue.py` and `status.py` (MD5 matches local: 5beb16d4..., 9e86655a...). Remote and local `selfhost/sanity.json` renamed to `sanity_attempt1.json`. Server started 20:07:05Z (`serve_attempt2.log` is session 1's working server log).

- Server ready 20:12:25Z. Sanity (one request at a time, 27 requests) 20:12:44Z to about 20:26Z: **SANITY: FAIL** (`outputs/selfhost/sanity.json`, `outputs/selfhost/logs/sanity.log`).
  - Every generation ran to max_tokens 4096 (`finish_reason=length`, about 30.1 s each at about 136 tokens/s) and none produced an Answer line: the 2 fresh answers without pre-fill, the 2 with `<think></think>` pre-filled, and all 6 trace continuations.
  - The visible content of those 4096-token outputs is essentially empty: `'<think>'`, `'\n'` or `' '`. So the model generated 4096 tokens that decode to nothing visible, which points to degenerate output (for example NaN logits giving the same special token every step) rather than long reasoning. Not verified; needs a token-level check.
  - The PASS checks are therefore vacuous: "not restarted" passes because the output is empty, and 8/8 identical repeats are identical empty outputs.
  - The session 1 fresh answers (`'<think>'`) were probably the same symptom, not "opened a thinking block and stopped".
- Downloaded `selfhost/` and logs (`serve_tail_session2.log`, `sanity.log`, `deadline.log`). Paused with `jl pause 548606 --yes` at 20:27:00Z. Session 2 runtime about 0.37 h (about ₹242). Total both sessions about 1.02 h (about ₹671). The pause stopped the deadline guard process.

## Session 3 (instruction_gpu_session3.md)

- Pre-boot (Mac, no credits): `gpu/template_check.py` -> `TEMPLATE CHECK: PASS` (Hindi A/B/C, English A, open-ended all PASS; "fresh" informational). Syntax check `SYNTAX_OK`.
- User change before boot: `gpu/continue.py` sanity now prints one flushed line after each of its 27 requests (`[sanity NN/27] label | finish | tokens | seconds | visible chars | answer | starts`) and stops at the first bad output of an essential request (empty content, or `finish_reason=length` without an Answer line) with `SANITY: FAIL (stopped at request N of 27, ...)` and exit code 4. Requests 1 to 23 are essential; the 4 informational "fresh" requests now run last (24 to 27) and only print a `BAD OUTPUT` flag. The early-abort `sanity.json` carries `"checks": {"stopped at the first bad output": false}` because `status.py` reads `sanity["checks"]`. Tested locally against a fake server in five cases (healthy: 27 lines, PASS, exit 0; broken from request 2: stopped at 2, exit 4; broken from request 6: stopped at 6; broken split-word: stopped at 1; broken informational only: completes); `status.py` reports `"sanity": "FAIL"` on the aborted file.
- Resumed with `jl resume 548606 --yes --json` at 2026-10-26T23:41:06Z. New machine id **548710** and a **new IP 217.18.55.59** (was 151.185.52.24). `instance.json`: `{"machine_id": "548710", "started_at": "2026-10-26T23:41:06+00:00", "work": "/home/trace-deletion", "previous_hours": 1.02}`.
- SSH up 23:42:35Z. Checks: 2 x H100 (0 MiB used), 23 safetensors, vllm 0.15.0, 0 leftover servers, 107 GB free.
- Deadline guard (resume + 9000 s): `deadline guard active: pausing 548710 at Tue Oct 27 02:11:06 UTC 2026`. Session 2 log kept as `deadline_session2.log`.
- Uploaded `serve.sh`, `bringup.py`, `continue.py`, `status.py`; MD5 identical remote and local (serve 53a5f262..., bringup f80821e8..., continue 8b0cbc67..., status 3720030a...). Old sanity result renamed `sanity_attempt2.json` on the VM and locally.
- Bring-up attempt 1 started 23:43:20Z (log kept as `bringup_attempt1_fp8kv.log` / `.json` on the VM). Result: setting 1 (`bf16kv_flashmla`) started in 340 s; the short open-ended test PASSED (` Paris. It is a world-famous city...`, 21 tokens), the Hindi trace continuation FAILED: 2048 tokens, `' यह<pad><pad>...'` (1 real token, then `<pad>` for the rest), same signature as session 2. Setting 2 (`FLASH_ATTN_MLA`) exited with code 1 at start-up. Setting 3 (`TRITON_MLA`) was starting when the bring-up was stopped by hand at 23:50:32Z (about 7 minutes after it began).
- **Root cause of the "bf16" setting not being bf16:** `serve.log` for setting 1 contains `Using fp8 data type to store kv cache` although the server was started with `--kv-cache-dtype auto`. The checkpoint's `hf_quant_config.json` has `"kv_cache_quant_algo": "FP8"` (and `config.json` has a `kv_cache_scheme`), and vLLM's ModelOpt loader (`quantization/modelopt.py`, `kv_cache_quant_algo`) applies it when the KV dtype is `auto`. So all four ladder settings in attempt 1 used an FP8 KV cache, the same cache as session 2. The failure at setting 1 therefore does not test bf16 KV. vLLM 0.15 accepts an explicit `bfloat16` (`CacheDType = Literal["auto","bfloat16","fp8",...]`).
- Fix (a flag, allowed by the rules): `gpu/serve.sh` default `KV_DTYPE=${KV_DTYPE:-bfloat16}`; `gpu/bringup.py` all four settings changed from `"KV_DTYPE": "auto"` to `"KV_DTYPE": "bfloat16"`. Uploaded; MD5 local = remote (serve 2e4ba87a..., bringup dde152d6...). Leftover server killed (`kill -9`), GPUs 0 MiB. Bring-up attempt 2 started 23:51:32Z.

### Session 3 outcome: BRINGUP did not pass; VM 548710 paused 23:56:25Z

- Attempt 2 (explicit `bfloat16` KV cache), started 23:51:32Z:
  - Setting 1 `bf16kv_flashmla`: vLLM auto-selected `FLASH_ATTN_MLA` (backends offered: FLASH_ATTN_MLA, FLASHMLA, TRITON_MLA), KV cache 269,504 tokens, then the first forward pass failed with `RuntimeError: Unsupported data type of kv cache: bfloat16`, raised in `vllm/_custom_ops.py` `concat_and_cache_mla` (called from `vllm/model_executor/layers/attention/mla_attention.py` line 2010). Server exited with code 1 after about 80 s.
  - Setting 2 `bf16kv_flashattn_mla`: same error, server exited with code 1.
  - Setting 3 `bf16kv_triton_mla`: `Using AttentionBackendEnum.TRITON_MLA backend`, KV cache 273,152 tokens, `/v1/models` answered after 60 s, but the first real request killed the engine with the same `Unsupported data type of kv cache: bfloat16` (`EngineDeadError`). `bringup.py` then crashed with `KeyError: 'choices'` (it does not handle an error response; the `except` covers only URLError/OSError/ValueError) and printed no `BRINGUP:` line (`EXIT=1`). Setting 4 (`--enforce-eager`) was never tried; it uses the same kernel.
  - Conclusion: in vLLM 0.15.0 an explicit `--kv-cache-dtype bfloat16` does not work for this MLA model on any of the three backends, because the shared kernel `concat_and_cache_mla` rejects the string `bfloat16`. `auto` follows the checkpoint's `kv_cache_quant_algo: FP8` and gives the FP8 cache that produced `<pad>` output in sessions 2 and 3 attempt 1.
- Candidate fixes (not tried): (A) edit the VM copy of the checkpoint metadata: `kv_cache_quant_algo` to null in `hf_quant_config.json` and remove `kv_cache_scheme` from `config.json` (back up first), then `--kv-cache-dtype auto` gives the model dtype (bf16); (B) keep the FP8 cache with `--calculate-kv-scales` (option exists in `vllm/config/cache.py`; MLA support unknown).
- The log download at the end of the session FAILED (my `scp` call quoted the file list as one path), and the VM was paused anyway to stop billing. Still on the VM disk in `/home/trace-deletion/`: `bringup.log`, `bringup.json` (attempt 2), `bringup_attempt1_fp8kv.log` / `.json`, `serve.log` (about 1,800 lines, all attempts), `deadline.log`, `deadline_session2.log`. Download them at the next resume.
- Cost: session 3 ran 23:41:06Z to 23:56:25Z = 0.255 h (about 169 INR). Sessions 1 to 3 total about 1.275 h (about 843 INR). The pause stopped the deadline guard (it was set for 02:11:06Z).

## Probe (19:21Z)

- `ubuntu` (uid 1000), passwordless sudo works. Ubuntu 22.04.5 LTS, Python 3.10.12, `venv` available, `wget` and `curl` present.
- **pip missing** (`No module named pip`).
- `nvidia-smi`: 2 x NVIDIA H100 80GB HBM3 (81559 MiB each), driver 580.126.20, CUDA 13.0.
- Disk: `/dev/vda1` 243G mounted at `/` (227G free); `/home` is on the same disk, so no symlinks were needed. `/home` is root-owned.

## Environment fixes (no change to continue.py, decoding settings or requests)

- Installed pip with `sudo apt-get install -y python3-pip` (pip 22.0.2). Reason: the image has no pip.
- Created `/home/trace-deletion` and `/home/models` with `sudo mkdir -p` and `sudo chown -R ubuntu:`. Reason: `/home` is not writable by `ubuntu`; the scripts and monitor use these absolute paths.
- `gpu/setup.sh` and `gpu/serve.sh`: added `export PATH="$HOME/.local/bin:$PATH"` after `set -euo pipefail`. Reason: as a non-root user pip installs to `~/.local`, so `hf`/`huggingface-cli` (setup.sh) and `vllm` (serve.sh) would not be on PATH in a fresh shell.
- Setup finished at about 19:38Z: `105G`, `vllm 0.15.0`, `PATCH_OK`, `23`, `SETUP_DONE`. Torch check: `2.9.1+cu128 12.8 True 2`. Server started 19:40Z.
- `gpu/serve.sh`: added `--block-size 64`. Reason: the first start (log kept as `serve_attempt1.log`) crashed at 19:41Z with `ValueError: No common block size for 16`. vLLM picked the FLASHMLA attention backend (`Using FLASHMLA attention backend out of potential backends: ('FLASHMLA',)`), which only supports KV-cache blocks of 64 tokens, while the KV manager defaulted to 16. Block size changes only the KV-cache memory layout, not the decoding settings. Restarted 19:42:48Z.
- Server ready 19:44Z (`/v1/models` lists `sarvam-105b-fp8`).
- Sanity 19:45Z: **SANITY: FAIL**. Split-word continuation PASS ('us.'); English A continuations PASS (0 of 4 restarted); **fresh answers FAIL**: both fresh answers (`add_generation_prompt=true`, `enable_thinking=false`) returned the content `<think>` and nothing else. Same request twice identical: 0/8 (informational). Downloaded `outputs/selfhost/sanity.json`; paused the VM with `jl pause 548505 --yes` at 19:50:24Z, as the instructions require on FAIL. Runtime about 0.65 h (19:11:29Z to 19:50:24Z), about ₹429. The pause stopped the deadline guard process; it must be restarted if the VM is resumed.
- Deadline guard launched with `PATH=$HOME/.local/bin:$PATH` in its environment (not a change to `deadline.sh`), for the same reason: `deadline.sh` pip-installs `jl` and then calls it. `deadline.log`: `deadline guard active: pausing 548505 at Mon Oct 26 23:41:29 UTC 2026` (start + 16200 s).

## Session 4 (final attempt)
- 2026-10-27T12:27:55Z: resumed VM (old id 548710) after waiting ~1.5 h for 2 free H100 VMs in IN2. NEW machine id 549870, IP 217.18.55.174. previous_hours 1.275.
- Budget: 2.5 h max (deadline guard at resume + 9000 s = 14:57:55Z). 90-minute bring-up limit = 13:57:55Z.
- 12:53:30Z SSH finally answered (26 min after resume, about 290 INR spent waiting). 2 H100s, 23 safetensors, no server. Session 3 logs downloaded to `outputs/selfhost/logs/session3/`, renamed `*_session3.*` on the VM. Deadline guard active (14:57:55Z). All uploads MD5-matched.
- Install: first attempt failed on `Permission denied: /home/venv031` (/home is root-owned) -> `sudo mkdir /home/venv031 && sudo chown ubuntu` -> second attempt `PATCH_LOADER_OK`, vllm 0.31.0 | torch 2.13.0+cu130 | gpus 2, EXIT=0 in about 2 min. pip freeze saved.
- Bring-up run 1 (13:04-13:08Z): settings 1 and 2 died with `FileNotFoundError: 'ninja'` (flashinfer JIT of trtllm_mnnvl_comm; venv bin and nvcc not on PATH). Setting 3 (0.15 + metadata edit, bf16 KV via auto): Paris PASS, Hindi A PASS (97 tok), English A FAIL (2048 tok repetition loop, no Answer). My polling loop also repeated stale lines for ~3 min.
- Fix: `serve031.sh` now exports `PATH=$VENV/bin:/usr/local/cuda/bin:$PATH` and `CUDA_HOME=/usr/local/cuda`. Bring-up run 2 (13:14-13:19Z), 0.31 only: setting 1 (default backend) Paris PASS, Hindi A FAIL (2048 tok loop "= 2026-07-24 + 08"); setting 2 (TRITON_MLA) Paris, Hindi A (143 tok), English A (289 tok) PASS; longest prefix (5250 chars) FAIL: 2048 tok, no Answer, no garbage tokens.
- Sanity on 0.31 TRITON_MLA (13:24Z): request 3 of 27 (`very_long/date_addition_hi_IN/44/similar_insertion/cot/A`) hit 4096 tokens without an Answer, text coherent Hindi but nonsense arithmetic -> `SANITY: FAIL`, EXIT=4. `outputs/selfhost_s4/sanity.json`.
- Paused VM 549870 at 13:25:01Z. Session 4 runtime 12:27:55-13:25:01 = 0.95 h (about 630 INR). Sessions 1-4 about 2.22 h (about 1,470 INR). Model metadata backups (`*.orig_session4`) and all logs remain on the VM disk.

## Session 5 (pre-boot only, no VM started)
- `check_redhat.py`: CHECK REDHAT: FAIL on 4 items. (1) shard total 112,662,325,736 B vs EXPECTED 109,762,325,736 in `download_rh.sh` (2.9 GB off; Sarvam's own FP8 is 112,528,239,472 B). (2) `special_tokens_map.json` and (3) `tokenizer_config.json` differ only in pad_token (`<pad>` vs `<|end_of_turn|>`). (4) `generation_config.json` differs only in transformers_version (4.56.2 vs 4.57.2). All other checks PASS (sarvam_mla, compressed-tensors, no KV quant, per-token dynamic activations, no static input scales, same architecture).
- User chose to stop and report; nothing was changed. Syntax check passed. VM 549870 stays paused (disk only). IN2 H100 VM had 4 free at check time; L4 VM 0 free; `jl resume` CPU options (--vcpus/--ram) apply to CPU VMs only.

## Session 5 run
- 2026-10-27T14:06:36Z: resumed paused VM 549870 directly on 2 x H100 (user chose to skip the cheap-machine phase and to go from download straight into phase 2 without pausing). NEW machine id 549976, IP 217.18.55.104. previous_hours 2.22. Check redhat: PASS after the user's script fixes (EXPECTED_BYTES 112662325736).
- Download phase (2 x H100, 14:06:36Z-14:40:19Z = 0.56 h, about 371 INR): DOWNLOAD_DONE, EXIT=0, 23 shards, 112,662,325,736 bytes matched. hf speed bursty (150 MB/s early, stalls of 2-3 min later). Old Sarvam FP8 weights deleted (user-approved). Went straight into phase 2 (no pause). instance.json: previous_hours 2.78, phase experiment, started 14:40:19Z.
- Phase 2 (14:40:19Z-14:50:07Z): deadline guard first restarted wrongly (my `pkill -f '[d]eadline.sh'` matched the ssh shell itself and killed the old guard too; restarted correctly at 14:41, active for 17:10:19Z). Uploads MD5-matched. Bring-up: `redhat_v031_default` smoke FAIL (longest prefix 2048 tok loop); `redhat_v031_triton_mla` smoke PASS on all 5 (longest prefix 1208 tok, stop) but CALIBRATION FAIL: finished 82/90 (needs 95%), accuracy self 63.3% vs API 73.3% (self-only correct 9, API-only 18, McNemar p=0.122), en_US 66.7% vs 84.4% (FAIL, limit 15 pts), hi_IN 60.0% vs 62.2% (PASS). 8 unfinished (4096 tok, 6 en_US, 2 hi_IN). BRINGUP: FAIL -> downloaded logs to outputs/selfhost/logs/session5/, calibration json to outputs/selfhost_s5/. Paused VM 549976 at 14:50:07Z.
- Cost session 5: 14:06:36Z-14:50:07Z = 0.725 h (about 479 INR). Sessions 1-5 about 2.95 h (about 1,950 INR). GPU work ends here per instructions. VM not destroyed; Red Hat weights (113 GB) and venv on its disk.

## Session 6 (G greedy then S sampling, one server)
- Pre-boot OK; balance ₹3,821.68. Resumed 549976 on 2xH100 (IN2) at 2026-10-27T22:06:21Z -> new machine id 550501, ip 217.18.55.160. previous_hours 2.95.
- Session 6 run 22:06:21Z-23:26:03Z = 1.328 h (about INR 878; Jarvislabs grants 3,821.68 -> 2,923.99). Sessions 1-6 about 4.28 h (about INR 2,830). Machine id changed to 550501 on resume; paused (not destroyed) at 23:26:03Z, all files downloaded and counted first.
- Server up in 240 s (redhat_v031_triton_mla, no smoke). Deadline guard (resume+14400 s) was active throughout.
- G greedy (T0, top-p 1, 12,288): calibration finished 81/90, self 67.8% vs API 73.3% (p=0.405), en 73.3% vs 84.4%, hi 62.2% vs 62.2%; sanity PASS (5/6 continuations reach Answer, 1 runaway); main 702 done, 99 without Answer line (14.1%), 102 cut off; repeat 234 done, identical text 22/234, same answer 123/234.
- S sampling (T0.8, top-p 0.95, 12,288): calibration PASS finished 89/90, self 71.1% vs API 73.3% (p=0.839), en 82.2% vs 84.4%, hi 60.0% vs 62.2%; main 702 done, 37 without Answer line (5.3%), 40 cut off; repeat 234 done, identical text 10/234, same answer 100/234.
- Two BAD OUTPUT flags in G main (097: ' \n\nAnswer: 0', 377: 'Answer: 2030-11-13') and one in S main (099) were false positives of the under-20-chars heuristic (valid Answer-only continuations); I did not pause on them.
- Outputs: outputs/selfhost_s6/{selfhost_G,selfhost_S,selfhost,logs}.
