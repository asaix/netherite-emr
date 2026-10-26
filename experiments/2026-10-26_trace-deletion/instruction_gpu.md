# Instructions for Claude Code: self-hosted trace deletion on Jarvislabs

## Goal

Run the trace-deletion experiment on our own copy of Sarvam-105B (FP8 weights, `sarvamai/sarvam-105b-fp8`) on a Jarvislabs VM with 2 x H100, using vLLM 0.15.0 plus Sarvam's hot-patch. Each edited trace is truly continued, and decoding is repeatable.

Read `PLAN.md`, section "Self-hosted run", for what the experiment is. The team's Jarvislabs credits are limited, so follow every limit below exactly.

Local working directory for every local command:

```
cd ~/Documents/IIIT/sem5/ANLP/anlp_project/netherite-emr/experiments/2026-10-26_trace-deletion
```

## Rules

- Never change:
  - `gpu/continue.py`;
  - `outputs/requests_cap1000.json`;
  - the decoding settings;
  - anything outside `gpu/` and `outputs/selfhost/`.
- You may fix environment problems in `gpu/setup.sh` or `gpu/serve.sh` (package versions, paths, a flag) if they fail. Write every change and its reason into `gpu/NOTES.md`.
- Pricing and machine:
  - On-demand pricing only. Never pick a 30/90/180/365/730-day plan.
  - Never use spot instances.
  - Only 2 x H100 in region IN2, with 250 GB storage.
- One VM only. Its machine id lives in `gpu/instance.json`.
- Before every step from 4 onward, check that the VM is still running with `jl list`. The user's monitor or the deadline guard may have paused it. If it is paused, stop and report to the user; never resume it on your own.
- Limits (2 x H100 costs about ₹661 per hour):
  - If the vLLM server is not answering within 2 hours of the VM starting, or the VM has run for 4 hours in total: download the logs, run `jl pause <id> --yes`, and stop and report.
- Do not commit or push with git.

## 0. Pre-flight (no VM yet, no credits spent)

1. Install the CLI with `pip install jarvislabs` (or `uv tool install jarvislabs`).
2. Ask the user for their Jarvislabs API token, then run `jl setup --token <TOKEN> --yes`.
3. Ask the user to confirm they have pasted their SSH public key (`cat ~/.ssh/id_ed25519.pub`) into Jarvislabs → Settings → SSH keys.
4. Run `python3 -m pip install --user jinja2` so the chat-template check can run.
5. Run `python3 gpu/preflight.py`.
6. Read the downloaded `gpu/hotpatch_vllm.py` yourself and confirm three things:
   - it installs `vllm==0.15.0`;
   - it patches `registry.py`;
   - it registers `SarvamMLAForCausalLM`.

Every line of the pre-flight must be PASS. If anything fails, fix it if it is a local setup issue; otherwise stop and report. When everything passes, show the user the pre-flight output and ask: "Pre-flight passed. Start the 2 x H100 VM now?" Do not continue until the user says yes.

## 1. Create the VM and arm the safety switches

1. Create the VM:

   ```
   jl create --gpu H100 --num-gpus 2 --storage 250 --template pytorch --name netherite-trace --yes --json
   ```

2. Immediately write `gpu/instance.json` with the machine id and the start time in UTC ISO format, for example `{"machine_id": "<id>", "started_at": "2026-10-26T18:00:00+00:00", "work": "/home/trace-deletion"}`. Write the same into `gpu/NOTES.md`.
3. Check the hardware:
   - `jl exec <id> -- nvidia-smi` must show 2 H100 GPUs with 80 GB each.
   - `jl exec <id> -- df -h /home` must show at least 200 GB free.

   If either fails, destroy the VM with `jl destroy <id> --yes` and report.
4. Upload the files:

   ```
   jl exec <id> -- mkdir -p /home/trace-deletion
   jl upload <id> gpu/setup.sh /home/trace-deletion/setup.sh
   jl upload <id> gpu/serve.sh /home/trace-deletion/serve.sh
   jl upload <id> gpu/continue.py /home/trace-deletion/continue.py
   jl upload <id> gpu/status.py /home/trace-deletion/status.py
   jl upload <id> gpu/deadline.sh /home/trace-deletion/deadline.sh
   jl upload <id> outputs/requests_cap1000.json /home/trace-deletion/requests_cap1000.json
   ```

5. Start the deadline guard. This is a backstop that pauses the VM 4.5 hours after it started, even if the user's Mac is asleep. `<deadline_epoch>` is the start time + 16200 seconds, as a Unix timestamp:

   ```
   jl exec <id> -- bash -lc 'JL_API_KEY=<TOKEN> nohup bash /home/trace-deletion/deadline.sh <id> <deadline_epoch> > /home/trace-deletion/deadline.log 2>&1 &'
   ```

   Wait about a minute. `deadline.log` must say `deadline guard active`. If it does not, tell the user the backstop is not active and continue.
6. Tell the user to open a new Terminal window and run the live monitor:

   ```
   cd ~/Documents/IIIT/sem5/ANLP/anlp_project/netherite-emr/experiments/2026-10-26_trace-deletion
   python3 gpu/monitor.py watch
   ```

   Explain that it refreshes every minute and shows the stage, progress, cost so far, GPU use and errors. It pauses the VM by itself after 4 hours or after 25 minutes without any progress. `python3 gpu/monitor.py kill` pauses the VM immediately. Continue without waiting.

## 2. Install vLLM and download the model (about 20 to 40 minutes)

```
jl exec <id> -- bash -lc 'cd /home/trace-deletion && nohup bash setup.sh > setup.log 2>&1 &'
```

- Every 5 minutes, check progress: `jl exec <id> -- bash -lc 'cd /home/trace-deletion && tail -n 3 setup.log download.log hotpatch.log; du -sh /home/models/sarvam-105b-fp8'`.
- It is done when `setup.log` contains `PATCH_OK`, then `23` (the shard count), then `SETUP_DONE`. The model folder should be about 105 GiB, and vLLM should be 0.15.x.
- If it fails, read the logs, fix, note the fix, and run `setup.sh` again. Downloads resume.

## 3. Start the server (about 10 to 20 minutes to load)

```
jl exec <id> -- bash -lc 'cd /home/trace-deletion && nohup bash serve.sh > serve.log 2>&1 &'
```

- Every 2 minutes, check: `jl exec <id> -- bash -lc 'curl -s localhost:3002/v1/models; tail -n 3 /home/trace-deletion/serve.log'`.
- It is ready when `/v1/models` lists `sarvam-105b-fp8`.
- If `serve.log` shows a crash (out of memory, unsupported option, etc.), read it, fix `serve.sh`, note the fix, kill the old process, and restart.

## 4. Sanity check (a few minutes)

```
jl exec <id> -- bash -lc 'cd /home/trace-deletion && python3 continue.py --mode sanity'
```

- **`SANITY: FAIL`:**
  1. Download the results: `jl download <id> /home/trace-deletion/selfhost outputs -r`.
  2. Pause the VM: `jl pause <id> --yes`.
  3. Show the user the full sanity output and tell them to go back to the Claude chat.
- **`SANITY: PASS`:** continue straight away. The GPU is billed while idle, so do not wait.

## 5. Main run, then the repeat run (about 10 to 30 minutes each)

```
jl exec <id> -- bash -lc 'cd /home/trace-deletion && nohup python3 continue.py --mode main > main.log 2>&1 &'
```

Poll `main.log` until a line starts with `done:`. If it stops with an error, run the same command again; it resumes. Then run:

```
jl exec <id> -- bash -lc 'cd /home/trace-deletion && nohup python3 continue.py --mode repeat > repeat.log 2>&1 &'
```

Poll `repeat.log` the same way.

## 6. Download everything, then destroy the VM

```
mkdir -p outputs/selfhost/logs
jl download <id> /home/trace-deletion/selfhost outputs -r
jl exec <id> -- bash -lc 'cd /home/trace-deletion && tail -n 300 serve.log > serve_tail.log && python3 -m pip freeze > pip_freeze.txt'
for f in setup.log hotpatch.log download.log serve_tail.log main.log repeat.log deadline.log pip_freeze.txt; do jl download <id> /home/trace-deletion/$f outputs/selfhost/logs/$f; done
```

Check before destroying:
- `outputs/selfhost/results.json` has 702 records.
- `outputs/selfhost/results_repeat.json` has 234 records.
- `outputs/selfhost/sanity.json` exists.

If the download made a nested `outputs/selfhost/selfhost/` folder, move its files up one level. Only then destroy the VM:

```
jl destroy <id> --yes
jl list
```

`jl list` must no longer show the VM, and the user's monitor will stop by itself. In `gpu/NOTES.md`, write the destroy time, the total hours, and the cost (hours x ₹661).

## 7. Analysis and report

```
python3 analyze.py --output outputs/selfhost
```

Tell the user:
- the sanity output;
- the total hours and cost;
- the `done:` lines;
- the "By language" table and the "Repeatability" line from `outputs/selfhost/SUMMARY.md`.

Then tell them to go back to the Claude chat for the full results.
