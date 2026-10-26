import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
INSTANCE = HERE / "instance.json"
LOG = HERE.parent / "outputs" / "selfhost" / "monitor.log"
MODEL_GB = 112.6
TOTAL = {"main": 702, "repeat": 234}


def jl(*args, timeout=120):
    return subprocess.run(["jl", *args], capture_output=True, text=True, timeout=timeout)


def instance():
    if not INSTANCE.exists():
        sys.exit(f"{INSTANCE} not found: no instance has been started by Claude Code yet")
    return json.load(open(INSTANCE))


def started(inst):
    return datetime.fromisoformat(inst["started_at"]).timestamp()


def pause(inst, reason, dry):
    print(f"\n*** KILL SWITCH: pausing {inst['machine_id']} ({reason}) ***", flush=True)
    log({"event": "pause", "reason": reason})
    if dry:
        print("(dry run: not pausing)")
        return True
    r = jl("pause", inst["machine_id"], "--yes")
    print(r.stdout.strip(), r.stderr.strip())
    return r.returncode == 0


def log(entry):
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps({"at": datetime.now(timezone.utc).isoformat(), **entry}, ensure_ascii=False) + "\n")


def fetch(inst):
    try:
        r = jl("exec", inst["machine_id"], "--", "python3", f"{inst.get('work', '/home/trace-deletion')}/status.py", timeout=90)
    except subprocess.TimeoutExpired:
        return None, "status call timed out"
    for line in r.stdout.splitlines():
        if line.startswith("STATUS "):
            return json.loads(line[7:]), None
    return None, (r.stderr or r.stdout).strip()[-300:] or f"exit code {r.returncode}"


def vm_state(inst):
    try:
        data = json.loads(jl("list", "--json").stdout)
    except (ValueError, subprocess.TimeoutExpired):
        return "unknown"
    items = data if isinstance(data, list) else next((v for v in data.values() if isinstance(v, list)), []) if isinstance(data, dict) else []
    for item in items:
        if isinstance(item, dict) and str(inst["machine_id"]) in map(str, item.values()):
            status = next((str(v).lower() for k, v in item.items() if "status" in k.lower()), "")
            return "running" if any(w in status for w in ("running", "start", "resum", "creat")) else ("stopped" if status else "unknown")
    return "gone"


def stage(s):
    tag = " (batched)" if s.get("run_dir") == "selfhost_batched" else ""
    if s["repeat_finished"]:
        return "FINISHED: waiting for Claude Code to download results and destroy the VM"
    if s["main_finished"]:
        return f"repeat run{tag} {s['repeat_done']}/{TOTAL['repeat']}"
    if s["main_done"]:
        return f"main run{tag} {s['main_done']}/{TOTAL['main']}"
    if s["sanity"] == "FAIL":
        return "SANITY FAILED: Claude Code should pause the VM and report"
    if s["sanity"] == "PASS":
        return "sanity passed, starting main run"
    if s["server_ready"]:
        return "server ready, sanity check running"
    if s["setup_done"]:
        return "loading the model into the GPUs"
    if s["logs"]:
        return f"setup: downloading {s['download_gb']}/{MODEL_GB} GB, installing vLLM"
    return "VM up, waiting for setup to start"


def signature(s):
    logs = {k: v["bytes"] for k, v in s["logs"].items() if not (k == "serve.log" and s["server_ready"])}
    return json.dumps([s["download_gb"], s["setup_done"], s["server_ready"], s["sanity"], s["main_done"], s["repeat_done"], logs], sort_keys=True)


def watch(args):
    inst = instance()
    if sys.platform == "darwin" and shutil.which("caffeinate"):
        subprocess.Popen(["caffeinate", "-dims", "-w", str(os.getpid())])
    last_sig, last_change, unreachable_since = None, time.time(), None
    while True:
        inst = instance()
        now = time.time()
        hours = (now - started(inst)) / 3600
        cost = hours * args.rate
        s, err = fetch(inst)
        os.system("clear")
        print(f"Netherite trace deletion | VM {inst['machine_id']} | {datetime.now().strftime('%H:%M:%S')}")
        print(f"running {hours:.2f} h | cost so far ~₹{cost:,.0f} | auto-pause at {args.max_hours} h (~₹{args.max_hours * args.rate:,.0f}) or after {args.stall} min without progress")
        if s is None:
            unreachable_since = unreachable_since or now
            down = (now - unreachable_since) / 60
            print(f"\nVM not reachable for {down:.0f} min: {err}")
            state = vm_state(inst)
            print(f"VM state from jl list: {state}")
            if state in ("gone", "stopped"):
                print("The VM is no longer running (paused or destroyed). Monitor stopping.")
                log({"event": "stopped", "reason": f"instance {state}"})
                return
            if down >= args.unreachable:
                pause(inst, f"VM unreachable for {down:.0f} min", args.dry_run)
                return
        else:
            unreachable_since = None
            sig = signature(s)
            if sig != last_sig:
                last_sig, last_change = sig, now
            idle = (now - last_change) / 60
            print(f"\nstage: {stage(s)}")
            print(f"download {s['download_gb']}/{MODEL_GB} GB | disk free {s['disk_free_gb']} GB | patch ok {s['patch_ok']} | server {'ready' if s['server_ready'] else 'not ready'} | sanity {s['sanity']}")
            print(f"main {s['main_done']}/{TOTAL['main']} | repeat {s['repeat_done']}/{TOTAL['repeat']} | no progress for {idle:.0f} min")
            for i, g in enumerate(s["gpus"]):
                print(f"GPU{i}: {g['util_pct']}% busy, {g['mem_used_mb'] / 1024:.0f}/{g['mem_total_mb'] / 1024:.0f} GB")
            for name, l in s["logs"].items():
                print(f"  {name:13} idle {l['idle_s']:>5}s | {l['last'][-110:]}")
            if s["errors"]:
                print("\nrecent error lines:")
                for e in s["errors"]:
                    print("  " + e[-160:])
            log({"hours": round(hours, 3), "stage": stage(s), "idle_min": round(idle, 1), "main": s["main_done"], "repeat": s["repeat_done"]})
            if hours >= args.max_hours:
                pause(inst, f"time limit {args.max_hours} h reached", args.dry_run)
                return
            if idle >= args.stall:
                pause(inst, f"no progress for {idle:.0f} min", args.dry_run)
                return
        print(f"\nCtrl+C stops watching (the VM keeps running). Kill switch: python3 gpu/monitor.py kill")
        time.sleep(args.interval)


def main():
    ap = argparse.ArgumentParser(description="Live monitor and kill switch for the Jarvislabs run")
    ap.add_argument("command", choices=["watch", "status", "kill", "destroy"])
    ap.add_argument("--interval", type=int, default=60)
    ap.add_argument("--max-hours", type=float, default=4.0)
    ap.add_argument("--stall", type=float, default=25)
    ap.add_argument("--unreachable", type=float, default=15)
    ap.add_argument("--rate", type=float, default=661)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    if args.command == "watch":
        watch(args)
    elif args.command == "status":
        s, err = fetch(instance())
        print(json.dumps(s, indent=2, ensure_ascii=False) if s else err)
    elif args.command == "kill":
        pause(instance(), "manual kill switch", args.dry_run)
    else:
        inst = instance()
        if input(f"Type the machine id ({inst['machine_id']}) to destroy it permanently: ").strip() == inst["machine_id"]:
            print(jl("destroy", inst["machine_id"], "--yes").stdout)
            log({"event": "destroy", "reason": "manual"})


if __name__ == "__main__":
    main()
