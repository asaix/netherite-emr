import json
import pickle
import random
import re
import subprocess
import sys
import zlib
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import binomtest, chi2_contingency, fisher_exact, ks_2samp
from statsmodels.stats.contingency_tables import StratifiedTable
from statsmodels.stats.multitest import multipletests

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "tools" / "temporal-reasoning-dataset" / "src"))
if not (HERE / "cache" / "rows.pkl").exists():
    subprocess.run([sys.executable, str(HERE / "build_rows.py")], check=True)
import build_rows as BR

FIG = HERE / "fig_data"
FIG.mkdir(exist_ok=True)
B = 2000
LEVELS, TASKS, INS = BR.LEVELS, BR.TASKS, BR.INS
CONDS = ["en_direct", "en_cot", "hi_direct", "hi_cot", "clp", "encot"]
NUM = {}
df = pd.DataFrame(pickle.load(open(HERE / "cache" / "rows.pkl", "rb")))
texts = pickle.load(open(HERE / "cache" / "texts.pkl", "rb"))
feats = pd.DataFrame(pickle.load(open(HERE / "cache" / "feats.pkl", "rb")))
df["c"] = df["correct"].map(lambda x: np.nan if x is None or x != x else float(x))
idx = [(l, t, q) for l in LEVELS for t in TASKS for q in range(150)]
QI = {k: i for i, k in enumerate(idx)}
INSI = {k: i for i, k in enumerate(INS)}
df["qi"] = [QI[k] for k in zip(df["level"], df["task"], df["q"])]
df["ii"] = df["ins"].map(INSI)
LV = np.array([k[0] for k in idx])
TK = np.array([k[1] for k in idx])
QN = np.array([k[2] for k in idx])
FULL = {}
for cond, g in df.groupby("cond"):
    a = np.full((6750, 3), np.nan)
    a[g["qi"].to_numpy(), g["ii"].to_numpy()] = g["c"].to_numpy()
    FULL[cond] = a
SUB = np.where(QN < 50)[0]
Y = {c: FULL[c][SUB] for c in CONDS}
LVS, TKS = LV[SUB], TK[SUB]
Q = len(SUB)
RNG = np.random.default_rng(0)
W = np.stack([np.bincount(RNG.integers(0, Q, Q), minlength=Q) for _ in range(B)]).astype(np.int32)
ALLI = [0, 1, 2]


def mask(level=None, task=None, tasks=None):
    m = np.ones(Q, bool)
    if level is not None:
        m &= LVS == level
    if task is not None:
        m &= TKS == task
    if tasks is not None:
        m &= np.isin(TKS, tasks)
    return m


def strict(a):
    return np.nan_to_num(a, nan=0.0)


def acc(a, m=None, ins=ALLI):
    m = np.ones(len(a), bool) if m is None else m
    return float(np.nanmean(a[m][:, ins])) * 100


def sums(a, m, ins):
    s = a[:, ins]
    return np.nansum(s, 1) * m, (~np.isnan(s)).sum(1) * m


def boot_acc(a, m=None, ins=ALLI, w=None):
    w = W if w is None else w
    m = np.ones(len(a), bool) if m is None else m
    c, n = sums(a, m, ins)
    return 100 * (w @ c) / (w @ n)


def ci(x):
    lo, hi = np.percentile(x, [2.5, 97.5])
    return [round(float(lo), 2), round(float(hi), 2)]


def diff_ci(a, b, m=None, ins=ALLI):
    return round(acc(a, m, ins) - acc(b, m, ins), 2), ci(boot_acc(a, m, ins) - boot_acc(b, m, ins))


def mcn(a, b, m=None, ins=ALLI):
    m = np.ones(len(a), bool) if m is None else m
    x, y = a[m][:, ins].ravel(), b[m][:, ins].ravel()
    ok = ~np.isnan(x) & ~np.isnan(y)
    x, y = x[ok], y[ok]
    p, q = int(((x == 1) & (y == 0)).sum()), int(((x == 0) & (y == 1)).sum())
    return {"pairs": int(ok.sum()), "a_only": p, "b_only": q, "p": float(binomtest(p, p + q, 0.5).pvalue) if p + q else 1.0}


def r1(x):
    return round(float(x), 1)


print("A1")
t = {}
for task in TASKS + ["all"]:
    m = mask(task=None if task == "all" else task)
    row = {c: r1(acc(Y[c], m)) for c in CONDS}
    row.update({c + "_strict": r1(acc(strict(Y[c]), m)) for c in CONDS})
    for ins_name, ii in zip(INS, range(3)):
        row.update({f"{c}_{ins_name[:3]}": r1(acc(Y[c], m, [ii])) for c in CONDS})
    t[task] = row
for a, b in [("clp", "hi_cot"), ("clp", "hi_direct"), ("clp", "en_cot"), ("encot", "clp")]:
    ps = []
    for task in TASKS:
        m = mask(task=task)
        v, c_ = diff_ci(Y[a], Y[b], m)
        mc = mcn(Y[a], Y[b], m)
        t[task][f"{a}-{b}"] = {"diff": v, "ci": c_, **mc}
        ps.append(mc["p"])
    h = multipletests(ps, method="holm")[1]
    for task, p in zip(TASKS, h):
        t[task][f"{a}-{b}"]["p_holm"] = float(p)
    v, c_ = diff_ci(Y[a], Y[b])
    t["all"][f"{a}-{b}"] = {"diff": v, "ci": c_, **mcn(Y[a], Y[b])}
NUM["A1"] = t
pd.DataFrame([{"task": k, **{c: v[c] for c in CONDS}, **{c + "_strict": v[c + "_strict"] for c in CONDS}} for k, v in t.items()]).to_csv(FIG / "table_a1_accuracy_by_task.csv", index=False)

head = {}
for name, ii in [("pooled", ALLI), ("none", [0]), ("time", [1]), ("unrelated", [2])]:
    h = {}
    for a, b in [("clp", "hi_cot"), ("clp", "hi_direct"), ("en_cot", "clp"), ("en_cot", "hi_cot"), ("encot", "clp")]:
        v, c_ = diff_ci(Y[a], Y[b], None, ii)
        vs, cs = diff_ci(strict(Y[a]), strict(Y[b]), None, ii)
        mc = mcn(Y[a], Y[b], None, ii)
        tasks_sig = 0
        ps = [mcn(Y[a], Y[b], mask(task=x), ii)["p"] for x in TASKS]
        hp = multipletests(ps, method="holm")[1]
        pos = [acc(Y[a], mask(task=x), ii) > acc(Y[b], mask(task=x), ii) for x in TASKS]
        h[f"{a}-{b}"] = {"diff": v, "ci": c_, "strict_diff": vs, "strict_ci": cs, **mc, "tasks_positive_and_holm_sig": int(sum(1 for x, y in zip(hp, pos) if x < 0.05 and y)), "tasks_negative_and_holm_sig": int(sum(1 for x, y in zip(hp, pos) if x < 0.05 and not y))}
    h["acc"] = {c: r1(acc(Y[c], None, ii)) for c in CONDS}
    h["acc_strict"] = {c: r1(acc(strict(Y[c]), None, ii)) for c in CONDS}
    head[name] = h
NUM["headline_by_distractor"] = head
rows = []
for name in head:
    for k, v in head[name].items():
        if k.startswith("acc"):
            continue
        rows.append({"distractor": name, "contrast": k, "diff_answered": v["diff"], "lo": v["ci"][0], "hi": v["ci"][1], "diff_strict": v["strict_diff"], "strict_lo": v["strict_ci"][0], "strict_hi": v["strict_ci"][1], "pairs": v["pairs"], "first_only": v["a_only"], "second_only": v["b_only"], "p": v["p"], "tasks_pos_sig": v["tasks_positive_and_holm_sig"], "tasks_neg_sig": v["tasks_negative_and_holm_sig"]})
pd.DataFrame(rows).to_csv(FIG / "new_headline_by_distractor.csv", index=False)
un = {}
for c in CONDS:
    g = df[(df["q"] < 50) & (df["cond"] == c)]
    un[c] = {"unanswered": int((~g["scored"]).sum()), "unanswered_cutoff": int(((~g["scored"]) & g["cutoff"]).sum()), "cutoff_total": int(g["cutoff"].sum()),
             "by_ins": {k: int((~v["scored"]).sum()) for k, v in g.groupby("ins")},
             "lenient_acc": r1(100 * g.loc[g["scored"], "lenient"].astype(float).mean()), "format_only_wrong": int(((g["lenient"] == True) & (g["correct"] == False)).sum())}
NUM["unanswered"] = un

print("A2")
t = {}
for lev in LEVELS:
    m = mask(level=lev)
    row = {c: r1(acc(Y[c], m)) for c in CONDS}
    row["strict"] = {c: r1(acc(strict(Y[c]), m)) for c in CONDS}
    for a, b in [("en_cot", "hi_cot"), ("en_cot", "clp"), ("clp", "hi_cot")]:
        v, c_ = diff_ci(Y[a], Y[b], m)
        row[f"{a}-{b}"] = {"diff": v, "ci": c_}
        row[f"{a}-{b}_strict"] = diff_ci(strict(Y[a]), strict(Y[b]), m)[0]
        for nm, ii in [("none", [0]), ("time", [1]), ("unrelated", [2])]:
            row[f"{a}-{b}_{nm}"] = diff_ci(Y[a], Y[b], m, ii)[0]
    t[lev] = row
NUM["A2"] = t
pd.DataFrame([{"level": k, **{c: v[c] for c in CONDS}, **{f"{c}_lo": ci(boot_acc(Y[c], mask(level=k)))[0] for c in CONDS}, **{f"{c}_hi": ci(boot_acc(Y[c], mask(level=k)))[1] for c in CONDS}} for k, v in t.items()]).to_csv(FIG / "figure_a1_accuracy_by_level.csv", index=False)


def logit(p):
    return np.log(p / (100 - p))


wid = {}
ms, mv = mask(level="short"), mask(level="very_very_long")
for a, b in [("en_cot", "clp"), ("en_cot", "hi_cot"), ("clp", "hi_cot"), ("en_cot", "encot")]:
    for nm, fn in [("answered", lambda z: z), ("strict", strict)]:
        A, Bb = fn(Y[a]), fn(Y[b])
        ga = boot_acc(A, mv) - boot_acc(Bb, mv) - (boot_acc(A, ms) - boot_acc(Bb, ms))
        pt = acc(A, mv) - acc(Bb, mv) - (acc(A, ms) - acc(Bb, ms))
        la = logit(boot_acc(A, mv)) - logit(boot_acc(Bb, mv)) - (logit(boot_acc(A, ms)) - logit(boot_acc(Bb, ms)))
        lp = logit(acc(A, mv)) - logit(acc(Bb, mv)) - (logit(acc(A, ms)) - logit(acc(Bb, ms)))
        wid[f"{a}-{b}_{nm}"] = {"points_change": round(pt, 2), "points_ci": ci(ga), "log_odds_gap_short": round(float(logit(acc(A, ms)) - logit(acc(Bb, ms))), 2), "log_odds_gap_vvl": round(float(logit(acc(A, mv)) - logit(acc(Bb, mv))), 2), "log_odds_change": round(float(lp), 2), "log_odds_ci": ci(la)}
    for nm, ii in [("none", [0]), ("time", [1]), ("unrelated", [2])]:
        ga = boot_acc(Y[a], mv, ii) - boot_acc(Y[b], mv, ii) - (boot_acc(Y[a], ms, ii) - boot_acc(Y[b], ms, ii))
        pt = acc(Y[a], mv, ii) - acc(Y[b], mv, ii) - (acc(Y[a], ms, ii) - acc(Y[b], ms, ii))
        wid[f"{a}-{b}_{nm}"] = {"points_change": round(pt, 2), "points_ci": ci(ga)}
NUM["gap_widening"] = wid
wide_tasks = {}
for task in TASKS:
    m1, m2 = ms & (TKS == task), mv & (TKS == task)
    wide_tasks[task] = {c: [r1(acc(Y[c], m1)), r1(acc(Y[c], m2))] for c in ["en_cot", "clp", "hi_cot", "encot"]}
NUM["level_by_task_short_vs_vvl"] = wide_tasks

print("A3/A4")
clp = df[(df["cond"] == "clp") & (df["q"] < 50)].copy()
for col_ in ["s1_has_date", "s1_cutoff", "s1_ver"]:
    clp[col_] = clp[col_].astype(bool)
for col_ in ["s1_tokens", "s1_chars", "s1_hi_words", "s1_en_words"]:
    clp[col_] = clp[col_].astype(float)
DT =["date_addition", "date_subtraction", "date_recurrence"]
dt = clp[clp["task"].isin(DT) & clp["scored"]].copy()
dt["s2_c"] = dt["correct"].astype(bool)
dt["s1_g"] = dt["s1_gold"].astype(bool)
dt["eq"] = [BR.same_date(l, a) if l is not None and a is not None else False for l, a in zip(dt["s1_last"], dt["parsed"])]
a3 = {"n": len(dt), "has_other_date": r1(100 * clp[clp["task"].isin(DT)]["s1_has_date"].mean()), "has_other_date_answered": r1(100 * dt["s1_has_date"].mean()),
      "s1_gold_n": int(dt["s1_g"].sum()), "s1_other_n": int((~dt["s1_g"]).sum()), "s1_gold_pct": r1(100 * dt["s1_g"].mean()),
      "s2_correct_given_gold": r1(100 * dt[dt["s1_g"]]["s2_c"].mean()), "s2_correct_given_other": r1(100 * dt[~dt["s1_g"]]["s2_c"].mean()), "s2_correct_all": r1(100 * dt["s2_c"].mean()),
      "eq_given_gold": r1(100 * dt[dt["s1_g"]]["eq"].mean()), "eq_given_other": r1(100 * dt[~dt["s1_g"]]["eq"].mean()), "eq_all": r1(100 * dt["eq"].mean()),
      "wrong_s2": int((~dt["s2_c"]).sum()), "wrong_s2_repeat": int(((~dt["s2_c"]) & dt["eq"]).sum()),
      "s1_none_n": int((~dt["s1_has_date"]).sum()), "s2_correct_given_none": r1(100 * dt[~dt["s1_has_date"]]["s2_c"].mean()),
      "s2_correct_given_other_date_only": r1(100 * dt[(~dt["s1_g"]) & dt["s1_has_date"]]["s2_c"].mean()),
      "s1_any_gold_not_last": int((dt["s1_any_gold"].astype(bool) & ~dt["s1_g"]).sum()),
      "s2_correct_any_gold_not_last": r1(100 * dt[dt["s1_any_gold"].astype(bool) & ~dt["s1_g"]]["s2_c"].mean()),
      "by_task": {x: {"n": int((dt["task"] == x).sum()), "s1_gold": r1(100 * dt[dt["task"] == x]["s1_g"].mean()), "s2_correct": r1(100 * dt[dt["task"] == x]["s2_c"].mean()),
                      "s2_given_gold": r1(100 * dt[(dt["task"] == x) & dt["s1_g"]]["s2_c"].mean()), "s2_given_other": r1(100 * dt[(dt["task"] == x) & ~dt["s1_g"]]["s2_c"].mean()),
                      "eq_given_other": r1(100 * dt[(dt["task"] == x) & ~dt["s1_g"]]["eq"].mean())} for x in DT},
      "by_ins": {x: {"n": int((dt["ins"] == x).sum()), "s1_gold": r1(100 * dt[dt["ins"] == x]["s1_g"].mean()), "s2_correct": r1(100 * dt[dt["ins"] == x]["s2_c"].mean()),
                     "s2_given_gold": r1(100 * dt[(dt["ins"] == x) & dt["s1_g"]]["s2_c"].mean()), "s2_given_other": r1(100 * dt[(dt["ins"] == x) & ~dt["s1_g"]]["s2_c"].mean()),
                     "eq_all": r1(100 * dt[dt["ins"] == x]["eq"].mean())} for x in INS},
      "tri_task_acc": {c: r1(acc(Y[c], mask(tasks=DT))) for c in CONDS}, "tri_task_acc_strict": {c: r1(acc(strict(Y[c]), mask(tasks=DT))) for c in CONDS}}
NUM["A3"] = a3
dt[["level", "task", "q", "ins", "s1_g", "s2_c", "eq"]].to_csv(FIG / "table_a3_stage1_stage2.csv", index=False)


def mh(frame, exposure, outcome, by=("task", "level")):
    tabs = []
    for _, g in frame.groupby(list(by)):
        e, y = g[exposure].astype(bool), g[outcome].astype(bool)
        tb = np.array([[(e & y).sum(), (e & ~y).sum()], [(~e & y).sum(), (~e & ~y).sum()]], float)
        if tb[0].sum() and tb[1].sum():
            tabs.append(tb)
    if not tabs:
        return {"or": None, "ci": [None, None], "strata": 0}
    st = StratifiedTable(tabs)
    lo, hi = st.oddsratio_pooled_confint()
    return {"or": round(float(st.oddsratio_pooled), 2), "ci": [round(float(lo), 2), round(float(hi), 2)], "p": float(st.test_null_odds().pvalue), "strata": len(tabs)}


ctl = {}
ctl["raw_rd"] = round(100 * (dt[dt["s1_g"]]["s2_c"].mean() - dt[~dt["s1_g"]]["s2_c"].mean()), 1)
ctl["mh_task_level"] = mh(dt, "s1_g", "s2_c")
cells = dt.groupby(["task", "level"])
rd, wt = [], []
for _, g in cells:
    a, b = g[g["s1_g"]]["s2_c"], g[~g["s1_g"]]["s2_c"]
    if len(a) and len(b):
        n = len(a) * len(b) / (len(a) + len(b))
        rd.append(a.mean() - b.mean())
        wt.append(n)
ctl["mh_risk_difference_task_level"] = round(100 * float(np.average(rd, weights=wt)), 1)
for bench, name in [("encot", "encot_benchmark"), ("hi_cot", "hi_cot_benchmark"), ("en_cot", "en_cot_benchmark")]:
    other = df[(df["cond"] == bench) & (df["q"] < 50) & df["scored"]][["level", "task", "q", "ins", "correct"]].rename(columns={"correct": "bench"})
    m = dt.merge(other, on=["level", "task", "q", "ins"])
    m["bench"] = m["bench"].astype(bool)
    rd, wt = [], []
    for _, g in m.groupby(["task", "level"]):
        a, b = g[g["s1_g"]]["bench"], g[~g["s1_g"]]["bench"]
        if len(a) and len(b):
            rd.append(a.mean() - b.mean())
            wt.append(len(a) * len(b) / (len(a) + len(b)))
    ctl[name] = {"n": len(m), "bench_acc_given_s1_gold": r1(100 * m[m["s1_g"]]["bench"].mean()), "bench_acc_given_s1_other": r1(100 * m[~m["s1_g"]]["bench"].mean()),
                 "raw_rd": round(100 * (m[m["s1_g"]]["bench"].mean() - m[~m["s1_g"]]["bench"].mean()), 1),
                 "mh": mh(m, "s1_g", "bench"), "mh_rd": round(100 * float(np.average(rd, weights=wt)), 1), "s2_given_s1_gold_same_rows": r1(100 * m[m["s1_g"]]["s2_c"].mean()), "s2_given_s1_other_same_rows": r1(100 * m[~m["s1_g"]]["s2_c"].mean())}
    if bench == "encot":
        by = {}
        for x in DT:
            g = m[m["task"] == x]
            by[x] = {"encot_given_gold": r1(100 * g[g["s1_g"]]["bench"].mean()), "encot_given_other": r1(100 * g[~g["s1_g"]]["bench"].mean()), "clp_given_gold": r1(100 * g[g["s1_g"]]["s2_c"].mean()), "clp_given_other": r1(100 * g[~g["s1_g"]]["s2_c"].mean()), "n_gold": int(g["s1_g"].sum()), "n_other": int((~g["s1_g"]).sum())}
        ctl["encot_by_task"] = by
dq = dt.copy()
dq["qk"] = dq["level"] + "/" + dq["task"] + "/" + dq["q"].astype(str)
g = dq.groupby("qk")
dq["s1w"] = dq["s1_g"].astype(float) - g["s1_g"].transform(lambda x: x.astype(float).mean())
dq["s2w"] = dq["s2_c"].astype(float) - g["s2_c"].transform(lambda x: x.astype(float).mean())
fe = float((dq["s1w"] * dq["s2w"]).sum() / (dq["s1w"] ** 2).sum()) * 100
qk = dq["qk"].unique()
qmap = {k: i for i, k in enumerate(qk)}
dq["qid"] = dq["qk"].map(qmap)
sxy = np.bincount(dq["qid"], weights=dq["s1w"] * dq["s2w"], minlength=len(qk))
sxx = np.bincount(dq["qid"], weights=dq["s1w"] ** 2, minlength=len(qk))
rw = np.random.default_rng(1)
bs = []
for _ in range(B):
    w_ = np.bincount(rw.integers(0, len(qk), len(qk)), minlength=len(qk))
    bs.append(100 * (w_ @ sxy) / (w_ @ sxx))
disc = dq.groupby("qk").filter(lambda x: x["s1_g"].nunique() > 1)
ctl["within_question_fe"] = {"beta_points": round(fe, 1), "ci": ci(np.array(bs)), "questions_with_varying_s1": int(disc["qk"].nunique()), "responses": len(disc),
                             "s2_given_gold_within": r1(100 * disc[disc["s1_g"]]["s2_c"].mean()), "s2_given_other_within": r1(100 * disc[~disc["s1_g"]]["s2_c"].mean())}
other = df[(df["cond"] == "encot") & (df["q"] < 50) & df["scored"]][["level", "task", "q", "ins", "correct"]].rename(columns={"correct": "bench"})
dq2 = disc.merge(other, on=["level", "task", "q", "ins"])
ctl["within_question_encot_negative_control"] = {"n": len(dq2), "encot_given_gold_within": r1(100 * dq2[dq2["s1_g"]]["bench"].astype(float).mean()), "encot_given_other_within": r1(100 * dq2[~dq2["s1_g"]]["bench"].astype(float).mean())}
NUM["A3_controlled"] = ctl

g = clp.copy()
g["all_tokens"] = g["s1_tokens"] + g["tokens"]
sc = df[(df["q"] < 50) & df["scored"]]
a4 = {"median_tokens_clp_two_stages": float(g["all_tokens"].median()), "median_s1": float(g["s1_tokens"].median()), "median_s2": float(g["tokens"].median()),
      "median_scored_clp_two": float(g[g["scored"]]["all_tokens"].median()), "median_hi_cot": float(df[(df["q"] < 50) & (df["cond"] == "hi_cot")]["tokens"].median()), "median_en_cot": float(df[(df["q"] < 50) & (df["cond"] == "en_cot")]["tokens"].median()), "median_encot": float(df[(df["q"] < 50) & (df["cond"] == "encot")]["tokens"].median()),
      "median_hi_cot_scored": float(sc[sc["cond"] == "hi_cot"]["tokens"].median()), "median_en_cot_scored": float(sc[sc["cond"] == "en_cot"]["tokens"].median()), "median_encot_scored": float(sc[sc["cond"] == "encot"]["tokens"].median()),
      "ver_s1": r1(100 * g["s1_ver"].mean()), "ver_s2": r1(100 * g["ver"].mean()), "ver_s1_scored": r1(100 * g[g["scored"]]["s1_ver"].mean()), "ver_s2_scored": r1(100 * g[g["scored"]]["ver"].mean()),
      "ver_hi_cot": r1(100 * sc[sc["cond"] == "hi_cot"]["ver"].mean()), "ver_en_cot": r1(100 * sc[sc["cond"] == "en_cot"]["ver"].mean()), "ver_encot": r1(100 * sc[sc["cond"] == "encot"]["ver"].mean()),
      "en_share_s1_mean": round(float((g["s1_en_words"] / (g["s1_en_words"] + g["s1_hi_words"]).replace(0, np.nan)).mean()), 3), "en_share_s1_pooled": round(float(g["s1_en_words"].sum() / (g["s1_en_words"] + g["s1_hi_words"]).sum()), 3),
      "en_share_s2_mean": round(float((g["en_words"] / (g["en_words"] + g["hi_words"]).replace(0, np.nan)).mean()), 3), "en_share_s2_pooled": round(float(g["en_words"].sum() / (g["en_words"] + g["hi_words"]).sum()), 3),
      "s1_cutoff": int(g["s1_cutoff"].sum()), "s2_cutoff": int(g["cutoff"].sum()), "s1_label_answer_share": r1(100 * g["s1_label_answer"].notna().mean())}
NUM["A4"] = a4

print("A4 table")
drop = {}
for c in CONDS:
    v = {"none": r1(acc(Y[c], None, [0])), "time": r1(acc(Y[c], None, [1])), "unrelated": r1(acc(Y[c], None, [2]))}
    for nm, ii in [("time", 1), ("unrelated", 2)]:
        pt = acc(Y[c], None, [0]) - acc(Y[c], None, [ii])
        v[f"drop_{nm}"] = round(pt, 2)
        v[f"drop_{nm}_ci"] = ci(boot_acc(Y[c], None, [0]) - boot_acc(Y[c], None, [ii]))
        x, y = Y[c][:, 0], Y[c][:, ii]
        ok = ~np.isnan(x) & ~np.isnan(y)
        p, q_ = int(((x == 1) & (y == 0))[ok].sum()), int(((x == 0) & (y == 1))[ok].sum())
        v[f"mcnemar_{nm}"] = {"none_only": p, "with_only": q_, "p": float(binomtest(p, p + q_, 0.5).pvalue)}
        pts = acc(strict(Y[c]), None, [0]) - acc(strict(Y[c]), None, [ii])
        v[f"drop_{nm}_strict"] = round(pts, 2)
        v[f"drop_{nm}_strict_ci"] = ci(boot_acc(strict(Y[c]), None, [0]) - boot_acc(strict(Y[c]), None, [ii]))
    drop[c] = v
keys = [(c, nm) for c in ["en_direct", "en_cot", "hi_direct", "hi_cot", "clp"] for nm in ("time", "unrelated")]
hp = multipletests([drop[c][f"mcnemar_{nm}"]["p"] for c, nm in keys], method="holm")[1]
for (c, nm), p in zip(keys, hp):
    drop[c][f"holm10_{nm}"] = float(p)
for c in ["hi_cot", "clp"]:
    for nm, ii in [("time", 1), ("unrelated", 2)]:
        pen = (acc(Y[c], None, [0]) - acc(Y[c], None, [ii])) - (acc(Y["hi_direct"], None, [0]) - acc(Y["hi_direct"], None, [ii]))
        bp = (boot_acc(Y[c], None, [0]) - boot_acc(Y[c], None, [ii])) - (boot_acc(Y["hi_direct"], None, [0]) - boot_acc(Y["hi_direct"], None, [ii]))
        drop[c][f"penalty_{nm}"] = {"value": round(pen, 2), "ci": ci(bp)}
pen = (acc(Y["en_cot"], None, [0]) - acc(Y["en_cot"], None, [1])) - (acc(Y["en_direct"], None, [0]) - acc(Y["en_direct"], None, [1]))
bp = (boot_acc(Y["en_cot"], None, [0]) - boot_acc(Y["en_cot"], None, [1])) - (boot_acc(Y["en_direct"], None, [0]) - boot_acc(Y["en_direct"], None, [1]))
drop["en_cot"]["penalty_time"] = {"value": round(pen, 2), "ci": ci(bp)}
NUM["A4_table"] = drop
pd.DataFrame([{"cond": c, "none": v["none"], "time": v["time"], "unrelated": v["unrelated"], "drop_time": v["drop_time"], "drop_time_lo": v["drop_time_ci"][0], "drop_time_hi": v["drop_time_ci"][1], "drop_unrelated": v["drop_unrelated"], "drop_unrelated_lo": v["drop_unrelated_ci"][0], "drop_unrelated_hi": v["drop_unrelated_ci"][1]} for c, v in drop.items()]).to_csv(FIG / "table_a4_drops.csv", index=False)

print("unrelated gain")
gain = {"by_task": {}, "by_level": {}, "by_sentence": []}
for name, rows_ in [("by_task", TASKS), ("by_level", LEVELS)]:
    ps = []
    for x in rows_:
        m = mask(task=x) if name == "by_task" else mask(level=x)
        v = {"none": r1(acc(Y["clp"], m, [0])), "unrelated": r1(acc(Y["clp"], m, [2])), "time": r1(acc(Y["clp"], m, [1]))}
        v["gain"] = round(acc(Y["clp"], m, [2]) - acc(Y["clp"], m, [0]), 2)
        v["ci"] = ci(boot_acc(Y["clp"], m, [2]) - boot_acc(Y["clp"], m, [0]))
        a_, b_ = Y["clp"][m, 0], Y["clp"][m, 2]
        ok = ~np.isnan(a_) & ~np.isnan(b_)
        p1, p2 = int(((a_ == 0) & (b_ == 1))[ok].sum()), int(((a_ == 1) & (b_ == 0))[ok].sum())
        v["wrong_to_right"], v["right_to_wrong"], v["p"] = p1, p2, float(binomtest(p1, p1 + p2, 0.5).pvalue)
        for c in ["hi_cot", "encot", "en_cot", "hi_direct"]:
            v[f"gain_{c}"] = round(acc(Y[c], m, [2]) - acc(Y[c], m, [0]), 2)
        gain[name][x] = v
        ps.append(v["p"])
    hp = multipletests(ps, method="holm")[1]
    for x, p in zip(rows_, hp):
        gain[name][x]["p_holm"] = float(p)
pd.DataFrame([{"task": k, **{a: b for a, b in v.items() if a != "ci"}, "lo": v["ci"][0], "hi": v["ci"][1]} for k, v in gain["by_task"].items()]).to_csv(FIG / "new_unrelated_gain_by_task.csv", index=False)
fs = feats[feats["q"] < 50].copy()
fs["qi_s"] = [np.where(SUB == QI[(l, t, q)])[0][0] for l, t, q in zip(fs["level"], fs["task"], fs["q"])]
sent = fs.set_index("qi_s")["hi_dis"].reindex(range(Q)).to_numpy()
sent_sim = fs.set_index("qi_s")["hi_sim"].reindex(range(Q)).to_numpy()
keys = sorted({(t, s) for t, s in zip(TKS, sent)})
ps = []
for t_, s_ in keys:
    m = (TKS == t_) & (sent == s_)
    a_, b_ = Y["clp"][m, 0], Y["clp"][m, 2]
    ok = ~np.isnan(a_) & ~np.isnan(b_)
    p1, p2 = int(((a_ == 0) & (b_ == 1))[ok].sum()), int(((a_ == 1) & (b_ == 0))[ok].sum())
    rec = {"task": t_, "sentence": s_, "questions": int(m.sum()), "none": r1(acc(Y["clp"], m, [0])), "unrelated": r1(acc(Y["clp"], m, [2])), "gain": round(acc(Y["clp"], m, [2]) - acc(Y["clp"], m, [0]), 1), "wrong_to_right": p1, "right_to_wrong": p2, "p": float(binomtest(p1, p1 + p2, 0.5).pvalue) if p1 + p2 else 1.0,
           "gain_encot": round(acc(Y["encot"], m, [2]) - acc(Y["encot"], m, [0]), 1), "gain_hi_cot": round(acc(Y["hi_cot"], m, [2]) - acc(Y["hi_cot"], m, [0]), 1)}
    gain["by_sentence"].append(rec)
    ps.append(rec["p"])
hp = multipletests(ps, method="holm")[1]
for r_, p in zip(gain["by_sentence"], hp):
    r_["p_holm"] = float(p)
gain["by_sentence"].sort(key=lambda x: x["p"])
pd.DataFrame(gain["by_sentence"]).to_csv(FIG / "new_unrelated_gain_by_sentence.csv", index=False)
gain["sentences_nominal_p05"] = int(sum(1 for r_ in gain["by_sentence"] if r_["p"] < 0.05))
gain["sentences_holm_p05"] = int(sum(1 for r_ in gain["by_sentence"] if r_["p_holm"] < 0.05))
gain["sentences_positive"] = int(sum(1 for r_ in gain["by_sentence"] if r_["gain"] > 0))
gain["sentences_negative"] = int(sum(1 for r_ in gain["by_sentence"] if r_["gain"] < 0))
gain["sentences_total"] = len(keys)
gain["sign_test_p"] = float(binomtest(gain["sentences_positive"], gain["sentences_positive"] + gain["sentences_negative"], 0.5).pvalue)
keyid = {k: i for i, k in enumerate(keys)}
cl = np.array([keyid[k] for k in zip(TKS, sent)])
d_ = Y["clp"][:, 2] - Y["clp"][:, 0]
ok = ~np.isnan(d_)
num = np.bincount(cl[ok], weights=d_[ok], minlength=len(keys))
den = np.bincount(cl[ok], minlength=len(keys))
rw = np.random.default_rng(2)
bs = []
for _ in range(5000):
    s = rw.integers(0, len(keys), len(keys))
    bs.append(100 * num[s].sum() / den[s].sum())
gain["sentence_cluster_boot"] = {"paired_gain": round(100 * num.sum() / den.sum(), 2), "ci": ci(np.array(bs)), "clusters": len(keys)}
perm = []
ds = d_[ok]
for _ in range(5000):
    sg = rw.choice([-1, 1], size=len(keys))
    perm.append((sg[cl[ok]] * ds).sum() / len(ds) * 100)
perm = np.array(perm)
gain["sentence_sign_flip_p"] = float(np.mean(np.abs(perm) >= abs(100 * ds.mean())))
loo = {t_: round(float(acc(Y["clp"], TKS != t_, [2]) - acc(Y["clp"], TKS != t_, [0])), 2) for t_ in TASKS}
gain["leave_one_task_out"] = loo
loo_ci = {t_: ci(boot_acc(Y["clp"], TKS != t_, [2]) - boot_acc(Y["clp"], TKS != t_, [0])) for t_ in TASKS}
gain["leave_one_task_out_ci"] = loo_ci
mech = {}
for col in ["s1_tokens", "tokens", "s1_chars"]:
    mech[col] = {i: float(clp[clp["ins"] == i][col].median()) for i in INS}
    mech[col + "_mean"] = {i: r1(clp[clp["ins"] == i][col].mean()) for i in INS}
for col in ["s1_has_date", "s1_gold", "s1_any_gold"]:
    mech[col] = {i: r1(100 * clp[(clp["ins"] == i) & clp["task"].isin(DT)][col].astype(float).mean()) for i in INS}
for col in ["ver", "s1_ver"]:
    mech[col] = {i: r1(100 * clp[clp["ins"] == i][col].mean()) for i in INS}
mech["s1_gold_by_task"] = {x: {i: r1(100 * clp[(clp["ins"] == i) & (clp["task"] == x)]["s1_gold"].astype(float).mean()) for i in INS} for x in DT}
mech["s2_given_s1_gold"] = {i: r1(100 * dt[(dt["ins"] == i) & dt["s1_g"]]["s2_c"].mean()) for i in INS}
mech["s2_given_s1_other"] = {i: r1(100 * dt[(dt["ins"] == i) & ~dt["s1_g"]]["s2_c"].mean()) for i in INS}
gain["mechanism"] = mech
hg = {}
for level in LEVELS:
    for rec in json.load(open(ROOT / "responses" / "hinglish" / f"{level}.json", encoding="utf-8")):
        m_ = rec["meta"]
        a_, _ = BR.answer(rec["content"])
        hg.setdefault(m_["insertion"], []).append(np.nan if a_ is None else float(BR.correct(a_, m_["answer"], m_["task"])))
gain["hinglish_acc_by_ins"] = {k: r1(100 * np.nanmean(v)) for k, v in hg.items()}
gain["hinglish_n"] = {k: len(v) for k, v in hg.items()}
del hg
NUM["unrelated_gain"] = gain

print("mention")
qmeta = feats.set_index(["level", "task", "q"])
ment = {}


def mflag(frame, kind, prefix, langs):
    cols = [frame[f"{prefix}m_{kind}_{l}"] for l in langs]
    known = pd.concat([c.notna() for c in cols], axis=1).any(axis=1)
    val = pd.concat([c.map(lambda x: x is True or x == 1) for c in cols], axis=1).any(axis=1)
    return val.where(known, other=np.nan)


RULES = {"en_cot": ["en"], "hi_cot": ["hi"], "clp": ["en", "hi"], "encot": ["en", "hi"]}
wordrows = []
for label, c, prefix in [("en_cot", "en_cot", ""), ("hi_cot", "hi_cot", ""), ("clp_s1", "clp", "s1"), ("clp_s2", "clp", ""), ("encot", "encot", "")]:
    g = df[(df["q"] < 50) & (df["cond"] == c) & df["scored"]]
    rec = {}
    for kind, insn in [("sim", "similar_insertion"), ("dis", "dissimilar_insertion")]:
        for rname, langs in [("doc", RULES[c]), ("en_only", ["en"]), ("hi_only", ["hi"]), ("both", ["en", "hi"])]:
            f = mflag(g, kind, prefix, langs)
            ins_mask, plc_mask = (g["ins"] == insn) & f.notna(), (g["ins"] == "no_insertion") & f.notna()
            rate, plc = 100 * f[ins_mask].astype(float).mean(), 100 * f[plc_mask].astype(float).mean()
            a_ = g[ins_mask].assign(flag=f[ins_mask].astype(float))[["qi", "flag"]].set_index("qi")["flag"]
            b_ = g[plc_mask].assign(flag=f[plc_mask].astype(float))[["qi", "flag"]].set_index("qi")["flag"]
            j = pd.concat([a_, b_], axis=1, keys=["a", "b"]).dropna()
            ids = np.searchsorted(SUB, j.index.to_numpy())
            pd_w = np.stack([(W[:300, :] [:, ids] * (j["a"] - j["b"]).to_numpy()).sum(1) / W[:300, :][:, ids].sum(1) for _ in [0]])[0] * 100
            res = {"n": int(ins_mask.sum()), "rate": r1(rate), "placebo": r1(plc), "net": round(rate - plc, 1), "net_paired": round(100 * float((j["a"] - j["b"]).mean()), 1), "net_paired_ci": ci(pd_w), "excess_adjusted": round(100 * (rate - plc) / (100 - plc), 1)}
            if rname == "doc":
                sub_ = g[ins_mask].assign(flag=f[ins_mask].astype(float) > 0)
                sub_["y"] = sub_["correct"].astype(bool)
                res["or"] = mh(sub_, "flag", "y")
                res["acc_mention"] = r1(100 * sub_[sub_["flag"]]["y"].mean())
                res["acc_no_mention"] = r1(100 * sub_[~sub_["flag"]]["y"].mean())
                res["by_task"] = {x: {"rate": r1(100 * f[ins_mask & (g["task"] == x)].astype(float).mean()), "placebo": r1(100 * f[plc_mask & (g["task"] == x)].astype(float).mean())} for x in TASKS}
                res["by_level"] = {x: {"rate": r1(100 * f[ins_mask & (g["level"] == x)].astype(float).mean()), "placebo": r1(100 * f[plc_mask & (g["level"] == x)].astype(float).mean())} for x in LEVELS}
            rec[f"{kind}_{rname}"] = res
        cnt_i, cnt_p = Counter(), Counter()
        for l in RULES[c]:
            for w_s, i_ in zip(g[f"{prefix}w_{kind}_{l}"], g["ins"]):
                if isinstance(w_s, str) and w_s:
                    (cnt_p if i_ == "no_insertion" else cnt_i).update(w_s.split("|"))
        for w_, n_ in cnt_p.most_common(15):
            wordrows.append({"reasoning": label, "kind": kind, "arm": "placebo", "word": w_, "responses": n_})
        for w_, n_ in cnt_i.most_common(15):
            wordrows.append({"reasoning": label, "kind": kind, "arm": "inserted", "word": w_, "responses": n_})
    ment[label] = rec
NUM["mention"] = ment
pd.DataFrame(wordrows).to_csv(FIG / "new_mention_top_words.csv", index=False)
pd.DataFrame([{"reasoning": k, "kind": kk.split("_")[0], "rule": "_".join(kk.split("_")[1:]), **{a: b for a, b in v.items() if a in ("n", "rate", "placebo", "net", "net_paired", "excess_adjusted")}} for k, r_ in ment.items() for kk, v in r_.items()]).to_csv(FIG / "table_a5_mentions_by_rule.csv", index=False)

specific = {}
for label, c, prefix in [("en_cot", "en_cot", ""), ("hi_cot", "hi_cot", ""), ("clp_s1", "clp", "s1"), ("clp_s2", "clp", ""), ("encot", "encot", "")]:
    g = df[(df["q"] < 50) & (df["cond"] == c) & df["scored"]]
    res = {}
    for kind, insn in [("sim", "similar_insertion"), ("dis", "dissimilar_insertion")]:
        chance = Counter()
        for l in RULES[c]:
            for w_s, i_ in zip(g[f"{prefix}w_{kind}_{l}"], g["ins"]):
                if i_ == "no_insertion" and isinstance(w_s, str) and w_s:
                    chance.update(w_s.split("|"))
        banned = {w_ for w_, n_ in chance.items() if n_ >= 1}
        hit, n = 0, 0
        hit_p, n_p = 0, 0
        for i_, *ws in zip(g["ins"], *[g[f"{prefix}w_{kind}_{l}"] for l in RULES[c]]):
            if i_ not in (insn, "no_insertion"):
                continue
            known = [x for x in ws if isinstance(x, str)]
            if not known and all(x is None or x != x for x in ws):
                continue
            words_hit = {w_ for x in known if x for w_ in x.split("|")} - banned
            if i_ == insn:
                n += 1
                hit += bool(words_hit)
        res[kind] = {"rate_excluding_any_word_seen_in_placebo": r1(100 * hit / n), "banned_words": len(banned), "n": n}
    specific[label] = res
NUM["mention_specific"] = specific

print("reuse")


def features(text):
    text = BR.norm(text).casefold()
    tok = BR.TOK.findall(text)
    nums = {int(x) for x in re.findall(r"\d+", text)} | {7 for t_ in tok if t_ in ("seven", "सात")}
    return {"num": nums, "hour": nums | {x + 12 for x in nums if x < 12}, "mon": {BR.MONTH[t_] for t_ in tok if t_ in BR.MONTH}, "wd": {BR.WEEKDAY[t_] for t_ in tok if t_ in BR.WEEKDAY}}


def comps(kind, v):
    if kind == "date":
        return [("num", v.year), ("mon", v.month), ("num", v.day)]
    if kind == "iv":
        return comps("date", v[0]) + comps("date", v[1])
    if kind == "t":
        return [("hour", v // 60), ("num", v % 60)]
    if kind == "wd":
        return [("wd", v)]
    return [("num", v)]


fq = {(r_.level, r_.task, r_.q): r_ for r_ in feats[feats["q"] < 50].itertuples()}
reuse = {}
for c, l in [("en_direct", "en"), ("en_cot", "en"), ("hi_direct", "hi"), ("hi_cot", "hi"), ("clp", "hi"), ("clp_both", "both"), ("encot", "hi")]:
    cc = "clp" if c == "clp_both" else c
    g = df[(df["q"] < 50) & (df["cond"] == cc) & (df["correct"] == False)]
    cnt = {"similar_insertion": [0, 0], "no_insertion": [0, 0], "dissimilar_insertion": [0, 0]}
    cnt2 = {"dissimilar_insertion": [0, 0], "no_insertion": [0, 0]}
    for r_ in g.itertuples():
        if r_.parsed is None or (isinstance(r_.parsed, float) and np.isnan(r_.parsed)):
            continue
        qr = fq[(r_.level, r_.task, r_.q)]
        kind = BR.KIND[r_.task]
        for dname, target, store in [("sim", ("similar_insertion", "no_insertion"), cnt), ("dis", ("dissimilar_insertion", "no_insertion"), cnt2)]:
            if r_.ins not in target:
                continue
            txt = getattr(qr, f"hi_{dname}") if l == "hi" else getattr(qr, f"en_{dname}") if l == "en" else getattr(qr, f"hi_{dname}") + " " + getattr(qr, f"en_{dname}")
            fea = features(txt)
            if not any(fea.values()):
                continue
            store[r_.ins][1] += 1
            hit = any(a_ != b_ and a_ in fea[n_] for (n_, a_), (_, b_) in zip(comps(kind, r_.parsed), comps(kind, r_.gold)))
            store[r_.ins][0] += hit
    a_, n1 = cnt["similar_insertion"]
    b_, n2 = cnt["no_insertion"]
    reuse[c] = {"inserted": a_, "inserted_n": n1, "rate": r1(100 * a_ / n1), "placebo": b_, "placebo_n": n2, "placebo_rate": r1(100 * b_ / n2), "fisher_p": float(fisher_exact([[a_, n1 - a_], [b_, n2 - b_]])[1])}
    a_, n1 = cnt2["dissimilar_insertion"]
    b_, n2 = cnt2["no_insertion"]
    reuse[c]["dissimilar"] = {"inserted": a_, "inserted_n": n1, "rate": r1(100 * a_ / n1) if n1 else None, "placebo": b_, "placebo_n": n2, "placebo_rate": r1(100 * b_ / n2) if n2 else None, "fisher_p": float(fisher_exact([[a_, n1 - a_], [b_, n2 - b_]])[1]) if n1 and n2 else None}
NUM["reuse"] = reuse

print("phi")


def phi_cells(a, b, ii=ALLI):
    out = []
    cells_ = 0
    for lev in LEVELS:
        for task in TASKS:
            m = mask(level=lev, task=task)
            x, y = a[m][:, ii].ravel(), b[m][:, ii].ravel()
            ok = ~np.isnan(x) & ~np.isnan(y)
            x, y = x[ok], y[ok]
            px, py = x.mean(), y.mean()
            den = np.sqrt(px * (1 - px) * py * (1 - py))
            r_ = {"level": lev, "task": task, "n": len(x), "px": float(px), "py": float(py), "phi": float(((x * y).mean() - px * py) / den) if den else np.nan}
            if den:
                pmax = min(px, py)
                r_["phi_max"] = float((pmax - px * py) / den)
                r_["phi_over_max"] = r_["phi"] / r_["phi_max"] if r_["phi_max"] else np.nan
            out.append(r_)
    return pd.DataFrame(out)


def pooled(a, b, ii=ALLI):
    tabs, exp_ww, obs_ww, num, dx, dy = [], 0.0, 0, 0.0, 0.0, 0.0
    bs_cells = []
    for lev in LEVELS:
        for task in TASKS:
            m = mask(level=lev, task=task)
            x, y = a[m][:, ii].ravel(), b[m][:, ii].ravel()
            ok = ~np.isnan(x) & ~np.isnan(y)
            x, y = x[ok], y[ok]
            tb = np.array([[((x == 1) & (y == 1)).sum(), ((x == 1) & (y == 0)).sum()], [((x == 0) & (y == 1)).sum(), ((x == 0) & (y == 0)).sum()]], float)
            if tb[0].sum() and tb[1].sum():
                tabs.append(tb)
            obs_ww += tb[1, 1]
            exp_ww += tb[1].sum() * tb[:, 1].sum() / tb.sum()
            num += ((x - x.mean()) * (y - y.mean())).sum()
            dx += ((x - x.mean()) ** 2).sum()
            dy += ((y - y.mean()) ** 2).sum()
    st = StratifiedTable(tabs)
    return {"mh_or": float(st.oddsratio_pooled), "both_wrong_obs": int(obs_ww), "both_wrong_exp": float(exp_ww), "ratio": float(obs_ww / exp_ww), "within_cell_r": float(num / np.sqrt(dx * dy)), "strata": len(tabs)}


def pooled_boot(a, b, ii=ALLI, n=400, seed=3):
    rw = np.random.default_rng(seed)
    out = []
    for _ in range(n):
        s = []
        for lev in LEVELS:
            for task in TASKS:
                ids = np.where((LVS == lev) & (TKS == task))[0]
                s.append(rw.choice(ids, len(ids)))
        s = np.concatenate(s)
        ao, bo = a[s], b[s]
        tabs, obs, exp_, num, dx, dy = [], 0.0, 0.0, 0.0, 0.0, 0.0
        for c_ in range(45):
            sl = slice(c_ * 50, (c_ + 1) * 50)
            x, y = ao[sl][:, ii].ravel(), bo[sl][:, ii].ravel()
            ok = ~np.isnan(x) & ~np.isnan(y)
            x, y = x[ok], y[ok]
            tb = np.array([[((x == 1) & (y == 1)).sum(), ((x == 1) & (y == 0)).sum()], [((x == 0) & (y == 1)).sum(), ((x == 0) & (y == 0)).sum()]], float)
            if tb[0].sum() and tb[1].sum():
                tabs.append(tb)
            obs += tb[1, 1]
            exp_ += tb[1].sum() * tb[:, 1].sum() / tb.sum()
            num += ((x - x.mean()) * (y - y.mean())).sum()
            dx += ((x - x.mean()) ** 2).sum()
            dy += ((y - y.mean()) ** 2).sum()
        R_ = sum(t_[0, 0] * t_[1, 1] / t_.sum() for t_ in tabs)
        S_ = sum(t_[0, 1] * t_[1, 0] / t_.sum() for t_ in tabs)
        out.append((R_ / S_, obs / exp_, num / np.sqrt(dx * dy)))
    out = np.array(out)
    return {"mh_or_ci": ci(out[:, 0]), "ratio_ci": ci(out[:, 1]), "within_cell_r_ci": ci(out[:, 2])}


PAIRS = [("hi_direct|en_direct", "hi_direct", "en_direct"), ("hi_cot|en_cot", "hi_cot", "en_cot"), ("clp|en_cot", "clp", "en_cot"), ("encot|en_cot", "encot", "en_cot"), ("clp|hi_cot", "clp", "hi_cot"), ("clp|encot", "clp", "encot"), ("hi_cot|hi_direct", "hi_cot", "hi_direct"), ("clp|hi_direct", "clp", "hi_direct")]
agree = {}
for name, a_, b_ in PAIRS:
    x, y = Y[a_].ravel(), Y[b_].ravel()
    ok = ~np.isnan(x) & ~np.isnan(y)
    pc = phi_cells(Y[a_], Y[b_])
    rec = {"pairs": int(ok.sum()), "both_right": int(((x == 1) & (y == 1)).sum()), "both_wrong": int(((x == 0) & (y == 0)).sum()), "only_a_right": int(((x == 1) & (y == 0)).sum()), "only_b_right": int(((x == 0) & (y == 1)).sum()),
           "cells_defined": int(pc["phi"].notna().sum()), "median_phi": round(float(pc["phi"].median()), 2), "phi_iqr": [round(float(v), 2) for v in np.nanpercentile(pc["phi"], [25, 75])],
           "median_phi_over_max": round(float(pc["phi_over_max"].median()), 2),
           "cells_missing": [f"{r_.level}/{r_.task}" for r_ in pc[pc["phi"].isna()].itertuples()], **{k: round(v, 3) if isinstance(v, float) else v for k, v in pooled(Y[a_], Y[b_]).items()}, **pooled_boot(Y[a_], Y[b_])}
    rec["by_distractor"] = {}
    for nm, ii in [("none", [0]), ("time", [1]), ("unrelated", [2])]:
        pi = phi_cells(Y[a_], Y[b_], ii)
        rec["by_distractor"][nm] = {"median_phi": round(float(pi["phi"].median()), 2), "cells": int(pi["phi"].notna().sum()), **{k: round(v, 3) if isinstance(v, float) else v for k, v in pooled(Y[a_], Y[b_], ii).items()}}
    agree[name] = rec
    pc.assign(pair=name).to_csv(FIG / f"new_phi_cells_{name.replace('|', '_vs_')}.csv", index=False)
ceil = {}
for c in ["en_cot", "hi_cot", "clp", "encot", "en_direct", "hi_direct"]:
    a_ = np.stack([Y[c][:, 0], Y[c][:, 0], Y[c][:, 1]], 1)
    b_ = np.stack([Y[c][:, 1], Y[c][:, 2], Y[c][:, 2]], 1)
    pc = phi_cells(a_, b_)
    p_ = pooled(a_, b_)
    ceil[c] = {"median_phi": round(float(pc["phi"].median()), 2), "cells": int(pc["phi"].notna().sum()), **{k: round(v, 3) if isinstance(v, float) else v for k, v in p_.items()}}
NUM["agreement"] = agree
NUM["self_agreement_across_distractor"] = ceil
for name, a_, b_ in PAIRS[:4]:
    agree[name]["disattenuated_r"] = round(agree[name]["within_cell_r"] / np.sqrt(ceil[a_]["within_cell_r"] * ceil[b_]["within_cell_r"]), 2)
    bt = {}
    for task in TASKS:
        m = mask(task=task)
        x, y = Y[a_][m].ravel(), Y[b_][m].ravel()
        ok = ~np.isnan(x) & ~np.isnan(y)
        bt[task] = int(ok.sum())
pd.DataFrame([{"pair": k, **{a: v[a] for a in ("pairs", "both_right", "both_wrong", "only_a_right", "only_b_right", "cells_defined", "median_phi", "mh_or", "both_wrong_obs", "both_wrong_exp", "ratio", "within_cell_r")}, "mh_lo": v["mh_or_ci"][0], "mh_hi": v["mh_or_ci"][1], "r_lo": v["within_cell_r_ci"][0], "r_hi": v["within_cell_r_ci"][1], "ratio_lo": v["ratio_ci"][0], "ratio_hi": v["ratio_ci"][1], "disattenuated_r": v.get("disattenuated_r")} for k, v in agree.items()]).to_csv(FIG / "table_a6_agreement_all_cells.csv", index=False)
same = {}
ansmap = {c: df[(df["q"] < 50) & (df["cond"] == c) & df["scored"]].set_index(["qi", "ii"])[["parsed", "correct", "task"]] for c in ["en_cot", "hi_cot", "clp", "encot", "en_direct", "hi_direct"]}
for name, a_, b_ in PAIRS[:6]:
    j = ansmap[a_].join(ansmap[b_], lsuffix="_a", rsuffix="_b", how="inner")
    w_ = j[(j["correct_a"] == False) & (j["correct_b"] == False) & j["parsed_a"].notna() & j["parsed_b"].notna()]
    same[name] = {"both_wrong_parsed": len(w_), "same_wrong_answer": int((w_["parsed_a"] == w_["parsed_b"]).sum()), "pct": r1(100 * (w_["parsed_a"] == w_["parsed_b"]).mean()),
                  "by_task": {t_: r1(100 * (g_["parsed_a"] == g_["parsed_b"]).mean()) for t_, g_ in w_.groupby("task_a")}}
NUM["same_wrong_answer"] = same
del ansmap

print("errors")


def classify(kind, a, gold, pv_):
    if a is None or a != a:
        return "invalid"
    if a == gold:
        return "format_only"
    if kind == "date":
        if (a - pv_).days == -(gold - pv_).days:
            return "wrong_direction"
        if abs((a - gold).days) == 1:
            return "off_by_one"
        if a.year == gold.year and a.day == gold.day:
            return "month_slip"
        if a.month == gold.month and a.day == gold.day:
            return "year_slip"
        return "other"
    if kind == "iv":
        sh = [(x - y).days for x, y in zip(a, gold)]
        if sh[0] == sh[1] and sh[0] % 7 == 0:
            return "week_shift"
        return "off_by_one" if all(abs(s_) <= 1 for s_ in sh) else "other"
    if kind == "wd":
        return "off_by_one" if abs((a - gold + 3) % 7 - 3) == 1 else "other"
    if kind == "t":
        if (a - pv_) % 1440 == (pv_ - gold) % 1440:
            return "wrong_direction"
        e_ = (a - gold + 720) % 1440 - 720
        return "off_by_one" if abs(e_) == 1 else "off_by_one_hour" if abs(e_) == 60 else "other"
    if abs(a - gold) == 1:
        return "off_by_one"
    return "other"


def pivot_of(q_, kind):
    q_ = BR.norm(q_)
    if kind == "t":
        m_ = BR.TIME.search(q_)
        return int(m_[1]) * 60 + int(m_[2]) if m_ else None
    m_ = BR.ISO.search(q_)
    return BR.d(*m_.groups()) if m_ else None


err = {}
errrows = []
for c, lang in [("en_cot", "en"), ("hi_cot", "hi"), ("clp", "hi"), ("encot", "hi"), ("hi_direct", "hi"), ("en_direct", "en")]:
    g = df[(df["q"] < 50) & (df["cond"] == c) & (df["correct"] == False)]
    cl_ = []
    for r_ in g.itertuples():
        kind = BR.KIND[r_.task]
        qr = fq[(r_.level, r_.task, r_.q)]
        cl_.append(classify(kind, r_.parsed, r_.gold, pivot_of(getattr(qr, lang), kind)))
    g = g.assign(err=cl_)
    res = {"n": len(g), "off_by_one": r1(100 * (g["err"] == "off_by_one").mean()), "dist": {k: r1(100 * v) for k, v in g["err"].value_counts(normalize=True).items()}}
    res["by_task"] = {t_: {"n": int((g["task"] == t_).sum()), "off_by_one": r1(100 * (g[g["task"] == t_]["err"] == "off_by_one").mean()) if (g["task"] == t_).any() else None} for t_ in TASKS}
    res["by_ins"] = {i_: {"n": int((g["ins"] == i_).sum()), "off_by_one": r1(100 * (g[g["ins"] == i_]["err"] == "off_by_one").mean())} for i_ in INS}
    res["task_mix"] = {t_: r1(100 * (g["task"] == t_).mean()) for t_ in TASKS}
    err[c] = res
    errrows += [{"cond": c, "task": t_, **v} for t_, v in res["by_task"].items()]
    g2 = g[["task", "err"]]
    res["_tab"] = g2.groupby("task")["err"].apply(lambda s_: (s_ == "off_by_one").mean()).to_dict()
mixes = {"uniform": {t_: 1 / 9 for t_ in TASKS}, "clp_error_mix": {t_: err["clp"]["task_mix"][t_] / 100 for t_ in TASKS}, "en_cot_error_mix": {t_: err["en_cot"]["task_mix"][t_] / 100 for t_ in TASKS}, "hi_cot_error_mix": {t_: err["hi_cot"]["task_mix"][t_] / 100 for t_ in TASKS}}
std_ = {}
for c in err:
    std_[c] = {mk: r1(100 * sum(w_ * err[c]["_tab"].get(t_, 0.0) for t_, w_ in mx.items())) for mk, mx in mixes.items()}
for c in err:
    del err[c]["_tab"]
NUM["errors"] = err
NUM["errors_task_standardised_off_by_one"] = std_
pd.DataFrame(errrows).to_csv(FIG / "new_off_by_one_by_task.csv", index=False)
dow = {}
for c in ["en_cot", "hi_cot", "clp", "encot", "en_direct", "hi_direct"]:
    g = df[(df["q"] < 50) & (df["cond"] == c) & (df["task"] == "day_of_week") & df["scored"]]
    ok = g["parsed"].notna()
    off = [(a - b + 3) % 7 - 3 for a, b in zip(g[ok]["parsed"], g[ok]["gold"])]
    cnt = Counter(off)
    dow[c] = {"n": int(ok.sum()), "plus1": r1(100 * cnt[1] / len(off)), "minus1": r1(100 * cnt[-1] / len(off)), "zero": r1(100 * cnt[0] / len(off)), "dist": {str(k): r1(100 * v / len(off)) for k, v in sorted(cnt.items())}, "unparsed": int((~ok).sum())}
    dow[c]["by_ins"] = {}
    for i_ in INS:
        gi = g[ok & (g["ins"] == i_)]
        offs = [(a - b + 3) % 7 - 3 for a, b in zip(gi["parsed"], gi["gold"])]
        dow[c]["by_ins"][i_] = r1(100 * offs.count(1) / len(offs))
NUM["day_of_week"] = dow
pd.DataFrame([{"cond": c, **{f"offset_{k}": v for k, v in x["dist"].items()}} for c, x in dow.items()]).to_csv(FIG / "new_weekday_offsets.csv", index=False)
rec_ = {}
for c, lang in [("en_cot", "en"), ("hi_cot", "hi"), ("clp", "hi"), ("encot", "hi"), ("hi_direct", "hi"), ("en_direct", "en")]:
    g = df[(df["q"] < 50) & (df["cond"] == c) & (df["task"] == "date_recurrence") & df["scored"]]
    pat = Counter()
    pat_ins = {i_: Counter() for i_ in INS}
    for r_ in g.itertuples():
        qt = BR.norm(getattr(fq[(r_.level, r_.task, r_.q)], lang))
        iv = re.search(r"every (\d+) day|हर (\d+) दिन", qt)
        k_ = re.search(r"the (\d+) occurrence|(\d+)वीं", qt)
        if r_.parsed is None or r_.parsed != r_.parsed or not iv or not k_:
            continue
        iv_, k2 = int(next(x for x in iv.groups() if x)), int(next(x for x in k_.groups() if x))
        o_ = (r_.parsed - pivot_of(qt, "date")).days
        lab = "correct" if o_ == iv_ * k2 else "mirror" if o_ == -iv_ * k2 else "first_step" if o_ == iv_ else "other"
        pat[lab] += 1
        pat_ins[r_.ins][lab] += 1
    tot = sum(pat.values())
    rec_[c] = {"n": tot, **{k: r1(100 * v / tot) for k, v in pat.items()}, "mirror_by_ins": {i_: r1(100 * pat_ins[i_]["mirror"] / max(1, sum(pat_ins[i_].values()))) for i_ in INS}}
NUM["recurrence_patterns"] = rec_

print("stage1 length/cutoff")
cl_rows = clp.copy()
for c in ["hi_cot", "encot", "en_cot"]:
    o_ = df[(df["cond"] == c) & (df["q"] < 50)][["level", "task", "q", "ins", "c", "tokens", "scored", "ver"]].rename(columns={"c": f"c_{c}", "tokens": f"tok_{c}", "scored": f"sc_{c}", "ver": f"ver_{c}"})
    cl_rows = cl_rows.merge(o_, on=["level", "task", "q", "ins"])
cl_rows["s1_rank"] = cl_rows.groupby(["task", "level"])["s1_tokens"].rank(pct=True)
cl_rows["s1_ter"] = pd.cut(cl_rows["s1_rank"], [0, 1 / 3, 2 / 3, 1.0], labels=["short", "mid", "long"])
s1len = {}
for ter, g in cl_rows.groupby("s1_ter", observed=True):
    a_, b_ = g[g["c"].notna() & g["c_hi_cot"].notna()], g[g["c"].notna() & g["c_encot"].notna()]
    s1len[str(ter)] = {"n": len(g), "median_s1_tokens": float(g["s1_tokens"].median()), "clp_acc": r1(100 * g["c"].mean()), "hi_cot_acc": r1(100 * g["c_hi_cot"].mean()), "encot_acc": r1(100 * g["c_encot"].mean()), "gain_vs_hi_cot": round(100 * (a_["c"] - a_["c_hi_cot"]).mean(), 1), "gain_vs_encot": round(100 * (b_["c"] - b_["c_encot"]).mean(), 1), "cutoffs_s1": int(g["s1_cutoff"].sum())}
cut = cl_rows[cl_rows["s1_cutoff"]]
nocut = cl_rows[~cl_rows["s1_cutoff"]]
s1cut = {"s1_cutoff_n": len(cut), "by_task": cut["task"].value_counts().to_dict(), "by_level": cut["level"].value_counts().to_dict(), "by_ins": cut["ins"].value_counts().to_dict(),
         "s2_answered": int(cut["scored"].sum()), "s2_cutoff": int(cut["cutoff"].sum()), "clp_acc_cut_answered": r1(100 * cut["c"].mean()), "clp_strict_cut": r1(100 * cut["c"].fillna(0).mean()), "hi_cot_on_same": r1(100 * cut["c_hi_cot"].mean()), "encot_on_same": r1(100 * cut["c_encot"].mean()), "en_cot_on_same": r1(100 * cut["c_en_cot"].mean()),
         "clp_acc_nocut": r1(100 * nocut["c"].mean()), "overall_if_cut_excluded": r1(100 * nocut["c"].mean()), "gain_vs_hi_cot_without_cut": round(100 * (nocut[nocut["c"].notna() & nocut["c_hi_cot"].notna()]["c"] - nocut[nocut["c"].notna() & nocut["c_hi_cot"].notna()]["c_hi_cot"]).mean(), 2),
         "gain_vs_hi_cot_all": round(100 * (cl_rows[cl_rows["c"].notna() & cl_rows["c_hi_cot"].notna()]["c"] - cl_rows[cl_rows["c"].notna() & cl_rows["c_hi_cot"].notna()]["c_hi_cot"]).mean(), 2),
         "s1_cutoff_median_s2_tokens": float(cut["tokens"].median()), "s2_cut_given_s1_cut": int((cut["cutoff"]).sum()), "s2_cut_given_s1_ok": int(nocut["cutoff"].sum())}
s2 = {"median_s2_tokens": float(cl_rows["tokens"].median()), "median_encot_tokens": float(cl_rows["tok_encot"].median()), "median_s1_tokens": float(cl_rows["s1_tokens"].median()), "median_ratio_s2_encot": round(float((cl_rows["tokens"] / cl_rows["tok_encot"]).median()), 2),
      "ver_s2": r1(100 * cl_rows["ver"].mean()), "ver_encot": r1(100 * cl_rows["ver_encot"].mean())}
s2["by_ins"] = {i_: {"median_s1": float(g["s1_tokens"].median()), "median_s2": float(g["tokens"].median()), "median_encot": float(g["tok_encot"].median()), "clp_acc": r1(100 * g["c"].mean()), "encot_acc": r1(100 * g["c_encot"].mean()), "ver_s2": r1(100 * g["ver"].mean()), "ver_encot": r1(100 * g["ver_encot"].mean())} for i_, g in cl_rows.groupby("ins")}
s2["by_task"] = {t_: {"median_s1": float(g["s1_tokens"].median()), "median_s2": float(g["tokens"].median()), "median_encot": float(g["tok_encot"].median()), "clp_acc": r1(100 * g["c"].mean()), "encot_acc": r1(100 * g["c_encot"].mean()), "ver_s2": r1(100 * g["ver"].mean()), "ver_encot": r1(100 * g["ver_encot"].mean())} for t_, g in cl_rows.groupby("task")}
vo = {}
for a_, name in [(True, "encot_verifies"), (False, "encot_no_verify")]:
    g = cl_rows[cl_rows["ver_encot"] == a_]
    vo[name] = {"n": len(g), "encot_acc": r1(100 * g["c_encot"].mean()), "clp_acc": r1(100 * g["c"].mean())}
s2["accuracy_by_encot_verification"] = vo
g_ = cl_rows[cl_rows["c"].notna() & cl_rows["c_encot"].notna()]
g_ = g_.assign(dt=g_["c"] - g_["c_encot"], l2=np.log(g_["tokens"].clip(lower=1)), le=np.log(g_["tok_encot"].clip(lower=1)), ldiff=lambda x: np.log(x["tokens"].clip(lower=1)) - np.log(x["tok_encot"].clip(lower=1)))
gx = g_.copy()
for col in ["dt", "ldiff"]:
    gx[col] = gx[col] - gx.groupby(["task", "level"])[col].transform("mean")
s2["within_cell_corr_gapvs_length_diff"] = round(float(np.corrcoef(gx["dt"], gx["ldiff"])[0, 1]), 3)
dd = cl_rows[cl_rows["task"].isin(DT) & cl_rows["c"].notna() & cl_rows["c_encot"].notna()].merge(dt[["level", "task", "q", "ins", "s1_g", "eq"]], on=["level", "task", "q", "ins"])
s2["date_tasks_by_stage1"] = {str(k): {"n": len(g), "clp_acc": r1(100 * g["c"].mean()), "encot_acc": r1(100 * g["c_encot"].mean()), "hi_cot_acc": r1(100 * g["c_hi_cot"].mean()), "median_s2_tokens": float(g["tokens"].median()), "median_encot_tokens": float(g["tok_encot"].median())} for k, g in dd.groupby("s1_g")}
NUM["stage1_length"] = s1len
NUM["stage1_cutoff"] = s1cut
NUM["stage2_vs_encot"] = s2
pd.DataFrame([{"tertile": k, **v} for k, v in s1len.items()]).to_csv(FIG / "new_gain_by_stage1_length.csv", index=False)
pd.DataFrame([{"task": k, **v} for k, v in s2["by_task"].items()]).to_csv(FIG / "new_stage2_vs_encot_by_task.csv", index=False)
gx2 = cl_rows.copy()
gx2["ls1"] = np.log(gx2["s1_tokens"].clip(lower=1))
gain_corr = {}
for other_, nm in [("c_hi_cot", "vs_hi_cot"), ("c_encot", "vs_encot")]:
    z = gx2[gx2["c"].notna() & gx2[other_].notna()].copy()
    z["d_"] = z["c"] - z[other_]
    z["d_w"] = z["d_"] - z.groupby(["task", "level"])["d_"].transform("mean")
    z["l_w"] = z["ls1"] - z.groupby(["task", "level"])["ls1"].transform("mean")
    beta = (z["d_w"] * z["l_w"]).sum() / (z["l_w"] ** 2).sum()
    rw = np.random.default_rng(4)
    uq = z["qi"].unique()
    pos = {q_: i_ for i_, q_ in enumerate(uq)}
    ids = z["qi"].map(pos).to_numpy()
    xy, xx = np.bincount(ids, z["d_w"] * z["l_w"], len(uq)), np.bincount(ids, z["l_w"] ** 2, len(uq))
    bs = [(lambda w_: 100 * (w_ @ xy) / (w_ @ xx))(np.bincount(rw.integers(0, len(uq), len(uq)), minlength=len(uq))) for _ in range(B)]
    gain_corr[nm] = {"points_per_log_token": round(100 * float(beta), 2), "ci": ci(np.array(bs)), "n": len(z)}
NUM["gain_vs_log_stage1_tokens_within_cell"] = gain_corr

print("subset")
SC = {c: FULL[c] for c in ["en_direct", "en_cot", "hi_direct", "hi_cot"]}
first = QN < 50
rest = ~first
rw = np.random.default_rng(5)
WF = np.stack([np.bincount(rw.integers(0, 6750, 6750), minlength=6750) for _ in range(B)]).astype(np.int32)


def facc(a, m, ins=ALLI):
    return float(np.nanmean(a[m][:, ins])) * 100


def fboot(a, m, ins=ALLI):
    s = a[:, ins]
    c_, n = np.nansum(s, 1) * m, (~np.isnan(s)).sum(1) * m
    return 100 * (WF @ c_) / (WF @ n)


subset = {"overall": {}, "by_task": {}, "by_level": {}, "cells": []}
for c, a in SC.items():
    full_v = facc(a, np.ones(6750, bool))
    subset["overall"][c] = {"first50": round(facc(a, first), 2), "full": round(full_v, 2), "rest": round(facc(a, rest), 2), "first_minus_rest": round(facc(a, first) - facc(a, rest), 2), "ci": ci(fboot(a, first) - fboot(a, rest))}
for name, rows_, arr in [("by_task", TASKS, TK), ("by_level", LEVELS, LV)]:
    for x in rows_:
        subset[name][x] = {c: {"first50": r1(facc(SC[c], first & (arr == x))), "full": r1(facc(SC[c], arr == x)), "rest": r1(facc(SC[c], rest & (arr == x))), "first_minus_rest": round(facc(SC[c], first & (arr == x)) - facc(SC[c], rest & (arr == x)), 2), "ci": ci(fboot(SC[c], first & (arr == x)) - fboot(SC[c], rest & (arr == x)))} for c in SC}
tests = []
for c, a in SC.items():
    for lev in LEVELS:
        for task in TASKS:
            m = (LV == lev) & (TK == task)
            q_ = np.nanmean(a, 1)
            x, y = q_[m & first], q_[m & rest]
            x, y = x[~np.isnan(x)], y[~np.isnan(y)]
            ob = x.mean() - y.mean()
            pooled_ = np.concatenate([x, y])
            prw = np.random.default_rng(zlib.crc32(f"{c}{lev}{task}".encode()))
            null = []
            for _ in range(2000):
                prw.shuffle(pooled_)
                null.append(pooled_[:len(x)].mean() - pooled_[len(x):].mean())
            p = float((np.sum(np.abs(null) >= abs(ob) - 1e-12) + 1) / 2001)
            tests.append({"cond": c, "level": lev, "task": task, "first50": r1(100 * x.mean()), "rest": r1(100 * y.mean()), "full": r1(100 * pooled_.mean()), "diff": round(100 * ob, 1), "p": p})
tdf = pd.DataFrame(tests)
tdf["p_bh"] = multipletests(tdf["p"], method="fdr_bh")[1]
tdf.to_csv(FIG / "new_subset_vs_rest_by_cell.csv", index=False)
subset["cell_tests"] = {"n": len(tdf), "p_lt_05": int((tdf["p"] < 0.05).sum()), "expected_under_null": round(0.05 * len(tdf), 1), "bh_lt_05": int((tdf["p_bh"] < 0.05).sum()), "abs_diff_mean": round(float(tdf["diff"].abs().mean()), 2), "signed_diff_mean": round(float(tdf["diff"].mean()), 2), "by_cond": {k: {"mean_diff": round(float(v["diff"].mean()), 2), "p_lt_05": int((v["p"] < 0.05).sum())} for k, v in tdf.groupby("cond")}, "largest": tdf.reindex(tdf["diff"].abs().sort_values(ascending=False).index).head(8).to_dict("records")}


def did(cot, direct, ms_, ii):
    return (facc(cot, ms_, [0]) - facc(cot, ms_, [ii])) - (facc(direct, ms_, [0]) - facc(direct, ms_, [ii]))


def did_boot(cot, direct, ms_, ii):
    return (fboot(cot, ms_, [0]) - fboot(cot, ms_, [ii])) - (fboot(direct, ms_, [0]) - fboot(direct, ms_, [ii]))


pen = {}
allm = np.ones(6750, bool)
for lang, cot, direct in [("hi", "hi_cot", "hi_direct"), ("en", "en_cot", "en_direct")]:
    for ii, nm in [(1, "time"), (2, "unrelated")]:
        a, b = SC[cot], SC[direct]
        pen[f"{lang}_{nm}"] = {"first50": round(did(a, b, first, ii), 2), "first50_ci": ci(did_boot(a, b, first, ii)), "full": round(did(a, b, allm, ii), 2), "full_ci": ci(did_boot(a, b, allm, ii)), "rest": round(did(a, b, rest, ii), 2), "rest_ci": ci(did_boot(a, b, rest, ii)), "first_minus_rest": round(did(a, b, first, ii) - did(a, b, rest, ii), 2), "first_minus_rest_ci": ci(did_boot(a, b, first, ii) - did_boot(a, b, rest, ii))}
        pen[f"{lang}_{nm}"]["cot_drop_first50"] = round(facc(a, first, [0]) - facc(a, first, [ii]), 2)
        pen[f"{lang}_{nm}"]["cot_drop_full"] = round(facc(a, allm, [0]) - facc(a, allm, [ii]), 2)
        pen[f"{lang}_{nm}"]["cot_drop_full_ci"] = ci(fboot(a, allm, [0]) - fboot(a, allm, [ii]))
        pen[f"{lang}_{nm}"]["direct_drop_first50"] = round(facc(b, first, [0]) - facc(b, first, [ii]), 2)
        pen[f"{lang}_{nm}"]["direct_drop_full"] = round(facc(b, allm, [0]) - facc(b, allm, [ii]), 2)
        pen[f"{lang}_{nm}"]["by_task"] = {t_: {"first50": round(did(a, b, first & (TK == t_), ii), 1), "rest": round(did(a, b, rest & (TK == t_), ii), 1)} for t_ in TASKS}
subset["penalty"] = pen
pd.DataFrame([{"contrast": k, **{a: b for a, b in v.items() if a not in ("by_task",) and not a.endswith("_ci")}, "first50_lo": v["first50_ci"][0], "first50_hi": v["first50_ci"][1], "full_lo": v["full_ci"][0], "full_hi": v["full_ci"][1], "rest_lo": v["rest_ci"][0], "rest_hi": v["rest_ci"][1]} for k, v in pen.items()]).to_csv(FIG / "new_subset_penalty.csv", index=False)
rw = np.random.default_rng(6)
cell_ids = {}
for i_, (l_, t_) in enumerate(zip(LV, TK)):
    cell_ids.setdefault((l_, t_), []).append(i_)
stack = {}
for c, a in SC.items():
    for ii in range(3):
        stack[c, ii, "c"] = np.nan_to_num(a[:, ii])
        stack[c, ii, "n"] = (~np.isnan(a[:, ii])).astype(float)
D = 5000
sim_ = {"hi_time": [], "hi_unrelated": [], "en_time": [], "hi_cot_acc": [], "hi_direct_acc": [], "en_cot_acc": [], "en_direct_acc": [], "hi_cot_drop_time": []}
for _ in range(D):
    mm = np.zeros(6750, bool)
    for ids in cell_ids.values():
        mm[rw.choice(ids, 50, replace=False)] = True
    def ra(c, ii):
        return 100 * stack[c, ii, "c"][mm].sum() / stack[c, ii, "n"][mm].sum()
    v = {(c, ii): ra(c, ii) for c in SC for ii in range(3)}
    sim_["hi_time"].append(v["hi_cot", 0] - v["hi_cot", 1] - (v["hi_direct", 0] - v["hi_direct", 1]))
    sim_["hi_unrelated"].append(v["hi_cot", 0] - v["hi_cot", 2] - (v["hi_direct", 0] - v["hi_direct", 2]))
    sim_["en_time"].append(v["en_cot", 0] - v["en_cot", 1] - (v["en_direct", 0] - v["en_direct", 1]))
    sim_["hi_cot_drop_time"].append(v["hi_cot", 0] - v["hi_cot", 1])
    for c in SC:
        sim_[c + "_acc"].append(float(np.mean([stack[c, ii, "c"][mm].sum() for ii in range(3)]) * 3 / np.sum([stack[c, ii, "n"][mm].sum() for ii in range(3)])) * 100)
obs = {"hi_time": did(SC["hi_cot"], SC["hi_direct"], first, 1), "hi_unrelated": did(SC["hi_cot"], SC["hi_direct"], first, 2), "en_time": did(SC["en_cot"], SC["en_direct"], first, 1), "hi_cot_drop_time": facc(SC["hi_cot"], first, [0]) - facc(SC["hi_cot"], first, [1]), **{c + "_acc": facc(SC[c], first) for c in SC}}
subset["random_subset_null"] = {k: {"observed_first50": round(obs[k], 2), "null_mean": round(float(np.mean(v)), 2), "null_sd": round(float(np.std(v)), 2), "null_2.5": round(float(np.percentile(v, 2.5)), 2), "null_97.5": round(float(np.percentile(v, 97.5)), 2), "two_sided_p": round(float(2 * min(np.mean(np.array(v) <= obs[k]), np.mean(np.array(v) >= obs[k]))), 3)} for k, v in sim_.items()}
pd.DataFrame({k: np.round(v, 3) for k, v in sim_.items() if k in ("hi_time", "hi_unrelated", "en_time", "hi_cot_drop_time")}).to_csv(FIG / "new_subset_random_draw_null.csv", index=False)
trend = {}
for c, a in SC.items():
    y_ = np.nanmean(a, 1)
    ok = ~np.isnan(y_)
    x_ = QN.astype(float)
    dfz = pd.DataFrame({"y": y_[ok], "x": x_[ok], "l": LV[ok], "t": TK[ok]})
    dfz["yw"] = dfz["y"] - dfz.groupby(["l", "t"])["y"].transform("mean")
    dfz["xw"] = dfz["x"] - dfz.groupby(["l", "t"])["x"].transform("mean")
    b_ = float((dfz["xw"] * dfz["yw"]).sum() / (dfz["xw"] ** 2).sum())
    e_ = dfz["yw"] - b_ * dfz["xw"]
    se = float(np.sqrt(((dfz["xw"] * e_) ** 2).sum()) / (dfz["xw"] ** 2).sum())
    trend[c] = {"points_per_100_questions": round(b_ * 10000, 2), "se": round(se * 10000, 2), "z": round(b_ / se, 2)}
subset["position_trend"] = trend


def gen_check():
    from trd.config.timeframes import DIFFICULTY_LEVELS, TimeframeConfig
    from trd.config.defaults import ALL_TASKS
    from trd.generators import GENERATOR_MAP
    from trd.templates.insertions import get_random_insertion, prepend_insertion
    out, match, total = [], 0, 0
    questions_seen = {}
    for lev in DIFFICULTY_LEVELS:
        cfg = TimeframeConfig.from_name(lev)
        random.seed(9)
        for task in ALL_TASKS:
            gens = {la: GENERATOR_MAP[task](cfg, la) for la in ("en_US", "hi_IN")}
            q = {la: {} for la in gens}
            order, draws, rej_pos = [], 0, []
            for _ in range(1500):
                st = random.getstate()
                dr = {}
                for la, g_ in gens.items():
                    random.setstate(st)
                    s_ = g_.generate_sample()
                    dr[la] = {"no_insertion": s_.question, "similar_insertion": prepend_insertion(s_.question, get_random_insertion(la, g_.template_key, True)), "dissimilar_insertion": prepend_insertion(s_.question, get_random_insertion(la, g_.template_key, False)), "answer": s_.answer}
                draws += 1
                if all(d_["no_insertion"] not in q[la] for la, d_ in dr.items()):
                    for la, d_ in dr.items():
                        q[la][d_["no_insertion"]] = d_
                    order.append(draws)
                else:
                    rej_pos.append(len(q["en_US"]))
                if len(q["en_US"]) == 150:
                    break
            data = json.load(open(ROOT / "dataset" / lev / f"{task}_en_US.json", encoding="utf-8"))
            same = all(data[str(i_)] == v for i_, v in enumerate(q["en_US"].values()))
            match += same
            total += 1
            out.append({"level": lev, "task": task, "draws": draws, "accepted": len(q["en_US"]), "rejected_total": draws - len(q["en_US"]), "rejected_before_50": sum(1 for x in rej_pos if x < 50), "rejected_after_50": sum(1 for x in rej_pos if x >= 50), "draw_of_q49": order[49], "matches_dataset": same})
    return out, match, total


rows_, match, total = gen_check()
gd = pd.DataFrame(rows_)
gd.to_csv(FIG / "new_generator_draws_by_cell.csv", index=False)
subset["generator"] = {"cells_regenerated_identical": match, "cells": total, "cells_with_any_rejection": int((gd["rejected_total"] > 0).sum()), "total_rejected": int(gd["rejected_total"].sum()), "rejected_before_50": int(gd["rejected_before_50"].sum()), "rejected_after_50": int(gd["rejected_after_50"].sum()), "largest": gd.sort_values("rejected_total", ascending=False).head(6).to_dict("records")}
ft = feats.copy()
ft["first"] = ft["q"] < 50
ft["nums"] = ft["en"].map(lambda s_: [int(x) for x in re.findall(r"\d+", re.sub(r"\d{4}-\d{2}-\d{2}|\d{1,2}:\d{2}", " ", s_))])
ft["offset"] = ft["nums"].map(lambda x: sum(x) if x else 0)
ft["month"] = ft["en"].map(lambda s_: int(BR.ISO.search(s_)[2]) if BR.ISO.search(s_) else -1)
ft["n_anchor"] = ft["en"].map(lambda s_: (BR.ISO.search(s_)[1]+BR.ISO.search(s_)[2]+BR.ISO.search(s_)[3]) if BR.ISO.search(s_) else (BR.TIME.search(s_)[1]+BR.TIME.search(s_)[2] if BR.TIME.search(s_) else "0"))
ft["anchor_num"] = ft["n_anchor"].astype(int)
ks_p, ks_a, chi_p, chi_d = [], [], [], []
for (l_, t_), g in ft.groupby(["level", "task"]):
    a_, b_ = g[g["first"]], g[~g["first"]]
    if g["offset"].nunique() > 1:
        ks_p.append(ks_2samp(a_["offset"], b_["offset"]).pvalue)
    if g["anchor_num"].nunique() > 1:
        ks_a.append(ks_2samp(a_["anchor_num"], b_["anchor_num"]).pvalue)
    for col, store in [("hi_sim", chi_p), ("hi_dis", chi_d)]:
        tb = pd.crosstab(g[col], g["first"])
        if len(tb) > 1:
            store.append(chi2_contingency(tb)[1])
subset["features"] = {"ks_offset_p_lt_05": int(sum(p < 0.05 for p in ks_p)), "ks_offset_tests": len(ks_p), "ks_offset_min_p": round(float(min(ks_p)), 4), "ks_anchor_p_lt_05": int(sum(p < 0.05 for p in ks_a)), "ks_anchor_tests": len(ks_a), "ks_anchor_min_p": round(float(min(ks_a)), 4),
                      "chi_time_distractor_p_lt_05": int(sum(p < 0.05 for p in chi_p)), "chi_time_tests": len(chi_p), "chi_time_min_p": round(float(min(chi_p)), 4), "chi_unrelated_p_lt_05": int(sum(p < 0.05 for p in chi_d)), "chi_unrelated_tests": len(chi_d), "chi_unrelated_min_p": round(float(min(chi_d)), 4)}
cross = {}
piv = ft.pivot_table(index=["task", "q"], columns="level", values="hi_sim", aggfunc="first")
piv2 = ft.pivot_table(index=["task", "q"], columns="level", values="hi_dis", aggfunc="first")
piv3 = ft.pivot_table(index=["task", "q"], columns="level", values="anchor_num", aggfunc="first")
cross["share_q_same_time_sentence_all_levels"] = {t_: r1(100 * float((g.nunique(axis=1) == 1).mean())) for t_, g in piv.groupby(level=0)}
cross["share_q_same_unrelated_sentence_all_levels"] = {t_: r1(100 * float((g.nunique(axis=1) == 1).mean())) for t_, g in piv2.groupby(level=0)}
cross["share_q_same_anchor_all_levels"] = {t_: r1(100 * float((g.nunique(axis=1) == 1).mean())) for t_, g in piv3.groupby(level=0)}
subset["cross_level_dependence"] = cross
cq = {}
for c in ["en_cot", "hi_cot", "clp"]:
    a = np.nanmean(Y[c], 1)
    a = a.reshape(5, 9, 50)
    vals = []
    for t_i in range(9):
        for i_ in range(5):
            for j_ in range(i_ + 1, 5):
                x, y = a[i_, t_i], a[j_, t_i]
                ok = ~np.isnan(x) & ~np.isnan(y)
                if ok.sum() > 2 and x[ok].std() > 0 and y[ok].std() > 0:
                    vals.append(np.corrcoef(x[ok], y[ok])[0, 1])
    cq[c] = {"mean_r_same_qid_across_levels": round(float(np.mean(vals)), 3), "pairs": len(vals)}
subset["cross_level_outcome_correlation"] = cq
rw = np.random.default_rng(7)
tq = np.array([f"{t_}/{q_}" for t_, q_ in zip(TKS, QN[SUB])])
uq = np.unique(tq)
pos = {k: i_ for i_, k in enumerate(uq)}
ids = np.array([pos[k] for k in tq])
a_c, a_n = sums(Y["clp"], np.ones(Q, bool), ALLI)
b_c, b_n = sums(Y["hi_cot"], np.ones(Q, bool), ALLI)
ca, na, cb, nb = [np.bincount(ids, v, len(uq)) for v in (a_c, a_n, b_c, b_n)]
bs = []
for _ in range(B):
    w_ = np.bincount(rw.integers(0, len(uq), len(uq)), minlength=len(uq))
    bs.append(100 * ((w_ @ ca) / (w_ @ na) - (w_ @ cb) / (w_ @ nb)))
subset["headline_ci_clustered_on_task_qid_across_levels"] = ci(np.array(bs))
NUM["subset"] = subset

print("stratified boot")
rw = np.random.default_rng(8)
Ws = []
for _ in range(B):
    w_ = np.zeros(Q, int)
    for c_ in range(45):
        w_[c_ * 50:(c_ + 1) * 50] = np.bincount(rw.integers(0, 50, 50), minlength=50)
    Ws.append(w_)
Ws = np.array(Ws, dtype=np.int32)
NUM["ci_sensitivity"] = {
    "clp-hi_cot": {"unstratified_B2000": ci(boot_acc(Y["clp"]) - boot_acc(Y["hi_cot"])), "stratified_task_level": ci(boot_acc(Y["clp"], w=Ws) - boot_acc(Y["hi_cot"], w=Ws))},
    "clp-hi_direct": {"unstratified_B2000": ci(boot_acc(Y["clp"]) - boot_acc(Y["hi_direct"])), "stratified_task_level": ci(boot_acc(Y["clp"], w=Ws) - boot_acc(Y["hi_direct"], w=Ws))},
    "en_cot-clp": {"unstratified_B2000": ci(boot_acc(Y["en_cot"]) - boot_acc(Y["clp"])), "stratified_task_level": ci(boot_acc(Y["en_cot"], w=Ws) - boot_acc(Y["clp"], w=Ws))},
    "clp_drop_unrelated": {"unstratified_B2000": ci(boot_acc(Y["clp"], None, [0]) - boot_acc(Y["clp"], None, [2])), "stratified_task_level": ci(boot_acc(Y["clp"], None, [0], Ws) - boot_acc(Y["clp"], None, [2], Ws))},
}

print("pipeline differential")
sys.path.insert(0, str(ROOT / "experiments" / "2026-10-27_full-grid-analysis"))
import temporal_answers as TA
PM = TA.M
diff_ex = []
tot, mism_a, mism_c = 0, 0, 0
for key, content in texts.items():
    if key[0] in ("s1",):
        continue
    cond, lev, task, q_, ins = key
    a_, _ = BR.answer(content)
    b_ = PM.extract_answer(content)
    tot += 1
    if a_ != b_:
        mism_a += 1
        if len(diff_ex) < 10:
            diff_ex.append({"key": list(map(str, key)), "mine": a_, "pipeline": b_, "tail": (content or "")[-160:]})
NUM["pipeline_extract_differential"] = {"responses_compared": tot, "answer_mismatches": mism_a, "examples": diff_ex}
NUM["data_checks"] = json.load(open(HERE / "data_checks.json", encoding="utf-8"))

print("extras")
ex = {}
clpall = df[(df["cond"] == "clp") & (df["q"] < 50)]
den = {}
for kind, insn in [("sim", "similar_insertion"), ("dis", "dissimilar_insertion")]:
    for pre in ("s1", "s1b"):
        f = mflag(clpall, kind, pre, ["en", "hi"])
        im, pm = (clpall["ins"] == insn) & f.notna(), (clpall["ins"] == "no_insertion") & f.notna()
        den[f"{kind}_{pre}_all_responses"] = {"rate": r1(100 * f[im].astype(float).mean()), "placebo": r1(100 * f[pm].astype(float).mean()), "n": int(im.sum())}
        sc_ = clpall[clpall["scored"]]
        fs_ = f[clpall["scored"]]
        im2, pm2 = (sc_["ins"] == insn) & fs_.notna(), (sc_["ins"] == "no_insertion") & fs_.notna()
        den[f"{kind}_{pre}_answered"] = {"rate": r1(100 * fs_[im2].astype(float).mean()), "placebo": r1(100 * fs_[pm2].astype(float).mean()), "n": int(im2.sum())}
ex["stage1_mention_denominators"] = den
ans_line = re.compile(r"(?:Answer|उत्तर(?:\s*है)?|जवाब)\s*\**\s*[:：]\s*(?!Answer|उत्तर|जवाब)(.*)")
share = {"s1": [0, 0], "s2": [0, 0], "s1_mean": [], "s2_mean": []}
for key, t_ in texts.items():
    if key[0] in ("s1", "s2"):
        body = ans_line.sub("", t_ or "")
        h_, e_ = len(BR.HI_W.findall(body)), len(BR.EN_W.findall(body))
        share[key[0]][0] += e_
        share[key[0]][1] += e_ + h_
        if e_ + h_:
            share[key[0] + "_mean"].append(e_ / (e_ + h_))
ex["english_share_answer_line_stripped"] = {"s1_pooled": round(share["s1"][0] / share["s1"][1], 3), "s2_pooled": round(share["s2"][0] / share["s2"][1], 3), "s1_mean": round(float(np.mean(share["s1_mean"])), 3), "s2_mean": round(float(np.mean(share["s2_mean"])), 3)}
dd_ = {}
for a, b in [("clp", "hi_cot"), ("clp", "encot"), ("clp", "en_cot"), ("encot", "hi_cot")]:
    for nm, ii in [("time", 1), ("unrelated", 2)]:
        v = (acc(Y[a], None, [0]) - acc(Y[a], None, [ii])) - (acc(Y[b], None, [0]) - acc(Y[b], None, [ii]))
        bs_ = (boot_acc(Y[a], None, [0]) - boot_acc(Y[a], None, [ii])) - (boot_acc(Y[b], None, [0]) - boot_acc(Y[b], None, [ii]))
        dd_[f"{a}-{b}_{nm}"] = {"diff_in_drop": round(v, 2), "ci": ci(bs_)}
ex["difference_in_drops"] = dd_
bs_ = boot_acc(Y["clp"], None, [0]) - boot_acc(Y["clp"], None, [1])
ex["clp_time_drop_90ci"] = [round(float(x), 2) for x in np.percentile(bs_, [5, 95])]
bs_ = boot_acc(Y["hi_cot"], None, [0]) - boot_acc(Y["hi_cot"], None, [1])
ex["hi_cot_time_drop_90ci"] = [round(float(x), 2) for x in np.percentile(bs_, [5, 95])]
td = {}
ps = []
for t_ in TASKS:
    m = mask(task=t_)
    a_, b_ = Y["clp"][m, 0], Y["clp"][m, 1]
    ok = ~np.isnan(a_) & ~np.isnan(b_)
    p1, p2 = int(((a_ == 1) & (b_ == 0))[ok].sum()), int(((a_ == 0) & (b_ == 1))[ok].sum())
    td[t_] = {"none": r1(acc(Y["clp"], m, [0])), "time": r1(acc(Y["clp"], m, [1])), "drop": round(acc(Y["clp"], m, [0]) - acc(Y["clp"], m, [1]), 2), "ci": ci(boot_acc(Y["clp"], m, [0]) - boot_acc(Y["clp"], m, [1])), "none_only": p1, "time_only": p2, "p": float(binomtest(p1, p1 + p2, 0.5).pvalue)}
    ps.append(td[t_]["p"])
for t_, p in zip(TASKS, multipletests(ps, method="holm")[1]):
    td[t_]["p_holm"] = float(p)
ex["clp_time_drop_by_task"] = td
ex["clp_time_drop_by_level"] = {l_: {"drop": round(acc(Y["clp"], mask(level=l_), [0]) - acc(Y["clp"], mask(level=l_), [1]), 2), "ci": ci(boot_acc(Y["clp"], mask(level=l_), [0]) - boot_acc(Y["clp"], mask(level=l_), [1]))} for l_ in LEVELS}
pd.DataFrame([{"task": k, **{a: b for a, b in v.items() if a != "ci"}, "lo": v["ci"][0], "hi": v["ci"][1]} for k, v in td.items()]).to_csv(FIG / "new_clp_time_drop_by_task.csv", index=False)
none_ = dt[~dt["s1_has_date"]].merge(df[(df["cond"] == "encot")][["level", "task", "q", "ins", "c"]].rename(columns={"c": "enc"}), on=["level", "task", "q", "ins"]).merge(df[(df["cond"] == "hi_cot")][["level", "task", "q", "ins", "c"]].rename(columns={"c": "hic"}), on=["level", "task", "q", "ins"])
ex["stage1_no_date_group"] = {"n": len(none_), "clp_acc": r1(100 * none_["s2_c"].mean()), "encot_acc": r1(100 * none_["enc"].mean()), "hi_cot_acc": r1(100 * none_["hic"].mean()), "by_task": none_["task"].value_counts().to_dict(), "by_ins": none_["ins"].value_counts().to_dict(), "recurrence_clp_acc": r1(100 * none_[none_["task"] == "date_recurrence"]["s2_c"].mean())}
dq3 = dt.merge(df[(df["cond"] == "encot") & df["scored"]][["level", "task", "q", "ins", "c"]].rename(columns={"c": "enc"}), on=["level", "task", "q", "ins"])
sg, so = dq3[dq3["s1_g"]], dq3[~dq3["s1_g"]]
ex["date_gap_decomposition"] = {"n": len(dq3), "share_s1_gold": r1(100 * len(sg) / len(dq3)), "encot_acc": r1(100 * dq3["enc"].mean()), "clp_acc": r1(100 * dq3["s2_c"].mean()), "gap": round(100 * (dq3["enc"].mean() - dq3["s2_c"].mean()), 1), "gap_s1_gold": round(100 * (sg["enc"].mean() - sg["s2_c"].mean()), 1), "gap_s1_other": round(100 * (so["enc"].mean() - so["s2_c"].mean()), 1), "contribution_s1_gold": round(100 * len(sg) / len(dq3) * (sg["enc"].mean() - sg["s2_c"].mean()), 1), "contribution_s1_other": round(100 * len(so) / len(dq3) * (so["enc"].mean() - so["s2_c"].mean()), 1)}
MODE = {"devanagari": re.compile(r"[ऀ-ॿ]{2,}"), "translate": re.compile(r"translat", re.I), "dismiss": re.compile(r"distract|irrelevant|not relevant|unrelated|does not affect|doesn't affect|not needed|extra (?:information|context|detail)|no bearing|not (?:directly )?related|contextual", re.I), "steps": re.compile(r"step[- ]by[- ]step breakdown|\*\*step 1|deconstruct|analy[sz]e the", re.I)}
md = clp[["level", "task", "q", "ins", "qi", "c", "s1_tokens"]].copy()
for k_, rx in MODE.items():
    md[k_] = [bool(rx.search(texts["s1", r_.level, r_.task, r_.q, r_.ins] or "")) for r_ in md.itertuples()]
md["analysis"] = md["devanagari"] | md["translate"]
mode = {"rates_by_ins": {k_: {i_: r1(100 * md[md["ins"] == i_][k_].mean()) for i_ in INS} for k_ in ["devanagari", "translate", "dismiss", "steps", "analysis"]}}
mode["recurrence_rates_by_ins"] = {k_: {i_: r1(100 * md[(md["ins"] == i_) & (md["task"] == "date_recurrence")][k_].mean()) for i_ in INS} for k_ in ["devanagari", "translate", "dismiss", "steps", "analysis"]}
md2 = md[md["c"].notna()].copy()
md2["y"] = md2["c"] == 1
mode["accuracy_by_analysis_mode_pooled"] = {str(k_): r1(100 * g["y"].mean()) for k_, g in md2.groupby("analysis")}
mode["mh_or_correct_by_analysis"] = {i_: mh(md2[md2["ins"] == i_], "analysis", "y") for i_ in INS}
mode["accuracy_by_mode_and_ins"] = {f"{i_}|{m_}": r1(100 * md2[(md2["ins"] == i_) & (md2["analysis"] == m_)]["y"].mean()) for i_ in INS for m_ in (True, False)}
mode["recurrence_accuracy_by_mode_and_ins"] = {f"{i_}|{m_}": {"acc": r1(100 * md2[(md2["ins"] == i_) & (md2["analysis"] == m_) & (md2["task"] == "date_recurrence")]["y"].mean()), "n": int(((md2["ins"] == i_) & (md2["analysis"] == m_) & (md2["task"] == "date_recurrence")).sum())} for i_ in INS for m_ in (True, False)}
pp = md2[md2["ins"].isin(["no_insertion", "dissimilar_insertion"])].copy()
pp["u"] = (pp["ins"] == "dissimilar_insertion").astype(float)
pp["a"] = pp["analysis"].astype(float)
pp["yy"] = pp["y"].astype(float)
for col_ in ["u", "a", "yy"]:
    pp[col_ + "w"] = pp[col_] - pp.groupby("qi")[col_].transform("mean")
X1 = pp[["uw"]].to_numpy()
X2 = pp[["uw", "aw"]].to_numpy()
y_ = pp["yyw"].to_numpy()
b1 = np.linalg.lstsq(X1, y_, rcond=None)[0]
b2 = np.linalg.lstsq(X2, y_, rcond=None)[0]
uq = pp["qi"].unique()
groups = {q_: g.index.to_numpy() for q_, g in pp.reset_index(drop=True).groupby("qi")}
pr = pp.reset_index(drop=True)
Xa, Xb, ya = pr[["uw"]].to_numpy(), pr[["uw", "aw"]].to_numpy(), pr["yyw"].to_numpy()
rw = np.random.default_rng(9)
keys_ = list(groups)
idx_arr = [groups[k_] for k_ in keys_]
bo = []
for _ in range(500):
    s = rw.integers(0, len(keys_), len(keys_))
    ii_ = np.concatenate([idx_arr[j_] for j_ in s])
    bo.append((np.linalg.lstsq(Xa[ii_], ya[ii_], rcond=None)[0][0], *np.linalg.lstsq(Xb[ii_], ya[ii_], rcond=None)[0]))
bo = np.array(bo) * 100
mode["within_question_mediation"] = {"gain_total_points": round(100 * float(b1[0]), 2), "gain_total_ci": ci(bo[:, 0]), "gain_after_analysis_mode": round(100 * float(b2[0]), 2), "gain_after_ci": ci(bo[:, 1]), "analysis_mode_effect_points": round(100 * float(b2[1]), 2), "analysis_mode_ci": ci(bo[:, 2]), "share_mediated": round(float(1 - b2[0] / b1[0]), 2)}
sim_u = md2[md2["ins"].isin(["no_insertion", "similar_insertion"])].copy()
sim_u["u"] = (sim_u["ins"] == "similar_insertion").astype(float)
sim_u["a"] = sim_u["analysis"].astype(float)
sim_u["yy"] = sim_u["y"].astype(float)
for col_ in ["u", "a", "yy"]:
    sim_u[col_ + "w"] = sim_u[col_] - sim_u.groupby("qi")[col_].transform("mean")
b3 = np.linalg.lstsq(sim_u[["uw", "aw"]].to_numpy(), sim_u["yyw"].to_numpy(), rcond=None)[0]
mode["time_related_same_model"] = {"direct_effect_of_time_sentence_given_mode": round(100 * float(b3[0]), 2), "analysis_mode_effect": round(100 * float(b3[1]), 2)}
ex["stage1_mode"] = mode
pd.DataFrame([{"feature": k_, **v} for k_, v in mode["rates_by_ins"].items()]).to_csv(FIG / "new_stage1_mode_rates.csv", index=False)
IRR = re.compile(r"distract|irrelevant|not relevant|unrelated|does not affect|doesn't affect|not needed|no bearing|not related|असंबंधित|अप्रासंगिक|संबंधित नहीं|प्रभावित नहीं|आवश्यक नहीं|जरूरी नहीं|ज़रूरी नहीं|ध्यान भटका", re.I)
irr = {}
for lab, cond_ in [("en_cot", "en_cot"), ("hi_cot", "hi_cot"), ("clp_s1", "s1"), ("clp_s2", "s2"), ("encot", "encot")]:
    cnt = {i_: [0, 0] for i_ in INS}
    for key, t_ in texts.items():
        if key[0] == cond_:
            cnt[key[4]][0] += bool(IRR.search(t_ or ""))
            cnt[key[4]][1] += 1
    irr[lab] = {i_: r1(100 * v[0] / v[1]) for i_, v in cnt.items()}
ex["dismissal_phrase_rate"] = irr
pd.DataFrame([{"reasoning": k_, **v} for k_, v in irr.items()]).to_csv(FIG / "new_dismissal_phrase_rates.csv", index=False)
msd = {}
for kind, insn, ii in [("sim", "similar_insertion", 1), ("dis", "dissimilar_insertion", 2)]:
    vals = {}
    for lab, c_, pre in [("clp_s2", "clp", ""), ("encot", "encot", ""), ("hi_cot", "hi_cot", "")]:
        g = df[(df["q"] < 50) & (df["cond"] == c_) & df["scored"]]
        f = mflag(g, kind, pre, RULES[c_])
        a_ = pd.Series(np.nan, index=range(6750), dtype=float)
        b_ = pd.Series(np.nan, index=range(6750), dtype=float)
        im, pm = (g["ins"] == insn) & f.notna(), (g["ins"] == "no_insertion") & f.notna()
        a_.loc[g[im]["qi"]] = f[im].astype(float).to_numpy()
        b_.loc[g[pm]["qi"]] = f[pm].astype(float).to_numpy()
        vals[lab] = (a_ - b_).to_numpy()[SUB]
    for x_, y2 in [("clp_s2", "encot"), ("clp_s2", "hi_cot"), ("encot", "hi_cot")]:
        ok = ~np.isnan(vals[x_]) & ~np.isnan(vals[y2])
        d3 = vals[x_] - vals[y2]
        bs_ = 100 * ((W * np.where(ok, np.nan_to_num(d3), 0)).sum(1) / (W * ok).sum(1))
        msd[f"{kind}:{x_}-{y2}"] = {"net_difference": round(100 * float(d3[ok].mean()), 1), "ci": ci(bs_), "n": int(ok.sum())}
ex["net_mention_paired_differences"] = msd
sa = {}
for c in ["en_cot", "hi_cot", "clp", "encot", "en_direct", "hi_direct"]:
    a_ = np.stack([Y[c][:, 0], Y[c][:, 0], Y[c][:, 1]], 1)
    b_ = np.stack([Y[c][:, 1], Y[c][:, 2], Y[c][:, 2]], 1)
    sa[c] = pooled_boot(a_, b_, n=300, seed=10)
ex["self_agreement_ci"] = sa
pd.DataFrame([{"cond": k_, **{a: b for a, b in ceil[k_].items()}, "mh_lo": sa[k_]["mh_or_ci"][0], "mh_hi": sa[k_]["mh_or_ci"][1], "r_lo": sa[k_]["within_cell_r_ci"][0], "r_hi": sa[k_]["within_cell_r_ci"][1]} for k_ in sa]).to_csv(FIG / "new_self_agreement.csv", index=False)
bytask = {}
for name_, a_, b_ in PAIRS[:4]:
    bytask[name_] = {}
    for t_ in TASKS:
        tabs = []
        num_, dx_, dy_ = 0.0, 0.0, 0.0
        for lev in LEVELS:
            m = mask(level=lev, task=t_)
            x, y = Y[a_][m].ravel(), Y[b_][m].ravel()
            ok = ~np.isnan(x) & ~np.isnan(y)
            x, y = x[ok], y[ok]
            num_ += ((x - x.mean()) * (y - y.mean())).sum()
            dx_ += ((x - x.mean()) ** 2).sum()
            dy_ += ((y - y.mean()) ** 2).sum()
        bytask[name_][t_] = round(float(num_ / np.sqrt(dx_ * dy_)), 3) if dx_ * dy_ > 0 else None
ex["within_cell_r_by_task"] = bytask
def gold_in_s1(r_):
    t_ = BR.norm(texts["s1", r_.level, r_.task, r_.q, r_.ins] or "")
    g_ = r_.gold
    k_ = BR.KIND[r_.task]
    if g_ is None or g_ != g_:
        return False
    if k_ == "date":
        return any(BR.same_date(v, g_) for _, v in BR.mentions(t_))
    if k_ == "iv":
        return all(any(BR.same_date(v, d_) for _, v in BR.mentions(t_)) for d_ in g_)
    if k_ == "n":
        return bool(re.search(rf"(?<![\d:-]){g_}(?![\d:-])", t_))
    if k_ == "wd":
        return any(BR.WEEKDAY.get(w_.casefold()) == g_ for w_ in re.findall(r"[A-Za-z]+|[ऀ-ॿ]+", t_))
    h_, m_ = g_ // 60, g_ % 60
    h12 = h_ % 12 or 12
    return bool(re.search(rf"(?<!\d)0?{h_}:{m_:02d}(?!\d)|(?<!\d)0?{h12}:{m_:02d}(?!\d)", t_))
gs = clp[clp["scored"]].copy()
gs["gold_in_s1"] = [gold_in_s1(r_) for r_ in gs.itertuples()]
gs["y"] = gs["correct"].astype(bool)
gis = {}
for t_ in TASKS:
    g = gs[gs["task"] == t_]
    gis[t_] = {"gold_in_s1": r1(100 * g["gold_in_s1"].mean()), "s2_correct": r1(100 * g["y"].mean()), "s2_given_gold_in_s1": r1(100 * g[g["gold_in_s1"]]["y"].mean()), "s2_given_not": r1(100 * g[~g["gold_in_s1"]]["y"].mean()), "n_not": int((~g["gold_in_s1"]).sum())}
ex["gold_string_in_stage1_by_task"] = gis
pd.DataFrame([{"task": k_, **v} for k_, v in gis.items()]).to_csv(FIG / "new_gold_in_stage1_by_task.csv", index=False)
hc = pd.read_csv(HERE / "hand_check_stage1.csv")
def wilson(k_, n_):
    z = 1.96
    p = k_ / n_
    c_ = (p + z * z / (2 * n_)) / (1 + z * z / n_)
    h_ = z * np.sqrt(p * (1 - p) / n_ + z * z / (4 * n_ * n_)) / (1 + z * z / n_)
    return [round(100 * float(c_ - h_), 1), round(100 * float(c_ + h_), 1)]
ex["hand_check_40"] = {"n": len(hc), "last_date_is_conclusion": int(hc["reader_correct"].sum()), "precision_pct": r1(100 * hc["reader_correct"].mean()), "precision_ci": wilson(int(hc["reader_correct"].sum()), len(hc)), "bin_correct": int(hc["bin_correct"].sum()), "bin_ci": wilson(int(hc["bin_correct"].sum()), len(hc)), "states_a_conclusion": int(hc["stage1_solves"].sum()), "solves_ci": wilson(int(hc["stage1_solves"].sum()), len(hc))}
hm = pd.read_csv(HERE / "hand_check_mentions.csv")
ex["hand_check_mentions"] = {k_: {"n": len(g), "true_mention": int(g["true_mention"].sum()), "precision": r1(100 * g["true_mention"].mean()), "ci": wilson(int(g["true_mention"].sum()), len(g))} for k_, g in hm.groupby("kind")}
hr = pd.read_csv(HERE / "hand_check_recoveries.csv")
ex["hand_check_recoveries"] = {"n": len(hr), "genuine": int(hr["genuine_recovery"].sum()), "ci": wilson(int(hr["genuine_recovery"].sum()), len(hr))}
pd.DataFrame([{"stage1_ends_at_gold": k_, **v} for k_, v in s2["date_tasks_by_stage1"].items()]).to_csv(FIG / "new_date_tasks_clp_vs_encot_by_stage1.csv", index=False)
pd.DataFrame([{"comparison": "cross", "pair": k_, "within_cell_r": agree[k_]["within_cell_r"], "lo": agree[k_]["within_cell_r_ci"][0], "hi": agree[k_]["within_cell_r_ci"][1], "mh_or": agree[k_]["mh_or"], "mh_lo": agree[k_]["mh_or_ci"][0], "mh_hi": agree[k_]["mh_or_ci"][1]} for k_ in list(agree)[:4]] + [{"comparison": "self_across_distractor", "pair": k_, "within_cell_r": ceil[k_]["within_cell_r"], "lo": sa[k_]["within_cell_r_ci"][0], "hi": sa[k_]["within_cell_r_ci"][1], "mh_or": ceil[k_]["mh_or"], "mh_lo": sa[k_]["mh_or_ci"][0], "mh_hi": sa[k_]["mh_or_ci"][1]} for k_ in sa]).to_csv(FIG / "new_agreement_vs_self.csv", index=False)
pcl = phi_cells(Y["clp"], Y["en_cot"])
ex["phi_missing_cells_clp_en"] = [{"cell": f"{r_.level}/{r_.task}", "clp_acc": round(100 * r_.px, 1), "en_cot_acc": round(100 * r_.py, 1)} for r_ in pcl[pcl["phi"].isna()].itertuples()]
pch = phi_cells(Y["hi_cot"], Y["en_cot"])
ex["phi_missing_cells_hi_en"] = [{"cell": f"{r_.level}/{r_.task}", "hi_cot_acc": round(100 * r_.px, 1), "en_cot_acc": round(100 * r_.py, 1)} for r_ in pch[pch["phi"].isna()].itertuples()]
def fisher_rate(k1, n1, k2, n2):
    return float(fisher_exact([[k1, n1 - k1], [k2, n2 - k2]])[1])
ex["task_failures_significance"] = {"dow_plus1_clp_vs_hi_cot_p": fisher_rate(round(dow["clp"]["plus1"] * dow["clp"]["n"] / 100), dow["clp"]["n"], round(dow["hi_cot"]["plus1"] * dow["hi_cot"]["n"] / 100), dow["hi_cot"]["n"]), "recurrence_mirror_clp_vs_hi_cot_p": fisher_rate(round(rec_["clp"]["mirror"] * rec_["clp"]["n"] / 100), rec_["clp"]["n"], round(rec_["hi_cot"]["mirror"] * rec_["hi_cot"]["n"] / 100), rec_["hi_cot"]["n"]), "recurrence_mirror_clp_vs_encot_p": fisher_rate(round(rec_["clp"]["mirror"] * rec_["clp"]["n"] / 100), rec_["clp"]["n"], round(rec_["encot"]["mirror"] * rec_["encot"]["n"] / 100), rec_["encot"]["n"])}
cfg = Counter()
lrule = 0
for lev in LEVELS:
    for rec in json.load(open(ROOT / "responses" / "clp" / f"{lev}.json", encoding="utf-8")):
        for st_ in ("stage1", "stage2"):
            q_ = rec[st_]["request"]
            cfg[(q_["model"], q_["temperature"], q_["top_p"], q_["max_tokens"], q_["reasoning_effort"])] += 1
        cfg["stage2_history_contains_stage1"] += rec["stage2"]["request"]["messages"][1]["content"] == (rec["stage1"]["content"] or "")
        lrule += bool(re.search(r"entire response|in English as requested|written in English|write my|respond entirely in English", rec["stage1"]["content"] or "", re.I))
ex["clp_request_settings"] = {str(k_): v for k_, v in cfg.items()}
ex["stage1_echoes_language_rule_pct"] = r1(100 * lrule / 6750)
fg = json.load(open(ROOT / "experiments" / "2026-10-27_full-grid-analysis" / "outputs" / "full" / "numbers.json", encoding="utf-8"))
ex["pipeline_full_numbers_keys"] = sorted(fg)[:40]
NUM["extras"] = ex

with open(HERE / "numbers.json", "w", encoding="utf-8") as f:
    json.dump(NUM, f, indent=2, ensure_ascii=False, default=lambda o: o.item() if hasattr(o, "item") else str(o))
print("done")
