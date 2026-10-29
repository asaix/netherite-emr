# Instructions for Claude Code: session 4 (final attempt)

## Why this session exists

- **Sessions 1–3 failed because of the KV cache.** The FP8 KV cache produced garbage (one real token, then `<pad>`).
- **vLLM 0.15 cannot avoid it for this checkpoint:**
  - `auto` follows the checkpoint's `kv_cache_quant_algo: FP8`.
  - `bfloat16` crashes in the cache kernel.
- **This session:**
  - installs vLLM 0.31.0, which supports Sarvam natively and accepts `--kv-cache-dtype bfloat16`, in a separate virtual environment at `/home/venv031`;
  - keeps vLLM 0.15 plus a metadata edit as the fallback.
- **The bring-up ladder tries three settings:**
  - 0.31 with bf16 KV;
  - 0.31 with bf16 KV and TRITON_MLA;
  - 0.15 with the KV-cache FP8 tag removed from the model's `config.json`/`hf_quant_config.json`, so `auto` gives bf16.

  It keeps the first setting that passes a strict smoke test:
  - long prompts, including the longest trace prefix;
  - outputs spanning many 64-token blocks;
  - fail on `<pad>`, NaN log-probabilities, a token repeated 20+ times, a missing Answer line, or an error response.
- **This is the last GPU attempt.** If bring-up fails, the GPU work stops for good.

All rules in `instruction_gpu.md` still apply unless this file changes them. Local working directory for every local command:

```
cd ~/Documents/IIIT/sem5/ANLP/anlp_project/netherite-emr/experiments/2026-10-26_trace-deletion
```

## Live output and abort rules (the user's requirement)

- **Every script prints each step as it happens:**
  - `setup031.sh`: timestamped steps and pip's output.
  - `bringup.py`: a heartbeat every 30 s with the latest `serve.log` line while the server starts, `running: <test>` before each smoke test, and a result line after it.
  - `continue.py`:
    - sanity: one line per request;
    - main and repeat: one line per request (`[main 001/702] id | finish | tokens | seconds | answer | gold | correct/wrong | chars`).
- **Unbuffered output.** Run every Python script with `python3 -u` (or `PYTHONUNBUFFERED=1`) so lines reach the log file immediately.
- **Polling.** Poll the active log every 30–60 seconds. Show the user every new line since the last poll, not just the last few.
- **When to abort.** Pause the VM immediately (`jl pause <id> --yes`, or the user runs `python3 gpu/monitor.py kill`) and report if you see any of these:
  - a line containing `BAD OUTPUT`, `DEGENERATE STOP`, `ERROR STOP`, `SANITY: FAIL`, or `[FAIL]` on the last bring-up setting;
  - a `Traceback` in `setup031.log`.

  The one exception is a `[FAIL]` inside bring-up while settings remain: bring-up moves on by itself.
- **How the user can watch live in their own Terminal window:** `jl ssh <id>`, then `tail -F /home/trace-deletion/setup031.log /home/trace-deletion/bringup.log /home/trace-deletion/sanity.log /home/trace-deletion/main.log /home/trace-deletion/repeat.log`. Also `python3 gpu/monitor.py watch --max-hours 2.5 --interval 20`.

## Budget

- Sessions 1–3 used 1.275 h (about ₹843).
- This session may run at most **2.5 hours** from the resume (about ₹1,650):
  - monitor: `--max-hours 2.5`;
  - deadline guard: resume + 9000 s.
- **Internal limit:** if there is no `BRINGUP: PASS` within **90 minutes** of the resume, download everything, pause, and report.

## 0. Pre-boot checks (no VM, no credits)

1. Run `python3 gpu/preboot/check_checkpoint.py` and show the user the full output. The verdict must say `model_type/arch as vLLM 0.31 expects: YES`; if it says NO, stop and report. The loader patch is applied in every case. It only drops KV-scale tensors and layers beyond `num_hidden_layers`, which are unused with a bf16 cache.
2. Check syntax:

   ```
   bash -n gpu/setup031.sh && bash -n gpu/serve031.sh && bash -n gpu/serve.sh && python3 -m py_compile gpu/bringup.py gpu/continue.py gpu/status.py gpu/monitor.py gpu/fallback015_meta.py gpu/preboot/patch_sarvam_loader.py && echo SYNTAX_OK
   ```

3. Ask the user: "Pre-boot checks passed. Resume the VM for the final attempt?" Wait for yes.

## 1. Resume, collect session 3's logs, arm the safety switches

1. Run `jl resume 548710 --yes --json`. Use the returned machine id from now on.
2. Update `gpu/instance.json`:
   - `machine_id`;
   - `started_at` = the resume time in UTC ISO;
   - `"previous_hours": 1.275`.

   Record the resume in `gpu/NOTES.md`.
3. When SSH answers, check:
   - `nvidia-smi` shows 2 H100s;
   - 23 safetensors are present;
   - `pgrep -af "vllm serve"` is empty. Kill any leftover server.
4. **Download session 3's logs first** into `outputs/selfhost/logs/session3/`, one file per `jl download` call: `bringup.log`, `bringup.json`, `bringup_attempt1_fp8kv.log`, `bringup_attempt1_fp8kv.json`, `serve.log`, `deadline.log`. Then rename them on the VM:

   ```
   jl exec <id> -- bash -lc 'cd /home/trace-deletion && for f in bringup.log bringup.json serve.log; do [ -f $f ] && mv $f ${f%.*}_session3.${f##*.}; done; true'
   ```

5. Restart the deadline guard with deadline = resume + 9000 s, and confirm `deadline guard active`.
6. Tell the user to start the monitor in a separate Terminal window:

   ```
   cd ~/Documents/IIIT/sem5/ANLP/anlp_project/netherite-emr/experiments/2026-10-26_trace-deletion
   python3 gpu/monitor.py watch --max-hours 2.5 --interval 20
   ```

   For a live view of every log line in another Terminal window: `jl ssh <id>`, then `tail -F /home/trace-deletion/*.log`.

## 2. Upload

```
for f in setup031.sh serve031.sh fallback015_meta.py bringup.py status.py continue.py; do jl upload <id> gpu/$f /home/trace-deletion/$f; done
jl upload <id> gpu/preboot/patch_sarvam_loader.py /home/trace-deletion/patch_sarvam_loader.py
jl upload <id> gpu/preboot/vllm031-py310-lock.txt /home/trace-deletion/vllm031-py310-lock.txt
```

Compare the remote MD5s (`md5sum`) with the local ones (`md5`). They must match.

## 3. Install vLLM 0.31.0 (about 5 to 15 minutes)

```
jl exec <id> -- bash -lc 'cd /home/trace-deletion && nohup bash -c "bash setup031.sh; echo EXIT=\$?" > setup031.log 2>&1 &'
```

Poll `tail -n 5 setup031.log` every 2 minutes. Success looks like:
- `PATCH_LOADER_OK` (or `already patched`);
- a line `vllm 0.31.0 | torch 2.13.0 | ... | available True | gpus 2`;
- `SETUP031_DONE`;
- `EXIT=0`.

If it ends with `EXIT` not 0, or runs longer than 30 minutes:
- record the last 40 lines in `gpu/NOTES.md`;
- continue to step 4 anyway. The bring-up skips the 0.31 settings if `/home/venv031/bin/vllm` is missing, and a broken install fails fast and moves on to the fallback.

## 4. Bring-up (about 10 to 45 minutes; the first 0.31 start compiles and can take up to 25 minutes)

```
jl exec <id> -- bash -lc 'cd /home/trace-deletion && nohup bash -c "python3 -u bringup.py; echo EXIT=\$?" > bringup.log 2>&1 &'
```

Poll `bringup.log` every 2 minutes, and show the user each new smoke-test line.

- **`BRINGUP: PASS <setting>`:** record the setting in `gpu/NOTES.md`.
  - For a 0.31 setting, also run `jl exec <id> -- bash -lc '/home/venv031/bin/python -m pip freeze > /home/trace-deletion/pip_freeze_venv031.txt'`.
  - Then go to step 5.
- **`BRINGUP: FAIL`, or the 90-minute limit:**
  1. Download `bringup.log`, `bringup.json`, `setup031.log` and the last 600 lines of `serve.log`.
  2. Pause the VM.
  3. Report to the user and tell them to go back to the Claude chat. Do nothing else.

## 5. Sanity, main run, repeat run

Follow steps 4 to 6 of `instruction_gpu_session3.md`, with three changes:
- every `python3 continue.py` becomes `python3 -u continue.py`;
- poll every 30–60 seconds and show every new line;
- `EXIT=5` (`ERROR STOP`, the server stopped answering) is handled like `EXIT=4`: download, pause, report.

The rest of those steps is unchanged:
- sanity with `nohup` and `EXIT=`;
- then `MODE: sequential` (`--concurrency 1 --budget-minutes 120`) or `MODE: batched`;
- `EXIT=3`: switch to batched on the same VM;
- `EXIT=4`: download, pause, report;
- then the repeat run in the same mode.

## 6. Download, check, destroy

Follow step 7 of `instruction_gpu_session3.md`. Also download:
- `setup031.log`;
- `pip_freeze_venv031.txt` (if it exists);
- the backed-up model metadata, if the fallback was used: `/home/models/sarvam-105b-fp8/config.json.orig_session4` and `hf_quant_config.json.orig_session4`, plus the edited versions.

Check the counts (702 results, 234 repeats), then destroy the VM and record the hours and cost of all four sessions in `gpu/NOTES.md`.

## 7. Analysis and report

Run `python3 analyze.py --output outputs/selfhost`, or with `outputs/selfhost_batched` for a batched run.

Tell the user:
- the checkpoint check verdict;
- the install result;
- the bring-up setting that passed;
- the sanity output and the mode;
- the speed;
- the hours and cost;
- the `done:` lines;
- the "By language" table and the "Repeatability" line.

Then tell them to go back to the Claude chat.
