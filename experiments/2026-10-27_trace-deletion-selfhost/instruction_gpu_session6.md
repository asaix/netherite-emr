# Instructions for Claude Code: session 6 (the experiment run)

## What changed since session 5

- **Session 5 result:**
  - The Red Hat checkpoint with vLLM 0.31 and `--attention-backend TRITON_MLA` passed every smoke test.
  - Calibration failed the gate on English only:
    - English: self 66.7% vs API 84.4%; only self right on 1 question, only API right on 9 (p = 0.02).
    - Hindi: at parity, 60.0% vs 62.2% (8 vs 9, p = 1.0).
    - 8 of 90 answers ran to 4,096 tokens; the API answered those same questions in 355–2,042 tokens.
- **User decision: run the experiment anyway.** 666 of the 702 requests are Hindi, and Hindi matches the API. The English gap is reported as a limitation (recorded in PLAN.md).
- **Code changes,** tested on a mock server; the session 5 versions are saved in `outputs/selfhost/logs/*_session5.py.txt`:
  - **`continue.py` requires the decoding on the command line:** `--temperature`, `--top-p`, `--max-tokens`.
  - **The token limit is 12,288 for every path.**
    - That is three times the old 4,096 and 3.5 times the API's longest calibration answer.
    - Longest prompt (about 2,500 tokens) + 12,288 fits the server's 16,384 context.
  - **Runaways no longer stop the run.** A runaway is the token limit reached with no Answer line.
    - Each one is printed as `RUNAWAY (token limit, no answer)` and counted as no answer.
    - The run stops only if more than 30% of at least 50 outputs are runaways (`RUNAWAY STOP`, `EXIT=4`).
    - Broken server output (empty or under 20 characters) still stops the run at once (`DEGENERATE STOP`, `EXIT=4`).
  - **Sanity is shorter:** 11 requests.
    - The repeat probe is removed, so there is no MODE decision any more; the mode is set on the command line.
    - Continuations must reach an Answer line in at least 4 of 6.
    - A server that does not answer gives `SANITY: FAIL` and `EXIT=5`.
  - **`bringup.py` takes environment switches:**
    - `SKIP_SMOKE=1`;
    - `CAL_MODE=gate|info|skip` (info runs calibration but never rejects the server);
    - `TEMPERATURE`, `TOP_P`, `CAL_MAX_TOKENS`;
    - `CAL_TAG` (suffix for the calibration file name).
- **No smoke test this session** (user decision). Only the setting that passed in session 5 is started: `redhat_v031_triton_mla`. The default setting looped in session 5, so never start it.
- **Runs are batched,** 16 at a time, as calibration was.
- **New `gpu/calibrate_only.py`:** runs the 90-question calibration against the server that is already running. It is information only and always exits 0, or 5 if the server does not answer.
- **`status.py` / `monitor.py` follow several run folders** (`selfhost_G`, `selfhost_S`) and the logs `cal_*.log`, `sanity_*.log`, `main_*.log`, `repeat_*.log`, so the stall detector sees progress in both runs.

## The plan (user decision): G first, then S, on one server

The decoding is set per request, so the server is started once and both runs use it. The token limit is 12,288 in both.

| | decoding | calibration | runs | output folder | logs |
|---|---|---|---|---|---|
| **G: greedy** | `--temperature 0 --top-p 1 --max-tokens 12288` | `TEMPERATURE=0 TOP_P=1 CAL_MAX_TOKENS=12288 CAL_TAG=_G` | sanity, main, repeat | `selfhost_G` | `cal_G.log`, `sanity_G.log`, `main_G.log`, `repeat_G.log` |
| **S: sampling** (Sarvam model card) | `--temperature 0.8 --top-p 0.95 --max-tokens 12288` | `TEMPERATURE=0.8 TOP_P=0.95 CAL_MAX_TOKENS=12288 CAL_TAG=_S` | main, repeat (no second sanity: same server) | `selfhost_S` | `cal_S.log`, `main_S.log`, `repeat_S.log` |

- **Calibration is information only.** Its `[FAIL]` and `CALIBRATION: FAIL` lines are not a reason to pause.
- **Show the user each calibration summary** next to this table, then continue without waiting:

| | finished | overall | English | Hindi |
|---|---|---|---|---|
| Session 5 greedy (4,096 tokens) | 82/90 | 63.3% | 66.7% | 60.0% |
| API | – | 73.3% | 84.4% | 62.2% |

## Rules (unchanged)

All rules in `instruction_gpu.md` and the live-output and abort rules in `instruction_gpu_session4.md` apply:
- `python3 -u`;
- poll every 30–60 s and show every new line;
- pause immediately on `BAD OUTPUT`, `DEGENERATE STOP`, `RUNAWAY STOP`, `ERROR STOP`, `SANITY: FAIL`, `BRINGUP: FAIL`, or a `Traceback`.

`RUNAWAY` lines are expected; they are not a reason to pause.

Never use `pkill -f` with a pattern that also matches your own shell command. Session 5 killed its own SSH shell and the old deadline guard that way. Find the pid with `pgrep` first, then `kill <pid>`.

Local working directory:

```
cd ~/Documents/IIIT/sem5/ANLP/anlp_project/netherite-emr/experiments/2026-10-26_trace-deletion
```

## Budget

- Sessions 1–5 used about 2.95 h (about ₹1,950).
- Expected for this session: about 1.5–2 h (about ₹1,000–1,300).
- Hard cap: 4 h from the resume (about ₹2,650). This is a safety net against a hung run, not a target.
  - Monitor: `--max-hours 4`.
  - Deadline guard: resume + 14400 s.
  - `--budget-minutes 150` on each main run.
- **User decision: run every step, both repeat runs included.** Do not skip any step for time, and do not ask before starting S. Using the remaining credits is fine.
- **Credit check:** if the Jarvislabs balance is below about ₹2,700 before resuming, tell the user the balance first.

## 0. Pre-boot (no credits)

```
python3 -m py_compile gpu/continue.py gpu/bringup.py gpu/calibrate_only.py gpu/status.py gpu/monitor.py && bash -n gpu/serve_rh.sh && echo SYNTAX_OK
python3 gpu/continue.py --mode main 2>&1 | tail -1    # must say the decoding flags are required
```

Check that 2 x H100 are free in IN2. Ask the user: "Pre-boot OK, 2 x H100 free. Resume VM 549976 on 2 x H100 at ₹661/h for G then S?" Wait for yes.

## 1. Resume and arm the safety switches

1. Run `jl resume 549976 --yes --json` with the 2 x H100 flags. Use the returned machine id from now on.
2. Update `gpu/instance.json` (`machine_id`, `started_at` = resume time, `"previous_hours": 2.95`) and `gpu/NOTES.md`.
3. When SSH answers, check:
   - `nvidia-smi` shows 2 H100s;
   - 23 shards are in `/home/models/sarvam-105b-fp8-dynamic`;
   - vLLM is 0.31.0 in `/home/venv031`;
   - `pgrep -af "vllm serve"` is empty.
4. Start the deadline guard (resume + 14400 s) and confirm `deadline guard active`.
5. Tell the user to start the monitor: `python3 gpu/monitor.py watch --max-hours 4 --interval 20`.

## 2. Archive session 5 on the VM and upload

```
jl exec <id> -- bash -lc 'cd /home/trace-deletion && for f in bringup.log bringup.json serve.log; do [ -f $f ] && mv $f ${f%.*}_session5.${f##*.}; done; [ -d selfhost ] && mv selfhost selfhost_session5; true'
for f in bringup.py continue.py calibrate_only.py status.py serve_rh.sh; do jl upload <id> gpu/$f /home/trace-deletion/$f; done
```

Compare MD5s of these five files and of `requests_cap1000.json` and `calibration_requests.json` with the local copies. Upload again any that differ.

## 3. Start the server (no smoke test, no calibration)

```
jl exec <id> -- bash -lc 'cd /home/trace-deletion && nohup env SKIP_SMOKE=1 CAL_MODE=skip bash -c "python3 -u bringup.py redhat_v031_triton_mla; echo EXIT=\$?" > bringup.log 2>&1 &'
```

- Expect server heartbeats, `smoke test skipped`, then `BRINGUP: PASS redhat_v031_triton_mla (server left running ...)`. It took 125 s in session 5.
- **No `BRINGUP: PASS` within 30 minutes of the resume:** download `bringup.log` and the last 600 lines of `serve.log`, pause, and report.

## 4. G block (greedy)

Run each step only after the previous one printed its final line (`EXIT=`).

```
# 4a calibration, about 3-6 min
jl exec <id> -- bash -lc 'cd /home/trace-deletion && nohup env TEMPERATURE=0 TOP_P=1 CAL_MAX_TOKENS=12288 CAL_TAG=_G bash -c "python3 -u calibrate_only.py; echo EXIT=\$?" > cal_G.log 2>&1 &'
# 4b sanity, 11 requests, about 2-5 min
jl exec <id> -- bash -lc 'cd /home/trace-deletion && nohup bash -c "python3 -u continue.py --mode sanity --temperature 0 --top-p 1 --max-tokens 12288 --concurrency 16 --out selfhost_G; echo EXIT=\$?" > sanity_G.log 2>&1 &'
# 4c main, 702 requests, about 15-30 min
jl exec <id> -- bash -lc 'cd /home/trace-deletion && nohup bash -c "python3 -u continue.py --mode main --temperature 0 --top-p 1 --max-tokens 12288 --concurrency 16 --budget-minutes 150 --out selfhost_G; echo EXIT=\$?" > main_G.log 2>&1 &'
# 4d repeat, 234 requests, about 5-10 min
jl exec <id> -- bash -lc 'cd /home/trace-deletion && nohup bash -c "python3 -u continue.py --mode repeat --temperature 0 --top-p 1 --max-tokens 12288 --concurrency 16 --out selfhost_G; echo EXIT=\$?" > repeat_G.log 2>&1 &'
```

- **4a, `EXIT=5`** (server not answering): download, pause, report.
- **4b, `SANITY: FAIL` or `EXIT` not 0:** download `sanity_G.log`, `selfhost_G/sanity.json` and `bringup.log`, pause, and report.
- **4c:**
  - `EXIT=0`: continue to 4d.
  - `EXIT=3` (budget): report to the user and ask; rerunning the same command resumes where it stopped.
  - `EXIT=4` or `EXIT=5`: download everything (step 6), pause, and report.
- **4d:** the same exit handling. Afterwards show the user the `done:` lines of 4c and 4d.

## 5. S block (sampling)

```
# 5a calibration
jl exec <id> -- bash -lc 'cd /home/trace-deletion && nohup env TEMPERATURE=0.8 TOP_P=0.95 CAL_MAX_TOKENS=12288 CAL_TAG=_S bash -c "python3 -u calibrate_only.py; echo EXIT=\$?" > cal_S.log 2>&1 &'
# 5b main
jl exec <id> -- bash -lc 'cd /home/trace-deletion && nohup bash -c "python3 -u continue.py --mode main --temperature 0.8 --top-p 0.95 --max-tokens 12288 --concurrency 16 --budget-minutes 150 --out selfhost_S; echo EXIT=\$?" > main_S.log 2>&1 &'
# 5c repeat (measures how much answers change from one sample to the next)
jl exec <id> -- bash -lc 'cd /home/trace-deletion && nohup bash -c "python3 -u continue.py --mode repeat --temperature 0.8 --top-p 0.95 --max-tokens 12288 --concurrency 16 --out selfhost_S; echo EXIT=\$?" > repeat_S.log 2>&1 &'
```

Exit handling is the same as in step 4.

## 6. Download, check, pause

```
mkdir -p outputs/selfhost_s6/logs
jl download <id> /home/trace-deletion/selfhost_G outputs/selfhost_s6 -r
jl download <id> /home/trace-deletion/selfhost_S outputs/selfhost_s6 -r
jl download <id> /home/trace-deletion/selfhost outputs/selfhost_s6 -r
jl exec <id> -- bash -lc 'cd /home/trace-deletion && tail -n 600 serve.log > serve_tail600.log'
for f in bringup.json bringup.log cal_G.log sanity_G.log main_G.log repeat_G.log cal_S.log main_S.log repeat_S.log serve_tail600.log deadline.log; do jl download <id> /home/trace-deletion/$f outputs/selfhost_s6/logs/$f; done
```

- Missing files of skipped steps are fine.
- Fix nested folders so these exist:
  - `outputs/selfhost_s6/selfhost_G/results.json`;
  - `outputs/selfhost_s6/selfhost_S/results.json`;
  - `outputs/selfhost_s6/selfhost/calibration_redhat_v031_triton_mla_G.json` and `..._S.json`.
- Check: 702 results in each run folder, 234 repeats where the repeat run happened, and `selfhost_G/sanity.json` exists.
- Then **pause** with `jl pause <id> --yes`. Do not destroy: the user decides that after seeing the results.
- Record the hours and cost in `gpu/NOTES.md`.

## 7. Analysis and report

```
python3 analyze.py --output outputs/selfhost_s6/selfhost_G > outputs/selfhost_s6/analysis_G.md
python3 analyze.py --output outputs/selfhost_s6/selfhost_S > outputs/selfhost_s6/analysis_S.md
```

Tell the user:
- **calibration:** the G and S summaries next to the session 5 / API table;
- **sanity:** the result;
- **for each run:** the `done:` lines, the number of runaways and seconds per request;
- **cost:** the hours and cost;
- **for each run:** the "By language" table, the "Unanswered or cut off" table, and the "Repeatability" line.

Then tell them to go back to the Claude chat.
