import json
import math
import random
import sys
from collections import Counter, defaultdict

from audit import DATA, DIFFICULTIES, FIELDS, HERE, MAX_CELLS, SETS, align, pairs, source
from ed import CONFIG, partial, substitution

OUT = HERE / "outputs"
PER_KIND = 40
KINDS = ["padded~day", "day", "month", "MM-DD"]


def kind(a, b):
    found = set()
    for p, q in zip(a.split()[1:], b.split()[1:]):
        for x, y in zip(p.split(".."), q.split("..")):
            if x == y:
                continue
            short, full = (x, y) if partial(x, y) else (y, x)
            if full.count("-") == 1:
                found.add("month")
            elif "-" in short:
                found.add("MM-DD")
            else:
                found.add("padded~day" if short.startswith("0") else "day")
    return next(k for k in KINDS if k in found)


def side(a, b):
    for p, q in zip(a.split()[1:], b.split()[1:]):
        if p != q:
            return "en" if len(p) < len(q) else "hi"


def collect():
    subs, records = [], {}
    for s in SETS:
        for d in DIFFICULTIES:
            data = json.load(open(DATA / "parsed" / s / f"{d}.json", encoding="utf-8"))["records"]
            for field in FIELDS:
                for en, hi in pairs(data):
                    a, b = en[field]["parsed"], hi[field]["parsed"]
                    if a is None or b is None or len(a) * len(b) > MAX_CELLS:
                        continue
                    for step, x, y in align(a, b):
                        if step == "sub" and 0 < substitution(x, y) < 1:
                            subs.append({"set": s, "difficulty": d, "field": field, "en_id": en["id"], "hi_id": hi["id"], "en": x, "hi": y, "kind": kind(x, y), "partial_side": side(x, y), "longer": max(len(a), len(b))})
                            records[en["id"]], records[hi["id"]] = en, hi
    random.seed(0)
    by_kind = defaultdict(list)
    for i, x in enumerate(subs):
        by_kind[x["kind"]].append(i)
    sample = []
    for k, idx in by_kind.items():
        for i in random.sample(idx, min(PER_KIND, len(idx))):
            x = subs[i]
            sample.append({"index": i, **x, "en_source": source(records[x["en_id"]], x["field"], x["en"]), "hi_source": source(records[x["hi_id"]], x["field"], x["hi"])})
    OUT.mkdir(exist_ok=True)
    json.dump(subs, open(OUT / "half_subs.json", "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    json.dump(sample, open(OUT / "misfire_sample.json", "w", encoding="utf-8"), indent=2, ensure_ascii=False)


def interval(k, n):
    if not n:
        return None
    z, p = 1.96, k / n
    centre = (p + z * z / (2 * n)) / (1 + z * z / n)
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return [round(100 * (centre - half), 1), round(100 * (centre + half), 1)]


def stats():
    subs = json.load(open(OUT / "half_subs.json", encoding="utf-8"))
    sample = json.load(open(OUT / "misfire_sample.json", encoding="utf-8"))
    labels = json.load(open(OUT / "misfire_labels.json", encoding="utf-8"))
    labelled = [(x, labels[str(x["index"])]) for x in sample]
    rate, by_kind = {}, {}
    for k in KINDS:
        rows = [label for x, label in labelled if x["kind"] == k and label["verdict"] != "unclear"]
        wrong = sum(label["verdict"] == "misfire" for label in rows)
        rate[k] = wrong / len(rows) if rows else 0.0
        by_kind[k] = {"population": sum(x["kind"] == k for x in subs), "labelled": len(rows), "unclear": sum(x["kind"] == k and label["verdict"] == "unclear" for x, label in labelled), "misfires": wrong, "misfire_pct": round(100 * rate[k], 1) if rows else None, "ci95_pct": interval(wrong, len(rows)), "reasons": Counter(label["reason"] for label in rows if label["verdict"] == "misfire").most_common()}
    pairs_total = {}
    for s in SETS:
        for d in DIFFICULTIES:
            for field in FIELDS:
                path = DATA / "ed-partial" / s / f"{d}.csv"
                top = open(path, encoding="utf-8").read().split("\n\n", 1)[0].splitlines()
                head, overall = top[0].split(","), top[1].split(",")
                column = f"{field}_norm_edit_distance_count"
                if column in head and overall[head.index(column)]:
                    pairs_total[(s, field)] = pairs_total.get((s, field), 0) + int(float(overall[head.index(column)]))
    groups = defaultdict(lambda: {"half_subs": 0, "expected_misfires": 0.0, "rule_saving": 0.0, "misfire_saving": 0.0, "pairs_touched": set(), "pairs_with_likely_misfire": set()})
    for x in subs:
        g = groups[(x["set"], x["field"])]
        saving = (1 - CONFIG["partial_date_cost"]) / x["longer"]
        g["half_subs"] += 1
        g["expected_misfires"] += rate[x["kind"]]
        g["rule_saving"] += saving
        g["misfire_saving"] += rate[x["kind"]] * saving
        g["pairs_touched"].add(x["en_id"])
        if x["kind"] == "padded~day":
            g["pairs_with_likely_misfire"].add(x["en_id"])
    impact = {}
    for (s, field), g in sorted(groups.items()):
        n = pairs_total[(s, field)]
        impact[f"{s}/{field}"] = {
            "pairs": n,
            "half_subs": g["half_subs"],
            "expected_misfires": round(g["expected_misfires"], 1),
            "expected_misfire_pct": round(100 * g["expected_misfires"] / g["half_subs"], 1),
            "pairs_touched_pct": round(100 * len(g["pairs_touched"]) / n, 2),
            "rule_mean_shift_bound": round(g["rule_saving"] / n, 5),
            "misfire_mean_shift_bound": round(g["misfire_saving"] / n, 5),
        }
    result = {"by_kind": by_kind, "impact": impact}
    json.dump(result, open(OUT / "misfire_stats.json", "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    {"collect": collect, "stats": stats}[sys.argv[1]]()
