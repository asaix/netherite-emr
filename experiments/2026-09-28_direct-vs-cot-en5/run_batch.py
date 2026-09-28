"""Send a JSONL file of requests to the Sarvam API and save every response.

Input  (JSONL, one request per line):
  {"id": "...", "condition": "direct|cot",
   "messages": [{"role": "user", "content": "..."}],
   "meta": {...}}

Output (JSONL, one result per line, append-only).

Resumable: ids already in the output file are skipped, so re-running the
same command retries only what failed.

  python run_batch.py --input requests.jsonl --output runs/exp1.jsonl
"""
import argparse
import asyncio
import json
import os
import random
import time
from datetime import datetime, timezone

import httpx
from dotenv import load_dotenv
from tqdm.asyncio import tqdm_asyncio

load_dotenv()

API_URL = os.getenv("SARVAM_API_URL", "https://api.sarvam.ai/v1/chat/completions")
API_KEY = os.getenv("SARVAM_API_KEY")
MODEL = "sarvam-105b"

# Output budget per condition. Reasoning is disabled everywhere, so the only
# thing that varies is how much room the answer itself needs.
MAX_TOKENS = 4096 # assumed account cap.  

RETRY_STATUS = {429, 500, 502, 503, 504}


async def call_api(client, payload, max_retries=6):
    """One request, with backoff on rate limits and transient failures."""
    headers = {"api-subscription-key": API_KEY, "Content-Type": "application/json"}
    last_err = None

    for attempt in range(max_retries):
        try:
            r = await client.post(API_URL, json=payload, headers=headers, timeout=180)
        except (httpx.TimeoutException, httpx.TransportError) as e:
            last_err = repr(e)
        else:
            if r.status_code == 200:
                return r.json()
            if r.status_code not in RETRY_STATUS:
                raise RuntimeError(f"HTTP {r.status_code}: {r.text[:300]}")
            last_err = f"HTTP {r.status_code}"

        await asyncio.sleep(min(60, 2 ** attempt) + random.uniform(0, 1))

    raise RuntimeError(f"gave up after {max_retries} attempts: {last_err}")


async def worker(req, client, sem, lock, out_f, err_f, args):
    payload = {
        "model": MODEL,
        "messages": req["messages"],
        "reasoning_effort": None,
        "max_tokens": MAX_TOKENS,
        "temperature": args.temperature,
        "top_p": 1.0,
    }

    async with sem:
        t0 = time.perf_counter()
        try:
            data = await call_api(client, payload)
        except RuntimeError as e:
            async with lock:
                err_f.write(json.dumps({"id": req["id"], "error": str(e)}) + "\n")
                err_f.flush()
            return False
        latency = time.perf_counter() - t0

    choice = data["choices"][0]
    msg = choice.get("message") or {}
    rec = {
        "id": req["id"],
        "condition": req["condition"],
        "meta": req.get("meta", {}),
        "request": payload,
        "content": msg.get("content"),
        # Always expected to be null. If it is ever non-null, thinking was on
        # and the run is invalid - worth keeping as a cheap tripwire.
        "reasoning_content": msg.get("reasoning_content"),
        "finish_reason": choice.get("finish_reason"),
        "usage": data.get("usage") or {},
        "latency_s": round(latency, 3),
        "time": datetime.now(timezone.utc).isoformat(),
    }

    async with lock:
        out_f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        out_f.flush()
    return True


async def main(args):
    if not API_KEY:
        raise SystemExit("SARVAM_API_KEY not set (check .env)")

    with open(args.input, encoding="utf-8") as f:
        reqs = [json.loads(line) for line in f if line.strip()]

    ids = [r["id"] for r in reqs]
    if len(ids) != len(set(ids)):
        raise SystemExit("duplicate ids in input")
    unknown = {r["condition"] for r in reqs} - {"direct", "cot"}
    if unknown:
        raise SystemExit(f"unknown conditions: {unknown}")

    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
    errors_path = args.output.replace(".jsonl", "") + ".errors.jsonl"

    done = set()
    if os.path.exists(args.output):
        with open(args.output, encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    done.add(json.loads(line)["id"])

    todo = [r for r in reqs if r["id"] not in done]
    print(f"{len(reqs)} requests | {len(done)} already done | {len(todo)} to run")

    sem = asyncio.Semaphore(args.concurrency)
    lock = asyncio.Lock()
    async with httpx.AsyncClient() as client:
        with open(args.output, "a", encoding="utf-8") as out_f, \
             open(errors_path, "a", encoding="utf-8") as err_f:
            results = await tqdm_asyncio.gather(
                *[worker(r, client, sem, lock, out_f, err_f, args) for r in todo])

    failed = results.count(False)
    print(f"{len(todo) - failed} ok, {failed} failed")
    if failed:
        print(f"see {errors_path}; re-run the same command to retry")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--concurrency", type=int, default=2)
    ap.add_argument("--temperature", type=float, default=0.0)
    asyncio.run(main(ap.parse_args()))