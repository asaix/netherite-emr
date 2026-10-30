# Instructions for Claude Code: distractor resampling run (session 7)

## What this run is

- **Design:** see `README.md`.
- **Size:** 1,952 continuation requests per round (arms Q, P, M, P1 over 563 traces). Rounds repeat with a new seed until the credits are used.
- **Server and settings:** the same server as session 6 (`redhat_v031_triton_mla`, VM 550501, weights and venv on its disk). Decoding is temperature 0.8, top-p 0.95, 4,096 tokens, all set in `config/resample.cfg`.
- **The user's decision:** use the remaining credits on as many rounds as fit, with a safety margin.

Rules carried over from earlier sessions:
- `python3 -u` for every script;
- poll every 30–60 s;
- never `pkill -f` a pattern that can match your own shell: use `pgrep` to find the pid, then `kill <pid>`;
- **pause immediately and report** on any of these: `DEGENERATE STOP`, `RUNAWAY STOP`, `ERROR STOP`, `ROUNDS STOP`, `SANITY: FAIL`, `BRINGUP: FAIL`, a `Traceback`.

**What to show the user while rounds run.** Each round prints one line per request (1,952), so don't relay every line. Show:
- the progress lines (`NN/1952 | runaways so far ... | s per request | ...`, printed every 10 requests);
- every `===` round line;
- every line containing `BAD OUTPUT`, `STOP` or `Traceback`.

The user can watch every line live with `jl ssh <id>` and `tail -F /home/trace-deletion/rounds.log`.

**Single `BAD OUTPUT` lines** (an output under 20 characters) were all valid Answer-only continuations in session 6. The script stops itself if they become frequent (3 in the first 20, or over 10%), so a single one is not a reason to pause.

Local working directory:

```
cd ~/Documents/IIIT/sem5/ANLP/anlp_project/netherite-emr/experiments/2026-10-29_distractor-resampling
```

## 0. Pre-boot (no credits)

1. Check the syntax and the request file:

   ```
   python3 -m py_compile gpu/rounds.py gpu/continue.py gpu/status.py gpu/monitor.py analyze_resample.py build_resample.py && bash -n gpu/serve_rh.sh gpu/deadline.sh && echo SYNTAX_OK
   python3 -c "import json; r=json.load(open('outputs/requests_resample.json')); print(len(r))"    # must print 1952
   ```

2. Run the template check with the same Python environment that ran `template_check.py` in session 3. It needs `transformers` and `huggingface_hub`, and the Sarvam tokenizer is probably cached already:

   ```
   python3 gpu/template_check.py
   ```

   - It must end with `TEMPLATE CHECK: PASS`. Show the user the full output, in particular the `empty-prefix assistant part as rendered` line.
   - If it ends with FAIL, stop and report.

3. **Budget:**
   - Get the credit balance the same way as before session 6 (balance plus grants).
   - Hours `H = (balance - 150) / 661`, rounded down to 0.05 h, at most 4.5. The 150 is a margin for the resume wait and paused storage.
   - Tell the user the balance, `H` and the expected number of rounds. A round is expected to take 20–45 minutes, but that is not measured yet.

4. Check that 2 x H100 are free in IN2. Ask: "Pre-boot OK. Balance ₹<b>, budget <H> h. Resume VM 550501 on 2 x H100 at ₹661/h for the resampling rounds?" Wait for yes.

## 1. Resume and arm the safety switches

1. Run `jl resume 550501 --yes --json` with the 2 x H100 flags. Use the returned machine id from now on.
2. Write `gpu/instance.json`:
   - `machine_id`;
   - `started_at` = resume time in UTC ISO;
   - `"previous_hours": 4.28`;
   - `"phase": "resampling"`;
   - `"rate_inr_per_hour": 661`;
   - `"work": "/home/trace-deletion"`.

   Start a `## Session 7` section in `gpu/NOTES.md` (create the file).
3. When SSH answers, check:
   - `nvidia-smi` shows 2 H100s;
   - 23 shards are in `/home/models/sarvam-105b-fp8-dynamic`;
   - vLLM is 0.31.0 in `/home/venv031`;
   - `pgrep -af "vllm serve"` is empty.
4. **Deadline guard:** `DEADLINE = resume epoch + H * 3600`. Start it as before (`nohup bash deadline.sh <id> <DEADLINE> > deadline.log`, with `PATH=$HOME/.local/bin:$PATH`) and confirm `deadline guard active`.
5. Tell the user to start the monitor: `python3 gpu/monitor.py watch --max-hours <H> --interval 30`.

## 2. Upload

```
for f in rounds.py continue.py status.py; do jl upload <id> gpu/$f /home/trace-deletion/$f; done
jl upload <id> config/resample.cfg /home/trace-deletion/resample.cfg
jl upload <id> outputs/requests_resample.json /home/trace-deletion/requests_resample.json
```

Compare MD5s with the local files for these five, and also for `bringup.py` and `serve_rh.sh`, which are already on the VM and should match `gpu/`. Upload again any that differ.

## 3. Start the server (no smoke test, no calibration)

```
jl exec <id> -- bash -lc 'cd /home/trace-deletion && for f in bringup.log bringup.json serve.log; do [ -f $f ] && mv $f ${f%.*}_session6.${f##*.}; done; nohup env SKIP_SMOKE=1 CAL_MODE=skip bash -c "python3 -u bringup.py redhat_v031_triton_mla; echo EXIT=\$?" > bringup.log 2>&1 &'
```

- Wait for `BRINGUP: PASS redhat_v031_triton_mla (server left running ...)`. It took 240 s in session 6.
- **No PASS within 30 minutes of the resume:** download `bringup.log` and the last 600 lines of `serve.log`, pause, and report.

## 4. Sanity (about 2–5 minutes)

```
jl exec <id> -- bash -lc 'cd /home/trace-deletion && nohup bash -c "python3 -u continue.py --mode sanity --temperature 0.8 --top-p 0.95 --max-tokens 4096 --seed 0 --concurrency 16 --out resample_sanity; echo EXIT=\$?" > sanity_resample.log 2>&1 &'
```

- **`SANITY: PASS`:** continue.
- **Otherwise:** download `sanity_resample.log`, pause, and report.

## 5. Rounds

`STOP_AT = DEADLINE - 300`. The driver also keeps a 15-minute reserve for the download, so the last round ends at least 20 minutes before the deadline guard.

```
jl exec <id> -- bash -lc 'cd /home/trace-deletion && nohup bash -c "python3 -u rounds.py --stop-at <STOP_AT>; echo EXIT=\$?" > rounds.log 2>&1 &'
```

- **What the driver does:**
  - runs round 1, 2, ... (seed = round number) into `resample/round_NN/`;
  - starts a new round only if the last round's duration × 1.1 still fits before `STOP_AT` minus the reserve;
  - a round cut short by the time budget stays incomplete and is not analysed.
- **Restarting:** if anything forces a restart, the same command resumes the unfinished round.
- **`ROUNDS DONE ...` and `EXIT=0`:** continue to step 6.
- **`ROUNDS STOP`, any other `STOP`, or `EXIT` not 0:** step 6, then report.
- **After each `=== round NN complete` line:** tell the user the round's time and the runaway count from the last progress line.

## 6. Download, check, pause

```
mkdir -p outputs/logs
jl download <id> /home/trace-deletion/resample outputs -r
jl download <id> /home/trace-deletion/resample_sanity outputs -r
jl exec <id> -- bash -lc 'cd /home/trace-deletion && tail -n 600 serve.log > serve_tail600.log'
for f in bringup.log bringup.json sanity_resample.log rounds.log serve_tail600.log deadline.log; do jl download <id> /home/trace-deletion/$f outputs/logs/$f; done
```

- Fix nested folders so `outputs/resample/round_01/results.json` exists.
- **Check:** every complete round has 1,952 results with unique ids; list the rounds and their counts.
- **Pause** with `jl pause <id> --yes`. Record the hours and cost in `gpu/NOTES.md`.
- **Then ask the user:** "Downloads verified. Destroy VM <id> now? The credits are used up, and a paused VM still bills storage." Destroy only on yes (`jl destroy <id> --yes`, then `jl list`).

## 7. Analysis and report

```
python3 analyze_resample.py --output outputs/resample
```

Tell the user:
- the template check result;
- sanity;
- the number of complete rounds and the time per round;
- hours and cost;
- runaways per round;
- the "Accuracy by arm" and "Contrasts" tables for `hi_IN` and `en_US`;
- the mention table rows for `hi_IN` and `en_US`.

Then tell them to go back to the Claude chat.
