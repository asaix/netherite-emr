import argparse
import json
from collections import Counter
from pathlib import Path

from build_requests import HERE, M

EXPECTED = 60


def main(args):
    out = Path(args.output)
    pilot_ids = {r["id"] for r in json.load(open(HERE / "outputs" / "requests_pilot.json", encoding="utf-8"))}
    requests = {r["id"]: r for r in json.load(open(HERE / "outputs" / "requests_pilot.json", encoding="utf-8"))}
    results = [r for r in json.load(open(out / "results.json", encoding="utf-8")) if r["id"] in pilot_ids]
    errors = json.load(open(out / "errors.json", encoding="utf-8")) if (out / "errors.json").exists() else []
    unanswered, restarts, same, correct = [], [], [], Counter()
    for r in results:
        content = r["content"] or ""
        answer = M.extract_answer(content)
        v = r["meta"]["version"]
        if answer is None or r.get("finish_reason") == "length":
            unanswered.append(r["id"])
        prefix = requests[r["id"]]["messages"][1]["content"].strip()
        head = prefix[:40]
        if len(head) == 40 and head in content[:600]:
            restarts.append(r["id"])
        if v == "A":
            same.append(answer == r["meta"]["original_answer"])
        correct[v] += bool(answer is not None and M.is_correct(r))
    agreement = sum(same) / len(same) if same else 0
    checks = {
        f"all {EXPECTED} pilot requests answered by the API": len(results) == EXPECTED,
        "no API errors": not [e for e in errors if e["id"] in pilot_ids],
        "at most 2 continuations without an Answer line or cut off": len(unanswered) <= 2,
        "at most 2 continuations restart from the beginning": len(restarts) <= 2,
        "version A reproduces the original answer in at least 60% of traces": agreement >= 0.6,
    }
    print(f"results {len(results)}/{EXPECTED} | versions {dict(Counter(r['meta']['version'] for r in results))} | keys {dict(Counter(r.get('key') for r in results))}")
    print(f"unanswered/cut off: {len(unanswered)} {unanswered}")
    print(f"restarts: {len(restarts)} {restarts}")
    print(f"A = original answer: {sum(same)}/{len(same)} ({100 * agreement:.0f}%)")
    print(f"correct by version (of {len(same)} originally wrong traces): {dict(correct)}")
    for name, ok in checks.items():
        print(f"[{'PASS' if ok else 'FAIL'}] {name}")
    print("PILOT CHECK:", "PASS" if all(checks.values()) else "FAIL")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", default=str(HERE / "outputs"))
    main(ap.parse_args())
