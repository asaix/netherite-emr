import json
import math
import os
import re
import signal
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

WORK = Path(os.environ.get("WORK", "/home/trace-deletion"))
VENV = Path(os.environ.get("VENV", "/home/venv031"))
URL = os.environ.get("URL", "http://127.0.0.1:3002")
MODEL = "sarvam-105b-fp8"
CONFIGS = [
    {"name": "redhat_v031_default", "serve": "serve_rh.sh", "env": {"EXTRA_ARGS": ""}, "timeout": 1500, "needs_venv": True},
    {"name": "redhat_v031_triton_mla", "serve": "serve_rh.sh", "env": {"EXTRA_ARGS": "--attention-backend TRITON_MLA"}, "timeout": 1500, "needs_venv": True},
]
CALIBRATION = WORK / "calibration_requests.json"
CAL_CONCURRENCY = int(os.environ.get("CAL_CONCURRENCY", "16"))
CAL_MIN_FINISHED = 0.95
CAL_MAX_DROP = 0.10
CAL_MAX_DROP_LANG = 0.15
TEMPERATURE = float(os.environ.get("TEMPERATURE", "0.0"))
TOP_P = float(os.environ.get("TOP_P", "1.0"))
CAL_MAX_TOKENS = int(os.environ.get("CAL_MAX_TOKENS", "4096"))
CAL_MODE = os.environ.get("CAL_MODE", "gate")  # gate: must pass | info: run, never reject | skip
CAL_TAG = os.environ.get("CAL_TAG", "")
SKIP_SMOKE = os.environ.get("SKIP_SMOKE") == "1"
DIGITS = str.maketrans("०१२३४५६७८९٠١٢٣٤٥٦٧٨٩", "0123456789" * 2)
ANSWER_VALUE = re.compile(r"(?:Answer|उत्तर(?:\s*है)?|जवाब)\s*\**\s*[:：]\s*(.*)")
HINDI_TO = re.compile(r"\s+से\s+")
ANSWER = re.compile(r"(?:Answer|उत्तर(?:\s*है)?|जवाब)\s*\**\s*[:：]\s*\S")
SPECIAL = re.compile(r"<pad>|<eos>|<bos>|<unk>|<\|end_of_turn\|>")
EMPTY_THINK = {"role": "assistant", "content": "<think></think>"}
MAX_RUN = 20


def post(messages, max_tokens):
    payload = {"model": MODEL, "messages": messages, "temperature": TEMPERATURE, "top_p": TOP_P, "seed": 0, "max_tokens": max_tokens,
               "continue_final_message": True, "add_generation_prompt": False, "chat_template_kwargs": {"enable_thinking": False},
               "skip_special_tokens": False, "logprobs": True}
    req = urllib.request.Request(f"{URL}/v1/chat/completions", data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"})
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=900) as r:
            data = json.load(r)
    except urllib.error.HTTPError as e:
        return {"error": f"HTTP {e.code}: {e.read().decode(errors='replace')[:300]}"}
    if "choices" not in data:
        return {"error": f"no choices in response: {json.dumps(data)[:300]}"}
    c = data["choices"][0]
    lp = ((c.get("logprobs") or {}).get("content")) or []
    usage = data.get("usage") or {}
    return {"content": c["message"].get("content") or "", "finish_reason": c.get("finish_reason"), "tokens": usage.get("completion_tokens"),
            "prompt_tokens": usage.get("prompt_tokens"), "seconds": round(time.time() - t0, 2),
            "token_list": [t.get("token") for t in lp], "logprobs": [t.get("logprob") for t in lp]}


def longest_run(tokens):
    best = run = 0
    prev = object()
    for t in tokens:
        run = run + 1 if t == prev else 1
        prev = t
        best = max(best, run)
    return best


def problems_of(out, need_answer):
    if "error" in out:
        return [out["error"]]
    text, problems = out["content"], []
    visible = len(SPECIAL.sub("", text).strip())
    if SPECIAL.search(text):
        problems.append(f"special tokens in output ({len(SPECIAL.findall(text))})")
    if visible < 20:
        problems.append(f"only {visible} visible characters for {out['tokens']} tokens")
    bad = [x for x in out["logprobs"] if x is None or (isinstance(x, float) and (math.isnan(x) or math.isinf(x)))]
    if bad:
        problems.append(f"{len(bad)} NaN/inf/missing log-probabilities")
    if out["logprobs"] == [] and out["tokens"]:
        problems.append("no log-probabilities returned")
    run = longest_run(out["token_list"])
    if run > MAX_RUN:
        problems.append(f"the same token {run} times in a row")
    if need_answer and not ANSWER.search(text):
        problems.append("no Answer line")
    if need_answer and out["finish_reason"] != "stop":
        problems.append(f"finish_reason {out['finish_reason']}")
    return problems


def tests(reqs):
    a = [r for r in reqs if r["meta"]["version"] == "A"]
    hi = next(r for r in a if r["meta"]["language"] == "hi_IN")
    en = next(r for r in a if r["meta"]["language"] == "en_US")
    longest = max(a, key=lambda r: len(r["messages"][-1]["content"]))
    long_hi = [{"role": "user", "content": "हिंदी में लगभग 300 शब्दों में विस्तार से समझाइए कि दो तारीखों के बीच बीते दिनों की गिनती कैसे की जाती है, महीनों और लीप वर्ष का ध्यान रखते हुए।"},
               {"role": "assistant", "content": "दो तारीखों के बीच बीते दिनों की गिनती करने के लिए"}]
    return [
        ("short open-ended continuation", [{"role": "user", "content": "Write two sentences about the capital of France."}, {"role": "assistant", "content": "The capital of France is"}], 64, False, True),
        ("Hindi trace continuation (version A)", hi["messages"], 2048, True, True),
        ("English trace continuation (version A)", en["messages"], 2048, True, True),
        (f"longest trace prefix ({len(longest['messages'][-1]['content'])} characters, {longest['meta']['language']})", longest["messages"], 2048, True, True),
        ("long Hindi explanation (many 64-token blocks)", long_hi, 700, False, True),
        ("fresh Hindi answer with <think></think> pre-filled (informational)", [hi["messages"][0], EMPTY_THINK], 1536, True, False),
    ]


def extract(text):
    found = ANSWER_VALUE.findall(text or "")
    return HINDI_TO.sub(" to ", found[-1].strip().strip("*`.। ").translate(DIGITS)) if found else None


def calibrate(name):
    from concurrent.futures import ThreadPoolExecutor
    import threading
    items = json.load(open(CALIBRATION, encoding="utf-8"))
    print(f"  calibration: {len(items)} questions without distractor, fresh answers, {CAL_CONCURRENCY} at a time | temperature {TEMPERATURE} top_p {TOP_P} max_tokens {CAL_MAX_TOKENS} | mode {CAL_MODE}", flush=True)
    lock, rows = threading.Lock(), []

    def one(it):
        try:
            out = post(it["messages"], CAL_MAX_TOKENS)
        except Exception as e:
            out = {"error": f"request failed: {e!r}"}
        m = it["meta"]
        problems = problems_of(out, True)
        got = extract(out.get("content"))
        correct = got is not None and got.casefold() in m["accept"]
        row = {"id": it["id"], "language": m["language"], "task": m["task"], "difficulty": m["difficulty"], "gold": m["gold"], "answer": got,
               "correct": correct, "api_answer": m["api_answer"], "api_correct": m["api_correct"], "finished": not problems, "problems": problems,
               "tokens": out.get("tokens"), "seconds": out.get("seconds"), "content_start": (out.get("content") or "")[:300]}
        with lock:
            rows.append(row)
            print(f"  [cal {len(rows):02d}/{len(items)}] {m['language']} {m['task']}/{m['difficulty']} | {out.get('finish_reason')} | {out.get('tokens')} tok"
                  f" | answer {got!r} | gold {m['gold']!r} | {'correct' if correct else 'wrong'} | API {'correct' if m['api_correct'] else 'wrong'}"
                  + (f" | NOT FINISHED: {'; '.join(problems)}" if problems else ""), flush=True)

    with ThreadPoolExecutor(max_workers=CAL_CONCURRENCY) as pool:
        list(pool.map(one, items))
    n = len(rows)
    finished = sum(r["finished"] for r in rows)
    acc = sum(r["correct"] for r in rows) / n
    api = sum(r["api_correct"] for r in rows) / n
    b = sum(r["correct"] and not r["api_correct"] for r in rows)
    c = sum(r["api_correct"] and not r["correct"] for r in rows)
    from math import comb
    p = 1.0 if b + c == 0 else min(1.0, 2 * sum(comb(b + c, i) for i in range(min(b, c) + 1)) / 2 ** (b + c))
    langs = {}
    for lang in sorted({r["language"] for r in rows}):
        lr = [r for r in rows if r["language"] == lang]
        langs[lang] = {"n": len(lr), "self": sum(r["correct"] for r in lr) / len(lr), "api": sum(r["api_correct"] for r in lr) / len(lr),
                       "finished": sum(r["finished"] for r in lr)}
    checks = {
        f"finished (Answer line, stopped normally, no loop) >= {CAL_MIN_FINISHED:.0%}": finished >= CAL_MIN_FINISHED * n,
        f"accuracy at most {CAL_MAX_DROP:.0%} below the API's on the same questions": acc >= api - CAL_MAX_DROP,
        **{f"{lang}: accuracy at most {CAL_MAX_DROP_LANG:.0%} below the API's": v["self"] >= v["api"] - CAL_MAX_DROP_LANG for lang, v in langs.items()},
    }
    summary = {"config": name, "decoding": {"temperature": TEMPERATURE, "top_p": TOP_P, "max_tokens": CAL_MAX_TOKENS, "seed": 0}, "n": n, "finished": finished, "self_accuracy": acc, "api_accuracy": api, "self_only_correct": b, "api_only_correct": c,
               "mcnemar_p": p, "by_language": langs, "checks": checks, "pass": all(checks.values())}
    (WORK / "selfhost").mkdir(exist_ok=True)
    json.dump({"summary": summary, "rows": sorted(rows, key=lambda r: r["id"])}, open(WORK / "selfhost" / f"calibration_{name}{CAL_TAG}.json", "w"), indent=2, ensure_ascii=False)
    print(f"  calibration result: finished {finished}/{n} | accuracy self {acc:.1%} vs API {api:.1%} (self-only correct {b}, API-only correct {c}, McNemar p={p:.3g})", flush=True)
    for lang, v in langs.items():
        print(f"    {lang}: self {v['self']:.1%} vs API {v['api']:.1%}, finished {v['finished']}/{v['n']}", flush=True)
    for k, v in checks.items():
        print(f"  [{'PASS' if v else 'FAIL'}] {k}", flush=True)
    print(f"  CALIBRATION: {'PASS' if summary['pass'] else 'FAIL'}", flush=True)
    return summary["pass"], summary


def smoke(reqs):
    report, ok = [], True
    for name, messages, max_tokens, need_answer, blocking in tests(reqs):
        print(f"  running: {name} (max {max_tokens} tokens) ...", flush=True)
        try:
            out = post(messages, max_tokens)
        except Exception as e:
            out = {"error": f"request failed: {e!r}"}
        problems = problems_of(out, need_answer)
        slim = {k: v for k, v in out.items() if k not in ("token_list", "logprobs")}
        slim["content"] = out.get("content", "")[:1500]
        slim["longest_token_run"] = longest_run(out.get("token_list", []))
        report.append({"test": name, "blocking": blocking, "problems": problems, **slim})
        tag = "PASS" if not problems else ("FAIL" if blocking else "INFO")
        print(f"  [{tag}] {name}: prompt {out.get('prompt_tokens')} tok, output {out.get('tokens')} tok, {out.get('seconds')} s, finish={out.get('finish_reason')}"
              + (f" | problems: {'; '.join(problems)}" if problems else "") + f" | starts {out.get('content', '')[:90]!r}", flush=True)
        if problems and blocking:
            ok = False
            break
    return ok, report


FATAL = re.compile(r"Traceback|RuntimeError|ValueError|AssertionError|CUDA error|out of memory|EngineDeadError|Unsupported|NotImplementedError|ImportError|ModuleNotFoundError")


def serve_tail(start):
    try:
        with open(WORK / "serve.log", "rb") as f:
            f.seek(start)
            return f.read().decode(errors="replace")
    except OSError:
        return ""


def ready(proc, timeout, log_start):
    t0, last_beat, printed, last_size, last_growth = time.time(), 0.0, 0, -1, time.time()
    while time.time() - t0 < timeout:
        elapsed = time.time() - t0
        new = serve_tail(log_start)
        lines = [l for l in re.split(r"[\r\n]+", new) if l.strip()]
        if proc.poll() is not None:
            for l in [l for l in lines if FATAL.search(l)][-5:]:
                print(f"  serve.log: {l[-220:]}", flush=True)
            return False, f"server exited with code {proc.returncode} after {elapsed:.0f} s"
        fatal = [l for l in lines if FATAL.search(l)]
        if len(fatal) > printed:
            for l in fatal[printed:][-5:]:
                print(f"  serve.log ERROR-LIKE LINE: {l[-220:]}", flush=True)
            printed = len(fatal)
        if len(new) != last_size:
            last_size, last_growth = len(new), time.time()
        if fatal and time.time() - last_growth > 60:
            return False, f"error in serve.log and the log stopped growing for 60 s (at {elapsed:.0f} s)"
        try:
            with urllib.request.urlopen(f"{URL}/v1/models", timeout=5) as r:
                if r.status == 200:
                    return True, f"ready after {elapsed:.0f} s"
        except OSError:
            pass
        if time.time() - last_beat >= 30:
            last_beat = time.time()
            print(f"  waiting for server: {elapsed:.0f} s / {timeout} s | serve.log: {(lines[-1][-160:] if lines else '(empty)')!r}", flush=True)
        time.sleep(5)
    return False, f"not ready after {timeout} s"


def port_busy():
    try:
        urllib.request.urlopen(f"{URL}/v1/models", timeout=3)
        return True
    except OSError:
        return False


def stop(proc):
    if proc.poll() is None:
        os.killpg(proc.pid, signal.SIGTERM)
        try:
            proc.wait(timeout=120)
        except subprocess.TimeoutExpired:
            os.killpg(proc.pid, signal.SIGKILL)
            proc.wait()
    if shutil.which("nvidia-smi"):
        for _ in range(36):
            used = subprocess.run(["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"], capture_output=True, text=True).stdout.split()
            if used and max(map(int, used)) < 2000:
                break
            time.sleep(5)


def save(results, chosen):
    json.dump({"chosen": chosen, "attempts": results}, open(WORK / "bringup.json", "w"), indent=2, ensure_ascii=False)


def main():
    reqs = json.load(open(WORK / "requests_cap1000.json", encoding="utf-8"))
    only = sys.argv[1:] or [c["name"] for c in CONFIGS]
    results = []
    if port_busy():
        print("BRINGUP: FAIL (a server is already answering on port 3002; stop it first)", flush=True)
        return 1
    for cfg in [c for c in CONFIGS if c["name"] in only]:
        print(f"=== config {cfg['name']}: {cfg['serve']} {cfg['env']}", flush=True)
        if cfg.get("needs_venv") and not (VENV / "bin" / "vllm").exists():
            print(f"  skipped: {VENV}/bin/vllm not found (setup031 not done)", flush=True)
            results.append({"config": cfg, "skipped": "no venv"})
            continue
        if cfg.get("pre"):
            pre = subprocess.run(cfg["pre"], cwd=WORK, capture_output=True, text=True)
            print("  pre-step:", (pre.stdout + pre.stderr).strip().replace("\n", " | ")[-400:], flush=True)
            if pre.returncode != 0:
                results.append({"config": cfg, "pre_failed": pre.stdout + pre.stderr})
                continue
        with open(WORK / "serve.log", "a") as log:
            log.write(f"\n===== bringup config {cfg['name']} {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())} =====\n")
        log_start = (WORK / "serve.log").stat().st_size
        log = open(WORK / "serve.log", "a")
        proc = subprocess.Popen(["bash", str(WORK / cfg["serve"])], stdout=log, stderr=subprocess.STDOUT,
                                env={**os.environ, **cfg["env"]}, cwd=WORK, start_new_session=True)
        is_ready, note = ready(proc, int(os.environ.get("READY_TIMEOUT", cfg["timeout"])), log_start)
        print(f"  server: {note}", flush=True)
        entry = {"config": cfg, "ready": is_ready, "note": note}
        if is_ready:
            if SKIP_SMOKE:
                ok, report = True, "skipped (SKIP_SMOKE=1)"
                print("  smoke test skipped (SKIP_SMOKE=1)", flush=True)
            else:
                ok, report = smoke(reqs)
            entry.update({"smoke_pass": ok, "smoke": report})
            if ok and proc.poll() is None and CAL_MODE != "skip":
                cal_ok, cal = calibrate(cfg["name"])
                entry.update({"calibration_pass": cal_ok, "calibration": cal})
                if CAL_MODE == "gate":
                    ok = cal_ok
                else:
                    print(f"  calibration is informational (CAL_MODE={CAL_MODE}); the server stays up whatever the result", flush=True)
            if ok and proc.poll() is None:
                entry["server_pid"] = proc.pid
                results.append(entry)
                save(results, cfg)
                print(f"BRINGUP: PASS {cfg['name']} (server left running, pid {proc.pid})", flush=True)
                return 0
        results.append(entry)
        save(results, None)
        stop(proc)
    save(results, None)
    print("BRINGUP: FAIL (no configuration produced healthy output)", flush=True)
    return 1


if __name__ == "__main__":
    sys.exit(main())
