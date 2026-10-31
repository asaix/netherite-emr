from common import *
from scipy.stats import binomtest, ttest_1samp
from statsmodels.stats.multitest import multipletests

B = 2000
F = frame()
F["q"] = F.groupby("qid", sort=False).ngroup()
NQ = F.q.max() + 1
RNG = np.random.default_rng(20261031)
W = np.stack([np.bincount(RNG.integers(0, NQ, NQ), minlength=NQ) for _ in range(B)]).astype(np.float32)


def mask(df=None, **kw):
    df = F if df is None else df
    m = np.ones(len(df), bool)
    for k, v in kw.items():
        m &= df[k].isin(v).to_numpy() if isinstance(v, (list, tuple, set)) else (df[k] == v).to_numpy()
    return m


def cn(m, col):
    s = F.loc[m & F[col].notna().to_numpy(), ["q", col]]
    return np.bincount(s.q, weights=s[col], minlength=NQ), np.bincount(s.q, minlength=NQ).astype(float)


def est(m, col):
    c, n = cn(m, col)
    return c.sum() / n.sum(), (W @ c.astype(np.float32)) / (W @ n.astype(np.float32))


def pct(v, s=None):
    if s is None:
        return round(100 * v, 2)
    lo, hi = np.nanpercentile(s, [2.5, 97.5])
    return {"v": round(100 * v, 2), "lo": round(100 * lo, 2), "hi": round(100 * hi, 2), "sig": bool(lo > 0 or hi < 0)}


def mcn(m, col):
    s = F.loc[m & F[col].notna().to_numpy(), ["qid", "insertion", "cond", col]]
    w = s.pivot_table(index=["qid", "insertion"], columns="cond", values=col).dropna()
    b, c = int(((w.cot == 1) & (w.direct == 0)).sum()), int(((w.cot == 0) & (w.direct == 1)).sum())
    return b, c, float(binomtest(b, b + c, 0.5).pvalue) if b + c else 1.0


def qlevel(m, col, fn):
    s = F.loc[m, ["q", "cond", "insertion", col]]
    return fn(s, col)


def delta_q(s, col):
    w = s.pivot_table(index=["q", "insertion"], columns="cond", values=col).dropna()
    return (w.cot - w.direct).groupby("q").mean().to_numpy()


def tp(x):
    if len(x) < 2 or np.std(x) == 0:
        return float("nan")
    return float(ttest_1samp(x, 0).pvalue)


def cot_delta(base, col="acc"):
    d, bd = est(base & mask(cond="direct"), col)
    c, bc = est(base & mask(cond="cot"), col)
    b, cc, p = mcn(base, col)
    x = qlevel(base, col, delta_q)
    return {"direct": pct(d), "cot": pct(c), **pct(c - d, bc - bd), "cot_wins": b, "direct_wins": cc, "mcnemar_p": p, "q_t_p": tp(x), "n_q": len(x)}


def pen_arrays(base, ins, col):
    drops = {}
    for cond in ("direct", "cot"):
        a0, b0 = est(base & mask(cond=cond, insertion="no_insertion"), col)
        a1, b1 = est(base & mask(cond=cond, insertion=ins), col)
        drops[cond] = (a0 - a1, b0 - b1)
    return drops


def pen_q(base, ins, col):
    s = F.loc[base & mask(insertion=["no_insertion", ins]), ["q", "cond", "insertion", col]]
    w = s.pivot_table(index="q", columns=["cond", "insertion"], values=col).dropna()
    d = (w["cot"]["no_insertion"] - w["cot"][ins]) - (w["direct"]["no_insertion"] - w["direct"][ins])
    return d


def penalty(base, ins, col="acc"):
    dr = pen_arrays(base, ins, col)
    x = pen_q(base, ins, col).to_numpy()
    return {"drop_direct": pct(dr["direct"][0], dr["direct"][1]), "drop_cot": pct(dr["cot"][0], dr["cot"][1]), **pct(dr["cot"][0] - dr["direct"][0], dr["cot"][1] - dr["direct"][1]), "q_t_p": tp(x), "n_q": len(x), "q_mean": round(100 * float(x.mean()), 2) if len(x) else None}


def interaction(base, ins, col="acc"):
    h = pen_arrays(base & mask(lang="hi_IN"), ins, col)
    e = pen_arrays(base & mask(lang="en_US"), ins, col)
    v = (h["cot"][0] - h["direct"][0]) - (e["cot"][0] - e["direct"][0])
    s = (h["cot"][1] - h["direct"][1]) - (e["cot"][1] - e["direct"][1])
    a = pen_q(base & mask(lang="hi_IN"), ins, col)
    b = pen_q(base & mask(lang="en_US"), ins, col)
    j = pd.concat([a, b], axis=1, join="inner")
    x = (j.iloc[:, 0] - j.iloc[:, 1]).to_numpy()
    return {**pct(v, s), "q_t_p": tp(x), "n_q": len(x)}


def holm(ps):
    ps = np.array(ps, float)
    ok = ~np.isnan(ps)
    out = np.full(len(ps), np.nan)
    if ok.any():
        out[ok] = multipletests(ps[ok], method="holm")[1]
    return out
