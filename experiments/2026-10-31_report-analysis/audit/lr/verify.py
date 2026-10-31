import json
import warnings
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd
import patsy
import yaml
import statsmodels.formula.api as smf
from scipy import optimize, stats
from scipy.special import expit
from statsmodels.stats.multitest import multipletests
from statsmodels.stats.proportion import proportion_confint
from statsmodels.stats.outliers_influence import variance_inflation_factor

warnings.filterwarnings("ignore")

OUT = Path(__file__).resolve().parent
TAB = OUT / "tables"
FIG = OUT / "fig_data"
SEED = 20261031
B = 2000
FOLDS = 10
DIFFICULTIES = ["short", "medium", "long", "very_long", "very_very_long"]
TASKS = ["date_addition", "date_duration", "date_recurrence", "date_subtraction", "day_of_week", "interval_date", "time_addition", "time_duration", "time_subtraction"]
INSERTIONS = ["no_insertion", "similar_insertion", "dissimilar_insertion"]
VIEWS = {
    "full": "RDS as reported (ops + operands + answer tokens)",
    "noans": "(a) answer tokens removed",
    "noansval": "(a+) answer tokens and any token holding an answer value removed",
    "ops": "(b) op types only, answer op types kept",
    "opsnoans": "(b+) op types only, answer ops removed",
    "opscore": "op types only, meta and answer ops removed",
    "prefix8": "first 8 non-answer tokens, with operands",
    "prefix8ops": "first 8 non-answer tokens, op types",
    "precheck": "non-answer tokens before first CHECK/REVISE",
    "precheckops": "op types before first CHECK/REVISE",
}
CONTROLS = "C(difficulty) + C(task) + C(insertion)"
RES = {}
WEEKDAYS = {n.casefold(): d for d, names in yaml.safe_load(open(OUT.parents[3] / "config/parser.yaml"))["weekdays"].items() for n in names}


def norm_answer(x):
    x = "" if pd.isna(x) else str(x).strip().casefold()
    return WEEKDAYS.get(x, x)


def save(df, name):
    df.to_csv(TAB / f"{name}.csv", index=False, float_format="%.6g")
    with pd.option_context("display.max_rows", None, "display.max_columns", None, "display.width", 250):
        print(f"\n== {name}\n{df.round(4).to_string(index=False)}", flush=True)
    return df


def load():
    d = pd.read_csv(OUT / "pairs.csv.gz", dtype={"gold": str, "en_answer": str, "hi_answer": str}, keep_default_na=False, na_values=[""])
    d["uid"] = d.difficulty + "|" + d.task + "|" + d.question_id.astype(str)
    d["cl"] = pd.factorize(d.uid)[0]
    d["difficulty"] = pd.Categorical(d.difficulty, DIFFICULTIES)
    d["task"] = pd.Categorical(d.task, TASKS)
    d["insertion"] = pd.Categorical(d.insertion, INSERTIONS)
    d["mode"] = pd.Categorical(d["mode"], ["off", "on"])
    d["answered"] = d.en_correct.notna() & d.hi_correct.notna()
    d["disagree"] = np.where(d.answered, (d.en_correct != d.hi_correct).astype(float), np.nan)
    d["en_strict"], d["hi_strict"] = d.en_correct.fillna(0), d.hi_correct.fillna(0)
    d["disagree_strict"] = (d.en_strict != d.hi_strict).astype(float)
    for v in VIEWS:
        for tag in "cr":
            e, h = d[f"{tag}_{v}_en"], d[f"{tag}_{v}_hi"]
            d[f"{tag}_{v}_gap"] = (e - h).abs() / np.maximum(e, h).where(lambda s: s > 0)
    d["rds"], d["gap"] = d.c_full, d.c_full_gap
    return d


def auc(y, s, w=None):
    y, s = np.asarray(y), np.asarray(s)
    w = np.ones(len(y)) if w is None else w
    _, inv = np.unique(s, return_inverse=True)
    pos, neg = np.bincount(inv, w * (y == 1)), np.bincount(inv, w * (y == 0))
    below = np.concatenate([[0], np.cumsum(neg)[:-1]])
    return ((below + 0.5 * neg) * pos).sum() / (pos.sum() * neg.sum())


def boot_weights(cl, rng, B=B):
    k = cl.max() + 1
    for _ in range(B):
        yield rng.multinomial(k, np.full(k, 1 / k))[cl]


def boot_auc(y, s, cl, seed=SEED, B=B):
    cl = pd.factorize(cl)[0]
    rng = np.random.default_rng(seed)
    vals = [auc(y, s, w) for w in boot_weights(cl, rng, B)]
    return np.percentile(vals, [2.5, 97.5])


def boot_rate(y, cl, seed=SEED):
    cl = pd.factorize(cl)[0]
    n, e = np.bincount(cl), np.bincount(cl, y)
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(n), (B, len(n)))
    return np.percentile(e[idx].sum(1) / n[idx].sum(1), [2.5, 97.5])


def summarize(res, var, data, ycol="disagree"):
    b, se = res.params[var], res.bse[var]
    i = list(res.params.index[1:]).index(var)
    me = res.get_margeff(at="overall")
    sd = data[var].std()
    z = 1.959964
    return {"n": int(res.nobs), "events": int(data[ycol].sum()), "clusters": int(data["cl"].nunique()), "beta": b, "se": se, "p": res.pvalues[var],
            "or_per_0.1": np.exp(0.1 * b), "or_lo": np.exp(0.1 * (b - z * se)), "or_hi": np.exp(0.1 * (b + z * se)),
            "sd": sd, "or_per_sd": np.exp(sd * b), "or_sd_lo": np.exp(sd * (b - z * se)), "or_sd_hi": np.exp(sd * (b + z * se)),
            "ame_pp_per_0.1": 10 * me.margeff[i], "ame_lo": 10 * (me.margeff[i] - z * me.margeff_se[i]), "ame_hi": 10 * (me.margeff[i] + z * me.margeff_se[i]),
            "ame_pp_per_sd": 100 * sd * me.margeff[i],
            "auc_insample": auc(data[ycol], res.predict(data)), "converged": bool(res.mle_retvals["converged"])}


def choice_sets(frame, xcols, gcol, ycol="disagree"):
    sets, chosen, gid = [], [], []
    for g, part in frame.groupby(gcol, sort=False, observed=True):
        y = part[ycol].to_numpy()
        k, n = int(y.sum()), len(y)
        if k == 0 or k == n:
            continue
        X = part[xcols].to_numpy(float)
        alts = list(combinations(range(n), k))
        Z = np.array([X[list(a)].sum(0) for a in alts])
        sets.append(Z)
        chosen.append(alts.index(tuple(np.flatnonzero(y))))
        gid.append(g)
    return sets, np.array(chosen), gid


def clogit_arrays(sets, chosen):
    m = max(len(s) for s in sets)
    p = sets[0].shape[1]
    Z = np.zeros((len(sets), m, p))
    mask = np.zeros((len(sets), m), bool)
    for i, s in enumerate(sets):
        Z[i, : len(s)] = s
        mask[i, : len(s)] = True
    return Z, mask, chosen


def clogit_fit(Z, mask, chosen, w=None, iters=40):
    G, m, p = Z.shape
    w = np.ones(G) if w is None else w
    beta = np.zeros(p)
    gi = np.arange(G)
    for _ in range(iters):
        eta = Z @ beta
        eta[~mask] = -np.inf
        eta -= eta.max(1, keepdims=True)
        P = np.exp(eta)
        P /= P.sum(1, keepdims=True)
        mean = (P[..., None] * Z).sum(1)
        score = ((Z[gi, chosen] - mean) * w[:, None]).sum(0)
        dev = Z - mean[:, None, :]
        H = np.einsum("g,gm,gmi,gmj->ij", w, P, dev, dev)
        step = np.linalg.solve(H + 1e-9 * np.eye(p), score)
        step = np.clip(step, -5, 5)
        beta = beta + step
        if np.abs(step).max() < 1e-8:
            break
    return beta, H, Z[gi, chosen] - mean


def clogit(frame, var, extra=(), gcol="uid", ycol="disagree", boot=True, seed=SEED):
    frame = frame.dropna(subset=[var])
    xcols = [var, *extra]
    sets, chosen, gid = choice_sets(frame, xcols, gcol, ycol)
    if len(sets) < 5:
        return {"groups": len(sets)}
    Z, mask, chosen = clogit_arrays(sets, chosen)
    beta, H, s = clogit_fit(Z, mask, chosen)
    Hi = np.linalg.pinv(H)
    se = np.sqrt(Hi[0, 0])
    robust = np.sqrt((Hi @ (s.T @ s) @ Hi)[0, 0])
    out = {"groups": len(sets), "beta": beta[0], "se_model": se, "se_robust": robust, "z": beta[0] / robust, "p": 2 * stats.norm.sf(abs(beta[0] / robust))}
    sd = frame.groupby(gcol, observed=True)[var].transform(lambda c: c - c.mean()).std()
    out |= {"within_sd": sd, "or_per_0.1": np.exp(0.1 * beta[0]), "or_per_within_sd": np.exp(sd * beta[0])}
    if boot:
        rng = np.random.default_rng(seed)
        G = len(sets)
        vals = []
        for _ in range(B):
            w = rng.multinomial(G, np.full(G, 1 / G)).astype(float)
            vals.append(clogit_fit(Z, mask, chosen, w, iters=12)[0][0])
        lo, hi = np.nanpercentile(vals, [2.5, 97.5])
        out |= {"or_lo_boot": np.exp(0.1 * lo), "or_hi_boot": np.exp(0.1 * hi)}
    out |= {"or_lo": np.exp(0.1 * (beta[0] - 1.96 * robust)), "or_hi": np.exp(0.1 * (beta[0] + 1.96 * robust))}
    return out


def within_concordance(frame, var, ycol="disagree", gcol="uid", seed=SEED):
    frame = frame.dropna(subset=[var])
    g = pd.factorize(frame[gcol])[0]
    order = np.argsort(g, kind="stable")
    y, s, g = frame[ycol].to_numpy()[order], frame[var].to_numpy()[order], g[order]
    starts = np.r_[0, np.flatnonzero(np.diff(g)) + 1, len(g)]
    wins, diffs, n = [], [], []
    for a, b in zip(starts[:-1], starts[1:]):
        if 0 < y[a:b].sum() < b - a:
            pos, neg = s[a:b][y[a:b] == 1], s[a:b][y[a:b] == 0]
            dif = (pos[:, None] - neg[None, :]).ravel()
            wins.append(((dif > 0) + 0.5 * (dif == 0)).sum())
            diffs.append(dif.sum())
            n.append(len(dif))
    wins, diffs, n = np.array(wins), np.array(diffs), np.array(n)
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(n), (B, len(n)))
    c = wins[idx].sum(1) / n[idx].sum(1)
    m = diffs[idx].sum(1) / n[idx].sum(1)
    return {"groups": len(n), "contrasts": int(n.sum()), "concordance": wins.sum() / n.sum(), "conc_lo": np.percentile(c, 2.5), "conc_hi": np.percentile(c, 97.5),
            "mean_diff": diffs.sum() / n.sum(), "diff_lo": np.percentile(m, 2.5), "diff_hi": np.percentile(m, 97.5)}


def irls(X, y, ridge=1e-6, iters=30):
    beta = np.zeros(X.shape[1])
    for _ in range(iters):
        p = expit(X @ beta)
        w = p * (1 - p) + 1e-9
        step = np.linalg.solve((X * w[:, None]).T @ X + ridge * np.eye(X.shape[1]), X.T @ (y - p) - ridge * beta)
        beta += step
        if np.abs(step).max() < 1e-7:
            break
    return beta


def firth(X, y, offset=None, iters=100, full=None):
    offset = np.zeros(len(y)) if offset is None else offset
    F = X if full is None else full
    beta = np.zeros(X.shape[1])
    for _ in range(iters):
        p = expit(X @ beta + offset)
        w = p * (1 - p)
        I = (F * w[:, None]).T @ F
        Ii = np.linalg.pinv(I)
        h = w * np.einsum("ij,jk,ik->i", F, Ii, F)
        U = X.T @ (y - p + h * (0.5 - p))
        step = np.linalg.solve((X * w[:, None]).T @ X + 1e-10 * np.eye(X.shape[1]), U)
        step = np.clip(step, -3, 3)
        beta += step
        if np.abs(step).max() < 1e-7:
            break
    p = expit(X @ beta + offset)
    w = p * (1 - p)
    ll = (y * np.log(p + 1e-300) + (1 - y) * np.log(1 - p + 1e-300)).sum() + 0.5 * np.linalg.slogdet((F * w[:, None]).T @ F)[1]
    return beta, ll


def firth_ci(X, y, j, beta, ll):
    others = [k for k in range(X.shape[1]) if k != j]

    def f(b):
        _, l = firth(X[:, others], y, offset=b * X[:, j], full=X)
        return 2 * (ll - l) - stats.chi2.ppf(0.95, 1)

    def solve(sign):
        step = 2.0
        hi = beta[j] + sign * step
        for _ in range(12):
            if f(hi) > 0:
                break
            hi += sign * step
        return optimize.brentq(f, beta[j], hi, xtol=1e-3)

    return solve(-1), solve(1), stats.chi2.sf(max(2 * (ll - firth(X[:, others], y, full=X)[1]), 0), 1)


def firth_row(frame, var, rhs, label, ycol="disagree"):
    frame = frame.dropna(subset=[var]).copy()
    X = np.asarray(patsy.dmatrix(f"{var} + {rhs}" if rhs else var, frame))
    names = patsy.dmatrix(f"{var} + {rhs}" if rhs else var, frame).design_info.column_names
    j = names.index(var)
    y = frame[ycol].to_numpy()
    keep = [k for k in range(X.shape[1]) if X[:, k].std() > 0 or k == 0]
    X = X[:, keep]
    j = keep.index(j)
    beta, ll = firth(X, y)
    lo, hi, p = firth_ci(X, y, j, beta, ll)
    rng = np.random.default_rng(SEED)
    cl = pd.factorize(frame.uid)[0]
    groups = [np.flatnonzero(cl == k) for k in range(cl.max() + 1)]
    vals = []
    for _ in range(500):
        take = np.concatenate([groups[k] for k in rng.integers(0, len(groups), len(groups))])
        if y[take].sum() >= 3:
            vals.append(firth(X[take], y[take], iters=25)[0][j])
    return {"model": label, "n": len(y), "events": int(y.sum()), "clusters": len(groups), "params": X.shape[1] - 1, "beta_firth": beta[j], "or_per_0.1": np.exp(0.1 * beta[j]),
            "or_lo_profile": np.exp(0.1 * lo), "or_hi_profile": np.exp(0.1 * hi), "p_plr": p, "or_lo_clboot": np.exp(0.1 * np.percentile(vals, 2.5)), "or_hi_clboot": np.exp(0.1 * np.percentile(vals, 97.5)),
            "sd": frame[var].std(), "or_per_sd": np.exp(frame[var].std() * beta[j]), "auc_raw": auc(y, frame[var])}


def reproduce(d):
    a = d[d.answered].copy()
    rows = []
    for mode, g in [("all", a), ("off", a[a["mode"] == "off"]), ("on", a[a["mode"] == "on"])]:
        lo, hi = proportion_confint(g.disagree.sum(), len(g), method="wilson")
        c = boot_rate(g.disagree.to_numpy(), g.cl.to_numpy())
        rows.append({"mode": mode, "n": len(g), "both_correct": int(((g.en_correct == 1) & (g.hi_correct == 1)).sum()), "en_only": int(((g.en_correct == 1) & (g.hi_correct == 0)).sum()),
                     "hi_only": int(((g.en_correct == 0) & (g.hi_correct == 1)).sum()), "both_wrong": int(((g.en_correct == 0) & (g.hi_correct == 0)).sum()), "disagree_rate": g.disagree.mean(),
                     "wilson_lo": lo, "wilson_hi": hi, "cluster_lo": c[0], "cluster_hi": c[1], "unique_questions": g.uid.nunique()})
    save(pd.DataFrame(rows), "t1_outcomes")
    rates = []
    for col in ["difficulty", "task", "insertion"]:
        for mode in ["all", "off", "on"]:
            part = a if mode == "all" else a[a["mode"] == mode]
            strict = d if mode == "all" else d[d["mode"] == mode]
            for level, g in part.groupby(col, observed=True):
                c = boot_rate(g.disagree.to_numpy(), g.cl.to_numpy())
                s = strict[strict[col] == level]
                rates.append({"by": col, "level": level, "mode": mode, "n": len(g), "events": int(g.disagree.sum()), "rate": g.disagree.mean(), "lo": c[0], "hi": c[1], "strict_n": len(s), "strict_rate": s.disagree_strict.mean()})
    save(pd.DataFrame(rates), "t1_rates")
    mw = []
    for label, g in [("all", a), ("off", a[a["mode"] == "off"]), ("on", a[a["mode"] == "on"])] + [(f"off_{i}", a[(a["mode"] == "off") & (a.insertion == i)]) for i in INSERTIONS] + [(f"all_{i}", a[a.insertion == i]) for i in INSERTIONS]:
        x, y = g.rds[g.disagree == 1], g.rds[g.disagree == 0]
        u, p = stats.mannwhitneyu(x, y)
        s = np.sort(y.to_numpy())
        strict = (np.searchsorted(s, x.to_numpy(), "left")).sum() / (len(x) * len(y))
        c = boot_auc(g.disagree.to_numpy(), g.rds.to_numpy(), g.cl.to_numpy())
        mw.append({"sample": label, "n_dis": len(x), "n_agr": len(y), "mean_dis": x.mean(), "mean_agr": y.mean(), "median_dis": x.median(), "median_agr": y.median(), "u_share": u / (len(x) * len(y)), "strict_greater": strict, "ties": u / (len(x) * len(y)) - strict, "cl_lo": c[0], "cl_hi": c[1], "p_iid": p})
    save(pd.DataFrame(mw), "t2_mann_whitney")
    models = {
        "primary": (a, f"disagree ~ rds + {CONTROLS} + C(mode)"),
        "length_adjusted": (a, f"disagree ~ rds + gap + {CONTROLS} + C(mode)"),
        "off_adjusted": (a[a["mode"] == "off"], f"disagree ~ rds + {CONTROLS}"),
        "off_rds_only": (a[a["mode"] == "off"], "disagree ~ rds"),
        "on_adjusted": (a[a["mode"] == "on"], f"disagree ~ rds + {CONTROLS}"),
        "on_rds_only": (a[a["mode"] == "on"], "disagree ~ rds"),
    }
    rows, fitted = [], {}
    for name, (g, f) in models.items():
        res = smf.logit(f, g).fit(disp=0, maxiter=200, cov_type="cluster", cov_kwds={"groups": g.cl.to_numpy()})
        fitted[name] = res
        rows.append({"model": name} | summarize(res, "rds", g) | {"params": len(res.params) - 1, "epv": min(g.disagree.sum(), len(g) - g.disagree.sum()) / (len(res.params) - 1), "max_abs_coef_other": res.params.drop(["Intercept", "rds"]).abs().max() if len(res.params) > 2 else np.nan,
                     "sep_note": str(res.summary().extra_txt or "")[:90].replace("\n", " ")})
    save(pd.DataFrame(rows), "t3_report_models")
    p = fitted["primary"]
    ci = p.conf_int()
    RES["mode_or_primary"] = [float(np.exp(p.params["C(mode)[T.on]"])), float(np.exp(ci.loc["C(mode)[T.on]", 0])), float(np.exp(ci.loc["C(mode)[T.on]", 1]))]
    la = fitted["length_adjusted"]
    RES["gap_beta"] = [float(la.params["gap"]), float(la.bse["gap"]), float(la.pvalues["gap"])]
    cells = a[a["mode"] == "on"].groupby("task", observed=True).disagree.agg(["size", "sum"]).reset_index()
    save(cells, "t3_on_task_cells")
    RES["share_rds_gt_0.7"] = float((a.rds > 0.7).mean())
    RES["share_off"] = float((a["mode"] == "off").mean())
    RES["en_share_of_disagree"] = float(((a.en_correct == 1) & (a.hi_correct == 0)).sum() / a.disagree.sum())
    RES["hi_failures_share_off"] = float(((a["mode"] == "off") & (a.en_correct == 1) & (a.hi_correct == 0)).sum() / ((a["mode"] == "off") & (a.disagree == 1)).sum())
    excl = pd.DataFrame([{"mode": m, "pairs": len(g), "excluded": int((~g.answered).sum()), "en_missing": int(g.en_correct.isna().sum()), "hi_missing": int(g.hi_correct.isna().sum()), "both_missing": int((g.en_correct.isna() & g.hi_correct.isna()).sum()), "rds_missing": int(g.rds.isna().sum()), "rds_missing_in_answered": int((g.rds.isna() & g.answered).sum())} for m, g in [("all", d), ("off", d[d["mode"] == "off"]), ("on", d[d["mode"] == "on"])]])
    save(excl, "t4_exclusions_counts")
    bins = np.round(np.linspace(0, 1, 11), 2)
    binned = a.assign(rds_bin=pd.cut(a.rds, bins, include_lowest=True))
    t = []
    for (mode, b), g in binned.groupby(["mode", "rds_bin"], observed=True):
        lo, hi = proportion_confint(g.disagree.sum(), len(g), method="wilson")
        c = boot_rate(g.disagree.to_numpy(), g.cl.to_numpy()) if len(g) >= 20 and g.disagree.sum() else (np.nan, np.nan)
        t.append({"mode": mode, "rds_bin": str(b), "mid": b.mid, "n": len(g), "events": int(g.disagree.sum()), "rate": g.disagree.mean(), "wilson_lo": lo, "wilson_hi": hi, "cluster_lo": c[0], "cluster_hi": c[1], "shown_in_report": len(g) >= 20})
    t = save(pd.DataFrame(t), "t5_bin_rates")
    t.to_csv(FIG / "fig2_rate_by_rds_bin.csv", index=False, float_format="%.6g")
    hist = []
    edges = np.linspace(0, 1, 26)
    for (mode, y), g in a.groupby(["mode", "disagree"], observed=True):
        c, _ = np.histogram(g.rds, edges, density=False)
        hist += [{"mode": mode, "disagree": int(y), "bin_lo": edges[i], "bin_hi": edges[i + 1], "count": int(c[i]), "density": c[i] / (len(g) * (edges[1] - edges[0])), "median": g.rds.median(), "n": len(g)} for i in range(25)]
    pd.DataFrame(hist).to_csv(FIG / "fig1_rds_distribution.csv", index=False, float_format="%.6g")
    p = fitted["primary"]
    grid = []
    X = a.copy()
    for g in np.round(np.arange(0.3, 1.0001, 0.05), 2):
        X["rds"] = g
        pr = p.predict(X)
        off = (a["mode"] == "off").to_numpy()
        grid.append({"rds": g, "adj_pred_off": pr[off].mean(), "adj_pred_on": pr[~off].mean()})
    save(pd.DataFrame(grid), "t5_adjusted_predictions")
    ame = []
    for name, (g, f) in models.items():
        res = fitted[name]
        base = res.predict(g)
        up = res.predict(g.assign(rds=g.rds + 0.1))
        clip = res.predict(g.assign(rds=(g.rds + 0.1).clip(upper=1)))
        sd = g.rds.std()
        half = res.predict(g.assign(rds=(g.rds + sd).clip(upper=1)))
        ame.append({"model": name, "base_rate": g.disagree.mean(), "ame_derivative_pp": 100 * 0.1 * res.params["rds"] * (base * (1 - base)).mean(), "mean_p1mp": (base * (1 - base)).mean(), "finite_diff_unclipped_pp": 100 * (up - base).mean(), "finite_diff_clipped_pp": 100 * (clip - base).mean(), "finite_sd_clipped_pp": 100 * (half - base).mean(), "share_rds_gt_0.9": (g.rds > 0.9).mean(), "sd_rds": sd})
    save(pd.DataFrame(ame), "t6_ame_scaling")
    return fitted


def views_table(d):
    a = d[d.answered].copy()
    cols = [f"c_{v}" for v in VIEWS]
    cc = a.dropna(subset=cols).copy()
    RES["views_complete_case_n"] = len(cc)
    rows, cond = [], []
    for v, desc in VIEWS.items():
        g = cc.assign(x=cc[f"c_{v}"], xgap=cc[f"c_{v}_gap"])
        off = g[g["mode"] == "off"]
        base = smf.logit(f"disagree ~ {CONTROLS} + C(mode)", g).fit(disp=0, maxiter=200)
        for label, sample, f in [("primary", g, f"disagree ~ x + {CONTROLS} + C(mode)"), ("length_adjusted", g, f"disagree ~ x + xgap + {CONTROLS} + C(mode)"), ("off_primary", off, f"disagree ~ x + {CONTROLS}")] + [(f"primary_{i}", g[g.insertion == i], f"disagree ~ x + C(difficulty) + C(task) + C(mode)") for i in INSERTIONS]:
            res = smf.logit(f, sample).fit(disp=0, maxiter=200, cov_type="cluster", cov_kwds={"groups": sample.cl.to_numpy()})
            rows.append({"view": v, "model": label} | summarize(res, "x", sample) | {"auc_view_alone": auc(sample.disagree, sample.x)})
        rows[-6]["auc_controls_only"] = auc(g.disagree, base.predict(g))
        o = off.assign(ins_sim=(off.insertion == "similar_insertion").astype(float), ins_dis=(off.insertion == "dissimilar_insertion").astype(float))
        cond.append({"view": v, "sample": "off"} | clogit(o, "x", ["ins_sim", "ins_dis"]) | within_concordance(o, "x"))
        cond[-1]["desc"] = desc
    save(pd.DataFrame(rows).drop(columns=["clusters", "converged"]), "t7_views_models")
    save(pd.DataFrame(cond), "t8_views_within_question")
    rows = []
    off = cc[cc["mode"] == "off"].copy()
    for pair in combinations(INSERTIONS, 2):
        g = off[off.insertion.isin(pair)]
        for v in ["full", "noans", "ops", "opsnoans"]:
            rows.append({"contrast": " vs ".join(pair), "view": v} | within_concordance(g.assign(x=g[f"c_{v}"]), "x"))
    save(pd.DataFrame(rows), "t8_within_question_by_insertion_contrast")
    flips = []
    w = d[d["mode"] == "off"].dropna(subset=cols)
    for label, cond_, y in [("hindi_flip_english_right", (w.en_correct == 1) & w.hi_correct.notna(), lambda g: 1 - g.hi_correct), ("english_flip_hindi_right", (w.hi_correct == 1) & w.en_correct.notna(), lambda g: 1 - g.en_correct), ("hindi_flip_english_wrong", (w.en_correct == 0) & w.hi_correct.notna(), lambda g: 1 - g.hi_correct)]:
        g = w[cond_].copy()
        g["y"] = y(g)
        for v in ["full", "noans", "noansval", "ops", "opsnoans", "prefix8ops"]:
            flips.append({"flip": label, "view": v} | within_concordance(g.assign(x=g[f"c_{v}"]), "x", ycol="y"))
    save(pd.DataFrame(flips), "t8_flip_types")
    flips = []
    g0 = w[(w.en_correct == 1) & w.hi_correct.notna()].copy()
    g0["y"] = 1 - g0.hi_correct
    for t in TASKS:
        for v in ["full", "noans", "opsnoans"]:
            flips.append({"task": t, "view": v} | within_concordance(g0[g0.task == t].assign(x=lambda z: z[f"c_{v}"]), "x", ycol="y"))
    save(pd.DataFrame(flips), "t8_hindi_flip_by_task")
    share = a[a["mode"] == "off"].assign(en=lambda z: z.c_en_answer_tokens / z.c_full_en.where(z.c_full_en > 0), hi=lambda z: z.c_hi_answer_tokens / z.c_full_hi.where(z.c_full_hi > 0)).groupby("task", observed=True)[["en", "hi", "c_full_en", "c_full_hi"]].mean().reset_index()
    save(share, "t8_answer_token_share_by_task")
    both_ok = a[(a.en_correct == 1) & (a.hi_correct == 1) & (a["mode"] == "off")]
    RES["mechanical_corruption"] = {"n_both_correct": len(both_ok), "rds_actual": float(both_ok.c_full.mean()), "rds_with_hindi_answer_token_values_replaced": float(both_ok.c_corrupted.mean()), "delta": float((both_ok.c_corrupted - both_ok.c_full).mean()),
                                    "observed_gap_disagree_vs_both_correct_off": float(a[(a["mode"] == "off") & (a.disagree == 1)].c_full.mean() - both_ok.c_full.mean()),
                                    "observed_gap_disagree_vs_agree_off": float(a[(a["mode"] == "off") & (a.disagree == 1)].c_full.mean() - a[(a["mode"] == "off") & (a.disagree == 0)].c_full.mean())}
    sim = pd.concat([both_ok.assign(y=0, x=both_ok.c_full), both_ok.assign(y=1, x=both_ok.c_corrupted)])
    RES["mechanical_corruption"]["auc_same_pairs_true_vs_corrupted"] = float(auc(sim.y, sim.x))
    return cc


def outcome_contrasts(d):
    a = d[d.answered & (d["mode"] == "off")].copy()
    a["o"] = np.select([(a.en_correct == 1) & (a.hi_correct == 1), (a.en_correct == 1) & (a.hi_correct == 0), (a.en_correct == 0) & (a.hi_correct == 1)], ["both_correct", "en_only", "hi_only"], "both_wrong")
    a["ans_same"] = a.en_answer.map(norm_answer) == a.hi_answer.map(norm_answer)
    rows = []
    for o, g in a.groupby("o"):
        rows.append({"outcome": o, "n": len(g)} | {v: g[f"c_{v}"].mean() for v in VIEWS} | {"en_len": g.c_full_en.median(), "hi_len": g.c_full_hi.median(), "gap": g.gap.mean()})
    save(pd.DataFrame(rows), "t9_rds_by_outcome").to_csv(FIG / "fig7_rds_by_outcome.csv", index=False, float_format="%.6g")
    rows = []
    for label, keep, y in [("disagree vs both_correct", a.o != "both_wrong", lambda g: g.disagree), ("disagree vs both_wrong", a.o != "both_correct", lambda g: g.disagree), ("any_wrong vs both_correct", a.o != "", lambda g: (g.o != "both_correct").astype(float)), ("both_wrong vs both_correct", a.o.isin(["both_wrong", "both_correct"]), lambda g: (g.o == "both_wrong").astype(float))]:
        base = a[keep].copy()
        base["y"] = y(base)
        for v in ["full", "noans", "ops", "opsnoans"]:
            g = base.assign(x=base[f"c_{v}"]).dropna(subset=["x"])
            res = smf.logit(f"y ~ x + {CONTROLS}", g).fit(disp=0, maxiter=200, cov_type="cluster", cov_kwds={"groups": g.cl.to_numpy()})
            s = summarize(res, "x", g, "y")
            rows.append({"contrast": label, "view": v, "n": s["n"], "events": s["events"], "or_per_0.1": s["or_per_0.1"], "or_lo": s["or_lo"], "or_hi": s["or_hi"], "or_per_sd": s["or_per_sd"], "p": s["p"], "auc_view_alone": auc(g.y, g.x)})
    save(pd.DataFrame(rows), "t9_outcome_contrasts")
    bw = a[a.o == "both_wrong"]
    save(bw.groupby("ans_same")[["c_full", "c_noans", "c_ops", "c_opsnoans"]].agg(["size", "mean"]).reset_index().pipe(lambda t: t.set_axis(["_".join(c).strip("_") for c in t.columns], axis=1)), "t9_both_wrong_same_answer")
    all_a = d[d.answered].copy()
    all_a["ans_differ"] = (all_a.en_answer.map(norm_answer) != all_a.hi_answer.map(norm_answer)).astype(float)
    tp = ((all_a.ans_differ == 1) & (all_a.disagree == 1)).sum()
    RES["answers_differ_rule"] = {"recall": float(tp / all_a.disagree.sum()), "precision": float(tp / all_a.ans_differ.sum()), "auc": float(auc(all_a.disagree, all_a.ans_differ)), "n": len(all_a),
                                  "note": "Comparing the two final answer strings is sufficient for this outcome: disagreement implies differing answers."}


def cross_val(cc):
    g = cc.reset_index(drop=True).copy()
    y = g.disagree.to_numpy()
    cl = pd.factorize(g.uid)[0]
    rng = np.random.default_rng(SEED)
    perm = rng.permutation(cl.max() + 1)
    fold = (perm % FOLDS)[cl]
    g["log_en"], g["log_hi"] = np.log1p(g.c_full_en), np.log1p(g.c_full_hi)
    base_a = f"{CONTROLS} + C(mode)"
    base_b = "C(difficulty):C(task) + C(insertion) + C(mode)"
    specs = {"base": base_a, "base_txd": base_b, "lengths_only": f"{base_a} + log_en + log_hi", "gap_only": f"{base_a} + gap"}
    for v in ["full", "noans", "noansval", "ops", "opsnoans", "opscore", "prefix8", "prefix8ops", "precheck", "precheckops"]:
        g[f"z_{v}"] = g[f"c_{v}"]
        specs[f"base+{v}"] = f"{base_a} + z_{v}"
        specs[f"base_txd+{v}"] = f"{base_b} + z_{v}"
    specs["base+full+lengths"] = f"{base_a} + z_full + log_en + log_hi"
    specs["base+opsnoans+lengths"] = f"{base_a} + z_opsnoans + log_en + log_hi"
    oof = {}
    for name, f in specs.items():
        X = np.asarray(patsy.dmatrix(f, g))
        scale = X.std(0)
        scale[scale == 0] = 1
        X = X / scale
        p = np.zeros(len(y))
        for k in range(FOLDS):
            te = fold == k
            p[te] = expit(X[te] @ irls(X[~te], y[~te]))
        oof[name] = p
    rows = []
    masks = {"all": np.ones(len(g), bool), "off": (g["mode"] == "off").to_numpy(), "on": (g["mode"] == "on").to_numpy()} | {i: (g.insertion == i).to_numpy() for i in INSERTIONS}
    tasks = g.task.astype(str).to_numpy()
    for name, p in oof.items():
        for mname, m in masks.items():
            within = np.mean([auc(y[m & (tasks == t)], p[m & (tasks == t)]) for t in TASKS if 0 < y[m & (tasks == t)].sum() < (m & (tasks == t)).sum()])
            rows.append({"model": name, "sample": mname, "n": int(m.sum()), "auc": auc(y[m], p[m]), "within_task_auc": within, "logloss": -(y[m] * np.log(p[m] + 1e-12) + (1 - y[m]) * np.log(1 - p[m] + 1e-12)).mean(), "brier": ((y[m] - p[m]) ** 2).mean()})
    t = save(pd.DataFrame(rows), "t10_cv_auc")
    delta = []
    rng = np.random.default_rng(SEED)
    weights = [rng.multinomial(cl.max() + 1, np.full(cl.max() + 1, 1 / (cl.max() + 1)))[cl] for _ in range(1000)]
    for ref in ["base", "base_txd"]:
        for v in ["full", "noans", "noansval", "ops", "opsnoans", "opscore", "prefix8", "prefix8ops", "precheck", "precheckops"]:
            for mname in ["all", "off"] + INSERTIONS:
                m = masks[mname]
                a0, a1 = oof[ref][m], oof[f"{ref}+{v}"][m]
                obs = auc(y[m], a1) - auc(y[m], a0)
                bs = [auc(y[m], a1, w[m]) - auc(y[m], a0, w[m]) for w in weights] if mname in ("all", "off") else [auc(y[m], a1, w[m]) - auc(y[m], a0, w[m]) for w in weights[:300]]
                delta.append({"baseline": ref, "view": v, "sample": mname, "n": int(m.sum()), "auc_base": auc(y[m], a0), "auc_with": auc(y[m], a1), "delta_auc": obs, "lo": np.percentile(bs, 2.5), "hi": np.percentile(bs, 97.5)})
    save(pd.DataFrame(delta), "t10_cv_delta").to_csv(FIG / "fig5_cv_delta_auc.csv", index=False, float_format="%.6g")
    return t


def mode_analysis(d):
    on_uids = set(d[d["mode"] == "on"].uid)
    m = d[d.uid.isin(on_uids)].copy()
    rows = []
    for mode, g in m.groupby("mode", observed=True):
        a = g[g.answered]
        c = boot_rate(a.disagree.to_numpy(), a.cl.to_numpy())
        rows.append({"mode": mode, "pairs": len(g), "answered": len(a), "unanswered_share": 1 - len(a) / len(g), "disagree_answered": a.disagree.mean(), "lo": c[0], "hi": c[1], "disagree_strict": g.disagree_strict.mean(), "en_acc_strict": g.en_strict.mean(), "hi_acc_strict": g.hi_strict.mean(), "en_acc_answered": g.en_correct.mean(), "hi_acc_answered": g.hi_correct.mean(), "gap_strict_pp": 100 * (g.en_strict.mean() - g.hi_strict.mean()), "mean_rds_content": a.c_full.mean(), "mean_rds_noans": a.c_noans.mean(), "mean_rds_opsnoans": a.c_opsnoans.mean(), "mean_rds_reasoning": a.r_full.mean(), "mean_en_toks": g.c_full_en.mean(), "mean_hi_toks": g.c_full_hi.mean(), "en_tokens_median": g.en_tokens.median(), "hi_tokens_median": g.hi_tokens.median(), "en_over_4096": (g.en_tokens > 4096).mean(), "hi_over_4096": (g.hi_tokens > 4096).mean(), "uids": g.uid.nunique()})
    save(pd.DataFrame(rows), "t11_matched_450_summary").to_csv(FIG / "fig8_matched_modes.csv", index=False, float_format="%.6g")
    on = d[d["mode"] == "on"]
    capped = on.assign(en_c=on.en_strict.where(on.en_tokens <= 4096, 0.0), hi_c=on.hi_strict.where(on.hi_tokens <= 4096, 0.0))
    pc = []
    for label, g in [("on_strict_16000", on.assign(en_c=on.en_strict, hi_c=on.hi_strict)), ("on_simulated_4096_cap_strict", capped), ("on_answered_within_4096_only", on[(on.en_tokens <= 4096) & (on.hi_tokens <= 4096) & on.answered].assign(en_c=lambda t: t.en_correct, hi_c=lambda t: t.hi_correct)), ("off_matched_strict", m[m["mode"] == "off"].assign(en_c=lambda t: t.en_strict, hi_c=lambda t: t.hi_strict))]:
        pc.append({"scenario": label, "n": len(g), "en_acc": g.en_c.mean(), "hi_acc": g.hi_c.mean(), "disagree": (g.en_c != g.hi_c).mean()})
    save(pd.DataFrame(pc), "t11_budget_sensitivity")
    wide = m.pivot_table(index=["uid", "insertion"], columns="mode", values=["disagree", "disagree_strict", "en_strict", "hi_strict"], observed=True)
    res = []
    for col in ["disagree", "disagree_strict"]:
        for label, part in [("all", wide)] + [(i, wide[wide.index.get_level_values("insertion") == i]) for i in INSERTIONS]:
            w = part[col].dropna()
            b, c = int(((w["off"] == 1) & (w["on"] == 0)).sum()), int(((w["off"] == 0) & (w["on"] == 1)).sum())
            r = stats.binomtest(b, b + c, 0.5).pvalue if b + c else np.nan
            lo, hi = stats.binomtest(c, b + c).proportion_ci(method="exact") if b + c else (np.nan, np.nan)
            res.append({"outcome": col, "insertion": label, "pairs": len(w), "off_rate": w["off"].mean(), "on_rate": w["on"].mean(), "off_only": b, "on_only": c, "matched_or_on_vs_off": c / b if b else np.nan, "or_lo": lo / (1 - lo) if b + c else np.nan, "or_hi": hi / (1 - hi) if b + c else np.nan, "mcnemar_p": r})
    save(pd.DataFrame(res), "t11_matched_mcnemar")
    a = m[m.answered].copy()
    a["on"] = (a["mode"] == "on").astype(float)
    pool = d[d.answered].copy()
    rows = []
    specs = [("all_questions, with content RDS", pool, f"disagree ~ rds + {CONTROLS} + C(mode)"), ("all_questions, no RDS", pool, f"disagree ~ {CONTROLS} + C(mode)"), ("all_questions, raw", pool, "disagree ~ C(mode)"),
             ("matched_450, with content RDS", a, f"disagree ~ rds + {CONTROLS} + C(mode)"), ("matched_450, no RDS", a, f"disagree ~ {CONTROLS} + C(mode)"), ("matched_450, raw", a, "disagree ~ C(mode)")]
    for label, g, f in specs:
        r = smf.logit(f, g).fit(disp=0, maxiter=200, cov_type="cluster", cov_kwds={"groups": g.cl.to_numpy()})
        ci = r.conf_int().loc["C(mode)[T.on]"]
        rows.append({"spec": label, "n": int(r.nobs), "or_on_vs_off": np.exp(r.params["C(mode)[T.on]"]), "lo": np.exp(ci[0]), "hi": np.exp(ci[1]), "p": r.pvalues["C(mode)[T.on]"]})
    sa = m.copy()
    sa["on"] = (sa["mode"] == "on").astype(float)
    r = smf.logit(f"disagree_strict ~ {CONTROLS} + C(mode)", sa).fit(disp=0, maxiter=200, cov_type="cluster", cov_kwds={"groups": sa.cl.to_numpy()})
    ci = r.conf_int().loc["C(mode)[T.on]"]
    rows.append({"spec": "matched_450, strict outcome, no RDS", "n": int(r.nobs), "or_on_vs_off": np.exp(r.params["C(mode)[T.on]"]), "lo": np.exp(ci[0]), "hi": np.exp(ci[1]), "p": r.pvalues["C(mode)[T.on]"]})
    save(pd.DataFrame(rows), "t11_mode_or")
    rows = []
    on_a = on[on.answered].copy()
    off_m = a[a["mode"] == "off"].copy()
    for tag, label in [("c", "content"), ("r", "reasoning")]:
        for v in ["full", "noans", "ops", "opsnoans", "precheckops"]:
            on_a["x"] = on_a[f"{tag}_{v}"]
            rows.append(firth_row(on_a, "x", "", f"ON, {label}, {v}, x only") | {"var": v, "channel": label})
    on_a["x"] = on_a.c_full
    rows.append(firth_row(on_a, "x", "C(difficulty) + C(insertion) + C(task)", "ON, content, full, fully adjusted") | {"var": "full", "channel": "content"})
    on_a["x"] = on_a.c_noans
    rows.append(firth_row(on_a, "x", "C(difficulty) + C(insertion) + C(task)", "ON, content, noans, fully adjusted") | {"var": "noans", "channel": "content"})
    on_a["x"] = on_a.c_opsnoans
    rows.append(firth_row(on_a, "x", "C(difficulty) + C(insertion) + C(task)", "ON, content, opsnoans, fully adjusted") | {"var": "opsnoans", "channel": "content"})
    on_a["x"] = on_a.r_full
    rows.append(firth_row(on_a, "x", "C(difficulty) + C(insertion) + C(task)", "ON, reasoning, full, fully adjusted") | {"var": "full", "channel": "reasoning"})
    on_a["x"] = on_a.r_opsnoans
    rows.append(firth_row(on_a, "x", "C(difficulty) + C(insertion) + C(task)", "ON, reasoning, opsnoans, fully adjusted") | {"var": "opsnoans", "channel": "reasoning"})
    save(pd.DataFrame(rows), "t12_on_firth")
    rows = []
    for tag, g, name in [("c", on_a, "ON content"), ("r", on_a, "ON reasoning"), ("c", off_m, "OFF same 450")]:
        for v in ["full", "noans", "ops", "opsnoans"]:
            x = g[f"{tag}_{v}"]
            k = x.notna()
            c = boot_auc(g.disagree[k].to_numpy(), x[k].to_numpy(), g.cl[k].to_numpy(), B=500)
            rows.append({"sample": name, "view": v, "n": int(k.sum()), "events": int(g.disagree[k].sum()), "mean_dis": x[g.disagree == 1].mean(), "mean_agr": x[g.disagree == 0].mean(), "auc": auc(g.disagree[k], x[k]), "lo": c[0], "hi": c[1]})
    save(pd.DataFrame(rows), "t12_on_auc")
    s = []
    for v in ["full", "noans", "ops", "opsnoans"]:
        g = off_m.assign(x=off_m[f"c_{v}"]).dropna(subset=["x"])
        res = smf.logit(f"disagree ~ x + {CONTROLS}", g).fit(disp=0, maxiter=200, cov_type="cluster", cov_kwds={"groups": g.cl.to_numpy()})
        s.append({"view": v} | summarize(res, "x", g))
    save(pd.DataFrame(s).drop(columns=["clusters"]), "t12_off_same_450_slope")
    res_on = smf.logit("disagree ~ rds", on_a).fit(disp=0, maxiter=200, cov_type="cluster", cov_kwds={"groups": on_a.cl.to_numpy()})
    loo = []
    ev_uids = on_a[on_a.disagree == 1].uid.unique()
    for u in ev_uids:
        g = on_a[on_a.uid != u]
        loo.append(smf.logit("disagree ~ rds", g).fit(disp=0, maxiter=200).params["rds"])
    RES["on_rds_only"] = {"beta": float(res_on.params["rds"]), "ll": float(res_on.llf), "sep_message": str(res_on.summary().extra_txt), "disagreeing_clusters": int(len(ev_uids)), "events": int(on_a.disagree.sum()), "loo_beta_min": float(min(loo)), "loo_beta_max": float(max(loo)), "min_rds_event": float(on_a.rds[on_a.disagree == 1].min()), "share_nonevents_below_min_event": float((on_a.rds[on_a.disagree == 0] < on_a.rds[on_a.disagree == 1].min()).mean())}


def exclusions(d):
    rows = []
    for col in ["mode", "difficulty", "task", "insertion"]:
        for level, g in d.groupby(col, observed=True):
            rows.append({"by": col, "level": level, "pairs": len(g), "excluded": int((~g.answered).sum()), "share": (~g.answered).mean(), "en_missing": int(g.en_correct.isna().sum()), "hi_missing": int(g.hi_correct.isna().sum())})
    save(pd.DataFrame(rows), "t13_exclusion_rates")
    rows = []
    for m, g in d.groupby("mode", observed=True):
        e = g[~g.answered]
        rows.append({"mode": m, "excluded": len(e), "en_cut_at_limit": int((e.en_correct.isna() & (e.en_finish == "length")).sum()), "hi_cut_at_limit": int((e.hi_correct.isna() & (e.hi_finish == "length")).sum()), "en_missing_stop": int((e.en_correct.isna() & (e.en_finish != "length")).sum()), "hi_missing_stop": int((e.hi_correct.isna() & (e.hi_finish != "length")).sum()),
                     "hi_correct_when_en_missing": e[e.en_correct.isna()].hi_correct.mean(), "en_correct_when_hi_missing": e[e.hi_correct.isna()].en_correct.mean(), "hi_acc_included": g[g.answered].hi_correct.mean(), "en_acc_included": g[g.answered].en_correct.mean(), "rds_excluded_mean": e.rds.mean(), "rds_excluded_defined": int(e.rds.notna().sum()), "rds_included_mean": g[g.answered].rds.mean(), "en_len_excl": e.c_full_en.median(), "hi_len_excl": e.c_full_hi.median(), "gap_excl": e.gap.mean(), "gap_incl": g[g.answered].gap.mean()})
    save(pd.DataFrame(rows), "t13_excluded_profile")
    ex = d.assign(excl=(~d.answered).astype(float))
    r = smf.logit(f"excl ~ {CONTROLS} + C(mode)", ex).fit(disp=0, maxiter=200, cov_type="cluster", cov_kwds={"groups": ex.cl.to_numpy()})
    w = r.wald_test(np.eye(len(r.params))[[i for i, n in enumerate(r.params.index) if "task" in n]], scalar=True)
    w2 = r.wald_test(np.eye(len(r.params))[[i for i, n in enumerate(r.params.index) if "difficulty" in n]], scalar=True)
    RES["exclusion_wald"] = {"task_chi2": float(w.statistic), "task_p": float(w.pvalue), "difficulty_chi2": float(w2.statistic), "difficulty_p": float(w2.pvalue), "auc": float(auc(ex.excl, r.predict(ex)))}
    rows = []
    def add(label, g, ycol, var="rds"):
        g = g.dropna(subset=[var])
        res = smf.logit(f"{ycol} ~ {var} + {CONTROLS} + C(mode)", g).fit(disp=0, maxiter=200, cov_type="cluster", cov_kwds={"groups": g.cl.to_numpy()})
        s = summarize(res, var, g, ycol)
        mi = res.params["C(mode)[T.on]"]
        rows.append({"scenario": label, "n": s["n"], "events": s["events"], "rate": g[ycol].mean(), "or_per_0.1": s["or_per_0.1"], "or_lo": s["or_lo"], "or_hi": s["or_hi"], "ame_pp": s["ame_pp_per_0.1"], "or_per_sd": s["or_per_sd"], "auc": s["auc_insample"], "mode_or": np.exp(mi)})
    add("answered only (report)", d[d.answered], "disagree")
    add("strict, RDS defined", d, "disagree_strict")
    imputed = d.assign(rds=d.rds.fillna(1.0))
    add("strict, undefined RDS set to 1", imputed, "disagree_strict")
    add("excluded counted as agree", d.assign(y=d.disagree.fillna(0)), "y")
    add("excluded counted as disagree", d.assign(y=d.disagree.fillna(1)), "y")
    for v in ["noans", "opsnoans"]:
        g = d.assign(x=d[f"c_{v}"])
        add(f"strict, {v}", g, "disagree_strict", "x")
        add(f"answered only, {v}", g[g.answered], "disagree", "x")
    save(pd.DataFrame(rows), "t14_exclusion_sensitivity")
    t = []
    for m, g in [("all", d), ("off", d[d["mode"] == "off"]), ("on", d[d["mode"] == "on"])]:
        t.append({"mode": m, "n": len(g), "both_correct": int(((g.en_strict == 1) & (g.hi_strict == 1)).sum()), "en_only": int(((g.en_strict == 1) & (g.hi_strict == 0)).sum()), "hi_only": int(((g.en_strict == 0) & (g.hi_strict == 1)).sum()), "both_wrong": int(((g.en_strict == 0) & (g.hi_strict == 0)).sum()), "disagree_strict": g.disagree_strict.mean(), "en_share_of_disagree": ((g.en_strict == 1) & (g.hi_strict == 0)).sum() / g.disagree_strict.sum(), "lo_hi": str(np.round(boot_rate(g.disagree_strict.to_numpy(), g.cl.to_numpy()), 4))})
    save(pd.DataFrame(t), "t14_strict_outcomes")
    s = d.assign(ins_sim=(d.insertion == "similar_insertion").astype(float), ins_dis=(d.insertion == "dissimilar_insertion").astype(float))
    off = s[s["mode"] == "off"]
    rows = [{"view": v, "outcome": "strict"} | clogit(off.assign(x=off[f"c_{v}"]), "x", ["ins_sim", "ins_dis"], ycol="disagree_strict", boot=False) for v in ["full", "noans", "opsnoans"]]
    save(pd.DataFrame(rows), "t14_strict_within_question")


def length_analysis(d):
    a = d[d.answered].copy()
    off = a[a["mode"] == "off"]
    rows = []
    for label, g in [("all", a), ("off", off), ("off, no_insertion", off[off.insertion == "no_insertion"]), ("off, similar", off[off.insertion == "similar_insertion"]), ("off, dissimilar", off[off.insertion == "dissimilar_insertion"])]:
        X = np.asarray(patsy.dmatrix(f"rds + gap + {CONTROLS}", g))
        names = patsy.dmatrix(f"rds + gap + {CONTROLS}", g).design_info.column_names
        keep = [i for i, n in enumerate(names) if X[:, i].std() > 0 or i == 0]
        X = X[:, keep]
        names = [names[i] for i in keep]
        rows.append({"sample": label, "pearson_rds_gap": g.rds.corr(g.gap), "spearman": g.rds.corr(g.gap, method="spearman"), "vif_rds": variance_inflation_factor(X, names.index("rds")), "vif_gap": variance_inflation_factor(X, names.index("gap")), "mean_floor_share_of_rds": (g.gap / g.rds).replace([np.inf], np.nan).mean(), "mean_ratio": g.gap.mean() / g.rds.mean(), "floor_violations": int((g.gap > g.rds + 1e-9).sum()), "mean_gap": g.gap.mean(), "mean_rds": g.rds.mean(), "gap_dis": g.gap[g.disagree == 1].mean(), "gap_agr": g.gap[g.disagree == 0].mean(), "auc_gap_alone": auc(g.disagree, g.gap), "auc_rds_alone": auc(g.disagree, g.rds)})
    save(pd.DataFrame(rows), "t15_length_collinearity")
    a["excess"] = a.rds - a.gap
    a["excess_norm"] = (a.rds - a.gap) / (1 - a.gap).where(lambda s: s > 0)
    a["log_en"], a["log_hi"] = np.log1p(a.c_full_en), np.log1p(a.c_full_hi)
    a["gap_na"], a["rds_na"] = a.c_noans_gap, a.c_noans
    a["gap_ops"], a["rds_ops"] = a.c_opsnoans_gap, a.c_opsnoans
    rows = []
    specs = [("gap only", ["gap"]), ("rds only", ["rds"]), ("rds + gap", ["rds", "gap"]), ("floor + excess", ["gap", "excess"]), ("rds + log_en + log_hi", ["rds", "log_en", "log_hi"]), ("log_en + log_hi only", ["log_en", "log_hi"]), ("noans only", ["rds_na"]), ("noans + gap", ["rds_na", "gap_na"]), ("opsnoans only", ["rds_ops"]), ("opsnoans + gap", ["rds_ops", "gap_ops"]), ("gap(noans) only", ["gap_na"])]
    g = a.dropna(subset=["rds_na", "rds_ops", "gap_na", "gap_ops"])
    for label, xs in specs:
        res = smf.logit(f"disagree ~ {' + '.join(xs)} + {CONTROLS} + C(mode)", g).fit(disp=0, maxiter=200, cov_type="cluster", cov_kwds={"groups": g.cl.to_numpy()})
        r = {"spec": label, "n": int(res.nobs), "auc": auc(g.disagree, res.predict(g)), "aic": res.aic, "bic": res.bic}
        for x in xs:
            ci = res.conf_int().loc[x]
            r[f"{x}_beta"], r[f"{x}_lo"], r[f"{x}_hi"] = res.params[x], ci[0], ci[1]
        rows.append(r)
    save(pd.DataFrame(rows), "t15_length_models")
    rows = []
    a["gap_band"] = pd.cut(a.gap, [-0.01, 0.2, 0.4, 0.6, 0.8, 1.0], labels=["0-0.2", "0.2-0.4", "0.4-0.6", "0.6-0.8", "0.8-1"])
    for band, part in a[a["mode"] == "off"].groupby("gap_band", observed=True):
        for v in ["full", "noans", "opsnoans"]:
            p = part.assign(x=part[f"c_{v}"]).dropna(subset=["x"])
            res = smf.logit(f"disagree ~ x + {CONTROLS}", p).fit(disp=0, maxiter=200, cov_type="cluster", cov_kwds={"groups": p.cl.to_numpy()})
            s = summarize(res, "x", p)
            rows.append({"gap_band": band, "view": v, "n": s["n"], "events": s["events"], "rate": p.disagree.mean(), "mean_x": p.x.mean(), "or_per_0.1": s["or_per_0.1"], "or_lo": s["or_lo"], "or_hi": s["or_hi"], "or_per_sd": s["or_per_sd"], "auc_x": auc(p.disagree, p.x)})
    save(pd.DataFrame(rows), "t15_slope_by_gap_band")
    rows = []
    for o, g2 in a[a["mode"] == "off"].groupby(["en_correct", "hi_correct"]):
        rows.append({"en_correct": o[0], "hi_correct": o[1], "n": len(g2), "en_len_med": g2.c_full_en.median(), "hi_len_med": g2.c_full_hi.median(), "en_longer_share": (g2.c_full_en > g2.c_full_hi).mean(), "gap_mean": g2.gap.mean(), "excess_mean": g2.excess.mean(), "rds_mean": g2.rds.mean(), "en_answer_tokens": g2.c_en_answer_tokens.mean(), "hi_answer_tokens": g2.c_hi_answer_tokens.mean()})
    save(pd.DataFrame(rows), "t15_length_by_outcome")


def linearity(d):
    a = d[d.answered].copy()
    rows, cal = [], []
    for v in ["full", "noans", "opsnoans"]:
        for label, g in [("all", a), ("off", a[a["mode"] == "off"])]:
            g = g.assign(x=g[f"c_{v}"]).dropna(subset=["x"])
            mode = " + C(mode)" if label == "all" else ""
            lin = smf.logit(f"disagree ~ x + {CONTROLS}{mode}", g).fit(disp=0, maxiter=200, cov_type="cluster", cov_kwds={"groups": g.cl.to_numpy()})
            spl = smf.logit(f"disagree ~ cr(x, df=5) + {CONTROLS}{mode}", g).fit(disp=0, maxiter=200, cov_type="cluster", cov_kwds={"groups": g.cl.to_numpy()})
            g2 = g.assign(a1=np.maximum(g.x - 0.7, 0), a2=np.maximum(g.x - 0.9, 0))
            pw = smf.logit(f"disagree ~ x + a1 + a2 + {CONTROLS}{mode}", g2).fit(disp=0, maxiter=200, cov_type="cluster", cov_kwds={"groups": g2.cl.to_numpy()})
            pc = pw.params
            terms = [i for i, n in enumerate(pw.params.index) if n in ("a1", "a2")]
            wald = pw.wald_test(np.eye(len(pc))[terms], scalar=True)
            rows.append({"view": v, "sample": label, "n": int(lin.nobs), "aic_linear": lin.aic, "aic_spline": spl.aic, "bic_linear": lin.bic, "bic_spline": spl.bic, "lr_chi2_vs_linear_iid": 2 * (spl.llf - lin.llf), "piecewise_wald_chi2_cluster": float(wald.statistic), "piecewise_wald_p": float(wald.pvalue), "slope_below_0.7_or01": np.exp(0.1 * pc["x"]), "slope_0.7_0.9_or01": np.exp(0.1 * (pc["x"] + pc["a1"])), "slope_above_0.9_or01": np.exp(0.1 * (pc["x"] + pc["a1"] + pc["a2"])), "auc_linear": auc(g.disagree, lin.predict(g)), "auc_spline": auc(g.disagree, spl.predict(g)), "share_gt_0.7": (g.x > 0.7).mean(), "share_gt_0.9": (g.x > 0.9).mean(), "share_eq_1": (g.x == 1).mean()})
            if label == "off":
                q = pd.qcut(g.x, 10, duplicates="drop")
                t = g.assign(p_lin=lin.predict(g), p_spl=spl.predict(g), q=q).groupby("q", observed=True).agg(n=("disagree", "size"), x=("x", "mean"), obs=("disagree", "mean"), lin=("p_lin", "mean"), spl=("p_spl", "mean")).reset_index()
                t["view"] = v
                t["q"] = t["q"].astype(str)
                cal.append(t)
    save(pd.DataFrame(rows), "t16_linearity")
    t = pd.concat(cal)
    save(t, "t16_calibration").to_csv(FIG / "fig6_calibration.csv", index=False, float_format="%.6g")


def splits(d):
    a = d[d.answered & (d["mode"] == "off")].copy()
    a["ins_sim"], a["ins_dis"] = (a.insertion == "similar_insertion").astype(float), (a.insertion == "dissimilar_insertion").astype(float)
    rows, cond = [], []
    for col, levels, ctl in [("task", TASKS, "C(difficulty) + C(insertion)"), ("insertion", INSERTIONS, "C(difficulty) + C(task)"), ("difficulty", DIFFICULTIES, "C(task) + C(insertion)")]:
        for lv in levels:
            part = a[a[col] == lv]
            for v in ["full", "noans", "noansval", "ops", "opsnoans"]:
                g = part.assign(x=part[f"c_{v}"]).dropna(subset=["x"])
                res = smf.logit(f"disagree ~ x + {ctl}", g).fit(disp=0, maxiter=200, cov_type="cluster", cov_kwds={"groups": g.cl.to_numpy()})
                s = summarize(res, "x", g)
                c = boot_auc(g.disagree.to_numpy(), g.x.to_numpy(), g.cl.to_numpy(), B=300) if col == "task" else (np.nan, np.nan)
                rows.append({"by": col, "level": lv, "view": v, "n": s["n"], "events": s["events"], "rate": g.disagree.mean(), "beta": s["beta"], "or_per_0.1": s["or_per_0.1"], "or_lo": s["or_lo"], "or_hi": s["or_hi"], "or_per_sd": s["or_per_sd"], "ame_pp_per_sd": s["ame_pp_per_sd"], "p": s["p"], "auc_x": auc(g.disagree, g.x), "auc_lo": c[0], "auc_hi": c[1], "mean_dis": g.x[g.disagree == 1].mean(), "mean_agr": g.x[g.disagree == 0].mean()})
                if col in ("task", "difficulty"):
                    ex = ["ins_sim", "ins_dis"]
                    k = clogit(g, "x", ex, boot=False)
                    cond.append({"by": col, "level": lv, "view": v} | k | within_concordance(g, "x"))
    t = pd.DataFrame(rows)
    t["p_holm_in_view"] = np.nan
    for (by, v), idx in t.groupby(["by", "view"]).groups.items():
        t.loc[idx, "p_holm_in_view"] = multipletests(t.loc[idx, "p"], method="holm")[1]
    save(t, "t17_splits").to_csv(FIG / "fig4_task_slopes.csv", index=False, float_format="%.6g")
    c = pd.DataFrame(cond)
    c["p_holm_in_view"] = np.nan
    for (by, v), idx in c.groupby(["by", "view"]).groups.items():
        c.loc[idx, "p_holm_in_view"] = multipletests(c.loc[idx, "p"].fillna(1), method="holm")[1]
    save(c, "t17_splits_within_question")
    het = []
    for v in ["full", "noans", "ops", "opsnoans"]:
        g = a.assign(x=a[f"c_{v}"]).dropna(subset=["x"])
        res = smf.logit(f"disagree ~ x * C(task) + C(difficulty) + C(insertion)", g).fit(disp=0, maxiter=200, cov_type="cluster", cov_kwds={"groups": g.cl.to_numpy()})
        idx = [i for i, n in enumerate(res.params.index) if n.startswith("x:")]
        w = res.wald_test(np.eye(len(res.params))[idx], scalar=True)
        res2 = smf.logit(f"disagree ~ x * C(insertion) + C(difficulty) + C(task)", g).fit(disp=0, maxiter=200, cov_type="cluster", cov_kwds={"groups": g.cl.to_numpy()})
        idx2 = [i for i, n in enumerate(res2.params.index) if n.startswith("x:")]
        w2 = res2.wald_test(np.eye(len(res2.params))[idx2], scalar=True)
        het.append({"view": v, "task_x_rds_wald": float(w.statistic), "task_df": len(idx), "task_p": float(w.pvalue), "insertion_x_rds_wald": float(w2.statistic), "insertion_df": len(idx2), "insertion_p": float(w2.pvalue)})
    save(pd.DataFrame(het), "t17_interactions")


def insertion_paired(d):
    rows = []
    off = d[d["mode"] == "off"]
    for ins in ["similar_insertion", "dissimilar_insertion"]:
        for col in ["disagree", "disagree_strict"]:
            w = off[off.insertion.isin(["no_insertion", ins])].pivot_table(index="uid", columns="insertion", values=col, observed=True).dropna()
            b, c = int(((w.no_insertion == 1) & (w[ins] == 0)).sum()), int(((w.no_insertion == 0) & (w[ins] == 1)).sum())
            diff = (w[ins] - w.no_insertion).to_numpy()
            rng = np.random.default_rng(SEED)
            boots = diff[rng.integers(0, len(diff), (B, len(diff)))].mean(1)
            rows.append({"contrast": ins, "outcome": col, "questions": len(w), "no_insertion_rate": w.no_insertion.mean(), "insertion_rate": w[ins].mean(), "diff_pp": 100 * diff.mean(), "lo": 100 * np.percentile(boots, 2.5), "hi": 100 * np.percentile(boots, 97.5), "only_no_insertion": b, "only_insertion": c, "mcnemar_p": stats.binomtest(b, b + c, 0.5).pvalue})
    save(pd.DataFrame(rows), "t18_insertion_paired")


def forest(d):
    t = pd.read_csv(TAB / "t7_views_models.csv")
    keep = t[t.model.isin(["primary", "length_adjusted", "off_primary"])][["view", "model", "or_per_sd", "or_sd_lo", "or_sd_hi", "or_per_0.1", "or_lo", "or_hi", "ame_pp_per_sd", "auc_insample", "auc_view_alone"]]
    keep.to_csv(FIG / "fig3_or_by_token_view.csv", index=False, float_format="%.6g")


def corrected_table():
    t = pd.read_csv(TAB / "t7_views_models.csv")
    w = pd.read_csv(TAB / "t8_views_within_question.csv").set_index("view")
    cv = pd.read_csv(TAB / "t10_cv_delta.csv")
    cv = cv[(cv["sample"] == "all") & (cv.baseline == "base")].set_index("view")
    rows = []
    for v in ["full", "noans", "noansval", "ops", "opsnoans", "prefix8ops"]:
        for m in ["primary", "length_adjusted"]:
            r = t[(t.view == v) & (t.model == m)].iloc[0]
            rows.append({"token_view": v, "description": VIEWS[v], "model": m, "n": r.n, "events": r.events, "or_per_sd": r.or_per_sd, "or_per_sd_lo": r.or_sd_lo, "or_per_sd_hi": r.or_sd_hi, "or_per_0.1": r["or_per_0.1"], "or_0.1_lo": r.or_lo, "or_0.1_hi": r.or_hi, "ame_pp_per_0.1_derivative": r["ame_pp_per_0.1"], "ame_pp_per_sd": r.ame_pp_per_sd, "auc_full_model_in_sample": r.auc_insample,
                         "auc_view_alone": r.auc_view_alone, "cv_auc_base": cv.loc[v, "auc_base"], "cv_auc_with_view": cv.loc[v, "auc_with"], "cv_delta_auc": cv.loc[v, "delta_auc"], "cv_delta_lo": cv.loc[v, "lo"], "cv_delta_hi": cv.loc[v, "hi"],
                         "fe_or_per_0.1_off": w.loc[v, "or_per_0.1"], "fe_or_lo": w.loc[v, "or_lo_boot"], "fe_or_hi": w.loc[v, "or_hi_boot"], "within_q_concordance": w.loc[v, "concordance"], "within_q_groups": w.loc[v, "groups"]})
    pd.DataFrame(rows).to_csv(OUT / "corrected_regression_table.csv", index=False, float_format="%.5g")


if __name__ == "__main__":
    data = load()
    reproduce(data)
    cc = views_table(data)
    outcome_contrasts(data)
    cross_val(cc)
    mode_analysis(data)
    exclusions(data)
    length_analysis(data)
    linearity(data)
    splits(data)
    insertion_paired(data)
    forest(data)
    corrected_table()
    json.dump(RES, open(TAB / "scalars.json", "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    print(json.dumps(RES, indent=2, ensure_ascii=False))
