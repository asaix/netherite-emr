import argparse
import asyncio
import json
import os
import random
import time
from datetime import datetime, timezone
from pathlib import Path

import httpx
import yaml
from tqdm.asyncio import tqdm_asyncio


def load(input_path, prompts_path, problems_per_task):
    # input_path: str, dataset dir or one <difficulty>/<task>_<lang>.json file
    # prompts_path: str
    # problems_per_task: int, first N question ids taken from each file
    # returns: list[dict], each shaped as
    #   {"id": str, "condition": str,
    #    "messages": [{"role": "user", "content": str}], "meta": dict}
    with open(prompts_path, encoding="utf-8") as f:
        prompts = yaml.safe_load(f)

    root = Path(input_path)
    reqs = []
    for path in sorted(root.rglob("*.json")) if root.is_dir() else [root]:
        difficulty = path.parent.name
        task, lang, region = path.stem.rsplit("_", 2)
        language = prompts["languages"][f"{lang}_{region}"]
        answer_format = prompts["formats"][task].format(language=language)
        with open(path, encoding="utf-8") as f:
            questions = json.load(f)

        for qid, q in list(questions.items())[:problems_per_task]:
            for insertion in ("no_insertion", "similar_insertion", "dissimilar_insertion"):
                for mode, instruction in prompts["modes"].items():
                    content = prompts["template"].format(
                        mode=instruction, language=language, format=answer_format, question=q[insertion])
                    reqs.append({
                        "id": f"{difficulty}/{path.stem}/{qid}/{insertion}/{mode}",
                        "condition": mode,
                        "messages": [{"role": "user", "content": content}],
                        "meta": {
                            "difficulty": difficulty,
                            "task": task,
                            "language": f"{lang}_{region}",
                            "question_id": qid,
                            "insertion": insertion,
                            "answer": q["answer"],
                        },
                    })
    return reqs


async def call_api(client, cfg, payload):
    headers = {"api-subscription-key": cfg["api_key"], "Content-Type": "application/json"}
    last_err = None

    for attempt in range(cfg["max_retries"]):
        try:
            r = await client.post(cfg["api_url"], json=payload, headers=headers, timeout=cfg["timeout"])
        except (httpx.TimeoutException, httpx.TransportError) as e:
            last_err = repr(e)
        else:
            if r.status_code == 200:
                return r.json()
            if r.status_code not in cfg["retry_status"]:
                raise RuntimeError(f"HTTP {r.status_code}: {r.text[:300]}")
            last_err = f"HTTP {r.status_code}"

        await asyncio.sleep(min(cfg["backoff_cap"], 2 ** attempt) + random.uniform(0, 1))

    raise RuntimeError(f"gave up after {cfg['max_retries']} attempts: {last_err}")


async def worker(req, client, cfg, sem, lock, out_f, err_f):
    payload = {
        "model": cfg["model"],
        "messages": req["messages"],
        "reasoning_effort": cfg["reasoning_effort"],
        "max_tokens": cfg["max_tokens"][req["condition"]],
        "temperature": cfg["temperature"],
        "top_p": cfg["top_p"],
    }

    async with sem:
        t0 = time.perf_counter()
        try:
            data = await call_api(client, cfg, payload)
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
    with open(args.config, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    with open(args.general, encoding="utf-8") as f:
        general = yaml.safe_load(f)

    reqs = load(args.input, args.prompts, general["problems_per_task"])

    ids = [r["id"] for r in reqs]
    if len(ids) != len(set(ids)):
        raise SystemExit("duplicate ids in input")
    unknown = {r["condition"] for r in reqs} - cfg["max_tokens"].keys()
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

    sem = asyncio.Semaphore(cfg["concurrency"])
    lock = asyncio.Lock()
    async with httpx.AsyncClient() as client:
        with open(args.output, "a", encoding="utf-8") as out_f, \
             open(errors_path, "a", encoding="utf-8") as err_f:
            results = await tqdm_asyncio.gather(
                *[worker(r, client, cfg, sem, lock, out_f, err_f) for r in todo])

    failed = results.count(False)
    print(f"{len(todo) - failed} ok, {failed} failed")
    if failed:
        print(f"see {errors_path}; re-run the same command to retry")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="config/sarvam.yaml")
    ap.add_argument("--prompts", default="config/prompt.yaml")
    ap.add_argument("--general", default="config/general.yaml")
    ap.add_argument("--input", required=True)
    ap.add_argument("--output", required=True)
    asyncio.run(main(ap.parse_args()))
