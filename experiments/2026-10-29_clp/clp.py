import argparse
import asyncio
import json
import time
from datetime import datetime, timezone
from pathlib import Path

import httpx
import yaml
from tqdm import tqdm

from sarvam import call_api, save_json


def load(input_path, prompts_path, problems_per_task):
    with open(prompts_path, encoding="utf-8") as f:
        prompts = yaml.safe_load(f)
    clp = prompts["clp"]
    source = prompts["languages"][clp["source"]]
    target = prompts["languages"][clp["target"]]

    root = Path(input_path)
    reqs = []
    for path in sorted(root.rglob(f"*_{clp['source']}.json")) if root.is_dir() else [root]:
        difficulty = path.parent.name
        task, lang, region = path.stem.rsplit("_", 2)
        answer_format = prompts["formats"][task].format(language=source)
        with open(path, encoding="utf-8") as f:
            questions = json.load(f)

        for qid, q in list(questions.items())[:problems_per_task]:
            for insertion in ("no_insertion", "similar_insertion", "dissimilar_insertion"):
                reqs.append({
                    "id": f"{difficulty}/{path.stem}/{qid}/{insertion}/clp",
                    "condition": "clp",
                    "stage1": clp["stage1"].format(source=source, target=target, question=q[insertion]),
                    "stage2": clp["stage2"].format(target=target, task=clp["task"], format=answer_format),
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


async def stage(client, cfg, messages, max_tokens):
    payload = {
        "model": cfg["model"],
        "messages": messages,
        "reasoning_effort": cfg["reasoning_effort"],
        "max_tokens": max_tokens,
        "temperature": cfg["temperature"],
        "top_p": cfg["top_p"],
    }
    if cfg["reasoning_effort"] is not None:
        payload["stream"] = True
        payload["stream_options"] = {"include_usage": True}

    t0 = time.perf_counter()
    data = await call_api(client, cfg, payload)
    choice = data["choices"][0]
    msg = choice.get("message") or {}
    return {
        "message": messages[-1]["content"],
        "request": payload,
        "content": msg.get("content"),
        "reasoning_content": msg.get("reasoning_content"),
        "finish_reason": choice.get("finish_reason"),
        "usage": data.get("usage") or {},
        "latency_s": round(time.perf_counter() - t0, 3),
        "time": datetime.now(timezone.utc).isoformat(),
    }


async def worker(req, client, cfg, sem, results, errors, save, pbar):
    messages = [{"role": "user", "content": req["stage1"]}]
    name = "stage1"
    async with sem:
        try:
            first = await stage(client, cfg, messages, cfg["max_tokens"]["clp-stage1"])
            messages = messages + [
                {"role": "assistant", "content": first["content"] or ""},
                {"role": "user", "content": req["stage2"]},
            ]
            name = "stage2"
            second = await stage(client, cfg, messages, cfg["max_tokens"]["clp-stage2"])
        except RuntimeError as e:
            errors.append({"id": req["id"], "stage": name, "error": str(e)})
            save()
            pbar.write(f"error {req['id']} ({name}): {e}")
            pbar.set_postfix(errors=len(errors))
            pbar.update()
            return False

    results.append({
        "id": req["id"],
        "condition": req["condition"],
        "meta": req["meta"],
        "stage1": first,
        "stage2": second,
    })
    if len(results) % cfg["save_every"] == 0:
        save()
    pbar.update()
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

    out_dir = Path(args.output)
    out_dir.mkdir(parents=True, exist_ok=True)
    results_path, errors_path = out_dir / "results.json", out_dir / "errors.json"

    results = []
    if results_path.exists():
        with open(results_path, encoding="utf-8") as f:
            results = json.load(f)
    errors = []
    done = {r["id"] for r in results}

    todo = [r for r in reqs if r["id"] not in done]
    print(f"{len(reqs)} requests | {len(done)} already done | {len(todo)} to run")

    def save():
        save_json(results_path, results)
        save_json(errors_path, errors)

    sem = asyncio.Semaphore(cfg["concurrency"])
    try:
        with tqdm(total=len(todo), postfix={"errors": 0}) as pbar:
            async with httpx.AsyncClient() as client:
                ok = await asyncio.gather(
                    *[worker(r, client, cfg, sem, results, errors, save, pbar) for r in todo])
    finally:
        save()

    failed = ok.count(False)
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
