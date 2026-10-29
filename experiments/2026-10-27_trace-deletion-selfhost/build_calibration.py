import json
import random
from collections import defaultdict

from build_requests import M, ROOT, RUNS, HERE, save

SEED = 27
names_by_day = defaultdict(set)
for lang_names in M.DAY_NAMES.values():
    for day, name in lang_names.items():
        names_by_day[day].add(name.casefold())

records = [r for run in RUNS for r in json.load(open(ROOT / "experiments" / run / "results.json", encoding="utf-8"))]
cells = defaultdict(list)
for r in records:
    m = r["meta"]
    if r["condition"] != "cot" or m["insertion"] != "no_insertion" or m["language"] not in ("hi_IN", "en_US"):
        continue
    if M.extract_answer(r["content"]) is None or r.get("finish_reason") == "length":
        continue
    cells[m["language"], m["task"], m["difficulty"]].append(r)

items = []
for cell in sorted(cells):
    pool = sorted(cells[cell], key=lambda r: r["id"])
    r = random.Random(f"{SEED}/{'/'.join(cell)}").choice(pool)
    m = r["meta"]
    gold = m["answer"]
    accept = sorted(names_by_day[M.WEEKDAYS[gold.casefold()]]) if m["task"] == "day_of_week" else [gold.casefold()]
    items.append({
        "id": r["id"] + "/calibration",
        "messages": [r["request"]["messages"][0], {"role": "assistant", "content": "<think></think>"}],
        "meta": {"source_id": r["id"], "language": m["language"], "task": m["task"], "difficulty": m["difficulty"], "gold": gold,
                 "accept": accept, "api_answer": M.extract_answer(r["content"]), "api_correct": bool(M.is_correct(r)),
                 "api_completion_tokens": (r.get("usage") or {}).get("completion_tokens")},
    })

save(HERE / "outputs" / "calibration_requests.json", items)
by_lang = defaultdict(list)
for it in items:
    by_lang[it["meta"]["language"]].append(it["meta"]["api_correct"])
print(f"{len(items)} calibration items; API accuracy on them: " + ", ".join(f"{k} {sum(v)}/{len(v)} ({100 * sum(v) / len(v):.0f}%)" for k, v in sorted(by_lang.items())))
print("overall API accuracy:", f"{100 * sum(it['meta']['api_correct'] for it in items) / len(items):.1f}%")
