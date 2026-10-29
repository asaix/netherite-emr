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
DECODING = {}  # filled from --temperature / --top-p / --max-tokens in main()
CONTINUE = {"continue_final_message": True, "add_generation_prompt": False, "chat_template_kwargs": {"enable_thinking": False}}
FRESH = {"add_generation_prompt": True, "chat_template_kwargs": {"enable_thinking": False}}
EMPTY_THINK = {"role": "assistant", "content": "<think></think>"}
REPEAT_ITEMS = 234
ERROR_STOP = 5
BUDGET_STOP = 3
DEGENERATE_STOP = 4


RUNAWAY_STOP_SHARE = 0.30


def degenerate(out):
    # broken server output (empty / a few characters, e.g. <pad> garbage): this is what stops a run
    return len((out.get("content") or "").strip()) < 20


def runaway(out):
    # the model kept reasoning until the token limit without an Answer line: recorded, counted as no answer, does not stop the run
    return out.get("finish_reason") == "length" and not answer(out.get("content"))


def broken(out):
    return not (out.get("content") or "").strip()


def answer(text):
    m = ANSWER.findall(text or "")
    return m[-1].strip().strip("*`.। ").translate(DIGITS) if m else None


def chat(args, messages, mode):
    payload = {"model": args.model, "messages": messages, **DECODING, **mode}
    req = urllib.request.Request(f"{args.url}/v1/chat/completions", data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"})
    err = None
    for attempt in range(3):
        try:
            t0 = time.perf_counter()
            with urllib.request.urlopen(req, timeout=1800) as r:
                data = json.load(r)
            choice = data["choices"][0]
            return {"content": choice["message"].get("content") or "", "reasoning_content": choice["message"].get("reasoning_content"),
                    "finish_reason": choice.get("finish_reason"), "usage": data.get("usage") or {}, "latency_s": round(time.perf_counter() - t0, 3)}
        except (urllib.error.URLError, OSError) as e:
            err = repr(e)
            time.sleep(2 * (attempt + 1))
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
    state = {"n": 0, "t0": time.time(), "bad": 0, "runaway": 0, "why": None, "errors": 0}
    label = "repeat" if path.name == "results_repeat.json" else "main"

    def one(it):
        if stop.is_set():
            return
        try:
            out = chat(args, it["messages"], CONTINUE)
        except Exception as e:
            with lock:
                state["errors"] += 1
                print(f"[{label}] ERROR {it['id']}: {e!r} ({state['errors']} in a row)", flush=True)
                if state["errors"] >= 3 and not stop.is_set():
                    stop.set()
                    state["why"] = "error"
                    print("ERROR STOP: 3 requests in a row failed; the server is probably down", flush=True)
            return
        rec = {"id": it["id"], "condition": "cot", "meta": it["meta"], "prefix_chars": len(it["messages"][-1]["content"]),
               "decoding": {**DECODING, **CONTINUE}, "concurrency": args.concurrency, **out, "time": datetime.now(timezone.utc).isoformat()}
        with lock:
            results.append(rec)
            state["n"] += 1
            state["errors"] = 0
            n = state["n"]
            bad = degenerate(out)
            ran = runaway(out)
            state["bad"] += bad
            state["runaway"] += ran
            m = it["meta"]
            got = answer(out["content"])
            print(f"[{label} {n:03d}/{len(todo)}] {it['id']} | {out['finish_reason']} | {out['usage'].get('completion_tokens')} tok | {out['latency_s']} s"
                  f" | answer {got!r} | gold {m['answer']!r} | {'correct' if got == m['answer'] else 'wrong'}"
                  f" | {len(out['content'].strip())} chars" + (" | BAD OUTPUT" if bad else "") + (" | RUNAWAY (token limit, no answer)" if ran else ""), flush=True)
            if not stop.is_set() and ((n <= 20 and state["bad"] >= 3) or (n >= 50 and state["bad"] > 0.1 * n)):
                stop.set()
                state["why"] = "degenerate"
                print(f"DEGENERATE STOP: {state['bad']} of {n} outputs are empty or nearly empty (broken server output)", flush=True)
            if not stop.is_set() and n >= 50 and state["runaway"] > RUNAWAY_STOP_SHARE * n:
                stop.set()
                state["why"] = "degenerate"
                print(f"RUNAWAY STOP: {state['runaway']} of {n} outputs ran to the {DECODING['max_tokens']}-token limit without an answer (over {RUNAWAY_STOP_SHARE:.0%})", flush=True)
            elapsed = time.time() - state["t0"]
            per = elapsed / n
            left = len(todo) - n
            if n % 10 == 0 or left == 0:
                save(path, results)
                print(f"{n}/{len(todo)} | runaways so far {state['runaway']} | broken {state['bad']} | {per:.1f} s per request | this run ends in ~{left * per / 60:.0f} min"
                      + (f" | then {extra} more requests ~{extra * per / 60:.0f} min" if extra else ""), flush=True)
            if args.budget_minutes and n >= 30 and not stop.is_set():
                projected = (elapsed + (left + extra) * per) / 60
                if projected > args.budget_minutes:
                    stop.set()
                    state["why"] = "budget"
                    print(f"BUDGET STOP: at {per:.1f} s per request the remaining {left + extra} requests would end at ~{projected:.0f} min, over the {args.budget_minutes} min budget", flush=True)

    with ThreadPoolExecutor(max_workers=args.concurrency) as pool:
        list(pool.map(one, todo))
    save(path, results)
    return results, state["why"]


def sanity(args, reqs):
    checks, info, log = {}, {}, {}
    a_reqs = [r for r in reqs if r["meta"]["version"] == "A"]
    hi = [r for r in a_reqs if r["meta"]["language"] == "hi_IN"]
    en = [r for r in a_reqs if r["meta"]["language"] == "en_US"]
    total, count = 11, [0]

    def step(label, messages, mode, essential=True):
        try:
            out = chat(args, messages, mode)
        except Exception as e:
            print(f"SANITY: FAIL (request {count[0] + 1} of {total}, {label!r}: the server did not answer: {e!r})", flush=True)
            sys.exit(ERROR_STOP)
        count[0] += 1
        text, bad = out["content"], broken(out)
        print(f"[sanity {count[0]:02d}/{total}] {label} | finish={out['finish_reason']} | {out['usage'].get('completion_tokens')} tokens | {out['latency_s']} s"
              f" | {len(text.strip())} visible chars | answer {answer(text)!r} | starts {text[:80]!r}" + (" | BAD OUTPUT" if bad else ""), flush=True)
        if bad and essential:
            save(Path(args.out) / "sanity.json", {"checks": {"stopped at the first bad output": False}, "aborted": True, "request": count[0], "label": label,
                                                   "finish_reason": out["finish_reason"], "completion_tokens": out["usage"].get("completion_tokens"), "content_start": text[:600], "log": log})
            print(f"SANITY: FAIL (stopped at request {count[0]} of {total}, {label!r}, to save GPU time: the server gives empty or unfinished output)", flush=True)
            sys.exit(DEGENERATE_STOP)
        return out

    paris = [{"role": "user", "content": "Write one sentence about the capital of France."}, {"role": "assistant", "content": "The capital of France is Par"}]
    c = step("split-word continuation", paris, CONTINUE)["content"]
    log["split_word"] = c
    checks["true continuation: 'The capital of France is Par' is not restarted"] = not c.lstrip().lower().startswith("the capital")

    full = []
    for i, r in enumerate(hi[1:4] + en[1:4], 1):
        out = step(f"trace continuation {i}/6 {r['id']}", r["messages"], CONTINUE)
        head = r["messages"][-1]["content"].strip()[:40]
        full.append({"id": r["id"], "answer": answer(out["content"]), "original_api_answer": r["meta"]["original_answer"], "gold": r["meta"]["answer"],
                     "finish_reason": out["finish_reason"], "completion_tokens": out["usage"].get("completion_tokens"), "latency_s": out["latency_s"],
                     "restarted": len(head) == 40 and head in out["content"][:600], "start": out["content"][:200]})
    log["full_continuations"] = full
    checks["continuations run to an Answer line and stop normally (at least 4 of 6)"] = sum(bool(f["answer"]) and f["finish_reason"] == "stop" for f in full) >= 4
    checks["continuations do not restart the reasoning (at most 1 of 6)"] = sum(f["restarted"] for f in full) <= 1

    checks["no continuation is empty"] = all(len(f["start"].strip()) >= 20 for f in full)
    info["continuations that ran to the token limit without an answer (counted as no answer in the main run)"] = sum(f["finish_reason"] == "length" and not f["answer"] for f in full)
    per = sum(f["latency_s"] for f in full) / len(full)
    info["one at a time: seconds per trace continuation"] = round(per, 2)
    info["decoding"] = dict(DECODING)
    mode = f"concurrency {args.concurrency}"

    raw = [step(f"fresh without pre-fill ({r['meta']['language']}, informational)", r["messages"][:1], FRESH, essential=False) for r in (hi[0], en[0])]
    log["fresh_without_prefill"] = [{"content": x["content"][:300], "finish_reason": x["finish_reason"], "completion_tokens": x["usage"].get("completion_tokens")} for x in raw]
    prefilled = [step(f"fresh with <think></think> pre-filled ({r['meta']['language']}, informational)", [r["messages"][0], EMPTY_THINK], CONTINUE, essential=False) for r in (hi[0], en[0])]
    log["fresh_with_empty_think"] = [{"content": x["content"][:600], "finish_reason": x["finish_reason"]} for x in prefilled]
    info["fresh answers with <think></think> pre-filled have an Answer line (not used by the experiment)"] = f"{sum(bool(answer(x['content'])) for x in prefilled)}/{len(prefilled)}"
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
    DECODING.update({"temperature": args.temperature, "top_p": args.top_p, "max_tokens": args.max_tokens, "seed": 0})
    print(f"decoding: {DECODING} | concurrency {args.concurrency}", flush=True)
    reqs = json.load(open(args.requests, encoding="utf-8"))
    if args.mode == "sanity":
        sanity(args, reqs)
        return 0
    if args.mode == "main":
        res, why = run_batch(args, reqs, out / "results.json", extra=REPEAT_ITEMS)
        if why:
            return {"degenerate": DEGENERATE_STOP, "error": ERROR_STOP}.get(why, BUDGET_STOP)
        print(f"done: {len(res)} results, {sum(not answer(r['content']) for r in res)} without an Answer line, {sum(r['finish_reason'] == 'length' for r in res)} cut off")
        return 0
    res, why = run_batch(args, [r for r in reqs if r["meta"]["version"] == "A"], out / "results_repeat.json")
    if why:
        return {"degenerate": DEGENERATE_STOP, "error": ERROR_STOP}.get(why, BUDGET_STOP)
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
    ap.add_argument("--temperature", type=float, required=True, help="0 = greedy; 0.8 = the value in Sarvam's model card")
    ap.add_argument("--top-p", type=float, required=True)
    ap.add_argument("--max-tokens", type=int, required=True)
    sys.exit(main(ap.parse_args()))
