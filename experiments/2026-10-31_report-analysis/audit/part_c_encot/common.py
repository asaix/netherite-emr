from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import binomtest
from statsmodels.stats.multitest import multipletests

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[3]
TAB = OUT / "tables"
FIG = OUT / "fig_data"
TAB.mkdir(exist_ok=True)
FIG.mkdir(exist_ok=True)
DIFFS = ["short", "medium", "long", "very_long", "very_very_long"]
TASKS = ["date_addition", "date_subtraction", "date_duration", "date_recurrence", "day_of_week",
         "interval_date", "time_addition", "time_subtraction", "time_duration"]
INS = ["no_insertion", "similar_insertion", "dissimilar_insertion"]
CONDS = ["English direct", "English CoT", "Hindi direct", "Hindi CoT", "Hindi CLP", "Hindi en-CoT"]
B = 2000


def load():
    df = pd.read_pickle(OUT / "cache" / "tidy.pkl")
    df["qid"] = df["difficulty"] + "/" + df["task"] + "/" + df["qn"].astype(str)
    name = {("standard", "en_US", "direct"): "English direct", ("standard", "en_US", "cot"): "English CoT",
            ("standard", "hi_IN", "direct"): "Hindi direct", ("standard", "hi_IN", "cot"): "Hindi CoT",
            ("clp", "hi_IN", "clp"): "Hindi CLP", ("en-cot", "hi_IN", "en-cot"): "Hindi en-CoT"}
    df["C"] = [name.get(k) for k in zip(df["source"], df["lang"], df["cond"])]
    return df


def subset(df):
    s = df[df["C"].notna() & (df["qn"] < 50)].copy()
    qlist = sorted(s["qid"].unique())
    s["qi"] = s["qid"].map({q: i for i, q in enumerate(qlist)})
    return s, qlist


def weights(Q, b=B, seed=0):
    rng = np.random.default_rng(seed)
    return np.stack([np.bincount(rng.integers(0, Q, Q), minlength=Q) for _ in range(b)]).astype(np.int32)


class Boot:
    def __init__(self, df, W, Q, strict=False):
        self.df, self.W, self.Q, self.strict = df, W, Q, strict

    def vec(self, mask):
        d = self.df[mask]
        if not self.strict:
            d = d[d["scored"]]
        c = np.bincount(d["qi"], weights=d["correct"].astype(float), minlength=self.Q)
        k = np.bincount(d["qi"], minlength=self.Q).astype(float)
        return c, k

    def acc(self, mask):
        c, k = self.vec(mask)
        return c.sum() / k.sum()

    def boot(self, mask):
        c, k = self.vec(mask)
        return (self.W @ c) / (self.W @ k)


def ci(x, digits=1):
    lo, hi = np.percentile(x, [2.5, 97.5])
    return round(100 * float(lo), digits), round(100 * float(hi), digits)


def pair_table(d, a, b, extra=()):
    idx = ["qid", "ins", *extra]
    x = d[d["scored"] & d["C"].isin([a, b])].pivot_table(index=idx, columns="C", values="correct", aggfunc="first")
    return x.dropna().astype(bool)


def mcnemar(d, a, b):
    w = pair_table(d, a, b)
    x, y = int((w[a] & ~w[b]).sum()), int((~w[a] & w[b]).sum())
    return x, y, binomtest(x, x + y).pvalue if x + y else 1.0


def holm(ps):
    return multipletests(ps, method="holm")[1]
