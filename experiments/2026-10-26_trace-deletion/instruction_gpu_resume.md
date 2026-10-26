# Instructions for Claude Code: resume the paused VM and run the experiment one request at a time

Context: the first attempt (see `gpu/NOTES.md`) set everything up on VM 548505. Its sanity check failed for two reasons.

1. Fresh answers came back as just `<think>`. In thinking-off mode Sarvam writes `<think></think>` before every answer. Our test did not pre-fill that, so the model opened a thinking block and stopped. The trace continuations already include it.
2. The same 8 requests sent together twice never gave identical text, because vLLM batching changes the arithmetic slightly.

The fixes:
- `gpu/continue.py` now pre-fills `<think></think>` for the fresh check.
- It checks that continuations reach an `Answer:` line.
- It tests repeatability with one request at a time.
- It can stop itself when the projected time goes over budget.

The user chose to run one request at a time. All rules in `instruction_gpu.md` still apply unless this file changes them.

Local working directory for every local command:

```
cd ~/Documents/IIIT/sem5/ANLP/anlp_project/netherite-emr/experiments/2026-10-26_trace-deletion
```

## Budget for this session

- The first session used about 0.65 h (about ₹429).
- This session may run at most 3 hours from the resume (about ₹1,980). That means:
  - the monitor runs with `--max-hours 3`;
  - the deadline guard pauses the VM at resume + 3.25 h.
- The one-at-a-time run gets a budget of 120 minutes for the main and repeat runs together. `continue.py` stops itself (`BUDGET STOP`, exit code 3) if its projection goes over. You then switch to batched mode on the same VM, as in step 7.

## 1. Resume the VM

1. Run `jl resume 548505 --yes --json`. The machine id may change, so use the one it returns from now on.
2. Update `gpu/instance.json`:
   - set `machine_id`;
   - set `started_at` to the resume time (UTC ISO);
   - add `"previous_hours": 0.65`.

   Keeping the old `started_at` would make the monitor count the paused hours and auto-pause immediately. Record the resume in `gpu/NOTES.md`.
3. Wait until SSH answers. Last time this took about 10 minutes.
4. Check the machine:
   - `jl exec <id> -- nvidia-smi` shows 2 H100.
   - `jl exec <id> -- bash -lc 'ls /home/models/sarvam-105b-fp8/*.safetensors | wc -l'` prints 23.
   - `jl exec <id> -- bash -lc 'export PATH=$HOME/.local/bin:$PATH; python3 -c "import vllm; print(vllm.__version__)"'` prints 0.15.0.

   If any of these fail, pause the VM and report.

## 2. Re-arm the safety switches

1. Restart the deadline guard with deadline = resume time + 11700 seconds, as a Unix timestamp. Use the same command as before, with `PATH=$HOME/.local/bin:$PATH` in its environment. Confirm that `deadline.log` says `deadline guard active`.
2. Tell the user to start the monitor again in a separate Terminal window. The old one exited when the VM paused.

   ```
   cd ~/Documents/IIIT/sem5/ANLP/anlp_project/netherite-emr/experiments/2026-10-26_trace-deletion
   python3 gpu/monitor.py watch --max-hours 3
   ```

## 3. Upload the new scripts and keep the old sanity result

```
jl upload <id> gpu/continue.py /home/trace-deletion/continue.py
jl upload <id> gpu/status.py /home/trace-deletion/status.py
jl exec <id> -- bash -lc 'cd /home/trace-deletion/selfhost && mv sanity.json sanity_attempt1.json'
mv outputs/selfhost/sanity.json outputs/selfhost/sanity_attempt1.json
```

## 4. Start the server

```
jl exec <id> -- bash -lc 'cd /home/trace-deletion && nohup bash serve.sh > serve.log 2>&1 &'
```

Poll every 2 minutes until `curl -s localhost:3002/v1/models` lists `sarvam-105b-fp8`. `serve.sh` already has `--block-size 64`.

## 5. Sanity check (about 5 to 10 minutes; it runs one request at a time)

```
jl exec <id> -- bash -lc 'cd /home/trace-deletion && python3 continue.py --mode sanity'
```

Show the user the full output. Then:

- **`SANITY: FAIL`:**
  1. Download `/home/trace-deletion/selfhost` into `outputs`.
  2. Pause the VM.
  3. Report, and tell the user to go back to the Claude chat.
- **`SANITY: PASS` and `MODE: sequential`** (one-at-a-time requests repeat): go to step 6.
- **`SANITY: PASS` and `MODE: batched`** (even one at a time does not repeat, so it gains nothing): tell the user, then go straight to step 7.

## 6. One request at a time (the user's choice)

```
jl exec <id> -- bash -lc 'cd /home/trace-deletion && nohup python3 continue.py --mode main --concurrency 1 --budget-minutes 120 > main.log 2>&1 &'
```

1. Every 5 minutes, show the user the last progress line of `main.log`. It gives the seconds per request and the projected minutes for the main and repeat runs.
2. If `main.log` contains `BUDGET STOP`, the run has stopped itself. Tell the user the measured speed and the projection, then go to step 7 on the same VM without pausing. Pausing and resuming would add about 15 billed minutes for boot and model reload. The partial one-at-a-time results stay in `selfhost/` and are kept.
3. When `main.log` has a `done:` line, run the repeat:

   ```
   jl exec <id> -- bash -lc 'cd /home/trace-deletion && nohup python3 continue.py --mode repeat --concurrency 1 > repeat.log 2>&1 &'
   ```

   Poll until `done:`. Then go to step 8.

## 7. Option 2: batched (only after `BUDGET STOP` or `MODE: batched`)

```
jl exec <id> -- bash -lc 'cd /home/trace-deletion && nohup python3 continue.py --mode main --concurrency 32 --out selfhost_batched > main_batched.log 2>&1 &'
```

Poll until `done:`. Then run:

```
jl exec <id> -- bash -lc 'cd /home/trace-deletion && nohup python3 continue.py --mode repeat --concurrency 32 --out selfhost_batched > repeat_batched.log 2>&1 &'
```

Poll until `done:`. The repeat line reports how often the batched answers repeat, which the paper reports.

## 8. Download, check, destroy

```
mkdir -p outputs/selfhost/logs
jl download <id> /home/trace-deletion/selfhost outputs -r
jl download <id> /home/trace-deletion/selfhost_batched outputs -r
jl exec <id> -- bash -lc 'cd /home/trace-deletion && tail -n 300 serve.log > serve_tail.log && python3 -m pip freeze > pip_freeze.txt'
for f in serve_tail.log main.log repeat.log main_batched.log repeat_batched.log deadline.log pip_freeze.txt; do jl download <id> /home/trace-deletion/$f outputs/selfhost/logs/$f; done
```

- The second download fails harmlessly if `selfhost_batched` does not exist, and some logs will not exist either.
- Fix any nested `selfhost/selfhost` folders.
- Before destroying, check that the completed run folder has 702 results and 234 repeats, and that `sanity.json` exists.

Then:

```
jl destroy <id> --yes
jl list
```

In `gpu/NOTES.md`, record the hours and cost of both sessions.

## 9. Analysis and report

Run `python3 analyze.py --output outputs/selfhost` for the one-at-a-time run. Run it with `outputs/selfhost_batched` too if that folder exists.

Tell the user:
- the sanity output;
- the mode used;
- the speed;
- the hours and cost of both sessions;
- the `done:` lines;
- the "By language" table and the "Repeatability" line for each run.

Then tell them to go back to the Claude chat.
