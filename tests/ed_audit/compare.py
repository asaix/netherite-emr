import json
from collections import defaultdict

from audit import DATA, DIFFICULTIES, FIELDS, HERE, SETS, pairs
from ed import CONFIG, correct, partial

import pandas as pd


def no_day(short, full):
    return "-" in short or full.count("-") == 1


def cost(rule):
    def substitution(a, b):
        if a == b:
            return 0
        x, y = a.split(" "), b.split(" ")
        if rule and len(x) == len(y) and x[0] == y[0]:
            ok = lambda p, q: p == q or rule(p, q) or rule(q, p)
            if all(len(p.split("..")) == len(q.split("..")) and all(map(ok, p.split(".."), q.split(".."))) for p, q in zip(x[1:], y[1:])):
                return CONFIG["partial_date_cost"]
        return 1
    return substitution


VARIANTS = {"A_no_rule": cost(None), "B_full_rule": cost(partial), "C_no_bare_day": cost(lambda p, q: partial(p, q) and no_day(p, q))}


def distance(a, b, substitution):
    previous = list(range(len(b) + 1))
    for i, x in enumerate(a, 1):
        current = [i]
        for j, y in enumerate(b, 1):
            current.append(min(previous[j] + 1, current[j - 1] + 1, previous[j - 1] + substitution(x, y)))
        previous = current
    return previous[-1] / max(len(a), len(b)) if a or b else 0.0


def auc(scores, labels):
    ranks = pd.Series(scores).rank().tolist()
    positives = sum(labels)
    negatives = len(labels) - positives
    if not positives or not negatives:
        return None
    return (sum(r for r, l in zip(ranks, labels) if l) - positives * (positives + 1) / 2) / (positives * negatives)


CACHE = HERE / "outputs" / "compare_pairs.csv"
if CACHE.exists():
    df = pd.read_csv(CACHE)
else:
    rows = []
    for s in SETS:
        for d in DIFFICULTIES:
            records = json.load(open(DATA / "parsed" / s / f"{d}.json", encoding="utf-8"))["records"]
            for en, hi in pairs(records):
                ec, hc = correct(en), correct(hi)
                for field in FIELDS:
                    a, b = en[field]["parsed"], hi[field]["parsed"]
                    if a is None or b is None:
                        continue
                    rows.append({"set": s, "difficulty": d, "field": field, "en_correct": ec, "hi_correct": hc, **{k: distance(a, b, f) for k, f in VARIANTS.items()}})
    df = pd.DataFrame(rows)
    df.to_csv(CACHE, index=False)
result = {}
for (s, field), g in df.groupby(["set", "field"], sort=False):
    v = list(VARIANTS)
    labelled = g.dropna(subset=["en_correct", "hi_correct"])
    disagree = (labelled["en_correct"] != labelled["hi_correct"]).astype(int).tolist()
    hi_wrong = (labelled["hi_correct"] == 0).astype(int).tolist()
    result[f"{s}/{field}"] = {
        "pairs": len(g),
        "mean": {k: round(g[k].mean(), 5) for k in v},
        "mean_by_difficulty": {d: {k: round(x[k].mean(), 4) for k in v} for d, x in g.groupby("difficulty", sort=False)},
        "pairs_changed_vs_A_pct": {k: round(100 * (g[k] != g["A_no_rule"]).mean(), 2) for k in v[1:]},
        "pairs_changed_B_vs_C_pct": round(100 * (g["B_full_rule"] != g["C_no_bare_day"]).mean(), 2),
        "max_pair_shift_vs_A": {k: round((g["A_no_rule"] - g[k]).max(), 4) for k in v[1:]},
        "spearman_vs_A": {k: round(g[k].rank().corr(g["A_no_rule"].rank()), 5) for k in v[1:]},
        "auc_disagreement": {k: round(auc(labelled[k].tolist(), disagree), 4) for k in v},
        "auc_hi_wrong": {k: round(auc(labelled[k].tolist(), hi_wrong), 4) for k in v},
    }
json.dump(result, open(HERE / "outputs" / "compare.json", "w", encoding="utf-8"), indent=2, ensure_ascii=False)
print(json.dumps(result, indent=2, ensure_ascii=False))
