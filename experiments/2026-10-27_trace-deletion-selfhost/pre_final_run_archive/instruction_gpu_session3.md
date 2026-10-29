# Instructions for Claude Code: session 3 (fix the garbage output, then run)

## What went wrong in session 2, and the fix

Every generation produced one correct token, then 4,095 invisible tokens.
- The first token comes from vLLM's prefill path (FlashAttention).
- Every later token comes from the FlashMLA decode kernel, which reads the KV cache.
- `serve.sh` stored that cache in FP8 (`--kv-cache-dtype fp8`), but the checkpoint has no KV-cache scale tensors and Sarvam's model code loads none. vLLM therefore used a scale of 1.0.
- MLA cache values outside the FP8 range (±448) become NaN. NaN logits make greedy decoding pick token 0 (`<pad>`) forever.
- With FP8 KV, FlashMLA was also the only backend allowed (log: `potential backends: ('FLASHMLA',)`).

The fix:
- **KV cache:** `serve.sh` now uses `--kv-cache-dtype auto` (bf16).
- **Server bring-up:** `gpu/bringup.py` tries a fixed ladder of server settings, from first to last:
  - bf16 KV + FlashMLA;
  - bf16 KV + FLASH_ATTN_MLA;
  - bf16 KV + TRITON_MLA;
  - TRITON_MLA with `--enforce-eager`.

  For each setting it waits for the server, then runs short smoke tests that take seconds. It keeps the first setting that produces real text with an Answer line, and leaves that server running.
- **Garbage-output guard:** `gpu/continue.py` stops by itself (`DEGENERATE STOP`, exit code 4) if outputs are empty or hit the token limit without an answer. The sanity check no longer counts identical empty outputs as repeatable.

All rules in `instruction_gpu.md` still apply unless this file changes them. Local working directory for every local command:

```
cd ~/Documents/IIIT/sem5/ANLP/anlp_project/netherite-emr/experiments/2026-10-26_trace-deletion
```

## Budget

- Sessions 1 and 2 used about 1.02 h (about ₹671).
- This session may run at most **2.5 hours** from the resume (about ₹1,650):
  - the monitor runs with `--max-hours 2.5`;
  - the deadline guard pauses at resume + 9000 s.
- The one-at-a-time main + repeat run must project 120 minutes or less (`--budget-minutes 120`).
- Never resume the VM a second time in this session without the user's go-ahead.

## 0. Pre-boot checks (no VM, no credits)

1. Check the real Sarvam tokenizer and chat template on this Mac. This renders the exact prompts vLLM will build:

   ```
   python3 -m venv /tmp/tc && /tmp/tc/bin/pip install -q "transformers>=4.57" jinja2 huggingface_hub
   /tmp/tc/bin/python gpu/template_check.py
   ```

   - It must end with `TEMPLATE CHECK: PASS`. Hindi A, B, C, English A and the open-ended case must all be PASS. The "fresh" case is informational.
   - If anything is FAIL, stop and report the full output to the user. Do not boot.
2. Check script syntax:

   ```
   bash -n gpu/serve.sh && python3 -m py_compile gpu/bringup.py gpu/continue.py gpu/status.py gpu/monitor.py && echo SYNTAX_OK
   ```

3. Show the user both outputs and ask: "Pre-boot checks passed. Resume the VM now?" Wait for yes.

## 1. Resume and check

1. Run `jl resume 548606 --yes --json`. Use the returned machine id from now on.
2. Update `gpu/instance.json`:
   - `machine_id`;
   - `started_at` = the resume time in UTC ISO;
   - `"previous_hours": 1.02`.

   Record the resume in `gpu/NOTES.md`.
3. When SSH answers, check:
   - `nvidia-smi` shows 2 H100s;
   - there are 23 `.safetensors` files in `/home/models/sarvam-105b-fp8`;
   - vLLM is 0.15.0 (with `PATH=$HOME/.local/bin:$PATH`);
   - `pgrep -af "vllm serve"` shows nothing. Kill any leftover server.

   If any check fails, pause and report.
4. Restart the deadline guard with deadline = resume + 9000 s, and confirm `deadline.log` says `deadline guard active`.
5. Tell the user to start the monitor in a separate Terminal window:

   ```
   cd ~/Documents/IIIT/sem5/ANLP/anlp_project/netherite-emr/experiments/2026-10-26_trace-deletion
   python3 gpu/monitor.py watch --max-hours 2.5
   ```

## 2. Upload the new files

```
jl upload <id> gpu/serve.sh /home/trace-deletion/serve.sh
jl upload <id> gpu/bringup.py /home/trace-deletion/bringup.py
jl upload <id> gpu/continue.py /home/trace-deletion/continue.py
jl upload <id> gpu/status.py /home/trace-deletion/status.py
jl exec <id> -- bash -lc 'cd /home/trace-deletion && md5sum serve.sh bringup.py continue.py status.py && mv selfhost/sanity.json selfhost/sanity_attempt2.json'
md5sum gpu/serve.sh gpu/bringup.py gpu/continue.py gpu/status.py 2>/dev/null || md5 gpu/serve.sh gpu/bringup.py gpu/continue.py gpu/status.py
mv outputs/selfhost/sanity.json outputs/selfhost/sanity_attempt2.json
```

The remote and local checksums must match.

## 3. Bring-up (about 5 to 25 minutes)

```
jl exec <id> -- bash -lc 'cd /home/trace-deletion && nohup bash -c "python3 bringup.py; echo EXIT=\$?" > bringup.log 2>&1 &'
```

Poll `bringup.log` every 2 minutes. Each setting prints its server start, then one line per smoke test.

- **`BRINGUP: PASS <setting>`:** the server is running with that setting. Note the setting in `gpu/NOTES.md` and continue.
- **`BRINGUP: FAIL`:**
  1. Download `bringup.json`, `bringup.log`, and the last 400 lines of `serve.log`.
  2. Pause the VM.
  3. Report to the user and tell them to go back to the Claude chat. Try nothing else.

## 4. Sanity check (about 3 to 8 minutes)

```
jl exec <id> -- bash -lc 'cd /home/trace-deletion && nohup bash -c "python3 continue.py --mode sanity; echo EXIT=\$?" > sanity.log 2>&1 &'
```

Poll until `sanity.log` has `SANITY:` and `EXIT=`. Show the user the full output. Then:

- **`SANITY: FAIL`:** download `selfhost/` and the logs, pause the VM, and report.
- **`SANITY: PASS`:** go to step 5 using the printed `MODE:`.

## 5. Main run

- **`MODE: sequential`:**

  ```
  jl exec <id> -- bash -lc 'cd /home/trace-deletion && nohup bash -c "python3 continue.py --mode main --concurrency 1 --budget-minutes 120; echo EXIT=\$?" > main.log 2>&1 &'
  ```

- **`MODE: batched`:**

  ```
  jl exec <id> -- bash -lc 'cd /home/trace-deletion && nohup bash -c "python3 continue.py --mode main --concurrency 32 --out selfhost_batched; echo EXIT=\$?" > main_batched.log 2>&1 &'
  ```

Every 5 minutes, show the user the last progress line (seconds per request, projected minutes). When `EXIT=` appears:

- **`EXIT=0`:** go to step 6.
- **`EXIT=3`** (`BUDGET STOP`, only in sequential mode): start the batched command above on the same VM. Do not pause. Keep the partial `selfhost/` results.
- **`EXIT=4`** (`DEGENERATE STOP`): download everything, pause the VM, and report. Do not switch modes.
- **Anything else:** rerun the same command once (it resumes). If it fails again, download, pause, and report.

## 6. Repeat run

Use the same mode as the finished main run:

```
jl exec <id> -- bash -lc 'cd /home/trace-deletion && nohup bash -c "python3 continue.py --mode repeat --concurrency 1; echo EXIT=\$?" > repeat.log 2>&1 &'
```

For batched mode, use `--concurrency 32 --out selfhost_batched` instead, writing to `repeat_batched.log`. Handle `EXIT=` codes as in step 5. A `DEGENERATE STOP` here means: download, pause, report.

## 7. Download, check, destroy

```
mkdir -p outputs/selfhost/logs
jl download <id> /home/trace-deletion/selfhost outputs -r
jl download <id> /home/trace-deletion/selfhost_batched outputs -r
jl exec <id> -- bash -lc 'cd /home/trace-deletion && tail -n 400 serve.log > serve_tail.log && python3 -m pip freeze > pip_freeze.txt'
for f in bringup.json bringup.log sanity.log serve_tail.log main.log repeat.log main_batched.log repeat_batched.log deadline.log pip_freeze.txt; do jl download <id> /home/trace-deletion/$f outputs/selfhost/logs/$f; done
```

- Missing optional files are fine.
- Fix any nested folders.
- Before destroying, check that the finished run folder has 702 results and 234 repeats, and that `sanity.json` and `bringup.json` exist.

Then run `jl destroy <id> --yes` and `jl list`. Record the hours and cost of all three sessions in `gpu/NOTES.md`.

## 8. Analysis and report

Run `python3 analyze.py --output outputs/selfhost`, or with `outputs/selfhost_batched` for a batched run, or both if both are complete.

Tell the user:
- the template check result;
- the bring-up result (which setting passed);
- the sanity output and the mode used;
- the speed;
- the hours and cost of all sessions;
- the `done:` lines;
- the "By language" table and the "Repeatability" line.

Then tell them to go back to the Claude chat.
