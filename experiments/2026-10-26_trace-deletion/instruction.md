# Instructions for Claude Code: run the trace-deletion experiment

You are running an already-built experiment on this Mac. The scripts, configs and request files are final. Your job is only to run them, watch them, and report. Read `PLAN.md` in this folder for what the experiment is.

Working directory for every command:

```
cd ~/Documents/IIIT/sem5/ANLP/anlp_project/netherite-emr/experiments/2026-10-26_trace-deletion
```

Use `python3`. If `python3` is missing, use `../../../.venv/bin/python` instead. The scripts need only the Python standard library, so do not install anything.

## Rules

- Do not edit any `.py`, `config/run.cfg`, `PLAN.md` or any `outputs/requests_*.json` file.
- Do not run `build_requests.py`. The request files are fixed, and the pilot requests are a subset of the main ones.
- Do not delete or move `outputs/results.json`. Every run appends to it, and re-running a command skips requests already done. This is how the pilot continues into the main run.
- Do not commit or push anything with git.
- The run uses two API keys from `config/run.cfg` and switches to the second one automatically when the first runs out of credit. If the run prints `all API keys exhausted`, stop and tell the user.

## Stage 1: pilot (60 API calls, a few minutes)

1. Run the pilot:

   ```
   python3 run.py --requests outputs/requests_pilot.json
   ```

   It should end with `done: {'ok': 60, 'error': 0, ...}`. If some requests errored, run the same command again; it retries only the missing ones. Do this up to 3 times.

2. Run the pilot check:

   ```
   python3 pilot_check.py
   ```

3. **Stop here.** Show the user the full output of `pilot_check.py` and the last lines of the `run.py` output. Tell the user: "The pilot is done. Results are in `outputs/results.json`. Go back to the Claude chat for the pilot review before starting Stage 2." Do not start Stage 2 until the user tells you to.

## Stage 1b: continuation diagnostic (13 API calls, a few minutes)

The pilot showed that continuations often restart or change the answer, so this diagnostic must run before the main run.

1. Run:

   ```
   python3 diag.py
   ```

   It writes only to `outputs/diag/continuation_diag.json` and does not touch `outputs/results.json`.

2. **Stop here.** Show the user the full output and tell them to go back to the Claude chat. Do not start Stage 2; the Claude chat will decide whether the method changes first.

## Stage 2: main run (543 more calls, roughly 30 to 60 minutes)

Only when the user says to proceed:

1. Start the main run in the background so it is not cut off by a command timeout, and write its log to a file:

   ```
   nohup python3 run.py --requests outputs/requests_cap10.json > outputs/run_main.log 2>&1 &
   ```

   It reports that 60 requests are already done (the pilot) and runs the remaining 543.

2. Check progress every few minutes:

   ```
   tail -c 400 outputs/run_main.log
   ```

   It is finished when the log contains a line starting with `done:`.

3. If the `done:` line shows errors, run the same `nohup` command again to retry the missing requests (up to 3 times). If the log says `all API keys exhausted`, stop and tell the user how many requests are done.

4. When everything is done, run the analysis:

   ```
   python3 analyze.py
   ```

5. Tell the user the run is complete. Show the final `done:` line, the contents of `outputs/key_log.json` if it exists, and the first table of `outputs/SUMMARY.md`. Tell them to go back to the Claude chat for the full results.
