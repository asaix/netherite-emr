import json
from pathlib import Path

import numpy as np
import pandas as pd

OUT = Path(__file__).resolve().parent
LEVELS = ["short", "medium", "long", "very_long", "very_very_long"]
TASKS = ["date_addition", "date_subtraction", "date_duration", "date_recurrence", "day_of_week",
         "interval_date", "time_addition", "time_subtraction", "time_duration"]
INS = ["no_insertion", "similar_insertion", "dissimilar_insertion"]
B, SEED = 2000, 20261031

d = pd.read_pickle(OUT / "audit" / "part_c_encot" / "cache" / "tidy.pkl")
d = d[["source", "difficulty", "task", "qn", "lang", "ins", "cond", "scored", "correct"]]
NAME = {("standard", "en_US", "direct"): "en_direct", ("standard", "en_US", "cot"): "en_cot",
        ("standard", "hi_IN", "direct"): "hi_direct", ("standard", "hi_IN", "cot"): "hi_cot",
        ("clp", "hi_IN", "clp"): "clp", ("en-cot", "hi_IN", "en-cot"): "encot",
        ("hinglish", "en_US", "cot"): "en_hing", ("hinglish", "hi_IN", "cot"): "hi_hing",
        ("hinglish", "en_US", "hinglish"): "en_hing", ("hinglish", "hi_IN", "hinglish"): "hi_hing"}
d["c"] = [NAME.get(k) for k in zip(d["source"], d["lang"], d["cond"])]
d = d[d["c"].notna()].copy()
d["qid"] = d["difficulty"] + "/" + d["task"] + "/" + d["qn"].astype(str)


class Grid:
    def __init__(self, df):
        self.df = df.copy()
        q = sorted(df["qid"].unique())
        self.Q = len(q)
        self.df["qi"] = self.df["qid"].map({x: i for i, x in enumerate(q)})
        rng = np.random.default_rng(SEED)
        self.W = np.stack([np.bincount(rng.integers(0, self.Q, self.Q), minlength=self.Q) for _ in range(B)]).astype(np.float32)

    def vec(self, c, strict, **f):
        x = self.df[self.df["c"] == c]
        for k, v in f.items():
            x = x[x[k] == v]
        if not strict:
            x = x[x["scored"]]
        return (np.bincount(x["qi"], weights=x["correct"].astype(float), minlength=self.Q).astype(np.float32),
                np.bincount(x["qi"], minlength=self.Q).astype(np.float32))

    def acc(self, c, strict=False, **f):
        a, k = self.vec(c, strict, **f)
        return 100 * self.W @ a / (self.W @ k), 100 * float(a.sum() / k.sum())


def ci(boot, point):
    lo, hi = np.percentile(boot, [2.5, 97.5])
    return [round(float(point), 4), round(float(lo), 4), round(float(hi), 4)]


def diff(g, a, b, strict=False, **f):
    ba, pa = g.acc(a, strict, **f)
    bb, pb = g.acc(b, strict, **f)
    return ci(ba - bb, pa - pb)


def both(g, a, b, **f):
    return {"answered": diff(g, a, b, False, **f), "strict": diff(g, a, b, True, **f)}


def splits(g, a, b):
    r = {"pooled": both(g, a, b)}
    for i in INS:
        r[i] = both(g, a, b, ins=i)
    return r


res = {"bootstrap": {"B": B, "seed": SEED, "unit": "question"}}

full = Grid(d[d["source"] == "standard"])
res["full"] = {"questions": full.Q, "acc": {}, "cot_delta": {}, "gap_cot": {}, "gap_direct": {}, "drop": {}, "penalty": {}}
for c in ["en_direct", "en_cot", "hi_direct", "hi_cot"]:
    res["full"]["acc"][c] = {s: round(full.acc(c, st)[1], 4) for s, st in [("answered", False), ("strict", True)]}
res["full"]["cot_delta"]["en"] = splits(full, "en_cot", "en_direct")
res["full"]["cot_delta"]["hi"] = splits(full, "hi_cot", "hi_direct")
res["full"]["gap_cot"] = splits(full, "en_cot", "hi_cot")
res["full"]["gap_direct"] = splits(full, "en_direct", "hi_direct")
res["full"]["gap_cot_by_level"] = {l: both(full, "en_cot", "hi_cot", difficulty=l) for l in LEVELS}
res["full"]["hi_delta_by_task"] = {t: {i: both(full, "hi_cot", "hi_direct", task=t, ins=i) for i in INS} for t in ["date_subtraction", "interval_date"]}
res["full"]["hi_delta_by_level"] = {l: {i: both(full, "hi_cot", "hi_direct", difficulty=l, ins=i) for i in INS} for l in ["short"]}
for lang, cot, direct in [("en", "en_cot", "en_direct"), ("hi", "hi_cot", "hi_direct")]:
    res["full"]["drop"][lang], res["full"]["penalty"][lang] = {}, {}
    for i in INS[1:]:
        res["full"]["drop"][lang][i], res["full"]["penalty"][lang][i] = {}, {}
        for s, st in [("answered", False), ("strict", True)]:
            b0, p0 = full.acc(cot, st, ins="no_insertion")
            b1, p1 = full.acc(cot, st, ins=i)
            d0, q0 = full.acc(direct, st, ins="no_insertion")
            d1, q1 = full.acc(direct, st, ins=i)
            res["full"]["drop"][lang][i][s] = ci(b0 - b1, p0 - p1)
            res["full"]["penalty"][lang][i][s] = ci((b0 - b1) - (d0 - d1), (p0 - p1) - (q0 - q1))
for i in INS[1:]:
    res["full"].setdefault("penalty_hi_minus_en", {})[i] = {}
    for s, st in [("answered", False), ("strict", True)]:
        v = []
        for c, dc in [("hi_cot", "hi_direct"), ("en_cot", "en_direct")]:
            a0, x0 = full.acc(c, st, ins="no_insertion")
            a1, x1 = full.acc(c, st, ins=i)
            b0, y0 = full.acc(dc, st, ins="no_insertion")
            b1, y1 = full.acc(dc, st, ins=i)
            v.append(((a0 - a1) - (b0 - b1), (x0 - x1) - (y0 - y1)))
        res["full"]["penalty_hi_minus_en"][i][s] = ci(v[0][0] - v[1][0], v[0][1] - v[1][1])
del full

sub = Grid(d[d["qn"] < 50])
CONDS = ["en_direct", "en_cot", "hi_direct", "hi_cot", "clp", "encot", "en_hing", "hi_hing"]
res["subset"] = {"questions": sub.Q, "acc": {}, "contrast": {}, "by_level": {}, "by_task": {}}
for c in CONDS:
    res["subset"]["acc"][c] = {s: round(sub.acc(c, st)[1], 4) for s, st in [("answered", False), ("strict", True)]}
    res["subset"]["acc"][c]["by_ins"] = {i: {s: round(sub.acc(c, st, ins=i)[1], 4) for s, st in [("answered", False), ("strict", True)]} for i in INS}
PAIRS = {"clp-hi_cot": ("clp", "hi_cot"), "clp-hi_direct": ("clp", "hi_direct"), "encot-hi_cot": ("encot", "hi_cot"),
         "encot-hi_direct": ("encot", "hi_direct"), "encot-clp": ("encot", "clp"), "en_cot-encot": ("en_cot", "encot"),
         "en_cot-hi_cot": ("en_cot", "hi_cot"), "en_cot-clp": ("en_cot", "clp"), "en_hing-en_cot": ("en_hing", "en_cot"),
         "hi_hing-hi_cot": ("hi_hing", "hi_cot"), "encot-en_hing": ("encot", "en_hing"), "en_direct-hi_direct": ("en_direct", "hi_direct")}
for k, (a, b) in PAIRS.items():
    res["subset"]["contrast"][k] = splits(sub, a, b)
for l in LEVELS:
    res["subset"]["by_level"][l] = {c: {s: round(sub.acc(c, st, difficulty=l)[1], 4) for s, st in [("answered", False), ("strict", True)]} for c in CONDS}
for t in TASKS:
    res["subset"]["by_task"][t] = {c: {s: round(sub.acc(c, st, task=t)[1], 4) for s, st in [("answered", False), ("strict", True)]} for c in CONDS}

ba, pa = sub.acc("encot", False)
bb, pb = sub.acc("hi_cot", False)
be, pe = sub.acc("en_cot", False)
res["subset"]["decomposition"] = {"answered_share": ci(100 * (ba - bb) / (be - bb), 100 * (pa - pb) / (pe - pb))}
ba, pa = sub.acc("encot", True)
bb, pb = sub.acc("hi_cot", True)
be, pe = sub.acc("en_cot", True)
res["subset"]["decomposition"]["strict_share"] = ci(100 * (ba - bb) / (be - bb), 100 * (pa - pb) / (pe - pb))

(OUT / "headline.json").write_text(json.dumps(res, indent=2, ensure_ascii=False))
print(json.dumps({k: res["subset"]["acc"][k] for k in CONDS if k in res["subset"]["acc"]}, indent=None)[:1200])
print(res["full"]["acc"], res["full"]["cot_delta"]["en"]["pooled"], res["full"]["cot_delta"]["hi"]["pooled"])
print(res["full"]["penalty"]["hi"], res["full"]["penalty_hi_minus_en"])
print(res["subset"]["contrast"]["encot-hi_cot"]["pooled"], res["subset"]["contrast"]["en_cot-encot"]["pooled"], res["subset"]["decomposition"])
