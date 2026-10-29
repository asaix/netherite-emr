# Instructions for Claude Code: session 5 (Red Hat checkpoint, cheap download, calibration gate)

## What and why

- **What session 4 showed:**
  - The bf16 KV cache fixed the garbage tokens.
  - But Sarvam's own FP8 checkpoint (`sarvamai/sarvam-105b-fp8`) on vLLM 0.31 reasoned badly on long traces: wrong months, absurd sums, loops to 4096 tokens. The API never did this.
  - Suspected cause: that checkpoint's fixed per-expert activation scales, which vLLM collapses to the per-layer maximum.
- **This session switches checkpoints** to Red Hat's FP8-dynamic quantization of the same Sarvam-105B (`RedHatAI/sarvam-105b-FP8-dynamic`):
  - weights per channel;
  - activations computed per token on the fly;
  - KV cache not quantized;
  - validated by Red Hat on vLLM at 99–101% of the original's accuracy (GSM8K 85.4 vs 84.4).
- **Everything else from session 4 is unchanged:**
  - vLLM 0.31 is already installed in `/home/venv031` on the VM disk;
  - the same continuation requests and the same scripts;
  - only `serve_rh.sh` differs: it points at the new model folder and drops `--quantization modelopt`.
- **New calibration gate.** After the smoke test, bring-up asks 90 no-distractor questions (one per language × task × difficulty, `calibration_requests.json`) and compares with the API's answers to the same questions. A setting is accepted only if all of these hold:
  - at least 95% of answers finish (Answer line, normal stop, no loop);
  - overall accuracy is no more than 10 points below the API's;
  - each language is no more than 15 points below the API's.
- **Cost saving (the user's instruction).** Download the 113 GB weights on the cheapest machine available, pause, then resume on 2 x H100 for the experiment.

All rules in `instruction_gpu.md` and the live-output and abort rules in `instruction_gpu_session4.md` still apply:
- `python3 -u`;
- poll every 30–60 s and show every new line;
- pause immediately on `BAD OUTPUT`, `STOP`, `SANITY: FAIL`, or a `Traceback` outside bring-up.

Local working directory for every local command:

```
cd ~/Documents/IIIT/sem5/ANLP/anlp_project/netherite-emr/experiments/2026-10-26_trace-deletion
```

## 0. Pre-boot checks (no VM, no credits)

1. Run `python3 gpu/preboot/check_redhat.py` and show the user the full output. It must end with `CHECK REDHAT: PASS`. It confirms:
   - the files are public: 23 shards, about 113 GB;
   - the chat template, tokenizer, special tokens, config code and generation config are byte-identical to Sarvam's;
   - `tokenizer_config.json` differs only in non-functional keys (it lists them);
   - it is `sarvam_mla` / `SarvamMLAForCausalLM`, in compressed-tensors format, with per-token dynamic activations;
   - there is no KV-cache quantization and no static input scales;
   - the architecture settings match Sarvam's;
   - the tensor-name patterns.

   If anything is FAIL, stop and report.
2. Check syntax:

   ```
   bash -n gpu/download_rh.sh && bash -n gpu/serve_rh.sh && python3 -m py_compile gpu/bringup.py gpu/continue.py gpu/status.py gpu/monitor.py && echo SYNTAX_OK
   ```

3. Find out how to resume on a different machine. Run `jl resume --help`, and check live availability in IN2, as in session 4. Write down, with the exact flags and the hourly price:
   - **A:** the cheapest option that can resume this VM's disk in IN2. Prefer a CPU-only VM, then L4 (about ₹41/h), then 1 x H100 (about ₹330/h).
   - **B:** whether 2 x H100 VMs are free right now.

   If `jl resume` cannot change the GPU type or count at all, say so. The download then happens on 2 x H100 at the start of phase 2.
4. Show the user the results of steps 1 to 3, the planned machine for the download, and its price. Ask: "Pre-boot checks passed. Start the download phase on <machine> at ₹<price>/h?" Wait for yes.

## Phase 1: download on the cheap machine (about 25 to 40 minutes)

1. Resume on machine A, e.g. `jl resume 549870 --yes --json` plus the flags for the cheap machine. Use the returned machine id from now on.
2. Write `gpu/instance.json`:
   - `machine_id`;
   - `started_at` = now in UTC ISO;
   - `"previous_hours": 2.22`;
   - `"phase": "download"`;
   - `"rate_inr_per_hour": <price>`.

   Record it in `gpu/NOTES.md`.
3. Tell the user to start the monitor with the cheap rate: `python3 gpu/monitor.py watch --rate <price> --max-hours 1 --interval 30`.
4. When SSH answers, check `df -h /home` and that `/home/models/sarvam-105b-fp8` and `/home/venv031/bin/hf` exist. If `hf` is missing, use `~/.local/bin/hf`, and note it.
5. Upload the scripts:

   ```
   jl upload <id> gpu/download_rh.sh /home/trace-deletion/download_rh.sh
   jl upload <id> gpu/status.py /home/trace-deletion/status.py
   ```

6. Start the download:

   ```
   jl exec <id> -- bash -lc 'cd /home/trace-deletion && nohup bash -c "bash download_rh.sh; echo EXIT=\$?" > download_rh.log 2>&1 &'
   ```

   - It first deletes the old FP8 weights (about 105 GB), which is needed for space and was approved by the user.
   - It prints the downloaded size every 30 seconds, then verifies 23 shards and the exact byte count (112,662,325,736).
   - Poll every 60 seconds and show every new line.
7. **Success** (`DOWNLOAD_DONE` and `EXIT=0`): pause immediately with `jl pause <id> --yes`. Record the phase-1 hours and cost in `gpu/NOTES.md`.
8. **Failure** (`EXIT` not 0): run the same command once more; `hf` resumes partial files. If it fails again, download `download_rh.log`, pause, and report.

## Phase 2: the experiment on 2 x H100

1. Check that 2 x H100 VMs are free in IN2.
   - If none are, tell the user and wait while paused (only storage is billed). Check every 10 minutes.
   - If none have appeared after 60 minutes, ask the user whether to keep waiting.
2. Resume with 2 x H100 (`jl resume <id> --yes --json` plus the H100 and 2-GPU flags). Update `gpu/instance.json`:
   - `machine_id`;
   - `started_at` = the resume time;
   - add the phase-1 hours to `previous_hours`;
   - `"phase": "experiment"`;
   - `"rate_inr_per_hour": 661`.
3. When SSH answers, check:
   - `nvidia-smi` shows 2 H100s;
   - there are 23 shards in `/home/models/sarvam-105b-fp8-dynamic`;
   - `/home/venv031/bin/python -c "import vllm; print(vllm.__version__)"` prints 0.31.0;
   - `pgrep -af "vllm serve"` is empty.
4. Restart the deadline guard (resume + 9000 s) and confirm `deadline guard active`. Tell the user to restart the monitor:

   ```
   python3 gpu/monitor.py watch --max-hours 2.5 --interval 20
   ```

5. Archive the session 4 files on the VM, then upload:

   ```
   jl exec <id> -- bash -lc 'cd /home/trace-deletion && for f in bringup.log bringup.json serve.log sanity.log; do [ -f $f ] && mv $f ${f%.*}_session4.${f##*.}; done; [ -d selfhost ] && mv selfhost selfhost_session4; true'
   for f in serve_rh.sh bringup.py continue.py status.py; do jl upload <id> gpu/$f /home/trace-deletion/$f; done
   jl upload <id> outputs/calibration_requests.json /home/trace-deletion/calibration_requests.json
   jl upload <id> outputs/requests_cap1000.json /home/trace-deletion/requests_cap1000.json
   ```

   Compare the MD5s with the local files.
6. **Bring-up with the calibration gate** (about 10 to 25 minutes):

   ```
   jl exec <id> -- bash -lc 'cd /home/trace-deletion && nohup bash -c "python3 -u bringup.py; echo EXIT=\$?" > bringup.log 2>&1 &'
   ```

   - It tries `redhat_v031_default`, then `redhat_v031_triton_mla`.
   - For each it shows: server heartbeats, then the smoke tests, then 90 calibration lines (`[cal NN/90] ... | answer | gold | correct/wrong | API correct/wrong`), then the calibration result with PASS/FAIL per check.
   - Poll every 30–60 s and show every new line.
   - **`BRINGUP: PASS <setting>`:** note it, together with the calibration summary line, and continue.
   - **`BRINGUP: FAIL`, or no PASS within 75 minutes of the resume:**
     1. Download `bringup.log`, `bringup.json`, `selfhost/calibration_*.json` and the last 600 lines of `serve.log`.
     2. Pause the VM.
     3. Report. **The GPU work then ends.**
7. **Sanity, main run, repeat run:** exactly as step 5 of `instruction_gpu_session4.md`. That covers:
   - sanity, then `MODE: sequential` (`--concurrency 1 --budget-minutes 120`) or batched;
   - `EXIT=3`: switch to batched on the same VM;
   - `EXIT=4` or `EXIT=5`: download, pause, report;
   - every request printed.
8. **Download, check, destroy:** step 7 of `instruction_gpu_session3.md`. Also download:
   - `selfhost/calibration_*.json`;
   - `download_rh.log`;
   - `pip_freeze_venv031.txt` (create it first with `/home/venv031/bin/python -m pip freeze`).

   Check the counts (702 results, 234 repeats). Then destroy the VM and record the hours and cost of every session and phase in `gpu/NOTES.md`.
9. **Report.** Run `python3 analyze.py --output outputs/selfhost` (or `selfhost_batched`). Tell the user:
   - the check result;
   - the download phase: machine, time and cost;
   - the bring-up setting;
   - **the calibration summary**: self vs API accuracy overall and per language, the finished count and McNemar p;
   - the sanity output and the mode;
   - the speed;
   - the hours and cost;
   - the `done:` lines;
   - the "By language" table and the "Repeatability" line.

   Then tell them to go back to the Claude chat.
