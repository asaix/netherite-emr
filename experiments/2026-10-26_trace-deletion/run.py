import argparse
import configparser
import json
import os
import random
import re
import threading
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXHAUSTED = re.compile(r"credit|quota|insufficient|balance|exhaust|payment|billing|recharge|top.?up", re.I)
RATE = re.compile(r"rate", re.I)


def now():
    return datetime.now(timezone.utc).isoformat()


class OutOfKeys(Exception):
    pass


class Keys:
    def __init__(self, keys):
        self.keys, self.index, self.lock, self.log = keys, 0, threading.Lock(), []

    def current(self):
        with self.lock:
            return (self.index, self.keys[self.index]) if self.index < len(self.keys) else (None, None)

    def retire(self, index, reason):
        with self.lock:
            if index == self.index:
                self.log.append({"key": index + 1, "reason": reason, "time": now()})
                self.index += 1
                print(f"\nkey {index + 1} retired: {reason[:200]}", flush=True)


def post(cfg, key, payload):
    req = urllib.request.Request(cfg["url"], data=json.dumps(payload).encode(), headers={"api-subscription-key": key, "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=cfg["timeout"]) as r:
            return r.status, json.load(r), ""
    except urllib.error.HTTPError as e:
        return e.code, None, e.read().decode(errors="replace")


def call(cfg, keys, payload):
    last = None
    for attempt in range(cfg["max_retries"]):
        index, key = keys.current()
        if key is None:
            raise OutOfKeys(last)
        try:
            status, data, text = post(cfg, key, payload)
        except OSError as e:
            last = repr(e)
        else:
            if status == 200:
                return data, index
            last = f"HTTP {status}: {text[:300]}"
            if status in (401, 402, 403) or (EXHAUSTED.search(text) and not RATE.search(text)):
                keys.retire(index, last)
                continue
            if status not in cfg["retry_status"]:
                raise RuntimeError(last)
        time.sleep(min(cfg["backoff_cap"], 2 ** attempt) + random.uniform(0, 1))
    raise RuntimeError(f"gave up after {cfg['max_retries']} attempts: {last}")


def save(path, data):
    tmp = path.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    os.replace(tmp, path)


def load_config(path):
    c = configparser.ConfigParser()
    c.read(path)
    a = c["api"]
    return {
        "url": a["url"],
        "keys": [k.strip() for k in a["keys"].split(",") if k.strip()],
        "concurrency": a.getint("concurrency"),
        "max_retries": a.getint("max_retries"),
        "backoff_cap": a.getint("backoff_cap"),
        "timeout": a.getint("timeout"),
        "save_every": a.getint("save_every"),
        "retry_status": [int(s) for s in a["retry_status"].split(",")],
    }


def main(args):
    cfg = load_config(args.config)
    keys = Keys(cfg["keys"])
    reqs = json.load(open(args.requests, encoding="utf-8"))
    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)
    results_path, errors_path, keylog_path = out / "results.json", out / "errors.json", out / "key_log.json"
    results = json.load(open(results_path, encoding="utf-8")) if results_path.exists() else []
    done = {r["id"] for r in results}
    todo = [r for r in reqs if r["id"] not in done]
    print(f"{len(reqs)} requests | {len(done)} already done | {len(todo)} to run", flush=True)
    errors, lock, stop = [], threading.Lock(), threading.Event()

    def flush():
        save(results_path, results)
        save(errors_path, errors)
        if keys.log:
            save(keylog_path, keys.log)

    def one(req):
        if stop.is_set():
            return "skipped"
        payload = {**req["settings"], "messages": req["messages"]}
        t0 = time.perf_counter()
        try:
            data, index = call(cfg, keys, payload)
        except OutOfKeys as e:
            stop.set()
            with lock:
                errors.append({"id": req["id"], "error": f"all keys exhausted: {e}"})
            return "out_of_keys"
        except RuntimeError as e:
            with lock:
                errors.append({"id": req["id"], "error": str(e)})
            return "error"
        choice = data["choices"][0]
        msg = choice.get("message") or {}
        rec = {
            "id": req["id"],
            "condition": req["condition"],
            "meta": req["meta"],
            "request": payload,
            "key": index + 1,
            "content": msg.get("content"),
            "reasoning_content": msg.get("reasoning_content"),
            "finish_reason": choice.get("finish_reason"),
            "usage": data.get("usage") or {},
            "latency_s": round(time.perf_counter() - t0, 3),
            "time": now(),
        }
        with lock:
            results.append(rec)
            if len(results) % cfg["save_every"] == 0:
                flush()
        return "ok"

    status = {"ok": 0, "error": 0, "out_of_keys": 0, "skipped": 0}
    try:
        with ThreadPoolExecutor(max_workers=cfg["concurrency"]) as pool:
            futures = [pool.submit(one, r) for r in todo]
            for n, f in enumerate(as_completed(futures), 1):
                status[f.result()] += 1
                if n % 10 == 0 or n == len(futures):
                    print(f"\r{n}/{len(futures)} {status}", end="", flush=True)
    finally:
        with lock:
            flush()
    print(f"\ndone: {status}")
    if status["out_of_keys"] or status["skipped"]:
        print("all API keys exhausted; add a key to config/run.cfg and re-run the same command to continue")
    elif status["error"]:
        print(f"see {errors_path}; re-run the same command to retry")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--requests", required=True)
    ap.add_argument("--output", default=str(HERE / "outputs"))
    ap.add_argument("--config", default=str(HERE / "config" / "run.cfg"))
    main(ap.parse_args())
