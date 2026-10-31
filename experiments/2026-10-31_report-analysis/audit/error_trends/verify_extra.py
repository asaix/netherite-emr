import gc
import json
import re
import sys
from collections import Counter
from datetime import date, timedelta
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(HERE.parent / "baseline"))
from common import gold_typed, my_extract, typed

LEVELS = ["short", "medium", "long", "very_long", "very_very_long"]


def load(p):
    d = json.loads(p.read_text())
    return d["records"] if isinstance(d, dict) else d


def question(r):
    return r["request"]["messages"][-1]["content"].strip().split("\n\n")[-1].strip()


def key(s, r):
    lang = "en" if r["meta"]["language"] == "en_US" else "hi"
    return "en-cot" if s == "en-cot" else f"{s}_{lang}_{r['condition']}"


def feb29(a, b):
    a, b = sorted((a, b))
    return any(y % 4 == 0 and a <= date(y, 2, 29) <= b for y in range(a.year, b.year + 1))


def span(task, q):
    iso = re.findall(r"\d{4}-\d{2}-\d{2}", q)
    tail = q[q.rfind(iso[-2 if task == "date_duration" else -1]) :]
    nums = re.findall(r"\d{4}-\d{2}-\d{2}|\d+", tail)
    if task == "date_duration":
        return date.fromisoformat(iso[-2]), date.fromisoformat(iso[-1])
    t = date.fromisoformat(nums[0])
    if task == "date_addition":
        return t, t + timedelta(days=int(nums[1]))
    if task == "date_subtraction":
        return t - timedelta(days=int(nums[1])), t
    return t, t + timedelta(days=int(nums[1]) * int(nums[2]))


T = Counter()
out = {"examples": {}}
feb_ids = set()
for s in ("standard", "ron", "en-cot"):
    for lv in LEVELS:
        rows = load(ROOT / "responses" / s / f"{lv}.json")
        for r in rows:
            m, k = r["meta"], key(s, r)
            task = m["task"]
            raw, _ = my_extract(r.get("content"))
            pred = typed(task, raw)
            gold = gold_typed(task, m["answer"])
            ok = pred is not None and pred == gold
            T[f"{k}|{task}|n"] += 1
            T[f"{k}|{task}|wrong"] += not ok
            if ok or raw is not None:
                T[f"{k}|answered"] += 1
                T[f"{k}|answered_right"] += ok
            q = question(r)
            if task == "day_of_week" and not ok and pred is not None:
                T[f"{k}|dow_named"] += 1
                T[f"{k}|dow_late1"] += (pred - gold) % 7 == 1
            if task == "interval_date" and not ok and pred is not None:
                a, b = [date.fromisoformat(x) for x in pred.split(" to ")]
                g0 = date.fromisoformat(m["answer"].split(" to ")[0]) if " to " in m["answer"] else None
                T[f"{k}|int_valued"] += 1
                T[f"{k}|int_notweek"] += (b - a).days != 6
                if g0:
                    T[f"{k}|int_thisweek"] += (g0 - a).days == 7 and (b - a).days == 6
            if s == "standard" and task in ("date_addition", "date_subtraction", "date_duration", "date_recurrence"):
                a, b = span(task, q)
                f = feb29(a, b)
                if lv == "very_very_long" and k == "standard_en_cot":
                    T[f"vvl_en_cot|feb{int(f)}|n"] += 1
                    T[f"vvl_en_cot|feb{int(f)}|wrong"] += not ok
                if f and k == "standard_en_cot" and not ok:
                    feb_ids.add(r["id"])
            if s == "standard" and task in ("time_addition", "time_subtraction"):
                nums = re.findall(r"\d{1,2}:\d{2}|\d+", q[q.rfind(":") - 2 :])
                now = int(nums[0][:2]) * 60 + int(nums[0][3:])
                d = int(nums[1]) * 60 + int(nums[2])
                v = now + d if task == "time_addition" else now - d
                cross = v >= 1440 or v < 0
                T[f"{k}|midnight{int(cross)}|n"] += 1
                T[f"{k}|midnight{int(cross)}|wrong"] += not ok
            if s == "standard" and r["condition"] == "direct":
                if m["language"] == "en_US" and "2026-12-24" in q and task == "date_addition" and " 8 " in q and "31 days" in q:
                    out["examples"]["distractor_names_answer"] = {"q": q, "gold": m["answer"], "content": (r["content"] or "")[-60:]}
                if m["language"] == "en_US" and "2029-03-06" in q and task == "date_addition" and " 36 " in q and m["insertion"] == "no_insertion":
                    out["examples"]["tens"] = {"q": q, "gold": m["answer"], "content": (r["content"] or "")[-60:]}
            if s == "standard" and "motorcycle" in q.lower():
                T["motorcycle_mentions"] += 1
                out["examples"].setdefault("motorcycle", q)
        del rows
        gc.collect()

leap = Counter()
for lv in LEVELS:
    rows = load(ROOT / "experiments/2026-10-29_ed-analysis/parsed/standard" / f"{lv}.p.json")
    for r in rows:
        if r["id"] in feb_ids:
            toks = (r.get("content") or {}).get("parsed") or []
            leap["wrong"] += 1
            leap["mentions_leap"] += any(t.split()[0] == "LEAP" for t in toks)
    del rows
    gc.collect()

rows = load(ROOT / "experiments/2026-10-29_ed-analysis/parsed/ron/short.p.json")
for r in rows:
    if r["id"] == "short/date_addition_hi_IN/1/dissimilar_insertion/direct":
        toks = r["reasoning_content"]["parsed"]
        out["format_example"] = {"id": r["id"], "words": len(r["reasoning_content"]["original"].split()), "steps": len(toks), "format": sum(t.split()[0] == "FORMAT" for t in toks), "question": question(r)}
del rows

out["counts"] = dict(sorted(T.items()))
out["leap_mention_feb_wrong_en_cot"] = dict(leap)
(HERE / "verified_extra.json").write_text(json.dumps(out, indent=2, ensure_ascii=False))
print("done")
