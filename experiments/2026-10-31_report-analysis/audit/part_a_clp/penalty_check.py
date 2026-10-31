import json
import pickle
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
df = pd.DataFrame(pickle.load(open(HERE / "cache" / "rows.pkl", "rb")))
df = df[df["cond"].isin(["hi_cot", "hi_direct"])].copy()
df["c"] = df["correct"].map(lambda x: np.nan if x is None or x != x else float(x))
df["qk"] = df["level"] + "/" + df["task"] + "/" + df["q"].astype(str)
qs = sorted(df["qk"].unique())
pos = {k: i for i, k in enumerate(qs)}
A = {}
for (cond, ins), g in df.groupby(["cond", "ins"]):
    a = np.full(len(qs), np.nan)
    a[g["qk"].map(pos).to_numpy()] = g["c"].to_numpy()
    A[cond, ins] = a
W = np.stack([np.bincount(np.random.default_rng(100 + i).integers(0, len(qs), len(qs)), minlength=len(qs)) for i in range(2000)])
N, S = "no_insertion", "similar_insertion"


def ratio(a):
    return 100 * (W @ np.nan_to_num(a)) / (W @ (~np.isnan(a)).astype(float))


def summary(point, boot):
    return {"value": round(float(point), 2), "ci": [round(float(x), 2) for x in np.percentile(boot, [2.5, 97.5])]}


def drop(cond, mode):
    a, b = A[cond, N], A[cond, S]
    if mode == "strict":
        a, b = np.nan_to_num(a), np.nan_to_num(b)
    if mode == "both_answered":
        ok = ~np.isnan(a) & ~np.isnan(b)
        a, b = np.where(ok, a, np.nan), np.where(ok, b, np.nan)
    return np.nanmean(a) * 100 - np.nanmean(b) * 100, ratio(a) - ratio(b)


out = {}
for mode in ("answered", "strict", "both_answered"):
    pc, bc = drop("hi_cot", mode)
    pd_, bd = drop("hi_direct", mode)
    out[mode] = {"hi_cot_drop": summary(pc, bc), "hi_direct_drop": summary(pd_, bd), "penalty_cot_minus_direct": summary(pc - pd_, bc - bd)}
json.dump(out, open(HERE / "penalty_check.json", "w", encoding="utf-8"), indent=2, ensure_ascii=False)
print(json.dumps(out))
