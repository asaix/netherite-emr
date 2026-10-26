import argparse
import json
import os
import re
import sys
import threading
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

ANSWER = re.compile(r"(?:Answer|उत्तर(?:\s*है)?|जवाब)\s*\**\s*[:：]\s*(.*)")
DIGITS = str.maketrans("०१२३४५६७८९", "0123456789")
DECODING = {"temperature": 0.0, "top_p": 1.0, "max_tokens": 4096, "seed": 0}
CONTINUE = {"continue_final_message": True, "add_generation_prompt": False, "chat_template_kwargs": {"enable_thinking": False}}
FRESH = {"add_generation_prompt": True, "chat_template_kwargs": {"enable_thinking": False}}
EMPTY_THINK = {"role": "assistant", "content": "<think></think>"}
REPEAT_ITEMS = 234
BUDGET_STOP = 3


def answer(text):
    m = ANSWER.findall(text or "")
    return m[-1].strip().strip("*`.। ").translate(DIGITS) if m else None


def chat(args, messages, mode):
    payload = {"model": args.model, "messages": messages, **DECODING, **mode}
    req = urllib.request.Request(f"{args.url}/v1/chat/completions", data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"})
    err = None
    for attempt in range(4):
        try:
            t0 = time.perf_counter()
            with urllib.request.urlopen(req, timeout=1800) as r:
                data = json.load(r)
            choice = data["choices"][0]
            return {"content": choice["message"].get("content") or "", "reasoning_content": choice["message"].get("reasoning_content"),
                    "finish_reason": choice.get("finish_reason"), "usage": data.get("usage") or {}, "latency_s": round(time.perf_counter() - t0, 3)}
        except (urllib.error.URLError, OSError) as e:
            err = repr(e)
            time.sleep(5 * (attempt + 1))
    raise RuntimeError(err)


def save(path, data):
    tmp = Path(str(path) + ".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    os.replace(tmp, path)


def run_batch(args, items, path, extra=0):
    results = json.load(open(path, encoding="utf-8")) if path.exists() else []
    done = {r["id"] for r in results}
    todo = [it for it in items if it["id"] not in done]
    print(f"{len(items)} items | {len(done)} done | {len(todo)} to run | concurrency {args.concurrency}", flush=True)
    lock, stop = threading.Lock(), threading.Event()
    state = {"n": 0, "t0": time.time()}

    def one(it):
        if stop.is_set():
            return
        out = chat(args, it["messages"], CONTINUE)
        rec = {"id": it["id"], "condition": "cot", "meta": it["meta"], "prefix_chars": len(it["messages"][-1]["content"]),
               "decoding": {**DECODING, **CONTINUE}, "concurrency": args.concurrency, **out, "time": datetime.now(timezone.utc).isoformat()}
        with lock:
            results.append(rec)
            state["n"] += 1
            n = state["n"]
            elapsed = time.time() - state["t0"]
            per = elapsed / n
            left = len(todo) - n
            if n % 10 == 0 or left == 0:
                save(path, results)
                print(f"{n}/{len(todo)} | {per:.1f} s per request | this run ends in ~{left * per / 60:.0f} min"
                      + (f" | then {extra} more requests ~{extra * per / 60:.0f} min" if extra else ""), flush=True)
            if args.budget_minutes and n >= 30 and not stop.is_set():
                projected = (elapsed + (left + extra) * per) / 60
                if projected > args.budget_minutes:
                    stop.set()
                    print(f"BUDGET STOP: at {per:.1f} s per request the remaining {left + extra} requests would end at ~{projected:.0f} min, over the {args.budget_minutes} min budget", flush=True)

    with ThreadPoolExecutor(max_workers=args.concurrency) as pool:
        list(pool.map(one, todo))
    save(path, results)
    return results, stop.is_set()


def sanity(args, reqs):
    checks, info, log = {}, {}, {}
    a_reqs = [r for r in reqs if r["meta"]["version"] == "A"]
    hi = [r for r in a_reqs if r["meta"]["language"] == "hi_IN"]
    en = [r for r in a_reqs if r["meta"]["language"] == "en_US"]

    paris = [{"role": "user", "content": "Write one sentence about the capital of France."}, {"role": "assistant", "content": "The capital of France is Par"}]
    c = chat(args, paris, CONTINUE)["content"]
    log["split_word"] = c
    checks["true continuation: 'The capital of France is Par' is not restarted"] = not c.lstrip().lower().startswith("the capital")

    raw = [chat(args, r["messages"][:1], FRESH) for r in (hi[0], en[0])]
    log["fresh_without_prefill"] = [{"content": x["content"][:300], "finish_reason": x["finish_reason"], "completion_tokens": x["usage"].get("completion_tokens")} for x in raw]
    prefilled = [chat(args, [r["messages"][0], EMPTY_THINK], CONTINUE) for r in (hi[0], en[0])]
    log["fresh_with_empty_think"] = [{"content": x["content"][:600], "finish_reason": x["finish_reason"]} for x in prefilled]
    checks["fresh answers with the empty <think></think> pre-filled end with an Answer line and contain no <think>"] = all(answer(x["content"]) and "<think>" not in x["content"] for x in prefilled)

    full = []
    for r in hi[1:4] + en[1:4]:
        out = chat(args, r["messages"], CONTINUE)
        head = r["messages"][-1]["content"].strip()[:40]
        full.append({"id": r["id"], "answer": answer(out["content"]), "original_api_answer": r["meta"]["original_answer"], "gold": r["meta"]["answer"],
                     "finish_reason": out["finish_reason"], "completion_tokens": out["usage"].get("completion_tokens"), "latency_s": out["latency_s"],
                     "restarted": len(head) == 40 and head in out["content"][:600], "start": out["content"][:200]})
    log["full_continuations"] = full
    checks["continuations run to an Answer line and stop normally (at least 5 of 6)"] = sum(bool(f["answer"]) and f["finish_reason"] == "stop" for f in full) >= 5
    checks["continuations do not restart the reasoning (at most 1 of 6)"] = sum(f["restarted"] for f in full) <= 1

    probe = hi[4:8] + en[4:8]
    first = [chat(args, r["messages"], CONTINUE) for r in probe]
    second = [chat(args, r["messages"], CONTINUE) for r in probe]
    same_text = sum(x["content"] == y["content"] for x, y in zip(first, second))
    same_answer = sum(answer(x["content"]) == answer(y["content"]) for x, y in zip(first, second))
    per = sum(x["latency_s"] for x in first + second) / (2 * len(probe))
    minutes = per * (len(reqs) + REPEAT_ITEMS) / 60
    info["one at a time, same request twice: identical text"] = f"{same_text}/{len(probe)}"
    info["one at a time, same request twice: same answer"] = f"{same_answer}/{len(probe)}"
    info["one at a time: seconds per request"] = round(per, 2)
    info["one at a time: projected minutes for the main + repeat runs"] = round(minutes)
    mode = "sequential" if same_text >= len(probe) - 1 else "batched"
    info["recommended mode"] = mode
    save(Path(args.out) / "sanity.json", {"checks": checks, "info": info, "mode": mode, "log": log})

    print(f"split word -> {log['split_word'][:120]!r}")
    for x in log["fresh_without_prefill"]:
        print(f"fresh without pre-fill -> {x['content'][:80]!r} finish={x['finish_reason']} tokens={x['completion_tokens']}")
    for x in log["fresh_with_empty_think"]:
        print(f"fresh with <think></think> -> answer {answer(x['content'])!r} finish={x['finish_reason']}")
    for f in full:
        print(f"{f['id']}: answer {f['answer']} | API original {f['original_api_answer']} | gold {f['gold']} | {f['finish_reason']} | {f['completion_tokens']} tokens | {f['latency_s']} s | restarted={f['restarted']}")
    for name, ok in checks.items():
        print(f"[{'PASS' if ok else 'FAIL'}] {name}")
    for name, value in info.items():
        print(f"[INFO] {name}: {value}")
    print(f"MODE: {mode}")
    print("SANITY:", "PASS" if all(checks.values()) else "FAIL")


def main(args):
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    reqs = json.load(open(args.requests, encoding="utf-8"))
    if args.mode == "sanity":
        sanity(args, reqs)
        return 0
    if args.mode == "main":
        res, stopped = run_batch(args, reqs, out / "results.json", extra=REPEAT_ITEMS)
        if stopped:
            return BUDGET_STOP
        print(f"done: {len(res)} results, {sum(not answer(r['content']) for r in res)} without an Answer line, {sum(r['finish_reason'] == 'length' for r in res)} cut off")
        return 0
    res, stopped = run_batch(args, [r for r in reqs if r["meta"]["version"] == "A"], out / "results_repeat.json")
    if stopped:
        return BUDGET_STOP
    main_a = {r["id"]: r["content"] for r in json.load(open(out / "results.json", encoding="utf-8"))}
    same = sum(main_a.get(r["id"]) == r["content"] for r in res)
    same_answer = sum(answer(main_a.get(r["id"])) == answer(r["content"]) for r in res)
    print(f"done: {len(res)} repeats, identical text {same}/{len(res)}, same answer {same_answer}/{len(res)}")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["sanity", "main", "repeat"], required=True)
    ap.add_argument("--requests", default="requests_cap1000.json")
    ap.add_argument("--out", default="selfhost")
    ap.add_argument("--url", default="http://127.0.0.1:3002")
    ap.add_argument("--model", default="sarvam-105b-fp8")
    ap.add_argument("--concurrency", type=int, default=1)
    ap.add_argument("--budget-minutes", type=float, default=None)
    sys.exit(main(ap.parse_args()))
