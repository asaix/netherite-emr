import json
import re
import sys

import statsmodels.api as sm
from scipy.stats import norm as Z
from statsmodels.stats.contingency_tables import StratifiedTable

from build import DEV
from common import *

NUM = {}
df = load()
s, qlist = subset(df)
Q = len(qlist)
W2 = weights(Q, 2000, 0)
W = weights(Q, 10000, 20261031)
A = Boot(s, W, Q)
ST = Boot(s, W, Q, strict=True)
A0 = Boot(s, W2, Q)
LV = {d: i for i, d in enumerate(DIFFS)}


def M(**k):
    return np.logical_and.reduce([(s[a] == v).to_numpy() for a, v in k.items()]) if k else np.ones(len(s), bool)


def save(rows, name):
    d = pd.DataFrame(rows)
    d.to_csv(TAB / f"{name}.csv", index=False)
    print(f"\n== {name}\n" + d.to_string(index=False, max_colwidth=60))
    return d


def p100(x, n=1):
    return round(100 * float(x), n)


def wilson(k, n):
    from statsmodels.stats.proportion import proportion_confint
    return tuple(round(100 * x, 1) for x in proportion_confint(k, n, method="wilson")) if n else (None, None)


def c1():
    rows, tests = [], {}
    for t in TASKS + ["all"]:
        base = M(task=t) if t != "all" else M()
        d = s[base]
        r = {"task": t, **{c: p100(A.acc(base & M(C=c))) for c in CONDS}}
        for c in CONDS:
            r[f"strict {c}"] = p100(ST.acc(base & M(C=c)))
        for ref in ("Hindi CoT", "Hindi direct", "Hindi CLP", "English CoT"):
            x, y, p = mcnemar(d, "Hindi en-CoT", ref)
            r[f"d {ref}"] = p100(A.acc(base & M(C="Hindi en-CoT")) - A.acc(base & M(C=ref)))
            lo, hi = ci(A.boot(base & M(C="Hindi en-CoT")) - A.boot(base & M(C=ref)))
            r[f"ci {ref}"] = f"[{lo:+.1f}, {hi:+.1f}]"
            r[f"only {ref}"] = f"{x}/{y}"
            r[f"p {ref}"] = p
            tests.setdefault(ref, []).append(p)
        rows.append(r)
    for ref, ps in tests.items():
        for r, h in zip(rows, list(holm(ps[:-1])) + [ps[-1]]):
            r[f"holm {ref}"] = float(h)
    out = save(rows, "c1_by_task")
    out[["task"] + CONDS].to_csv(FIG / "figC2_accuracy_by_task.csv", index=False)
    rows = []
    for c in CONDS:
        d = s[M(C=c)]
        rows.append({"cond": c, "n": len(d), "answered": int(d.scored.sum()), "unanswered": int((~d.scored).sum()),
                     "unanswered_length": int(((~d.scored) & (d.finish == "length")).sum()),
                     "unanswered_stop": int(((~d.scored) & (d.finish != "length")).sum()),
                     "length_total": int((d.finish == "length").sum()), "answered_but_length": int((d.scored & (d.finish == "length")).sum()),
                     "answered_but_length_correct": int((d.correct & (d.finish == "length")).sum()),
                     "answered_acc": p100(d[d.scored].correct.mean()), "strict_acc": p100(d.correct.mean()),
                     "multi_answer_lines": int((d.n_answers > 1).sum())})
    save(rows, "c1_cutoffs")
    rows = []
    for c in ("English CoT", "Hindi CoT", "Hindi CLP", "Hindi en-CoT"):
        for by in ("task", "difficulty", "ins"):
            for k, g in s[M(C=c)].groupby(by):
                rows.append({"cond": c, "by": by, "key": k, "n": len(g), "unanswered": int((~g.scored).sum()), "pct": p100((~g.scored).mean())})
    save(rows, "c1_cutoffs_by").pivot_table(index=["by", "key"], columns="cond", values="unanswered")
    rows = []
    for ref in ("Hindi CoT", "Hindi direct", "Hindi CLP", "English CoT"):
        for name, a in (("answered", A), ("strict", ST)):
            for ins in ["pooled"] + INS:
                m = M() if ins == "pooled" else M(ins=ins)
                lo, hi = ci(a.boot(m & M(C="Hindi en-CoT")) - a.boot(m & M(C=ref)))
                rows.append({"ref": ref, "convention": name, "ins": ins, "en-CoT": p100(a.acc(m & M(C="Hindi en-CoT"))), "ref acc": p100(a.acc(m & M(C=ref))),
                             "diff": p100(a.acc(m & M(C="Hindi en-CoT")) - a.acc(m & M(C=ref))), "lo": lo, "hi": hi})
    save(rows, "c1_headline_by_distractor")
    rows = []
    for ref in ("Hindi CoT", "Hindi CLP", "Hindi direct"):
        for ins in INS:
            ps, ds_ = [], []
            for t in TASKS:
                d = s[M(task=t, ins=ins)]
                ps.append(mcnemar(d, "Hindi en-CoT", ref)[2])
                ds_.append(p100(A.acc(M(task=t, ins=ins, C="Hindi en-CoT")) - A.acc(M(task=t, ins=ins, C=ref))))
            h = holm(ps)
            for t, x, p in zip(TASKS, ds_, h):
                rows.append({"ref": ref, "ins": ins, "task": t, "diff": x, "holm9": float(p), "sig": bool(p < .05)})
    out = save(rows, "c1_task_by_distractor")
    print(out.groupby(["ref", "ins"]).sig.sum())
    rows = []
    for ref in ("Hindi CoT", "Hindi CLP", "Hindi direct"):
        for lv in DIFFS:
            ps, ds_ = [], []
            for t in TASKS:
                d = s[M(task=t, difficulty=lv)]
                ps.append(mcnemar(d, "Hindi en-CoT", ref)[2])
                ds_.append(p100(A.acc(M(task=t, difficulty=lv, C="Hindi en-CoT")) - A.acc(M(task=t, difficulty=lv, C=ref))))
            h = holm(ps)
            for t, x, p in zip(TASKS, ds_, h):
                rows.append({"ref": ref, "level": lv, "task": t, "diff": x, "holm9": float(p), "sig": bool(p < .05)})
    out = save(rows, "c1_task_by_level")
    print(out.groupby(["ref", "level"]).sig.sum())
    m = M(task="interval_date")
    g = A.boot(m & M(C="Hindi en-CoT")) - A.boot(m & M(C="Hindi direct"))
    NUM["interval_vs_direct"] = {"diff": p100(A.acc(m & M(C="Hindi en-CoT")) - A.acc(m & M(C="Hindi direct"))), "ci95": ci(g),
                                 "ci90": [p100(np.percentile(g, 5)), p100(np.percentile(g, 95))], "mcnemar": mcnemar(s[m], "Hindi en-CoT", "Hindi direct"),
                                 "strict": p100(ST.acc(m & M(C="Hindi en-CoT")) - ST.acc(m & M(C="Hindi direct"))),
                                 "strict_ci": ci(ST.boot(m & M(C="Hindi en-CoT")) - ST.boot(m & M(C="Hindi direct")))}
    rows = []
    for lv in DIFFS + INS:
        k = {"difficulty": lv} if lv in DIFFS else {"ins": lv}
        mm = m & M(**k)
        g = A.boot(mm & M(C="Hindi en-CoT")) - A.boot(mm & M(C="Hindi direct"))
        rows.append({"cut": lv, "en-CoT": p100(A.acc(mm & M(C="Hindi en-CoT"))), "direct": p100(A.acc(mm & M(C="Hindi direct"))), "Hi CoT": p100(A.acc(mm & M(C="Hindi CoT"))), "En CoT": p100(A.acc(mm & M(C="English CoT"))),
                     "diff": p100(A.acc(mm & M(C="Hindi en-CoT")) - A.acc(mm & M(C="Hindi direct"))), "ci": ci(g), **dict(zip(("only en", "only dir", "p"), mcnemar(s[mm], "Hindi en-CoT", "Hindi direct")))})
    save(rows, "c1_interval_vs_direct")


def c2():
    rows = []
    for lv in DIFFS:
        m = M(difficulty=lv)
        r = {"level": lv, **{c: p100(A.acc(m & M(C=c))) for c in CONDS}}
        for c in ("Hindi CoT", "Hindi CLP", "Hindi en-CoT"):
            r[f"gap {c}"] = p100(A.acc(m & M(C="English CoT")) - A.acc(m & M(C=c)))
            r[f"ci2000seed0 {c}"] = ci(A0.boot(m & M(C="English CoT")) - A0.boot(m & M(C=c)))
            r[f"ci10000 {c}"] = ci(A.boot(m & M(C="English CoT")) - A.boot(m & M(C=c)))
            r[f"strict gap {c}"] = p100(ST.acc(m & M(C="English CoT")) - ST.acc(m & M(C=c)))
            r[f"strict ci {c}"] = ci(ST.boot(m & M(C="English CoT")) - ST.boot(m & M(C=c)))
        for c in CONDS:
            r[f"ci acc {c}"] = ci(A.boot(m & M(C=c)))
        rows.append(r)
    out = save(rows, "c2_by_level")
    fig = []
    for r in rows:
        for c in CONDS:
            fig.append({"level": r["level"], "condition": c, "accuracy": r[c], "lo": r[f"ci acc {c}"][0], "hi": r[f"ci acc {c}"][1]})
    pd.DataFrame(fig).to_csv(FIG / "figC1_accuracy_by_level.csv", index=False)
    rows = []
    for ins in INS:
        for lv in DIFFS:
            m = M(difficulty=lv, ins=ins)
            for c in ("Hindi CoT", "Hindi en-CoT"):
                rows.append({"ins": ins, "level": lv, "cond": c, "gap": p100(A.acc(m & M(C="English CoT")) - A.acc(m & M(C=c))), "ci": ci(A.boot(m & M(C="English CoT")) - A.boot(m & M(C=c)))})
    save(rows, "c2_gap_level_by_distractor")


def gaps(boot_obj, base, c):
    g = []
    for lv in DIFFS:
        m = base & M(difficulty=lv)
        g.append(boot_obj.boot(m & M(C="English CoT")) - boot_obj.boot(m & M(C=c)))
    return np.stack(g, 1)


def point(boot_obj, base, c):
    return np.array([boot_obj.acc(base & M(difficulty=lv, C="English CoT")) - boot_obj.acc(base & M(difficulty=lv, C=c)) for lv in DIFFS])


def trend_row(label, a, base, c):
    pt = point(a, base, c)
    g = gaps(a, base, c)
    x = np.arange(5) - 2.0
    slope = g @ x / (x @ x)
    d = g[:, 0] - g[:, 4]
    d13 = g[:, 0] - g[:, 1:].mean(1)
    return {"cut": label, "cond": c, **{lv: p100(v) for lv, v in zip(DIFFS, pt)},
            "short-vvl": p100(pt[0] - pt[4]), "ci short-vvl": ci(d), "p boot": round(float(2 * min((d <= 0).mean(), (d >= 0).mean())), 4),
            "slope/level": p100(pt @ x / (x @ x), 2), "ci slope": ci(slope, 2), "p slope": round(float(2 * min((slope <= 0).mean(), (slope >= 0).mean())), 4),
            "short-rest": p100(pt[0] - pt[1:].mean()), "ci short-rest": ci(d13)}


def trend():
    all_m = M()
    norec = ~M(task="date_recurrence")
    k = s.rec_k.to_numpy(dtype=float)
    k12 = ~(M(task="date_recurrence") & (k <= 2))
    k1234 = ~(M(task="date_recurrence") & (k <= 4))
    nodow = ~M(task="day_of_week")
    rows = []
    for c in ("Hindi en-CoT", "Hindi CoT", "Hindi CLP"):
        rows.append(trend_row("all answered", A, all_m, c))
        rows.append(trend_row("all strict", ST, all_m, c))
    for label, base in (("no recurrence", norec), ("no recurrence k<=2", k12), ("no recurrence k<=4", k1234), ("no day_of_week", nodow), ("no rec, no dow", norec & nodow)):
        for name, a in (("answered", A), ("strict", ST)):
            rows.append(trend_row(f"{label} {name}", a, base, "Hindi en-CoT"))
    for ins in INS:
        for name, a in (("answered", A), ("strict", ST)):
            rows.append(trend_row(f"{ins} {name}", a, M(ins=ins), "Hindi en-CoT"))
    for t in TASKS:
        rows.append(trend_row(f"only {t} answered", A, M(task=t), "Hindi en-CoT"))
    for t in TASKS:
        rows.append(trend_row(f"drop {t} answered", A, ~M(task=t), "Hindi en-CoT"))
    out = save(rows, "c3_trend")
    only = out[out.cut.str.startswith("only")]
    NUM["trend_only_task_holm"] = dict(zip(only.cut, [float(x) for x in holm(np.maximum(only["p slope"].to_numpy(), 1e-4))]))
    print(NUM["trend_only_task_holm"])
    rows = []
    for c in CONDS:
        for lv in DIFFS:
            rows.append({"cond": c, "level": lv, "answered": p100(A.acc(M(C=c, difficulty=lv))), "strict": p100(ST.acc(M(C=c, difficulty=lv)))})
    d = pd.DataFrame(rows)
    change = {}
    for c in ("English CoT", "Hindi en-CoT", "Hindi CoT", "Hindi CLP"):
        x = A.boot(M(C=c, difficulty="short")) - A.boot(M(C=c, difficulty="very_very_long"))
        y = ST.boot(M(C=c, difficulty="short")) - ST.boot(M(C=c, difficulty="very_very_long"))
        change[c] = {"answered": p100(A.acc(M(C=c, difficulty="short")) - A.acc(M(C=c, difficulty="very_very_long"))), "ci": ci(x),
                     "strict": p100(ST.acc(M(C=c, difficulty="short")) - ST.acc(M(C=c, difficulty="very_very_long"))), "strict_ci": ci(y)}
    NUM["decline_short_to_vvl"] = change
    print(change)
    x = s[M(C="English CoT") | M(C="Hindi en-CoT")]
    x = x[x.scored].copy()
    x["en"] = (x.C == "English CoT").astype(float)
    x["lvl"] = x.difficulty.map(LV) - 2.0
    x["y"] = x.correct.astype(float)
    X = pd.get_dummies(x.task, drop_first=True, dtype=float)
    X["en"], X["lvl"], X["en_lvl"] = x.en, x.lvl, x.en * x.lvl
    X = sm.add_constant(X)
    g = sm.GEE(x.y, X, groups=x.qi, family=sm.families.Binomial(), cov_struct=sm.cov_struct.Exchangeable()).fit()
    NUM["gee_logit_en_x_level_task_fe"] = {"coef": float(g.params["en_lvl"]), "se": float(g.bse["en_lvl"]), "p": float(g.pvalues["en_lvl"])}
    no = x[x.task != "date_recurrence"]
    X = pd.get_dummies(no.task, drop_first=True, dtype=float)
    X["en"], X["lvl"], X["en_lvl"] = no.en, no.lvl, no.en * no.lvl
    X = sm.add_constant(X)
    g = sm.GEE(no.y, X, groups=no.qi, family=sm.families.Binomial(), cov_struct=sm.cov_struct.Exchangeable()).fit()
    NUM["gee_logit_no_recurrence"] = {"coef": float(g.params["en_lvl"]), "se": float(g.bse["en_lvl"]), "p": float(g.pvalues["en_lvl"])}
    print(NUM["gee_logit_en_x_level_task_fe"], NUM["gee_logit_no_recurrence"])
    rows = []
    for t in TASKS:
        for lv in DIFFS:
            m = M(task=t, difficulty=lv)
            rows.append({"task": t, "level": lv, "En CoT": p100(A.acc(m & M(C="English CoT"))), "en-CoT": p100(A.acc(m & M(C="Hindi en-CoT"))), "Hi CoT": p100(A.acc(m & M(C="Hindi CoT"))), "gap en-CoT": p100(A.acc(m & M(C="English CoT")) - A.acc(m & M(C="Hindi en-CoT"))),
                         "ci": ci(A.boot(m & M(C="English CoT")) - A.boot(m & M(C="Hindi en-CoT"))), "En unanswered": int((~s[m & M(C="English CoT")].scored).sum()), "en-CoT unanswered": int((~s[m & M(C="Hindi en-CoT")].scored).sum())})
    save(rows, "c3_gap_task_level")
    r = pd.DataFrame(rows).pivot(index="task", columns="level", values="gap en-CoT")[DIFFS].loc[TASKS]
    r.to_csv(FIG / "new_gap_task_level_heatmap.csv")
    print(r)
    rows = []
    for lv in DIFFS:
        pt = {t: (A.acc(M(task=t, difficulty=lv, C="English CoT")) - A.acc(M(task=t, difficulty=lv, C="Hindi en-CoT"))) for t in TASKS}
        tot = A.acc(M(difficulty=lv, C="English CoT")) - A.acc(M(difficulty=lv, C="Hindi en-CoT"))
        rows.append({"level": lv, "gap": p100(tot), **{t: p100(v / 9) for t, v in pt.items()}})
    save(rows, "c3_gap_contribution_points")


def part_a():
    tg = {("short", "Hindi CoT"): (20.7, 27.0), ("short", "Hindi CLP"): (13.0, 19.0), ("medium", "Hindi CoT"): (23.3, 29.1), ("medium", "Hindi CLP"): (13.3, 18.7),
          ("long", "Hindi CoT"): (25.7, 32.1), ("long", "Hindi CLP"): (15.2, 20.7), ("very_long", "Hindi CoT"): (30.1, 36.8), ("very_long", "Hindi CLP"): (18.4, 24.5),
          ("very_very_long", "Hindi CoT"): (31.6, 38.5), ("very_very_long", "Hindi CLP"): (18.1, 24.6)}
    pc = {("short", "Hindi CoT"): (20.6, 26.7), ("medium", "Hindi CoT"): (23.3, 29.0), ("long", "Hindi CoT"): (25.7, 32.2), ("very_long", "Hindi CoT"): (30.1, 37.0), ("very_very_long", "Hindi CoT"): (31.5, 38.4)}
    ends = {k: [] for k in tg}
    for seed in range(100):
        w_ = weights(Q, 2000, 5000 + seed)
        b_ = Boot(s, w_, Q)
        for (lv, c) in tg:
            ends[lv, c].append(ci(b_.boot(M(difficulty=lv, C="English CoT")) - b_.boot(M(difficulty=lv, C=c))))
    rows = []
    for (lv, c), t in tg.items():
        e = np.array(ends[lv, c])
        long_ = ci(A.boot(M(difficulty=lv, C="English CoT")) - A.boot(M(difficulty=lv, C=c)))
        rows.append({"level": lv, "cond": c, "part_A": t, "part_C": pc.get((lv, c)), "seed0_2000": ci(A0.boot(M(difficulty=lv, C="English CoT")) - A0.boot(M(difficulty=lv, C=c))),
                     "single_B10000": long_, "mc_sd_lo": round(float(e[:, 0].std()), 3), "mc_sd_hi": round(float(e[:, 1].std()), 3),
                     "seed_range_lo": (e[:, 0].min(), e[:, 0].max()), "seed_range_hi": (e[:, 1].min(), e[:, 1].max()),
                     "partA_in_range": bool(e[:, 0].min() <= t[0] <= e[:, 0].max() and e[:, 1].min() <= t[1] <= e[:, 1].max())})
    save(rows, "ci_partA_vs_partC")


def mh(sub, yes, right="correct"):
    tables = []
    for _, g in sub.groupby(["task", "difficulty"]):
        e, c = g[yes].astype(bool), g[right].astype(bool)
        t = np.array([[(e & c).sum(), (e & ~c).sum()], [(~e & c).sum(), (~e & ~c).sum()]], dtype=float)
        if t[0].sum() and t[1].sum():
            tables.append(t)
    st = StratifiedTable(tables)
    lo, hi = st.oddsratio_pooled_confint()
    return round(float(st.oddsratio_pooled), 2), round(float(lo), 2), round(float(hi), 2), len(tables)


def drop_row(a, base, c, ins):
    n, m = base & M(C=c, ins="no_insertion"), base & M(C=c, ins=ins)
    use = (n | m) if a.strict else (n | m) & s.scored.to_numpy()
    w = s[use].pivot_table(index="qid", columns="ins", values="correct", aggfunc="first").dropna().astype(bool)
    x, y = int((w["no_insertion"] & ~w[ins]).sum()), int((~w["no_insertion"] & w[ins]).sum())
    return {"none": p100(a.acc(n)), "with": p100(a.acc(m)), "drop": p100(a.acc(n) - a.acc(m)), "ci": ci(a.boot(n) - a.boot(m)), "lost": x, "gained": y, "p": binomtest(x, x + y).pvalue if x + y else 1.0}


def dist():
    rows = []
    for c in CONDS:
        for ins in INS[1:]:
            for name, a in (("answered", A), ("strict", ST)):
                r = {"cond": c, "ins": ins, "conv": name, **drop_row(a, M(), c, ins)}
                r["ci_seed0_2000"] = ci((A0 if name == "answered" else Boot(s, W2, Q, True)).boot(M(C=c, ins="no_insertion")) - (A0 if name == "answered" else Boot(s, W2, Q, True)).boot(M(C=c, ins=ins)))
                rows.append(r)
    out = pd.DataFrame(rows)
    for name in ("answered", "strict"):
        idx = out.conv == name
        out.loc[idx, "holm12"] = holm(out.loc[idx, "p"].to_numpy())
    out.to_csv(TAB / "c4_drops.csv", index=False)
    print(out.to_string())
    out[out.conv == "answered"][["cond", "ins", "none", "with", "drop", "ci"]].to_csv(FIG / "new_distractor_drops.csv", index=False)
    rows = []
    pairs = [("Hindi en-CoT", "Hindi direct"), ("Hindi CoT", "Hindi direct"), ("Hindi CLP", "Hindi direct"), ("English CoT", "English direct"), ("Hindi en-CoT", "Hindi CoT"), ("Hindi en-CoT", "Hindi CLP"), ("Hindi en-CoT", "English CoT")]
    for c, ref in pairs:
        for ins in INS[1:]:
            for name, a in (("answered", A), ("strict", ST)):
                g = (a.boot(M(C=c, ins="no_insertion")) - a.boot(M(C=c, ins=ins))) - (a.boot(M(C=ref, ins="no_insertion")) - a.boot(M(C=ref, ins=ins)))
                pt = (a.acc(M(C=c, ins="no_insertion")) - a.acc(M(C=c, ins=ins))) - (a.acc(M(C=ref, ins="no_insertion")) - a.acc(M(C=ref, ins=ins)))
                rows.append({"cond": c, "vs": ref, "ins": ins, "conv": name, "did": p100(pt), "ci": ci(g), "p_boot": round(float(2 * min((g <= 0).mean(), (g >= 0).mean())), 4)})
    d = pd.DataFrame(rows)
    d["holm_within_conv"] = 1.0
    for name in ("answered", "strict"):
        idx = d.conv == name
        d.loc[idx, "holm_within_conv"] = holm(np.maximum(d.loc[idx, "p_boot"].to_numpy(), 1e-4))
    d.to_csv(TAB / "c4_penalty_did.csv", index=False)
    print(d.to_string())
    rows = []
    for c in ("Hindi en-CoT", "English CoT", "Hindi CoT", "Hindi direct", "Hindi CLP"):
        for t in TASKS:
            rows.append({"cond": c, "task": t, **drop_row(A, M(task=t), c, "similar_insertion")})
    d = pd.DataFrame(rows)
    d["holm9"] = d.groupby("cond").p.transform(lambda x: holm(x.to_numpy()))
    d.to_csv(TAB / "c4_similar_by_task.csv", index=False)
    print(d.to_string())
    rows = []
    for t in TASKS:
        rows.append({"dropped": t, **drop_row(A, ~M(task=t), "Hindi en-CoT", "similar_insertion")})
    print(save(rows, "c4_similar_leave_one_task").to_string())
    rows = []
    for lv in DIFFS:
        rows.append({"level": lv, **drop_row(A, M(difficulty=lv), "Hindi en-CoT", "similar_insertion")})
    save(rows, "c4_similar_by_level")
    rows = []
    e = s[M(C="Hindi en-CoT")]
    base = e[e.ins == "no_insertion"].set_index("qid")
    for c in ("Hindi en-CoT", "English CoT", "Hindi CoT", "Hindi direct"):
        x = s[M(C=c)]
        base = x[x.ins == "no_insertion"].set_index("qid")
        lang_col = "hi" if c != "English CoT" else "en"
        for (t, sent), g in x[x.ins == "similar_insertion"].groupby(["task", "sentence"]):
            j = g.set_index("qid").join(base[["scored", "correct", "finish"]], rsuffix="_0")
            j2 = j[j.scored & j.scored_0]
            lost, gained = int((j2.correct_0 & ~j2.correct).sum()), int((~j2.correct_0 & j2.correct).sum())
            rows.append({"cond": c, "task": t, "sentence": sent, "n": len(j), "acc_none": p100(j2.correct_0.mean()) if len(j2) else None, "acc_with": p100(j2.correct.mean()) if len(j2) else None,
                         "lost": lost, "gained": gained, "p": binomtest(lost, lost + gained).pvalue if lost + gained else 1.0, "cutoff_with": int((j.finish == "length").sum()), "cutoff_none": int((j.finish_0 == "length").sum())})
    d = pd.DataFrame(rows)
    d["holm_within_cond"] = d.groupby("cond").p.transform(lambda x: holm(x.to_numpy()))
    d.to_csv(TAB / "c4_similar_by_sentence.csv", index=False)
    print(d[d.cond == "Hindi en-CoT"].sort_values("p").head(15).to_string())
    print(d[(d.holm_within_cond < .05)].to_string())
    rows = []
    for name, sub in (("first50", df[(df.source == "standard") & (df.qn < 50)]), ("rest100", df[(df.source == "standard") & (df.qn >= 50)]), ("all150", df[df.source == "standard"])):
        for (lang, cond), g in sub.groupby(["lang", "cond"]):
            a = g[g.scored].groupby("ins").correct.mean()
            rows.append({"set": name, "lang": lang, "cond": cond, **{i: p100(a[i]) for i in INS}, "drop_sim": p100(a[INS[0]] - a[INS[1]]), "drop_dis": p100(a[INS[0]] - a[INS[2]])})
    save(rows, "c4_drops_full_grid_context")


def mentions():
    rows = []
    for c in ("English CoT", "Hindi CoT", "Hindi en-CoT"):
        g = s[M(C=c) & s.scored.to_numpy()]
        for set_ in ("own", "hi", "en", "both"):
            for name in ("similar", "dissimilar"):
                col = f"m_{name}_{set_}"
                hit = g[g.ins == f"{name}_insertion"].dropna(subset=[col])
                plc = g[g.ins == "no_insertion"].dropna(subset=[col])
                h, p = hit[col].astype(bool), plc[col].astype(bool)
                dh = np.bincount(hit.qi, weights=h.astype(float), minlength=Q)
                kh = np.bincount(hit.qi, minlength=Q).astype(float)
                dp = np.bincount(plc.qi, weights=p.astype(float), minlength=Q)
                kp = np.bincount(plc.qi, minlength=Q).astype(float)
                net = (W @ dh) / (W @ kh) - (W @ dp) / (W @ kp)
                o = mh(hit.assign(m=h), "m") if set_ in ("own", "both") else (None, None, None, None)
                rows.append({"cond": c, "words": set_, "ins": name, "n": len(hit), "mention": p100(h.mean()), "placebo": p100(p.mean()), "net": p100(h.mean() - p.mean()), "net_ci": ci(net), "OR": o[:3], "strata": o[3]})
    d = save(rows, "c4_mentions")
    d.to_csv(FIG / "new_mentions_by_wordset.csv", index=False)


def within_corr(w, a, b, cell):
    x = w[a].astype(float) - w.groupby(cell)[a].transform("mean").astype(float)
    y = w[b].astype(float) - w.groupby(cell)[b].transform("mean").astype(float)
    return float((x * y).sum() / np.sqrt((x * x).sum() * (y * y).sum()))


def agree_row(w, a, b):
    ww = w.reset_index()
    ww["cell"] = ww.task + "/" + ww.difficulty
    tab = np.array([[(ww[a] & ww[b]).sum(), (ww[a] & ~ww[b]).sum()], [(~ww[a] & ww[b]).sum(), (~ww[a] & ~ww[b]).sum()]], dtype=float)
    phis = []
    for _, g in ww.groupby("cell"):
        if g[a].astype(float).std() > 0 and g[b].astype(float).std() > 0:
            phis.append(np.corrcoef(g[a].astype(float), g[b].astype(float))[0, 1])
    pooled = within_corr(ww, a, b, "cell")
    raw = np.corrcoef(ww[a].astype(float), ww[b].astype(float))[0, 1]
    tables = []
    for _, g in ww.groupby("cell"):
        t = np.array([[(g[a] & g[b]).sum(), (g[a] & ~g[b]).sum()], [(~g[a] & g[b]).sum(), (~g[a] & ~g[b]).sum()]], dtype=float)
        tables.append(t)
    st = StratifiedTable(tables)
    lo, hi = st.oddsratio_pooled_confint()
    pwgr = ww[~ww[a]][b].mean()
    pwgw = ww[ww[a]][b].mean()
    hw = (~ww[b]).astype(float)
    er = ((~ww[a]) & (~ww[b])).sum() / ((~ww[a]) | (~ww[b])).sum()
    pe = ((~ww[a]).mean() * (~ww[b]).mean())
    jexp = pe / ((~ww[a]).mean() + (~ww[b]).mean() - pe)
    return {"pairs": len(ww), "both right": int(tab[0, 0]), "both wrong": int(tab[1, 1]), "only ref": int(tab[0, 1]), "only cond": int(tab[1, 0]),
            "phi cells": len(phis), "median phi": round(float(np.median(phis)), 2), "iqr": [round(float(x), 2) for x in np.percentile(phis, [25, 75])],
            "raw phi": round(float(raw), 3), "within-cell phi (all cells)": round(pooled, 3), "MH OR": round(float(st.oddsratio_pooled), 2), "MH CI": (round(float(lo), 2), round(float(hi), 2)),
            "P(cond right|ref wrong)": p100(pwgr), "P(cond right|ref right)": p100(pwgw), "P(ref right|cond wrong)": p100(ww[~ww[b]][a].mean()), "jaccard errors": round(float(er), 3), "jaccard expected indep": round(float(jexp), 3)}


def agree():
    rows, boots = [], {}
    idx = ["qid", "ins", "task", "difficulty"]
    for c, ref in (("Hindi direct", "English direct"), ("Hindi CoT", "English CoT"), ("Hindi en-CoT", "English CoT"), ("Hindi CLP", "English CoT"), ("Hindi en-CoT", "Hindi CoT"), ("Hindi en-CoT", "Hindi CLP")):
        w = pair_table(s, ref, c, extra=("task", "difficulty"))
        r = {"cond": c, "ref": ref, **agree_row(w, ref, c)}
        ww = w.reset_index()
        ww["cell"] = ww.task + "/" + ww.difficulty
        ww["qi"] = ww.qid.map({q: i for i, q in enumerate(qlist)})
        for col in (ref, c):
            ww[col + "_d"] = ww[col].astype(float) - ww.groupby("cell")[col].transform(lambda v: v.astype(float).mean())
        xy = np.bincount(ww.qi, weights=ww[ref + "_d"] * ww[c + "_d"], minlength=Q)
        xx = np.bincount(ww.qi, weights=ww[ref + "_d"] ** 2, minlength=Q)
        yy = np.bincount(ww.qi, weights=ww[c + "_d"] ** 2, minlength=Q)
        cc = (W @ xy) / np.sqrt((W @ xx) * (W @ yy))
        r["within phi CI"] = tuple(np.round(np.percentile(cc, [2.5, 97.5]), 3))
        boots[c, ref] = cc
        rec = ww[(ww.task != "date_recurrence")]
        r["within phi no recurrence"] = round(within_corr(rec, ref, c, "cell"), 3)
        b1 = s[(s.C == c) & s.scored].set_index(["qid", "ins"])["answer"]
        b2 = s[(s.C == ref) & s.scored].set_index(["qid", "ins"])["answer"]
        wrong = ww[(~ww[ref]) & (~ww[c])].set_index(["qid", "ins"])
        a1, a2 = b1.reindex(wrong.index), b2.reindex(wrong.index)
        same = np.array([str(x).casefold() == str(y).casefold() for x, y in zip(a1, a2)])
        r["both wrong same answer %"] = p100(same.mean())
        rows.append(r)
    d = save(rows, "c5_agreement")
    d.to_csv(FIG / "new_error_overlap.csv", index=False)
    x = boots["Hindi en-CoT", "English CoT"] - boots["Hindi CoT", "English CoT"]
    NUM["within_phi_enCoT_minus_HiCoT"] = {"ci": tuple(np.round(np.percentile(x, [2.5, 97.5]), 3))}
    print(NUM["within_phi_enCoT_minus_HiCoT"])
    rows = []
    for c in ("English CoT", "Hindi CoT", "Hindi en-CoT", "Hindi CLP"):
        d_ = s[M(C=c) & s.scored.to_numpy()].pivot_table(index=["qid", "task", "difficulty"], columns="ins", values="correct", aggfunc="first").dropna().astype(bool)
        for i, j in (("no_insertion", "similar_insertion"), ("no_insertion", "dissimilar_insertion")):
            w = d_.reset_index()
            w["cell"] = w.task + "/" + w.difficulty
            rows.append({"cond": c, "a": i, "b": j, "n": len(w), "within phi": round(within_corr(w, i, j, "cell"), 3)})
    save(rows, "c5_self_ceiling")
    rows = []
    for c, ref in (("Hindi CoT", "English CoT"), ("Hindi en-CoT", "English CoT")):
        w = pair_table(s, ref, c, extra=("task", "difficulty")).reset_index()
        w["cell"] = w.task + "/" + w.difficulty
        for t, g in w.groupby("task"):
            rows.append({"cond": c, "task": t, "n": len(g), "within phi": round(within_corr(g, ref, c, "cell"), 3), "P(right|ref wrong)": p100(g[~g[ref]][c].mean()), "P(right|ref right)": p100(g[g[ref]][c].mean())})
    save(rows, "c5_within_phi_by_task")
    rows = []
    for c in ("English CoT", "Hindi CoT", "Hindi CLP", "Hindi en-CoT"):
        g = s[M(C=c) & s.scored.to_numpy()]
        wrong = g[~g.correct]
        r = {"cond": c, "off_by_one_share": p100((wrong.err == "off_by_one").mean()), "wrong": len(wrong), "median_tokens": float(g.ctok.median()), "verif": p100(g.verif.mean()), "verif_wide": p100(g.verif_wide.mean())}
        for t in TASKS:
            w = wrong[wrong.task == t]
            r[f"o1 {t}"] = p100((w.err == "off_by_one").mean()) if len(w) else None
            r[f"nw {t}"] = len(w)
        std = np.nanmean([r[f"o1 {t}"] for t in TASKS])
        r["off_by_one_task_std"] = round(float(std), 1)
        r["wrong_share_dow"] = p100((wrong.task == "day_of_week").mean())
        r["wrong_share_interval"] = p100((wrong.task == "interval_date").mean())
        r["o1 excl weekday"] = p100((wrong[wrong.task != "day_of_week"].err == "off_by_one").mean())
        r["median_tok_all"] = float(s[M(C=c)].ctok.median())
        rows.append(r)
    save(rows, "c5_error_profile")
    e = s[M(C="Hindi en-CoT")]
    e = e[(e.c_hiw + e.c_enw) > 0]
    NUM["en_word_share"] = {"mean_of_ratios": round(float((e.c_enw / (e.c_hiw + e.c_enw)).mean()), 4), "pooled": round(float(e.c_enw.sum() / (e.c_hiw + e.c_enw).sum()), 4)}
    print(NUM["en_word_share"])


def raw(source, diffs=DIFFS, task=None, lang=None, cond=None):
    for d in diffs:
        for r in json.load(open(ROOT / "responses" / source / f"{d}.json", encoding="utf-8")):
            m = r["meta"]
            if (task is None or m["task"] == task) and (lang is None or m["language"] == lang) and (cond is None or r["condition"] == cond):
                yield r


KBINS = [(1, 1, "1"), (2, 2, "2"), (3, 3, "3"), (4, 4, "4"), (5, 8, "5-8"), (9, 16, "9-16"), (17, 32, "17-32")]


def kbin(k):
    return next(n for lo, hi, n in KBINS if lo <= k <= hi)


def qboot(g, stat, n=2000, seed=1):
    qs = g.qid.unique()
    idx = {q: i for i, q in enumerate(qs)}
    qi = g.qid.map(idx).to_numpy()
    rng = np.random.default_rng(seed)
    w = np.stack([np.bincount(rng.integers(0, len(qs), len(qs)), minlength=len(qs)) for _ in range(n)])
    return stat(w, qi)


def rate_ci(g, col):
    y = g[col].astype(float).to_numpy()
    def st(w, qi):
        c = np.bincount(qi, weights=y, minlength=w.shape[1])
        k = np.bincount(qi, minlength=w.shape[1]).astype(float)
        return (w @ c) / (w @ k)
    return ci(qboot(g, st)) if len(g) else (None, None)


def recur():
    r = df[df.task == "date_recurrence"].copy()
    r["kb"] = r.rec_k.astype(int).map(kbin)
    r["mirror"] = r.rec_pattern == "mirror"
    r["rec_ok"] = r.rec_pattern == "correct"
    r["first"] = r.rec_pattern == "first_step"
    sets = {"En CoT (first50)": r[(r.C == "English CoT") & (r.qn < 50)], "Hi CoT (first50)": r[(r.C == "Hindi CoT") & (r.qn < 50)], "en-CoT": r[r.C == "Hindi en-CoT"], "CLP": r[r.C == "Hindi CLP"],
            "En direct (first50)": r[(r.C == "English direct") & (r.qn < 50)], "Hi direct (first50)": r[(r.C == "Hindi direct") & (r.qn < 50)],
            "En CoT (150)": r[r.C == "English CoT"], "Hi CoT (150)": r[r.C == "Hindi CoT"], "Hi direct (150)": r[r.C == "Hindi direct"], "En direct (150)": r[r.C == "English direct"],
            "ron Hi cot (q0-9)": r[(r.source == "ron") & (r.lang == "hi_IN") & (r.cond == "cot")], "ron En cot (q0-9)": r[(r.source == "ron") & (r.lang == "en_US") & (r.cond == "cot")],
            "hinglish Hi": r[(r.source == "hinglish") & (r.lang == "hi_IN")]}
    rows = []
    for name, g in sets.items():
        d = g[g.rec_pattern.notna()]
        lo, hi = rate_ci(d, "mirror")
        rows.append({"set": name, "k": "all", "n_qresp": len(g), "n": len(d), "mirror": int(d.mirror.sum()), "mirror%": p100(d.mirror.mean()), "lo": lo, "hi": hi, "acc%": p100(d.rec_ok.mean()), "first_step%": p100(d["first"].mean())})
        for lo_, hi_, b in KBINS:
            e = d[d.kb == b]
            if len(e):
                lo, hi = rate_ci(e, "mirror")
                rows.append({"set": name, "k": b, "n_qresp": int((g.kb == b).sum()), "n": len(e), "mirror": int(e.mirror.sum()), "mirror%": p100(e.mirror.mean()), "lo": lo, "hi": hi, "acc%": p100(e.rec_ok.mean()), "first_step%": p100(e["first"].mean())})
    out = save(rows, "c6_recurrence_by_k")
    out.to_csv(FIG / "new_backwards_by_k.csv", index=False)
    rows = []
    contrasts = [("short", [1], [2]), ("medium", [2], [3, 4]), ("medium", [3], [4]), ("long", [4], [5, 6, 7, 8]), ("very_long", [8], list(range(9, 17))), ("very_very_long", [16], list(range(17, 33)))]
    for name in ("en-CoT", "Hi CoT (150)", "En CoT (150)", "CLP", "Hi direct (150)"):
        g = sets[name]
        d = g[g.rec_pattern.notna()]
        for lv, a, b in contrasts:
            e = d[d.difficulty == lv]
            x, y = e[e.rec_k.isin(a)], e[e.rec_k.isin(b)]
            if not len(x) or not len(y):
                continue
            all_ = pd.concat([x.assign(g_=1), y.assign(g_=0)])
            def st(w, qi, col="mirror"):
                v = all_[col].astype(float).to_numpy()
                f = all_.g_.to_numpy().astype(bool)
                c1 = np.bincount(qi[f], weights=v[f], minlength=w.shape[1]); k1 = np.bincount(qi[f], minlength=w.shape[1]).astype(float)
                c0 = np.bincount(qi[~f], weights=v[~f], minlength=w.shape[1]); k0 = np.bincount(qi[~f], minlength=w.shape[1]).astype(float)
                return (w @ c1) / np.maximum(w @ k1, 1) - (w @ c0) / np.maximum(w @ k0, 1)
            rows.append({"set": name, "level": lv, "k_a": a[0], "k_b": f"{b[0]}-{b[-1]}", "n_a": len(x), "n_b": len(y), "mirror_a%": p100(x.mirror.mean()), "mirror_b%": p100(y.mirror.mean()), "diff": p100(x.mirror.mean() - y.mirror.mean()), "ci": ci(qboot(all_, st)), "acc_a%": p100(x.rec_ok.mean()), "acc_b%": p100(y.rec_ok.mean())})
    save(rows, "c6_within_level_k_contrasts")
    rows = []
    for lv in DIFFS:
        for name in ("En CoT (first50)", "Hi CoT (first50)", "en-CoT", "CLP"):
            d = sets[name]
            d = d[(d.difficulty == lv) & d.rec_pattern.notna()]
            rows.append({"level": lv, "set": name, "n": len(d), "mirror%": p100(d.mirror.mean()), "acc%": p100(d.rec_ok.mean())})
    save(rows, "c6_recurrence_by_level")
    rows = []
    for name in ("En CoT (first50)", "Hi CoT (first50)", "en-CoT"):
        g = sets[name]
        for b in ("1", "2"):
            d = g[(g.kb == b) & g.rec_offset.notna()].copy()
            d["ratio"] = d.rec_offset / d.rec_every
            top = d.ratio.round(2).value_counts(normalize=True).head(6)
            rows.append({"set": name, "k": b, "n": len(d), "offset/every top": {float(a): p100(v) for a, v in top.items()}})
    save(rows, "c6_offset_patterns")
    rows = []
    e = r[r.C == "Hindi en-CoT"].set_index(["qid", "ins"])
    en = r[(r.C == "English CoT") & (r.qn < 50)].set_index(["qid", "ins"])
    j = e.join(en[["mirror", "rec_ok", "rec_pattern"]], rsuffix="_en")
    for b in ["1", "2", "3", "4", "5-8", "9-16", "17-32"]:
        g = j[j.kb == b]
        rows.append({"k": b, "pairs": len(g), "en-CoT correct%": p100(g.correct.mean()), "en-CoT mirror%": p100(g.mirror.mean()), "English CoT mirror%": p100(g.mirror_en.mean()), "English correct%": p100(g.rec_ok_en.mean())})
    save(rows, "c6_gap_by_k")
    txt = []
    GLOSS = {"before": r"\bbefore\b", "previous": r"\bprevious|preceding|prior\b", "backward": r"backward|work back|going back|subtract", "excluding": r"excluding today|without counting|not counting|except today|exclud", "occurrence": r"occurrence", "frequency": r"frequenc", "repetition": r"repetition|recurrence", "instance": r"\binstance", "ordinal_ok": r"\b1st\b|\bfirst\b|\b2nd\b|\bsecond\b", "ungrammatical_note": r"ungrammatical|1वीं|2वीं|typo|unusual|awkward|grammat|ambiguous|ambiguity|unclear|confus"}
    for x in raw("en-cot", task="date_recurrence"):
        m = x["meta"]
        c = x["content"] or ""
        txt.append({"id": x["id"], **{k: bool(re.search(v, c, re.I)) for k, v in GLOSS.items()}})
    t = pd.DataFrame(txt).set_index("id")
    ee = r[r.C == "Hindi en-CoT"].set_index("id").join(t)
    rows = []
    for (b, p), g in ee[ee.rec_pattern.notna()].groupby(["kb", "rec_pattern"]):
        rows.append({"k": b, "pattern": p, "n": len(g), **{k: p100(g[k].mean(), 0) for k in GLOSS}})
    save(rows, "c6_trace_glosses")
    samples = {}
    for name, flt in (("mirror k1", (ee.rec_pattern == "mirror") & (ee.kb == "1")), ("mirror k2", (ee.rec_pattern == "mirror") & (ee.kb == "2")), ("correct k1", (ee.rec_pattern == "correct") & (ee.kb == "1"))):
        samples[name] = list(ee[flt].sample(min(8, int(flt.sum())), random_state=3).index)
    keep = {i: n for n, ids in samples.items() for i in ids}
    out = []
    for x in raw("en-cot", task="date_recurrence"):
        if x["id"] in keep:
            out.append({"group": keep[x["id"]], "id": x["id"], "question": x["request"]["messages"][0]["content"].split("\n\n")[-1].strip(), "answer": x["meta"]["answer"], "content": x["content"][:700]})
    with open(TAB / "c6_sample_traces.json", "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
    ph = 'Given the phrasing'
    hits = [x for x in raw("en-cot", task="date_recurrence") if "Given the phrasing" in (x["content"] or "")]
    NUM["quote_given_phrasing"] = {"n": len(hits), "exact": [x["id"] for x in hits if "this suggests we need to find what comes before" in x["content"]]}
    print(NUM["quote_given_phrasing"])
    pr = pair_table(s, "English CoT", "Hindi en-CoT", extra=("task", "difficulty"))
    only_en = pr[pr["English CoT"] & ~pr["Hindi en-CoT"]].reset_index()
    only_hi = pr[~pr["English CoT"] & pr["Hindi en-CoT"]].reset_index()
    x = s[s.C == "Hindi en-CoT"].set_index(["qid", "ins"])
    me = x.loc[list(zip(only_en.qid, only_en.ins))]
    NUM["attrib_only_english_right"] = {"pairs_only_en": len(only_en), "pairs_only_hi": len(only_hi), "net": len(only_en) - len(only_hi),
                                        "mirror_in_only_en": int((me.rec_pattern == "mirror").sum()), "one_late_in_only_en": int((me.wk_off == 1).sum()),
                                        "by_task_only_en": only_en.task.value_counts().to_dict(), "by_task_only_hi": only_hi.task.value_counts().to_dict()}
    print(NUM["attrib_only_english_right"])
    NUM["attrib_points"] = {t: p100((A.acc(M(task=t, C="English CoT")) - A.acc(M(task=t, C="Hindi en-CoT"))) / 9, 2) for t in TASKS}
    print(NUM["attrib_points"])


WK = "monday|tuesday|wednesday|thursday|friday|saturday|sunday"
WKI = {d: i for i, d in enumerate(WK.split("|"))}
JAN1 = re.compile(rf"(?:january\s*1(?:st)?\b(?:,?\s*(\d{{4}}))?|jan\.?\s*1\b(?:,?\s*(\d{{4}}))?|1(?:st)?\s+(?:of\s+)?january(?:,?\s*(\d{{4}}))?|(\d{{4}})-01-01)[^.\n]{{0,60}}?\b({WK})\b", re.I)
JAN1H = re.compile(r"(?:1\s*जनवरी|जनवरी\s*1|(\d{4})-01-01)[^।\n]{0,60}?(सोमवार|मंगलवार|बुधवार|गुरुवार|शुक्रवार|शनिवार|रविवार)")
HIW2 = {"सोमवार": 0, "मंगलवार": 1, "बुधवार": 2, "गुरुवार": 3, "शुक्रवार": 4, "शनिवार": 5, "रविवार": 6}
METHOD = {"zeller": r"zeller", "doomsday": r"doomsday", "anchor_jan1": r"january\s*1|jan\.?\s*1\b|1(?:st)?\s+(?:of\s+)?january|-01-01|1\s*जनवरी|जनवरी\s*1", "known_ref": r"known (?:reference|date|day)|reference (?:date|point)|ज्ञात", "code": r"key value|century code|month code|sakamoto|tomohiko|gauss"}


def dow_features(rec):
    from datetime import date as D
    m = rec["meta"]
    c = rec["content"] or ""
    q = rec["request"]["messages"][0]["content"].split("\n\n")[-1] if "request" in rec else ""
    y, mo, da = map(int, re.findall(r"(\d{4})-(\d{2})-(\d{2})", q.translate(str.maketrans("०१२३४५६७८९", "0123456789")))[-1])
    dt = D(y, mo, da)
    doy = (dt - D(y, 1, 1)).days + 1
    g = dt.weekday()
    nums = {int(n.replace(",", "")) for n in re.findall(r"(?<![\d-])\d{1,3}(?:,\d{3})+|(?<![\d-])\d+(?![\d-])", c.translate(str.maketrans("०१२३४५६७८९", "0123456789")))}
    out = {"id": rec["id"], "year": y, "doy": doy, "gold": g, "has_doy": doy in nums, "has_doy_1": (doy - 1) in nums, "jan_first_true": D(y, 1, 1).weekday()}
    a = None
    for mt in JAN1.finditer(c):
        yr = next((v for v in mt.groups()[:4] if v), None)
        if yr is None or int(yr) == y:
            a = WKI[mt.group(5).lower()]
            break
    if a is None:
        for mt in JAN1H.finditer(c):
            if mt.group(1) is None or int(mt.group(1)) == y:
                a = HIW2[mt.group(2)]
                break
    out["anchor_wd"] = a
    for k, v in METHOD.items():
        out[f"m_{k}"] = bool(re.search(v, c, re.I))
    out["says_inclusive"] = bool(re.search(r"count(?:ing)? (?:january 1|jan 1|day 1)|including (?:january 1|jan 1)|day 1 is|day 1 =", c, re.I))
    out["subtract_1"] = bool(re.search(rf"\b{doy}\s*[-−–]\s*1\b|\b{doy-1}\s+days?\b", c))
    return out


def dow():
    rows, fr = [], []
    for source, lang, cond, C in (("standard", "en_US", "cot", "English CoT"), ("standard", "hi_IN", "cot", "Hindi CoT"), ("en-cot", "hi_IN", "en-cot", "Hindi en-CoT")):
        for rec in raw(source, task="day_of_week", lang=lang, cond=cond):
            if int(rec["meta"]["question_id"]) < 50:
                fr.append({**dow_features(rec), "C": C})
    f = pd.DataFrame(fr)
    x = s[s.task == "day_of_week"][["id", "C", "scored", "correct", "wk_off", "wk_ans", "difficulty", "finish"]]
    j = x.merge(f, on=["id", "C"])
    j["anchor_right"] = j.anchor_wd == j.jan_first_true
    j["pred_inclusive"] = (j.anchor_wd + j.doy) % 7 == j.wk_ans
    j["pred_correct_calc"] = (j.anchor_wd + j.doy - 1) % 7 == j.wk_ans
    rows = []
    for C, g in j.groupby("C"):
        a = g[g.wk_off.notna()]
        for label, h in (("all answered", a), ("correct", a[a.wk_off == 0]), ("one late", a[a.wk_off == 1]), ("one early", a[a.wk_off == -1]), ("other wrong", a[~a.wk_off.isin([0, 1, -1])])):
            rows.append({"cond": C, "group": label, "n": len(h), "% of answered": p100(len(h) / len(a)), "jan1 anchor stated": p100(h.anchor_wd.notna().mean()), "anchor weekday right|stated": p100(h[h.anchor_wd.notna()].anchor_right.mean()),
                         "doy number in text": p100(h.has_doy.mean()), "doy-1 in text": p100(h.has_doy_1.mean()), "doy without doy-1": p100((h.has_doy & ~h.has_doy_1).mean()),
                         "zeller": p100(h.m_zeller.mean()), "doomsday": p100(h.m_doomsday.mean()), "code/formula": p100(h.m_code.mean()), "known ref": p100(h.m_known_ref.mean())})
    out = save(rows, "c6_dow_mechanism")
    out.to_csv(FIG / "new_dow_mechanism.csv", index=False)
    rows = []
    for C, g in j.groupby("C"):
        l = g[g.wk_off == 1]
        an = l[l.anchor_wd.notna()]
        strict_slip = an[an.anchor_right & an.has_doy & ~an.has_doy_1]
        ok_anchor_all = an[an.anchor_right]
        rows.append({"cond": C, "one_late": len(l), "share_answered": p100(len(l) / g.wk_off.notna().sum()), "stated_anchor": len(an), "right_anchor": len(ok_anchor_all), "wrong_anchor": len(an) - len(ok_anchor_all),
                     "right_anchor+doy no doy-1 (candidate slip)": len(strict_slip), "candidate share of late%": p100(len(strict_slip) / len(l)) if len(l) else None,
                     "wrong anchor shifted +1": int((an.anchor_wd == (an.jan_first_true + 1) % 7).sum()),
                     "no anchor": len(l) - len(an)})
    save(rows, "c6_dow_one_late_breakdown")
    rows = []
    for C, g in j.groupby("C"):
        for lv, h in g.groupby("difficulty"):
            a = h[h.wk_off.notna()]
            rows.append({"cond": C, "level": lv, "n": len(a), "correct%": p100((a.wk_off == 0).mean()), "late%": p100((a.wk_off == 1).mean()), "early%": p100((a.wk_off == -1).mean())})
    save(rows, "c6_dow_by_level")
    rng = np.random.default_rng(7)
    picks = {}
    for C in ("English CoT", "Hindi en-CoT"):
        l = j[(j.C == C) & (j.wk_off == 1)]
        for i in rng.choice(l.id.to_numpy(), size=min(12, len(l)), replace=False):
            picks[C, i] = True
    out = []
    for source, lang, cond, C in (("standard", "en_US", "cot", "English CoT"), ("en-cot", "hi_IN", "en-cot", "Hindi en-CoT")):
        for rec in raw(source, task="day_of_week", lang=lang, cond=cond):
            if (C, rec["id"]) in picks:
                out.append({"cond": C, "id": rec["id"], "gold": rec["meta"]["answer"], "content": (rec["content"] or "")[:1400]})
    with open(TAB / "c6_dow_sample_traces.json", "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2, ensure_ascii=False)


def decomp_row(label, a, base):
    e, c, h = a.boot(base & M(C="English CoT")), a.boot(base & M(C="Hindi en-CoT")), a.boot(base & M(C="Hindi CoT"))
    pe, pc, ph = a.acc(base & M(C="English CoT")), a.acc(base & M(C="Hindi en-CoT")), a.acc(base & M(C="Hindi CoT"))
    tot, reas, ques = pe - ph, pc - ph, pe - pc
    sh = (c - h) / (e - h)
    return {"cut": label, "En CoT": p100(pe), "en-CoT": p100(pc), "Hi CoT": p100(ph), "total gap": p100(tot), "ci total": ci(e - h), "reasoning part (en-CoT - Hi CoT)": p100(reas), "ci reasoning": ci(c - h),
            "question part (En CoT - en-CoT)": p100(ques), "ci question": ci(e - c), "reasoning share %": p100(reas / tot) if abs(tot) > 1e-9 else None, "ci share": ci(sh), "reasoning-question": p100(reas - ques), "ci r-q": ci((c - h) - (e - c))}


def decomp():
    rows = []
    for name, a in (("answered", A), ("strict", ST)):
        rows.append({"conv": name, **decomp_row("pooled", a, M())})
        for ins in INS:
            rows.append({"conv": name, **decomp_row(ins, a, M(ins=ins))})
        for lv in DIFFS:
            rows.append({"conv": name, **decomp_row(lv, a, M(difficulty=lv))})
        for t in TASKS:
            rows.append({"conv": name, **decomp_row(t, a, M(task=t))})
        rows.append({"conv": name, **decomp_row("no recurrence", a, ~M(task="date_recurrence"))})
        k = s.rec_k.to_numpy(dtype=float)
        rows.append({"conv": name, **decomp_row("no recurrence k<=2", a, ~(M(task="date_recurrence") & (k <= 2)))})
    d = save(rows, "decomposition")
    d[d.conv == "answered"].to_csv(FIG / "new_decomposition.csv", index=False)
    rows = []
    for ins in INS:
        for t in TASKS:
            rows.append(decomp_row(f"{ins}/{t}", A, M(ins=ins, task=t)))
    save(rows, "decomposition_task_by_distractor")
    c = s[M(C="Hindi en-CoT")]
    trans = []
    PAT = re.compile(r"translat|in english|the question (?:asks|is asking|says|states)|the problem (?:asks|states|says)|this (?:question|means)|means|asks", re.I)
    LIT = re.compile(r"translat", re.I)
    for rec in raw("en-cot"):
        cc = rec["content"] or ""
        head = cc[:400]
        trans.append({"id": rec["id"], "lit": bool(LIT.search(cc)), "restate": bool(PAT.search(head)), "dev_in_trace": bool(DEV.search(cc))})
    t = c.merge(pd.DataFrame(trans), on="id")
    NUM["encot_translation"] = {"mention_translate%": p100(t.lit.mean()), "restate_in_first_400_chars%": p100(t.restate.mean()), "any_devanagari%": p100(t.dev_in_trace.mean()),
                                "acc_translate": p100(t[t.scored & t.lit].correct.mean()), "acc_no_translate": p100(t[t.scored & ~t.lit].correct.mean())}
    print(NUM["encot_translation"])


def think():
    r = df[(df.source == "ron")].copy()
    r["r_total"] = r.r_hiw + r.r_enw
    r["r_en"] = r.r_enw / r.r_total.where(r.r_total > 0)
    r["r_letters_en"] = r.r_lat / (r.r_lat + r.r_dev).where((r.r_lat + r.r_dev) > 0)
    r["c_en"] = r.c_enw / (r.c_enw + r.c_hiw).where((r.c_enw + r.c_hiw) > 0)
    rows = []
    for (lang, cond), g in r.groupby(["lang", "cond"]):
        rows.append({"lang": lang, "cond": cond, "n": len(g), "answered": int(g.scored.sum()), "acc_answered": p100(g[g.scored].correct.mean()), "acc_strict": p100(g.correct.mean()), "reasoning present%": p100((g.r_total > 0).mean()),
                     "mean EN word share": p100(g.r_en.mean()), "pooled EN word share": p100(g.r_enw.sum() / g.r_total.sum()), "pooled non-Devanagari letter share": p100(g.r_lat.sum() / (g.r_lat + g.r_dev).sum()), "share with >=90% EN words": p100((g.r_en >= .9).mean()), "share <=10% EN": p100((g.r_en <= .1).mean()),
                     "median reasoning tok": float(g.rtok.median()), "max reasoning tok": float(g.rtok.max()), "cutoff": int((g.finish == "length").sum()), "visible EN word share": p100(g.c_en.mean()), "verif in reasoning%": p100(g.r_verif.mean()), "verif in visible%": p100(g.verif.mean())})
    save(rows, "think_summary")
    h = r[(r.lang == "hi_IN") & (r.cond == "cot")].copy()
    h["bin"] = pd.cut(h.r_en, [-.01, .25, .5, .75, .9, .99, 1.0])
    print(h.groupby("bin", observed=True).agg(n=("correct", "size"), acc=("correct", "mean"), tok=("rtok", "median")))
    h.groupby("bin", observed=True).agg(n=("correct", "size"), acc=("correct", "mean"), median_tok=("rtok", "median"), task_recurrence=("task", lambda x: (x == "date_recurrence").mean())).to_csv(FIG / "new_think_accuracy_by_english_share.csv")
    rows = []
    for name, sub in (("Hindi cot", h), ("Hindi cot+direct", r[r.lang == "hi_IN"])):
        d = sub[sub.scored & sub.r_en.notna()].copy()
        d["q"] = d.qid + "/" + d.cond
        d["cell"] = d.task + "/" + d.difficulty
        d["y"] = d.correct.astype(float)
        for fe, name2 in (("cell", "task×level FE"), ("qid", "question FE")):
            x_ = d.r_en - d.groupby(fe).r_en.transform("mean")
            y_ = d.y - d.groupby(fe).y.transform("mean")
            mod = sm.OLS(y_, x_).fit(cov_type="cluster", cov_kwds={"groups": pd.factorize(d.qid)[0]})
            rows.append({"set": name, "fe": name2, "n": len(d), "questions": d.qid.nunique(), "slope per 100% EN (points)": round(100 * float(mod.params.iloc[0]), 1), "ci": tuple(np.round(100 * mod.conf_int().iloc[0].to_numpy(), 1)), "p": float(mod.pvalues.iloc[0]), "sd within": round(float(x_.std()), 3)})
        for t, g in d.groupby("task"):
            x_ = g.r_en - g.groupby("cell").r_en.transform("mean")
            y_ = g.y - g.groupby("cell").y.transform("mean")
            if x_.std() > 0:
                mod = sm.OLS(y_, x_).fit(cov_type="cluster", cov_kwds={"groups": pd.factorize(g.qid)[0]})
                rows.append({"set": name, "fe": f"{t} cell FE", "n": len(g), "questions": g.qid.nunique(), "slope per 100% EN (points)": round(100 * float(mod.params.iloc[0]), 1), "ci": tuple(np.round(100 * mod.conf_int().iloc[0].to_numpy(), 1)), "p": float(mod.pvalues.iloc[0]), "sd within": round(float(x_.std()), 3)})
    save(rows, "think_within_hindi_slope")
    q10 = s[(s.qn < 10)].copy()
    tag = {("en_US", "cot"): "ron English CoT", ("hi_IN", "cot"): "ron Hindi CoT", ("en_US", "direct"): "ron English direct", ("hi_IN", "direct"): "ron Hindi direct"}
    rr = r.copy()
    rr["C"] = [tag[k] for k in zip(rr.lang, rr.cond)]
    c = pd.concat([q10, rr], ignore_index=True)
    rows = []
    allq = sorted(c.qid.unique())
    ix = {q: i for i, q in enumerate(allq)}
    c["qi2"] = c.qid.map(ix)
    w10 = weights(len(allq), 2000, 11)
    def vec(n, strict=False):
        d = c[c.C == n]
        d = d if strict else d[d.scored]
        cc = np.bincount(d.qi2, weights=d.correct.astype(float), minlength=len(allq))
        k = np.bincount(d.qi2, minlength=len(allq)).astype(float)
        return cc, k
    names = list(tag.values()) + CONDS
    for n in names:
        for strict in (False, True):
            cc, k = vec(n, strict)
            rows.append({"cond": n, "conv": "strict" if strict else "answered", "n": int(k.sum()), "acc": p100(cc.sum() / k.sum()), "ci": ci((w10 @ cc) / (w10 @ k))})
    d = save(rows, "think_q0_9_accuracy")
    d.to_csv(FIG / "new_think_q0_9.csv", index=False)
    rows = []
    for a_, b_ in (("ron Hindi CoT", "Hindi CoT"), ("ron Hindi CoT", "Hindi en-CoT"), ("ron Hindi CoT", "ron English CoT"), ("ron English CoT", "English CoT"), ("Hindi en-CoT", "Hindi CoT"), ("English CoT", "Hindi en-CoT")):
        for strict in (False, True):
            ca, ka = vec(a_, strict)
            cb, kb = vec(b_, strict)
            x = (w10 @ ca) / (w10 @ ka) - (w10 @ cb) / (w10 @ kb)
            w_ = c[c.C.isin([a_, b_])]
            w_ = w_ if strict else w_[w_.scored]
            pv = w_.pivot_table(index=["qid", "ins"], columns="C", values="correct", aggfunc="first").dropna().astype(bool)
            l, g = int((pv[a_] & ~pv[b_]).sum()), int((~pv[a_] & pv[b_]).sum())
            rows.append({"a": a_, "b": b_, "conv": "strict" if strict else "answered", "diff": p100(ca.sum() / ka.sum() - cb.sum() / kb.sum()), "ci": ci(x), "only a": l, "only b": g, "p": binomtest(l, l + g).pvalue if l + g else 1.0})
    save(rows, "think_q0_9_contrasts")
    rows = []
    for t in TASKS:
        g = rr[(rr.task == t)]
        rows.append({"task": t, "ron Hi CoT": p100(g[(g.C == "ron Hindi CoT") & g.scored].correct.mean()), "ron En CoT": p100(g[(g.C == "ron English CoT") & g.scored].correct.mean()),
                     "en-CoT q0-9": p100(q10[(q10.C == "Hindi en-CoT") & (q10.task == t) & q10.scored].correct.mean()), "Hi CoT q0-9": p100(q10[(q10.C == "Hindi CoT") & (q10.task == t) & q10.scored].correct.mean()), "En CoT q0-9": p100(q10[(q10.C == "English CoT") & (q10.task == t) & q10.scored].correct.mean()),
                     "ron Hi EN-share": p100(g[g.C == "ron Hindi CoT"].r_en.mean()), "ron Hi cutoff": int((g[g.C == "ron Hindi CoT"].finish == "length").sum())})
    save(rows, "think_by_task")


def verif():
    rows = []
    for c in ("English CoT", "Hindi en-CoT", "Hindi CLP", "Hindi CoT"):
        g = s[M(C=c) & s.scored.to_numpy()]
        o = mh(g.assign(v=g.verif), "v")
        rows.append({"cond": c, "n": len(g), "verif%": p100(g.verif.mean()), "acc verif": p100(g[g.verif].correct.mean()), "acc no verif": p100(g[~g.verif].correct.mean()), "MH OR task×level": o[:3], "strata": o[3]})
        for t in TASKS:
            h = g[g.task == t]
            tabs = []
            for _, x in h.groupby("difficulty"):
                e, y = x.verif, x.correct
                tb = np.array([[(e & y).sum(), (e & ~y).sum()], [(~e & y).sum(), (~e & ~y).sum()]], dtype=float)
                if tb[0].sum() and tb[1].sum():
                    tabs.append(tb)
            if tabs:
                st = StratifiedTable(tabs)
                lo, hi = st.oddsratio_pooled_confint()
                val = (round(float(st.oddsratio_pooled), 2), round(float(lo), 2), round(float(hi), 2))
            else:
                val = None
            rows.append({"cond": c, "task": t, "n": len(h), "verif%": p100(h.verif.mean()), "acc verif": p100(h[h.verif].correct.mean()), "acc no verif": p100(h[~h.verif].correct.mean()), "MH OR level": val})
    save(rows, "verif_within_task")
    cell = lambda d: d.task + "/" + d.difficulty
    e = s[M(C="Hindi en-CoT") & s.scored.to_numpy()].copy()
    h = s[M(C="Hindi CoT") & s.scored.to_numpy()].copy()
    e["cell"], h["cell"] = cell(e), cell(h)
    target = h.groupby("cell").verif.mean()
    def gform(ei):
        tot = 0
        ws = np.bincount(e.qi, minlength=Q)
        return None
    cells = sorted(e.cell.unique())
    ci_e = e.cell.map({c: i for i, c in enumerate(cells)}).to_numpy()
    res = []
    y = e.correct.to_numpy(dtype=float)
    v = e.verif.to_numpy(dtype=float)
    qi_e = e.qi.to_numpy()
    hc = h.cell.map({c: i for i, c in enumerate(cells)}).to_numpy()
    hv = h.verif.to_numpy(dtype=float)
    hy = h.correct.to_numpy(dtype=float)
    qi_h = h.qi.to_numpy()
    nc = len(cells)
    wsub = W2
    for b in range(wsub.shape[0] + 1):
        we = np.ones(len(e)) if b == wsub.shape[0] else wsub[b, qi_e].astype(float)
        wh = np.ones(len(h)) if b == wsub.shape[0] else wsub[b, qi_h].astype(float)
        n1 = np.bincount(ci_e, weights=we * v, minlength=nc)
        n0 = np.bincount(ci_e, weights=we * (1 - v), minlength=nc)
        c1 = np.bincount(ci_e, weights=we * v * y, minlength=nc)
        c0 = np.bincount(ci_e, weights=we * (1 - v) * y, minlength=nc)
        ne = n1 + n0
        pooled = (c1 + c0) / np.maximum(ne, 1)
        p1 = np.where(n1 > 0, c1 / np.maximum(n1, 1), pooled)
        p0 = np.where(n0 > 0, c0 / np.maximum(n0, 1), pooled)
        ph = np.bincount(hc, weights=wh * hv, minlength=nc) / np.maximum(np.bincount(hc, weights=wh, minlength=nc), 1)
        acf = p1 * ph + p0 * (1 - ph)
        afact = pooled
        hact = np.bincount(hc, weights=wh * hy, minlength=nc) / np.maximum(np.bincount(hc, weights=wh, minlength=nc), 1)
        res.append((afact.mean(), acf.mean(), hact.mean()))
    res = np.array(res)
    pt, bs = res[-1], res[:-1]
    NUM["verif_gformula"] = {"enCoT_cell_avg": p100(pt[0]), "enCoT_if_verif_at_HindiCoT_rate": p100(pt[1]), "HindiCoT_cell_avg": p100(pt[2]), "total": p100(pt[0] - pt[2]), "ci_total": ci(bs[:, 0] - bs[:, 2]),
                             "indirect_via_verif": p100(pt[0] - pt[1]), "ci_indirect": ci(bs[:, 0] - bs[:, 1]), "direct_rest": p100(pt[1] - pt[2]), "ci_direct": ci(bs[:, 1] - bs[:, 2]),
                             "share_mediated%": p100((pt[0] - pt[1]) / (pt[0] - pt[2])), "ci_share": ci((bs[:, 0] - bs[:, 1]) / (bs[:, 0] - bs[:, 2]))}
    print(NUM["verif_gformula"])
    e["tq"] = e.ctok
    rows = []
    for c_, src, lang, cond in (("Hindi en-CoT", "en-cot", "hi_IN", "en-cot"), ("English CoT", "standard", "en_US", "cot")):
        for task in ("date_addition", "date_subtraction", "date_recurrence", "interval_date", "day_of_week"):
            st = {"verif": 0, "before_has_answer": 0, "changed": 0, "changed_to_right": 0, "changed_to_wrong": 0, "correct_before": 0}
            for rec in raw(src, task=task, lang=lang, cond=cond):
                if int(rec["meta"]["question_id"]) >= 50:
                    continue
                c = rec["content"] or ""
                ans = re.findall(r"(?:Answer|उत्तर)\s*\**\s*[:：]\s*(.*)", c)
                mt = re.search(r"verif|double.?check|let me check|check (?:this|by|again)|sanity|alternatively|another way|cross.?check", c, re.I)
                if not ans or not mt:
                    continue
                st["verif"] += 1
                before = c[:mt.start()]
                final = ans[-1].strip().strip("*`. ")
                gold = rec["meta"]["answer"]
                if task == "day_of_week":
                    fin = WEEK_LOOK.get(final.casefold())
                    g_ = WEEK_LOOK.get(gold.casefold())
                    cands = [WEEK_LOOK[x.casefold()] for x in re.findall(WK + "|सोमवार|मंगलवार|बुधवार|गुरुवार|शुक्रवार|शनिवार|रविवार", before, re.I)]
                else:
                    fin = final
                    g_ = gold
                    cands = re.findall(r"\d{4}-\d{2}-\d{2}", before)
                    if task == "interval_date":
                        cands = [" to ".join(cands[-2:])] if len(cands) >= 2 else []
                if not cands:
                    continue
                last = cands[-1]
                st["before_has_answer"] += 1
                st["correct_before"] += int(last == g_)
                if last != fin:
                    st["changed"] += 1
                    st["changed_to_right"] += int(fin == g_)
                    st["changed_to_wrong"] += int(last == g_)
            rows.append({"cond": c_, "task": task, **st})
    save(rows, "verif_changes_answer")


WEEK_LOOK = {**WKI, **HIW2}


def subset():
    st = df[df.source == "standard"].copy()
    st["first"] = st.qn < 50
    qs = sorted(st.qid.unique())
    ix = {q: i for i, q in enumerate(qs)}
    st["qi2"] = st.qid.map(ix)
    w_ = weights(len(qs), 2000, 21)
    fq = np.array([int(q.rsplit("/", 1)[1]) < 50 for q in qs])
    def acc_boot(g, mask):
        c_ = np.bincount(g.qi2, weights=g.correct.astype(float), minlength=len(qs)) * mask
        k_ = np.bincount(g.qi2, minlength=len(qs)).astype(float) * mask
        return c_.sum() / k_.sum(), (w_ @ c_) / (w_ @ k_)
    rows = []
    for (lang, cond), g in st[st.scored].groupby(["lang", "cond"]):
        a, ab = acc_boot(g, fq)
        b, bb = acc_boot(g, ~fq)
        al, alb = acc_boot(g, np.ones(len(qs)))
        rows.append({"lang": lang, "cond": cond, "cut": "all", "first50": p100(a), "rest100": p100(b), "all150": p100(al), "first-rest": p100(a - b), "ci": ci(ab - bb)})
        for t in TASKS:
            gt = g[g.task == t]
            a, ab = acc_boot(gt, fq)
            b, bb = acc_boot(gt, ~fq)
            rows.append({"lang": lang, "cond": cond, "cut": t, "first50": p100(a), "rest100": p100(b), "all150": p100(acc_boot(gt, np.ones(len(qs)))[0]), "first-rest": p100(a - b), "ci": ci(ab - bb)})
        for lv in DIFFS:
            gt = g[g.difficulty == lv]
            a, ab = acc_boot(gt, fq)
            b, bb = acc_boot(gt, ~fq)
            rows.append({"lang": lang, "cond": cond, "cut": lv, "first50": p100(a), "rest100": p100(b), "all150": p100(acc_boot(gt, np.ones(len(qs)))[0]), "first-rest": p100(a - b), "ci": ci(ab - bb)})
    d = save(rows, "subset_first50_vs_rest")
    d["excl0"] = [not (c_[0] <= 0 <= c_[1]) for c_ in d.ci]
    print(d.groupby("cut").excl0.sum(), d.excl0.sum(), len(d))
    d.to_csv(FIG / "new_subset_first50_vs_rest.csv", index=False)
    r = st[st.scored & st.cond.isin(["cot"])]
    rows = []
    for lv in DIFFS + ["all"]:
        g = r if lv == "all" else r[r.difficulty == lv]
        ee, hh = g[g.lang == "en_US"], g[g.lang == "hi_IN"]
        rows.append({"level": lv, "En-Hi CoT gap first50": p100(ee[ee["first"]].correct.mean() - hh[hh["first"]].correct.mean()), "rest100": p100(ee[~ee["first"]].correct.mean() - hh[~hh["first"]].correct.mean()), "all150": p100(ee.correct.mean() - hh.correct.mean())})
    save(rows, "subset_gap")
    q = df[(df.source == "standard") & (df.lang == "hi_IN") & (df.cond == "cot") & (df.ins == "no_insertion") & (df.task == "date_recurrence")].copy()
    from scipy.stats import chi2_contingency
    rows = []
    q["first"] = q.qn < 50
    for lv in DIFFS:
        g = q[q.difficulty == lv]
        tb = pd.crosstab(g.rec_k, g["first"])
        rows.append({"level": lv, "k share first50": (g[g["first"]].rec_k.value_counts(normalize=True).sort_index().round(2).to_dict() if lv in ("short", "medium") else None), "k share rest": (g[~g["first"]].rec_k.value_counts(normalize=True).sort_index().round(2).to_dict() if lv in ("short", "medium") else None),
                     "mean k first50": round(float(g[g["first"]].rec_k.mean()), 2), "mean k rest": round(float(g[~g["first"]].rec_k.mean()), 2), "chi2 p": round(float(chi2_contingency(tb)[1]), 3)})
    save(rows, "subset_recurrence_k")
    rows = []
    for t in TASKS:
        qq = {}
        for lv in DIFFS:
            d_ = json.load(open(ROOT / "dataset" / lv / f"{t}_en_US.json", encoding="utf-8"))
            vals = []
            for i in range(150):
                m_ = re.search(r"\d{4}-\d{2}-\d{2}", d_[str(i)]["no_insertion"])
                tm = re.search(r"\d{1,2}:\d{2}", d_[str(i)]["no_insertion"])
                if m_:
                    vals.append((pd.Timestamp(m_.group()) - pd.Timestamp("2025-01-01")).days / {"short": 364, "medium": 1460, "long": 2190, "very_long": 3286, "very_very_long": 4382}[lv])
                else:
                    h_, mi = tm.group().split(":")
                    vals.append((int(h_) * 60 + int(mi)) / 1439)
            qq[lv] = vals
        from scipy.stats import spearmanr
        c0 = spearmanr(qq["short"], qq["medium"])[0]
        c1 = spearmanr(qq["short"], qq["very_very_long"])[0]
        rows.append({"task": t, "rank corr of first value, short vs medium": round(float(c0), 3), "short vs very very long": round(float(c1), 3), "first50 short vs medium": round(float(spearmanr(qq["short"][:50], qq["medium"][:50])[0]), 3)})
    save(rows, "subset_seed_correlation_across_levels")
    rows = []
    for c_ in ("English CoT", "Hindi CoT", "Hindi en-CoT"):
        x = s[M(C=c_) & s.scored.to_numpy()].groupby(["task", "difficulty", "qn"]).correct.mean().reset_index()
        pv = x.pivot_table(index=["task", "qn"], columns="difficulty", values="correct")
        rows.append({"cond": c_, "corr short-medium (within task)": round(float(pv.groupby("task").apply(lambda g: g["short"].corr(g["medium"])).mean()), 3), "short-vvl": round(float(pv.groupby("task").apply(lambda g: g["short"].corr(g["very_very_long"])).mean()), 3)})
    save(rows, "subset_outcome_corr_across_levels")


def batch():
    st = df[df.source == "standard"].copy()
    tb = st.groupby(["difficulty", "date"]).agg(n=("id", "size"), first_q=("qn", "min"), last_q=("qn", "max"), tasks=("task", "nunique"), acc=("correct", "mean")).reset_index()
    tb.to_csv(TAB / "batch_dates.csv", index=False)
    print(tb.to_string())
    rows = []
    for (lv, lang, cond), g in st[st.scored].groupby(["difficulty", "lang", "cond"]):
        days = g.date.value_counts()
        days = days[days >= 200].index.tolist()
        if len(days) < 2:
            continue
        d1, d2 = sorted(days)[:2]
        x = g[g.date.isin([d1, d2])].copy()
        x["cell"] = x.task + "/" + x.ins
        tabs = []
        for _, h in x.groupby("cell"):
            e, y = h.date == d2, h.correct
            t_ = np.array([[(e & y).sum(), (e & ~y).sum()], [(~e & y).sum(), (~e & ~y).sum()]], dtype=float)
            if t_[0].sum() and t_[1].sum():
                tabs.append(t_)
        if not tabs:
            continue
        o = StratifiedTable(tabs)
        lo, hi = o.oddsratio_pooled_confint()
        rows.append({"level": lv, "lang": lang, "cond": cond, "early": d1, "late": d2, "n_early": int((x.date == d1).sum()), "n_late": int((x.date == d2).sum()), "acc_early": p100(x[x.date == d1].correct.mean()), "acc_late": p100(x[x.date == d2].correct.mean()), "strata": len(tabs), "MH OR late vs early (task x ins)": round(float(o.oddsratio_pooled), 2), "ci": (round(float(lo), 2), round(float(hi), 2))})
    save(rows, "batch_effect")
    x = df[df.source == "standard"].copy()
    usage = x.groupby("date").rtok.apply(lambda v: float(v.notna().mean()))
    print(usage)
    NUM["usage_details_present_by_date"] = usage.round(3).to_dict()



def misc():
    r = df[(df.task == "date_recurrence") & df.rec_pattern.notna()].copy()
    r["mirror"] = r.rec_pattern == "mirror"
    sel = {"en-CoT": r[r.C == "Hindi en-CoT"], "Hi CoT 150": r[r.C == "Hindi CoT"], "Hi direct 150": r[r.C == "Hindi direct"], "En CoT 150": r[r.C == "English CoT"], "En direct 150": r[r.C == "English direct"], "CLP": r[r.C == "Hindi CLP"]}
    rows = []
    for n, g in sel.items():
        h = g[g.rec_k == 1]
        for by in ("rec_every", "ins"):
            for k_, e in h.groupby(by):
                rows.append({"set": n, "by": by, "key": k_, "n": len(e), "mirror%": p100(e.mirror.mean()), "correct%": p100((e.rec_pattern == "correct").mean())})
    save(rows, "c6_k1_by_interval_and_distractor")
    rows = []
    for n, g in sel.items():
        for k_ in (2, 3, 4):
            h = g[g.rec_k == k_].copy()
            q = h.rec_offset / h.rec_every
            rows.append({"set": n, "k": k_, "n": len(h), "k steps%": p100((q == k_).mean()), "k-1 steps%": p100((q == k_ - 1).mean()), "k+1 steps%": p100((q == k_ + 1).mean()), "1 step%": p100((q == 1).mean()), "minus k%": p100((q == -k_).mean())})
    save(rows, "c6_k234_offsets")
    rows = []
    for n, g in sel.items():
        h = g[g.rec_k == 2]
        for lv, e in h.groupby("difficulty"):
            rows.append({"set": n, "level": lv, "n": len(e), "first_step%": p100((e.rec_pattern == "first_step").mean()), "correct%": p100((e.rec_pattern == "correct").mean())})
    save(rows, "c6_k2_first_step_by_level")
    rows = []
    for C in CONDS:
        g = s[(s.C == C) & s.scored]
        wrong = g[~g.correct]
        rows.append({"cond": C, "answered": len(g), "format_only": int((wrong.err == "format_only").sum()), "invalid": int((wrong.err == "invalid").sum()), "exact%": p100(g.correct.mean()), "lenient%": p100((g.correct | (g.err == "format_only")).mean()), **{f"inv {t}": int((wrong[wrong.task == t].err == "invalid").sum()) + int((wrong[wrong.task == t].err == "format_only").sum()) for t in TASKS}})
    save(rows, "format_only")
    rows = []
    for t in TASKS:
        rows.append({"task": t, "En-Hi direct": p100(A.acc(M(task=t, C="English direct")) - A.acc(M(task=t, C="Hindi direct"))), "ci direct": ci(A.boot(M(task=t, C="English direct")) - A.boot(M(task=t, C="Hindi direct"))),
                     "En-Hi CoT": p100(A.acc(M(task=t, C="English CoT")) - A.acc(M(task=t, C="Hindi CoT"))), "En CoT - en-CoT": p100(A.acc(M(task=t, C="English CoT")) - A.acc(M(task=t, C="Hindi en-CoT"))), "ci q part": ci(A.boot(M(task=t, C="English CoT")) - A.boot(M(task=t, C="Hindi en-CoT"))),
                     "ron En - ron Hi (q0-9)": None})
    save(rows, "template_task_gaps")
    t_ = df[(df.source.isin(["standard", "en-cot"])) & (df.task == "date_addition") & (df.difficulty == "short") & (df.qn < 50)].copy()
    t_["n"] = t_.id.map(lambda _: None)
    ds = json.load(open(ROOT / "dataset" / "short" / "date_addition_hi_IN.json", encoding="utf-8"))
    nday = {int(k): int(re.search(r"(\d+) दिनों", v["no_insertion"]).group(1)) for k, v in ds.items()}
    t_["n"] = t_.qn.map(nday)
    rows = []
    for C_, g in t_[t_.C.notna() & t_.scored].groupby("C"):
        for n_, e in g.groupby("n"):
            rows.append({"cond": C_, "days": n_, "n": len(e), "acc%": p100(e.correct.mean())})
    save(rows, "template_one_days_plural")
    pr = df[(df.source == "en-cot")]
    NUM["encot_design"] = {"n": len(pr), "questions": pr.qid.nunique(), "ins": pr.ins.value_counts().to_dict(), "qn_max": int(pr.qn.max()), "dates": pr.date.value_counts().to_dict()}
    print(NUM["encot_design"])
    pp = []
    for rec in raw("en-cot"):
        q = rec["request"]
        pp.append((q["model"], q["max_tokens"], q["temperature"], q["top_p"], q["reasoning_effort"]))
    NUM["encot_request_params"] = {str(k): v for k, v in pd.Series(pp).value_counts().items()}
    print(NUM["encot_request_params"])
    loops = []
    for src, lang, cond, C_ in (("en-cot", "hi_IN", "en-cot", "Hindi en-CoT"), ("standard", "en_US", "cot", "English CoT"), ("standard", "hi_IN", "cot", "Hindi CoT")):
        for rec in raw(src, lang=lang, cond=cond):
            if int(rec["meta"]["question_id"]) >= 50 or rec.get("finish_reason") != "length":
                continue
            c = rec["content"] or ""
            tail = c[-120:]
            loops.append({"C": C_, "task": rec["meta"]["task"], "repeat_tail": c[:-120].count(tail) >= 1, "repeat_line": max(pd.Series([x.strip() for x in c.split("\n") if len(x.strip()) > 20]).value_counts().tolist() or [0]) >= 5})
    lp = pd.DataFrame(loops)
    NUM["cutoff_loops"] = lp.groupby("C")[["repeat_tail", "repeat_line"]].mean().round(3).to_dict()
    NUM["cutoff_n"] = lp.groupby("C").size().to_dict()
    print(NUM["cutoff_loops"], NUM["cutoff_n"])
    xs = []
    for rec in raw("ron", lang="hi_IN", cond="cot"):
        t = rec.get("reasoning_content") or ""
        h1, e1 = len(HIW_.findall(t[:1000])), len(ENW_.findall(t[:1000]))
        h3, e3 = len(HIW_.findall(t[:3000])), len(ENW_.findall(t[:3000]))
        xs.append({"id": rec["id"], "e1000": e1 / (h1 + e1) if h1 + e1 else None, "e3000": e3 / (h3 + e3) if h3 + e3 else None, "first_dev": (DEV.search(t).start() if DEV.search(t) else len(t)), "len": len(t)})
    x = pd.DataFrame(xs)
    h = df[(df.source == "ron") & (df.lang == "hi_IN") & (df.cond == "cot")].merge(x, on="id")
    h["r_en"] = h.r_enw / (h.r_enw + h.r_hiw).where((h.r_enw + h.r_hiw) > 0)
    h["cell"] = h.task + "/" + h.difficulty
    h["y"] = h.correct.astype(float)
    h["ltok"] = np.log1p(h.rtok.astype(float))
    rows = []
    for name, d_, cols in (("whole trace, answered", h[h.scored], ["r_en"]), ("whole trace, answered, +log tokens", h[h.scored], ["r_en", "ltok"]), ("first 1000 chars, answered", h[h.scored], ["e1000"]), ("first 1000 chars, +log tokens", h[h.scored], ["e1000", "ltok"]), ("first 3000 chars, answered", h[h.scored], ["e3000"]), ("first 1000 chars, strict", h, ["e1000"]), ("whole trace, strict", h, ["r_en"])):
        d_ = d_.dropna(subset=cols)
        X_ = d_[cols] - d_.groupby("qid")[cols].transform("mean")
        y_ = d_.y - d_.groupby("qid").y.transform("mean")
        m_ = sm.OLS(y_, X_).fit(cov_type="cluster", cov_kwds={"groups": pd.factorize(d_.qid)[0]})
        rows.append({"model": name, "fe": "question", "n": len(d_), "slope EN share per 100%": round(100 * float(m_.params.iloc[0]), 1), "ci": tuple(np.round(100 * m_.conf_int().iloc[0].to_numpy(), 1)), "p": float(m_.pvalues.iloc[0]), "share mean": round(float(d_[cols[0]].mean()), 3), "share sd": round(float(d_[cols[0]].std()), 3)})
    save(rows, "think_within_hindi_slope_robust")
    print(h[["r_en", "e1000", "first_dev", "len"]].describe().round(3))
    print(h[["r_en", "ltok", "e1000"]].corr().round(3))
    h2 = h.assign(bin=pd.cut(h.e1000, [-.01, .5, .7, .8, .9, 1.0]))
    t1 = h2.groupby("bin", observed=True).agg(n=("y", "size"), acc_strict=("y", "mean"), acc_answered=("y", lambda v: v[h2.loc[v.index, "scored"]].mean()), median_tok=("rtok", "median"))
    t1.to_csv(FIG / "new_think_accuracy_by_early_english_share.csv")
    print(t1)
    e = s[M(C="Hindi en-CoT") & s.scored.to_numpy()]
    n_ = s[M(C="English CoT") & s.scored.to_numpy()]
    rows = []
    for label, tasks in (("day_of_week", ["day_of_week"]), ("all tasks", TASKS), ("no dow", [t for t in TASKS if t != "day_of_week"])):
        res = []
        ee, nn = e[e.task.isin(tasks)], n_[n_.task.isin(tasks)]
        cells = sorted((ee.task + "/" + ee.difficulty).unique())
        cix = {c: i for i, c in enumerate(cells)}
        ec, nc = (ee.task + "/" + ee.difficulty).map(cix).to_numpy(), (nn.task + "/" + nn.difficulty).map(cix).to_numpy()
        for b in range(W2.shape[0] + 1):
            we = np.ones(len(ee)) if b == W2.shape[0] else W2[b, ee.qi.to_numpy()].astype(float)
            wn = np.ones(len(nn)) if b == W2.shape[0] else W2[b, nn.qi.to_numpy()].astype(float)
            v, y = ee.verif.to_numpy(float), ee.correct.to_numpy(float)
            m1 = np.bincount(ec, weights=we * v, minlength=len(cells))
            m0 = np.bincount(ec, weights=we * (1 - v), minlength=len(cells))
            c1 = np.bincount(ec, weights=we * v * y, minlength=len(cells))
            c0 = np.bincount(ec, weights=we * (1 - v) * y, minlength=len(cells))
            act = (c1 + c0) / np.maximum(m1 + m0, 1)
            p1 = np.where(m1 > 0, c1 / np.maximum(m1, 1), act)
            p0 = np.where(m0 > 0, c0 / np.maximum(m0, 1), act)
            pv = np.bincount(nc, weights=wn * nn.verif.to_numpy(float), minlength=len(cells)) / np.maximum(np.bincount(nc, weights=wn, minlength=len(cells)), 1)
            ya = np.bincount(nc, weights=wn * nn.correct.to_numpy(float), minlength=len(cells)) / np.maximum(np.bincount(nc, weights=wn, minlength=len(cells)), 1)
            cf = p1 * pv + p0 * (1 - pv)
            res.append((act.mean(), cf.mean(), ya.mean()))
        res = np.array(res)
        pt_, bs_ = res[-1], res[:-1]
        rows.append({"cut": label, "en-CoT": p100(pt_[0]), "en-CoT at English verif rate": p100(pt_[1]), "English CoT": p100(pt_[2]), "gap": p100(pt_[2] - pt_[0]), "ci gap": ci(bs_[:, 2] - bs_[:, 0]), "closed by verif": p100(pt_[1] - pt_[0]), "ci closed": ci(bs_[:, 1] - bs_[:, 0]), "share": p100((pt_[1] - pt_[0]) / (pt_[2] - pt_[0])), "ci share": ci((bs_[:, 1] - bs_[:, 0]) / (bs_[:, 2] - bs_[:, 0]))})
    save(rows, "verif_mediation_enCoT_to_English")
    w = pair_table(s, "English CoT", "Hindi en-CoT", extra=("task", "difficulty")).reset_index()
    cc = w.groupby(["task", "difficulty"]).agg(n=("qid", "size"), en_wrong=("English CoT", lambda v: int((~v).sum())), hi_wrong=("Hindi en-CoT", lambda v: int((~v).sum()))).reset_index()
    cc.to_csv(TAB / "c5_cell_error_counts.csv", index=False)
    NUM["phi_cells"] = {"cells": len(cc), "En_wrong_le2": int((cc.en_wrong <= 2).sum()), "En_wrong_le5": int((cc.en_wrong <= 5).sum()), "En_wrong_median": float(cc.en_wrong.median()), "hi_wrong_median": float(cc.hi_wrong.median()), "defined": int(((cc.en_wrong > 0) & (cc.hi_wrong > 0) & (cc.en_wrong < cc.n) & (cc.hi_wrong < cc.n)).sum())}
    print(NUM["phi_cells"])
    d_ = s[(s.task == "date_recurrence") & (s.difficulty == "short") & s.scored]
    rows = []
    for C_ in CONDS:
        g = d_[d_.C == C_]
        acc = g.groupby("rec_k").correct.mean()
        rows.append({"cond": C_, "k1 n": int((g.rec_k == 1).sum()), "k2 n": int((g.rec_k == 2).sum()), "first50 weights": p100(g.correct.mean()), "k1": p100(acc.get(1, np.nan)), "k2": p100(acc.get(2, np.nan)), "50/50 reweighted": p100((acc.get(1, 0) + acc.get(2, 0)) / 2)})
    save(rows, "subset_short_recurrence_reweight")
    for f in ("subset_first50_vs_rest",):
        z = pd.read_csv(FIG / "new_subset_first50_vs_rest.csv")
        NUM["subset_cells_excluding_zero"] = {"n": len(z), "excl": int(z.excl0.sum()), "list": z[z.excl0][["lang", "cond", "cut", "first-rest"]].to_dict(orient="records")}
        print(NUM["subset_cells_excluding_zero"])
    rows = []
    from build import load_dataset
    ds = load_dataset("short")
    import sys as _s
    _s.path.insert(0, str(ROOT / "tools" / "temporal-reasoning-dataset" / "src"))
    from trd.templates.insertions import SIMILAR_INSERTIONS, DISSIMILAR_INSERTIONS
    for key in sorted(SIMILAR_INSERTIONS["en_US"]):
        for i, (a_, b_) in enumerate(zip(SIMILAR_INSERTIONS["en_US"][key], SIMILAR_INSERTIONS["hi_IN"][key])):
            rows.append({"kind": "similar", "template": key, "i": i, "en": a_, "hi": b_})
    dis_en, dis_hi = DISSIMILAR_INSERTIONS["en_US"], DISSIMILAR_INSERTIONS["hi_IN"]
    if isinstance(dis_en, dict):
        for key in sorted(dis_en):
            for i, (a_, b_) in enumerate(zip(dis_en[key], dis_hi[key])):
                rows.append({"kind": "dissimilar", "template": key, "i": i, "en": a_, "hi": b_})
    else:
        for i, (a_, b_) in enumerate(zip(dis_en, dis_hi)):
            rows.append({"kind": "dissimilar", "template": "all", "i": i, "en": a_, "hi": b_})
    z = pd.DataFrame(rows)
    z.to_csv(TAB / "template_distractor_pairs.csv", index=False)
    print(z.to_string())
    m_ = s[(s.C == "Hindi en-CoT") & (s.ins != "no_insertion")].copy()
    e_ = df[(df.source == "standard") & (df.lang == "en_US") & (df.cond == "cot") & (df.qn < 50)].set_index(["qid", "ins"]).sentence
    m_["en_sent"] = [e_.get((q, i)) for q, i in zip(m_.qid, m_.ins)]
    pm = m_.groupby(["ins", "task", "sentence", "en_sent"]).size().reset_index(name="n")
    pm.to_csv(TAB / "template_distractor_pairs_observed.csv", index=False)
    NUM["distractor_pair_ok"] = {"unique_pairs": len(pm), "unique_hi": int(pm.sentence.nunique()), "unique_en": int(pm.en_sent.nunique())}
    print(NUM["distractor_pair_ok"])


HIW_ = re.compile(r"[ऀ-ॣॱ-ॿ]+")
ENW_ = re.compile(r"[A-Za-z]+")


def kminus1():
    r = df[(df.task == "date_recurrence") & df.rec_offset.notna()].copy()
    r["q"] = r.rec_offset / r.rec_every
    r["kb"] = r.rec_k.astype(int).map(kbin)
    r["km1"] = r.q == r.rec_k - 1
    r["ok"] = r.q == r.rec_k
    r["minus"] = r.q == -r.rec_k
    r["today"] = r.rec_offset == 0
    sets = {"En CoT": r[(r.C == "English CoT") & (r.qn < 50)], "Hi CoT": r[(r.C == "Hindi CoT") & (r.qn < 50)], "en-CoT": r[r.C == "Hindi en-CoT"], "CLP": r[r.C == "Hindi CLP"], "En direct": r[(r.C == "English direct") & (r.qn < 50)], "Hi direct": r[(r.C == "Hindi direct") & (r.qn < 50)],
            "ron Hi CoT": r[(r.source == "ron") & (r.lang == "hi_IN") & (r.cond == "cot")], "ron En CoT": r[(r.source == "ron") & (r.lang == "en_US") & (r.cond == "cot")], "hinglish Hi": r[(r.source == "hinglish") & (r.lang == "hi_IN")]}
    rows = []
    for n, g in sets.items():
        for _, _, b in KBINS:
            e = g[g.kb == b]
            if len(e):
                rows.append({"set": n, "k": b, "n": len(e), "correct%": p100(e.ok.mean()), "backwards%": p100(e.minus.mean()), "k-1 steps%": p100(e.km1.mean()), "today%": p100(e.today.mean()), "other%": p100(1 - (e.ok | e.minus | e.km1 | e.today).mean())})
    out = save(rows, "c6_k_error_types")
    out.to_csv(FIG / "new_recurrence_error_types_by_k.csv", index=False)
    txt = []
    TOD = re.compile(r"today[^.\n]{0,60}(?:1st|first|occurrence 1|1 occurrence)|(?:1st|first)[^.\n]{0,40}(?:is|=|:|would be)[^.\n]{0,20}today|today \(?(?:the )?(?:1st|first)", re.I)
    BEF = re.compile(r"before today|prior to today|backward|previous occurrence|in the past|go(?:ing)? back", re.I)
    for x in raw("en-cot", task="date_recurrence"):
        c = x["content"] or ""
        txt.append({"id": x["id"], "today_as_first": bool(TOD.search(c)), "looks_back": bool(BEF.search(c[:600])), "head": c[:600]})
    t = pd.DataFrame(txt)
    e = r[r.C == "Hindi en-CoT"].merge(t, on="id")
    e["pat"] = np.select([e.ok, e.minus, e.km1], ["correct", "backwards", "k-1"], "other")
    d = e.groupby(["kb", "pat"]).agg(n=("id", "size"), today_as_first=("today_as_first", "mean"), looks_back=("looks_back", "mean")).reset_index()
    d[["today_as_first", "looks_back"]] = (d[["today_as_first", "looks_back"]] * 100).round(1)
    d.to_csv(TAB / "c6_trace_mechanism_k.csv", index=False)
    print(d.to_string())
    smp = e[(e.rec_k == 2) & (e.pat == "k-1")].sample(6, random_state=1)
    for _, x in smp.iterrows():
        print("##", x.id, x.answer, x["head"][:420].replace("\n", " / "))
    smp = e[(e.rec_k == 3) & (e.pat == "k-1")].sample(3, random_state=1)
    for _, x in smp.iterrows():
        print("##", x.id, x.answer, x["head"][:420].replace("\n", " / "))
    pr = pair_table(s, "English CoT", "Hindi en-CoT", extra=("task", "difficulty"))
    rr = s[s.task == "date_recurrence"]
    base = M(task="date_recurrence")
    k = s.rec_k.to_numpy(dtype=float)
    rows = []
    for label, m_ in (("k=1", base & (k == 1)), ("k=2", base & (k == 2)), ("k=3,4", base & (k >= 3) & (k <= 4)), ("k=5-8", base & (k >= 5) & (k <= 8)), ("k=9-16", base & (k >= 9) & (k <= 16)), ("k=17-32", base & (k >= 17)), ("k>=3", base & (k >= 3)), ("k>=5", base & (k >= 5))):
        rows.append({"cut": label, "En CoT": p100(A.acc(m_ & M(C="English CoT"))), "en-CoT": p100(A.acc(m_ & M(C="Hindi en-CoT"))), "Hi CoT": p100(A.acc(m_ & M(C="Hindi CoT"))), "CLP": p100(A.acc(m_ & M(C="Hindi CLP"))),
                     "gap En-enCoT": p100(A.acc(m_ & M(C="English CoT")) - A.acc(m_ & M(C="Hindi en-CoT"))), "ci": ci(A.boot(m_ & M(C="English CoT")) - A.boot(m_ & M(C="Hindi en-CoT"))),
                     "en-CoT - Hi CoT": p100(A.acc(m_ & M(C="Hindi en-CoT")) - A.acc(m_ & M(C="Hindi CoT"))), "ci2": ci(A.boot(m_ & M(C="Hindi en-CoT")) - A.boot(m_ & M(C="Hindi CoT")))})
    save(rows, "c6_recurrence_acc_by_k_with_ci")
    p_all = A.acc(M(C="English CoT")) - A.acc(M(C="Hindi en-CoT"))
    no1 = ~(base & (k == 1))
    no12 = ~(base & (k <= 2))
    NUM["gap_no_k1"] = {"gap": p100(A.acc(no1 & M(C="English CoT")) - A.acc(no1 & M(C="Hindi en-CoT"))), "ci": ci(A.boot(no1 & M(C="English CoT")) - A.boot(no1 & M(C="Hindi en-CoT"))),
                        "enCoT_acc": p100(A.acc(no1 & M(C="Hindi en-CoT"))), "HiCoT_acc": p100(A.acc(no1 & M(C="Hindi CoT")))}
    NUM["gap_no_k12"] = {"gap": p100(A.acc(no12 & M(C="English CoT")) - A.acc(no12 & M(C="Hindi en-CoT"))), "ci": ci(A.boot(no12 & M(C="English CoT")) - A.boot(no12 & M(C="Hindi en-CoT"))),
                         "enCoT_acc": p100(A.acc(no12 & M(C="Hindi en-CoT"))), "HiCoT_acc": p100(A.acc(no12 & M(C="Hindi CoT"))), "En_acc": p100(A.acc(no12 & M(C="English CoT")))}
    print(NUM["gap_no_k1"], NUM["gap_no_k12"], p100(p_all))
    rows = []
    for label, m_ in (("no k=1", no1), ("no k<=2", no12)):
        rows.append(trend_row(label, A, m_, "Hindi en-CoT"))
        rows.append(trend_row(label + " strict", ST, m_, "Hindi en-CoT"))
    save(rows, "c3_trend_k_removed")


def extra():
    rows = []
    for name, a in (("answered", A), ("strict", ST)):
        rows.append({"contrast": "English direct - Hindi direct", "conv": name, "diff": p100(a.acc(M(C="English direct")) - a.acc(M(C="Hindi direct"))), "ci": ci(a.boot(M(C="English direct")) - a.boot(M(C="Hindi direct")))})
        for ins in INS:
            rows.append({"contrast": f"English direct - Hindi direct {ins}", "conv": name, "diff": p100(a.acc(M(C="English direct", ins=ins)) - a.acc(M(C="Hindi direct", ins=ins))), "ci": ci(a.boot(M(C="English direct", ins=ins)) - a.boot(M(C="Hindi direct", ins=ins)))})
    save(rows, "direct_gap")


SECTIONS = {k: v for k, v in list(globals().items()) if k in ("c1", "c2", "trend", "part_a", "dist", "mentions", "agree", "recur", "dow", "decomp", "think", "verif", "subset", "batch", "misc", "kminus1", "extra")}

if __name__ == "__main__":
    for name in (sys.argv[1:] or SECTIONS):
        SECTIONS[name]()
    path = OUT / "numbers.json"
    old = json.load(open(path, encoding="utf-8")) if path.exists() else {}
    with open(path, "w", encoding="utf-8") as f:
        json.dump({**old, **NUM}, f, indent=2, ensure_ascii=False, default=str)
