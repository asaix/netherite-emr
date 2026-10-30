import argparse
import configparser
import json
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent


def main(args):
    cfg = configparser.ConfigParser()
    cfg.read(args.config)
    d, r = cfg["decoding"], cfg["run"]
    requests = HERE / r["requests"]
    n = len(json.load(open(requests, encoding="utf-8")))
    reserve = r.getfloat("reserve_minutes") * 60
    last = None
    print(f"rounds: {n} requests per round | up to {r.getint('max_rounds')} rounds | stop starting rounds at {time.strftime('%H:%M:%S', time.gmtime(args.stop_at))} UTC minus {reserve / 60:.0f} min reserve", flush=True)
    for k in range(1, r.getint("max_rounds") + 1):
        out = HERE / r["out"] / f"round_{k:02d}"
        done = len(json.load(open(out / "results.json", encoding="utf-8"))) if (out / "results.json").exists() else 0
        if done >= n:
            print(f"round {k:02d}: already complete", flush=True)
            continue
        left = args.stop_at - reserve - time.time()
        if last and left < last * 1.1:
            print(f"ROUNDS DONE: {k - 1} rounds; round {k:02d} would need ~{last * 1.1 / 60:.0f} min, only {left / 60:.0f} min left", flush=True)
            return 0
        if left <= 0:
            print(f"ROUNDS DONE: {k - 1} rounds; no time left", flush=True)
            return 0
        print(f"=== round {k:02d} (seed {k}) | {done} already done | {left / 60:.0f} min left before the reserve", flush=True)
        t0 = time.time()
        code = subprocess.call([sys.executable, "-u", str(HERE / "continue.py"), "--mode", "main", "--requests", str(requests), "--out", str(out),
                                "--temperature", d["temperature"], "--top-p", d["top_p"], "--max-tokens", d["max_tokens"], "--seed", str(k),
                                "--concurrency", r["concurrency"], "--budget-minutes", f"{left / 60:.1f}", "--no-repeat-extra"])
        if code == 3:
            print(f"ROUNDS DONE: round {k:02d} stopped by the time budget and is incomplete; {k - 1} complete rounds", flush=True)
            return 0
        if code != 0:
            print(f"ROUNDS STOP: round {k:02d} exited with {code}", flush=True)
            return code
        last = (time.time() - t0) * n / max(1, n - done)
        print(f"=== round {k:02d} complete in {(time.time() - t0) / 60:.1f} min", flush=True)
    print(f"ROUNDS DONE: all {r.getint('max_rounds')} rounds", flush=True)
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default=str(HERE / "resample.cfg"))
    ap.add_argument("--stop-at", type=float, required=True)
    sys.exit(main(ap.parse_args()))
