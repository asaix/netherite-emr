import json
import os
import re
import subprocess
import time
import urllib.request
from pathlib import Path

WORK = Path(os.environ.get("WORK", "/home/trace-deletion"))
MODEL = Path(os.environ.get("MODEL_DIR", "/home/models/sarvam-105b-fp8-dynamic"))
LOGS = ["download_rh.log", "setup031.log", "bringup.log", "setup.log", "pip_hf.log", "download.log", "hotpatch.log", "serve.log", "main.log", "repeat.log", "main_batched.log", "repeat_batched.log", "rounds.log"]
ERROR = re.compile(r"Traceback|Error|error:|out of memory|CUDA error|Killed|No space left", re.I)


def size(path):
    if not path.exists():
        return 0
    return sum(f.stat().st_size for f in path.rglob("*") if f.is_file())


def count(path):
    try:
        return len(json.load(open(path, encoding="utf-8")))
    except (OSError, ValueError):
        return 0


def text(path):
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def server_ready():
    try:
        with urllib.request.urlopen("http://127.0.0.1:3002/v1/models", timeout=5) as r:
            return r.status == 200
    except OSError:
        return False


def gpus():
    try:
        out = subprocess.run(["nvidia-smi", "--query-gpu=utilization.gpu,memory.used,memory.total", "--format=csv,noheader,nounits"], capture_output=True, text=True, timeout=20).stdout
        return [dict(zip(["util_pct", "mem_used_mb", "mem_total_mb"], map(int, line.split(", ")))) for line in out.strip().splitlines()]
    except (OSError, ValueError, subprocess.SubprocessError):
        return []


now = time.time()
logs = {}
errors = []
for p in [WORK / n for n in LOGS] + sorted(set(WORK.glob("main_*.log")) | set(WORK.glob("repeat_*.log")) | set(WORK.glob("cal_*.log")) | set(WORK.glob("sanity*.log")) - {WORK / n for n in LOGS}):
    name = p.name
    if p.exists():
        body = text(p)
        lines = [l for l in re.split(r"[\r\n]+", body) if l.strip()]
        logs[name] = {"bytes": p.stat().st_size, "idle_s": int(now - p.stat().st_mtime), "last": lines[-1][-200:] if lines else ""}
        errors += [f"{name}: {l[-200:]}" for l in lines[-40:] if ERROR.search(l)]
RUN_DIRS = [d for d in WORK.glob("selfhost*") if d.is_dir() and not d.name.startswith("selfhost_session")]
WITH_RESULTS = [d for d in RUN_DIRS if (d / "results.json").exists()]
ACTIVE = max(WITH_RESULTS, key=lambda d: max(f.stat().st_mtime for f in d.glob("results*.json"))) if WITH_RESULTS else WORK / "selfhost"
SUFFIX = ACTIVE.name[len("selfhost"):]  # "", "_batched", "_G", "_S"
SANITY_FILES = sorted((d / "sanity.json" for d in RUN_DIRS if (d / "sanity.json").exists()), key=lambda f: f.stat().st_mtime)
sanity = json.load(open(SANITY_FILES[-1], encoding="utf-8")) if SANITY_FILES else None
RESAMPLE = sorted((WORK / "resample").glob("round_*/results.json"))
CAL_LOGS = sorted(WORK.glob("cal_*.log"), key=lambda f: f.stat().st_mtime)
CAL_TEXT = text(CAL_LOGS[-1]) if CAL_LOGS else text(WORK / "bringup.log")
status = {
    "time": now,
    "disk_free_gb": round(os.statvfs(str(WORK)).f_bavail * os.statvfs(str(WORK)).f_frsize / 1e9, 1) if WORK.exists() else None,
    "download_gb": round(size(MODEL) / 1e9, 1),
    "setup_done": "SETUP_DONE" in text(WORK / "setup.log"),
    "download_started": (WORK / "download_rh.log").exists(),
    "download_done": "DOWNLOAD_DONE" in text(WORK / "download_rh.log"),
    "calibration": "PASS" if "CALIBRATION: PASS" in CAL_TEXT else ("FAIL" if "CALIBRATION: FAIL" in CAL_TEXT else None),
    "patch_ok": "PATCH_OK" in text(WORK / "setup.log"),
    "server_ready": server_ready(),
    "sanity": None if sanity is None else ("PASS" if all(sanity["checks"].values()) else "FAIL"),
    "run_dir": ACTIVE.name,
    "main_done": count(ACTIVE / "results.json"),
    "main_finished": "done:" in text(WORK / f"main{SUFFIX}.log"),
    "repeat_done": count(ACTIVE / "results_repeat.json"),
    "repeat_finished": "done:" in text(WORK / f"repeat{SUFFIX}.log"),
    "resample_rounds": len(RESAMPLE),
    "resample_done": sum(count(p) for p in RESAMPLE),
    "rounds_finished": "ROUNDS DONE" in text(WORK / "rounds.log") or "ROUNDS STOP" in text(WORK / "rounds.log"),
    "gpus": gpus(),
    "logs": logs,
    "errors": errors[-6:],
}
print("STATUS " + json.dumps(status, ensure_ascii=False))
