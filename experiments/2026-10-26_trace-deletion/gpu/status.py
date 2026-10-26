import json
import os
import re
import subprocess
import time
import urllib.request
from pathlib import Path

WORK = Path(os.environ.get("WORK", "/home/trace-deletion"))
MODEL = Path(os.environ.get("MODEL_DIR", "/home/models/sarvam-105b-fp8"))
LOGS = ["setup.log", "pip_hf.log", "download.log", "hotpatch.log", "serve.log", "main.log", "repeat.log", "main_batched.log", "repeat_batched.log"]
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
for name in LOGS:
    p = WORK / name
    if p.exists():
        body = text(p)
        lines = [l for l in re.split(r"[\r\n]+", body) if l.strip()]
        logs[name] = {"bytes": p.stat().st_size, "idle_s": int(now - p.stat().st_mtime), "last": lines[-1][-200:] if lines else ""}
        errors += [f"{name}: {l[-200:]}" for l in lines[-40:] if ERROR.search(l)]
ACTIVE = WORK / "selfhost_batched" if (WORK / "selfhost_batched").exists() else WORK / "selfhost"
sanity = json.load(open(WORK / "selfhost" / "sanity.json", encoding="utf-8")) if (WORK / "selfhost" / "sanity.json").exists() else None
status = {
    "time": now,
    "disk_free_gb": round(os.statvfs(str(WORK)).f_bavail * os.statvfs(str(WORK)).f_frsize / 1e9, 1) if WORK.exists() else None,
    "download_gb": round(size(MODEL) / 1e9, 1),
    "setup_done": "SETUP_DONE" in text(WORK / "setup.log"),
    "patch_ok": "PATCH_OK" in text(WORK / "setup.log"),
    "server_ready": server_ready(),
    "sanity": None if sanity is None else ("PASS" if all(sanity["checks"].values()) else "FAIL"),
    "run_dir": ACTIVE.name,
    "main_done": count(ACTIVE / "results.json"),
    "main_finished": "done:" in text(WORK / ("main_batched.log" if ACTIVE.name == "selfhost_batched" else "main.log")),
    "repeat_done": count(ACTIVE / "results_repeat.json"),
    "repeat_finished": "done:" in text(WORK / ("repeat_batched.log" if ACTIVE.name == "selfhost_batched" else "repeat.log")),
    "gpus": gpus(),
    "logs": logs,
    "errors": errors[-6:],
}
print("STATUS " + json.dumps(status, ensure_ascii=False))
