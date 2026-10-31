import gc
import json
import re
import statistics
import sys
from collections import Counter, defaultdict
from datetime import date, timedelta
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(HERE.parent / "baseline"))
from common import EN_DAYS, HI_DAYS, MONTHS, gold_typed, my_extract, parse_question, typed

LEVELS = ["short", "medium", "long", "very_long", "very_very_long"]
TIME = {"time_addition", "time_subtraction", "time_duration"}
DAYDIFF = {"date_addition", "date_subtraction", "date_duration"}
SPAN = {"date_addition", "date_subtraction", "date_duration", "date_recurrence"}


def load(path):
    d = json.loads(path.read_text())
    return d["records"] if isinstance(d, dict) else d


def question(r):
    return r["request"]["messages"][-1]["content"].strip().split("\n\n")[-1].strip()


def condkey(s, r):
    lang = "en" if r["meta"]["language"] == "en_US" else "hi"
    return "en-cot" if s == "en-cot" else f"{s}_{lang}_{r['condition']}"


def minutes(v):
    if ":" in v:
        h, m = v.split(":")
        return int(h) * 60 + int(m)
    return int(v)


def grade(r):
    task = r["meta"]["task"]
    raw, _ = my_extract(r.get("content"))
    pred = typed(task, raw)
    gold = gold_typed(task, r["meta"]["answer"])
    return pred, gold, pred is not None and pred == gold, raw is None


def has_feb29(a, b):
    a, b = sorted((a, b))
    for y in range(a.year, b.year + 1):
        if y % 4 == 0 and (y % 100 or y % 400 == 0) and a <= date(y, 2, 29) <= b:
            return True
    return False


def span(task, q):
    iso = list(re.finditer(r"\d{4}-\d{2}-\d{2}", q))
    q = q[iso[-2 if task == "date_duration" else -1].start():]
    p = parse_question(task, q)
    if task == "date_addition":
        a = date.fromisoformat(p["today"])
        return a, a + timedelta(days=p["n"])
    if task == "date_subtraction":
        a = date.fromisoformat(p["today"])
        return a - timedelta(days=p["n"]), a
    if task == "date_recurrence":
        a = date.fromisoformat(p["today"])
        return a, a + timedelta(days=p["every"] * p["k"])
    return date.fromisoformat(p["a"]), date.fromisoformat(p["b"])


def markers(text):
    t = text.lower()
    out = set(int(x) for x in re.findall(r"(?<![\d:-])\d+(?![\d:-])", t))
    out |= {v for k, v in MONTHS.items() if k in t}
    return out


C = defaultdict(Counter)
ron_strict = {}
std_strict = {}
same = defaultdict(list)
midnight_tasks = Counter()
cutoff_tasks = Counter()
hi_midnight_level = Counter()
zero = Counter()
for s, path in (("standard", ROOT / "responses/standard"), ("ron", ROOT / "responses/ron"), ("en-cot", ROOT / "responses/en-cot")):
    for lv in LEVELS:
        rows = load(path / f"{lv}.json")
        for r in rows:
            k = condkey(s, r)
            m = r["meta"]
            task = m["task"]
            pred, gold, ok, unanswered = grade(r)
            c = C[k]
            c["n"] += 1
            c["wrong"] += not ok
            C["all"]["n"] += 1
            C["all"]["wrong"] += not ok
            C[f"set_{s}"]["n"] += 1
            C[f"set_{s}"]["wrong"] += not ok
            if not ok and unanswered:
                c["cut"] += 1
                C["all"]["cut"] += 1
                C[f"set_{s}"]["cut"] += 1
                cutoff_tasks[(k, task)] += 1
            if s in ("standard", "ron") and r["condition"] == "cot" and int(m["question_id"]) < 10:
                d = std_strict if s == "standard" else ron_strict
                d[(m["language"], lv, task, m["question_id"], m["insertion"])] = ok
            q = question(r)
            if task in TIME:
                c["time_n"] += 1
                c["time_wrong"] += not ok
                if not ok and pred is not None:
                    try:
                        diff = abs(minutes(str(pred)) - minutes(str(gold)))
                    except ValueError:
                        diff = None
                    c["time_valued"] += 1
                    if diff and diff % 60 == 0:
                        c["whole_hours"] += 1
                        C["all"]["whole_hours"] += 1
                    if diff == 720:
                        c["twelve"] += 1
                if k == "standard_hi_cot" and task == "time_addition":
                    hi_midnight_level[(lv, "n")] += 1
                    hi_midnight_level[(lv, "wrong")] += not ok
                if k == "standard_hi_cot" and pred == "00:00":
                    zero[m["insertion"]] += 1
            if task in DAYDIFF and not ok and pred is not None:
                if task == "date_duration":
                    diff = abs(int(pred) - int(gold))
                else:
                    diff = abs((date.fromisoformat(pred) - date.fromisoformat(gold)).days)
                c["date_valued"] += 1
                if diff in (10, 20, 30):
                    c["tens"] += 1
                    C["all"]["tens"] += 1
            if task in SPAN:
                a, b = span(task, q)
                if has_feb29(a, b):
                    c["feb_n"] += 1
                    c["feb_wrong"] += not ok
                    if not ok:
                        C["all"]["feb_wrong"] += 1
            if task in DAYDIFF | {"date_recurrence"} | {"time_addition", "time_subtraction"} and m["insertion"] != "dissimilar_insertion" and not ok and pred is not None and task != "date_duration":
                same[(lv, task, m["language"], m["question_id"], k)].append((m["insertion"], str(pred), q))
        del rows
        gc.collect()

reuse = Counter()
for key, vals in same.items():
    by = dict((i, (p, q)) for i, p, q in vals)
    k = key[4]
    if "similar_insertion" in by:
        p, q = by["similar_insertion"]
        reuse[(k, "dist_n")] += 1
        if "no_insertion" in by:
            base = by["no_insertion"][1]
        else:
            base = None
        if base and q.endswith(base) and len(q) > len(base):
            dist = q[: -len(base)]
            parts = set(int(x) for x in re.findall(r"\d+", p))
            hit = bool(parts & markers(dist))
            reuse[(k, "dist_checked")] += 1
            reuse[(k, "dist_hit")] += hit
del same
gc.collect()

fmt = defaultdict(Counter)
fmt_trace = defaultdict(list)
bytask = defaultdict(Counter)
bylevel = defaultdict(Counter)
longest = None
for s, field in (("ron", "reasoning_content"), ("ron", "content"), ("standard", "content")):
    for lv in LEVELS:
        rows = load(ROOT / "experiments/2026-10-29_ed-analysis/parsed" / s / f"{lv}.p.json")
        for r in rows:
            toks = (r.get(field) or {}).get("parsed") or []
            k = condkey(s, r) + "_" + field
            n = sum(1 for t in toks if t.split()[0] == "FORMAT")
            fmt[k]["format"] += n
            fmt[k]["tokens"] += len(toks)
            fmt[k]["traces"] += 1
            if s == "ron" and field == "reasoning_content" and r["meta"]["language"] == "hi_IN" and r["condition"] == "direct":
                _, _, ok, _ = grade({"meta": r["meta"], "content": r["content"]["original"] if r.get("content") else None})
                fmt_trace["right" if ok else "wrong"].append(n)
                bytask[r["meta"]["task"]]["format"] += n
                bytask[r["meta"]["task"]]["tokens"] += len(toks)
                words = len((r["reasoning_content"]["original"] or "").split())
                if ok and (longest is None or (lv == "short" and words > longest["words"])) and lv == "short":
                    longest = {"id": r["id"], "words": words, "steps": len(toks), "format": n, "question": question(r)}
            if s == "ron" and field == "reasoning_content":
                bylevel[lv]["format"] += n
                bylevel[lv]["tokens"] += len(toks)
            if s == "standard" and r["condition"] == "cot":
                fmt[k + "_lens"]["sum"] += len(toks)
                fmt_trace[k + "_lens"].append(len(toks))
        del rows
        gc.collect()

keys = sorted(set(std_strict) & set(ron_strict))
acc = {}
for name, d in (("standard", std_strict), ("ron", ron_strict)):
    for lang in ("en_US", "hi_IN"):
        v = [d[k] for k in keys if k[0] == lang]
        acc[f"{name}_{lang}"] = {"n": len(v), "strict_pct": round(100 * sum(v) / len(v), 1)}
    acc[f"{name}_gap"] = round(acc[f"{name}_en_US"]["strict_pct"] - acc[f"{name}_hi_IN"]["strict_pct"], 1)

out = {
    "counts": {k: dict(v) for k, v in C.items()},
    "same_questions_strict": acc,
    "format": {k: {**v, "share_pct": round(100 * v["format"] / v["tokens"], 1) if v.get("tokens") else None} for k, v in fmt.items() if not k.endswith("_lens")},
    "format_hi_direct_mean_per_trace": {k: round(statistics.mean(fmt_trace[k]), 1) for k in ("right", "wrong")},
    "format_hi_direct_by_task_pct": {k: round(100 * v["format"] / v["tokens"], 1) for k, v in bytask.items()},
    "format_all_ron_by_level_pct": {k: round(100 * v["format"] / v["tokens"], 1) for k, v in bylevel.items()},
    "longest_right_short_hi_direct": longest,
    "median_cot_tokens": {k: statistics.median(v) for k, v in fmt_trace.items() if k.endswith("_lens")},
    "cutoff_by_task_en_cot": {t: n for (k, t), n in cutoff_tasks.items() if k == "standard_en_cot"},
    "hi_cot_time_addition_wrong_pct_by_level": {lv: round(100 * hi_midnight_level[(lv, "wrong")] / hi_midnight_level[(lv, "n")], 1) for lv in LEVELS},
    "hi_cot_answers_0000_by_insertion": dict(zero),
    "distractor_reuse_similar": {k: {m: reuse[(k, m)] for m in ("dist_n", "dist_checked", "dist_hit")} for k in {x[0] for x in reuse}},
}
(HERE / "verified.json").write_text(json.dumps(out, indent=2, ensure_ascii=False))
print(json.dumps(out, indent=2, ensure_ascii=False))
