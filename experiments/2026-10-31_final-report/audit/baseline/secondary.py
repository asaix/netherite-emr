import warnings

import statsmodels.api as sm
import statsmodels.formula.api as smf
from scipy.stats import binomtest, fisher_exact

from stats_core import *

warnings.simplefilter("ignore")
R = {}
A = F[F.answered]
MID = set(json.load(open(CACHE / "mid_qids.json")))
F["in_mid"] = F.qid.isin(MID)


def mh(sub, exp, y="acc", strata=("task", "level")):
    r, s, pq, ps_qr, qs, vr, num, den, var = 0.0, 0.0, 0.0, 0.0, 0.0, 0, 0.0, 0.0, 0.0
    nstr = 0
    for _, g in sub.groupby(list(strata)):
        e, c = g[exp].astype(bool).to_numpy(), (g[y] == 1).to_numpy()
        a, b, cc, d = (e & c).sum(), (e & ~c).sum(), (~e & c).sum(), (~e & ~c).sum()
        n = a + b + cc + d
        if not (a + b) or not (cc + d):
            continue
        nstr += 1
        Ri, Si = a * d / n, b * cc / n
        Pi, Qi = (a + d) / n, (b + cc) / n
        r += Ri
        s += Si
        pq += Pi * Ri
        ps_qr += Pi * Si + Qi * Ri
        qs += Qi * Si
        num += a - (a + b) * (a + cc) / n
        var += (a + b) * (cc + d) * (a + cc) * (b + d) / (n * n * (n - 1)) if n > 1 else 0
    if s == 0 or r == 0:
        return {"or": None, "strata": nstr}
    or_ = r / s
    se = np.sqrt(pq / (2 * r * r) + ps_qr / (2 * r * s) + qs / (2 * s * s))
    from scipy.stats import chi2
    p = float(chi2.sf(num * num / var, 1)) if var > 0 else float("nan")
    return {"or": round(float(or_), 3), "lo": round(float(np.exp(np.log(or_) - 1.96 * se)), 3), "hi": round(float(np.exp(np.log(or_) + 1.96 * se)), 3), "p": p, "strata": nstr}


def boot_mh(sub, exp, y="acc", nb=500, seed=1):
    W2 = W[:nb]
    r, sv = np.zeros(nb), np.zeros(nb)
    for _, g in sub.groupby(["task", "level"]):
        e, c, q = g[exp].astype(bool).to_numpy(), (g[y] == 1).to_numpy(), g.q.to_numpy()
        ca = np.bincount(q[e & c], minlength=NQ).astype(np.float32)
        cb = np.bincount(q[e & ~c], minlength=NQ).astype(np.float32)
        cc = np.bincount(q[~e & c], minlength=NQ).astype(np.float32)
        cd = np.bincount(q[~e & ~c], minlength=NQ).astype(np.float32)
        A, Bb, C, D = W2 @ ca, W2 @ cb, W2 @ cc, W2 @ cd
        n = A + Bb + C + D
        n[n == 0] = 1
        r += A * D / n
        sv += Bb * C / n
    ors = np.log(r / np.where(sv == 0, np.nan, sv))
    lo, hi = np.nanpercentile(ors, [2.5, 97.5])
    return [round(float(np.exp(lo)), 3), round(float(np.exp(hi)), 3)]


# mention
M = {}
for lang in LANGS:
    for kind, name in (("sim", "similar"), ("dis", "dissimilar")):
        ins = F[mask(lang=lang, cond="cot", insertion=f"{name}_insertion") & F[f"men_{kind}"].notna().to_numpy()].copy()
        plc = F[mask(lang=lang, cond="cot", insertion="no_insertion") & F[f"men_{kind}"].notna().to_numpy()]
        ins["m"] = ins[f"men_{kind}"].astype(bool)
        ins["m_nq"] = ins[f"men_nq_{kind}"].astype(bool)
        allq = F[mask(lang=lang, cond="cot", insertion=f"{name}_insertion")]
        ent = {"rate": pct(ins.m.mean()), "placebo": pct(plc[f"men_{kind}"].astype(bool).mean()), "n": len(ins), "excess": pct(ins.m.mean() - plc[f"men_{kind}"].astype(bool).mean()), "acc_mention": pct(ins[ins.m].acc.mean()), "acc_no_mention": pct(ins[~ins.m].acc.mean()), "mh": mh(ins, "m"), "mh_cluster_ci": boot_mh(ins, "m"), "quote_rate": pct(allq[f"quote_{kind}"].astype(bool).mean()), "rate_excl_verbatim": pct(ins.m_nq.mean()), "mh_excl_verbatim": mh(ins, "m_nq")}
        for scope, sub in (("new", ins[~ins.qid.isin(MID)]), ("mid", ins[ins.qid.isin(MID)])):
            ent[f"mh_{scope}"] = mh(sub, "m")
        ent["by_task"] = {t: {"rate": pct(g.m.mean()), "or": mh(g, "m").get("or"), "n": len(g)} for t, g in ins.groupby("task")}
        M[f"{lang}/{name}"] = ent
R["mention"] = M

# reuse
RU = {}
for lang in LANGS:
    for cond in ("direct", "cot"):
        for kind, name in (("sim", "similar"), ("dis", "dissimilar")):
            a = F[mask(lang=lang, cond=cond, insertion=f"{name}_insertion") & F[f"reuse_{kind}"].notna().to_numpy()]
            b = F[mask(lang=lang, cond=cond, insertion="no_insertion") & F[f"reuse_{kind}"].notna().to_numpy()]
            x, n1, y, n2 = int(a[f"reuse_{kind}"].astype(bool).sum()), len(a), int(b[f"reuse_{kind}"].astype(bool).sum()), len(b)
            idx = f"{kind}_idx"
            by = a.groupby(["task", idx])[f"reuse_{kind}"].agg(lambda s: int(s.astype(bool).sum())).sort_values(ascending=False)
            RU[f"{lang}/{cond}/{name}"] = {"inserted": x, "inserted_n": n1, "placebo": y, "placebo_n": n2, "rate": pct(x / n1) if n1 else None, "placebo_rate": pct(y / n2) if n2 else None, "fisher_p": float(fisher_exact([[x, n1 - x], [y, n2 - y]])[1]) if n1 and n2 else None, "top_sentence_share": round(float(by.iloc[:3].sum() / max(x, 1)), 3), "top": {f"{t}#{i}": int(v) for (t, i), v in by.iloc[:3].items()}}
R["reuse"] = RU

# traces
T = {}
for lang in LANGS:
    c = F[mask(lang=lang, cond="cot")]
    s = c[c.answered].copy()
    tot = s.hi_w + s.en_w
    tar = s.hi_w if lang == "hi_IN" else s.en_w
    s["ratio"] = tar / tot.where(tot > 0)
    s["drift"] = s.ratio < 0.9
    T[lang] = {"unscored_pct": pct((~c.answered).mean()), "median_words": float(tot.median()), "median_tokens": float(s.ctok.median()), "tlr_pooled": round(float(tar.sum() / tot.sum()), 3), "tlr_mean": round(float(s.ratio.mean()), 3), "below_09": pct(s.drift.mean()), "n_below_09": int(s.drift.sum()), "verification": pct(s.verif.mean()), "acc_drift": pct(s[s.drift].acc.mean()) if s.drift.any() else None, "acc_nodrift": pct(s[~s.drift].acc.mean()), "wrong": int((s.acc == 0).sum())}
    T[lang]["verification_mh"] = mh(s, "verif")
    T[lang]["verif_acc_with"], T[lang]["verif_acc_without"] = pct(s[s.verif].acc.mean()), pct(s[~s.verif].acc.mean())
    T[lang]["verif_by_task"] = {t: {"rate": pct(g.verif.mean()), "or": mh(g, "verif").get("or")} for t, g in s.groupby("task")}
    if lang == "hi_IN":
        T[lang]["drift_mh"] = mh(s, "drift")
        T[lang]["drift_cluster_ci"] = boot_mh(s, "drift")
        T[lang]["drift_by_task"] = {t: {"n": int(g.drift.sum()), "acc_drift": pct(g[g.drift].acc.mean()) if g.drift.any() else None, "acc_nodrift": pct(g[~g.drift].acc.mean()), "or": mh(g, "drift").get("or")} for t, g in s.groupby("task")}
        T[lang]["drift_mh_new"] = mh(s[~s.qid.isin(MID)], "drift")
        T[lang]["drift_by_ins"] = {i: {"n": int(g.drift.sum()), "rate": pct(g.drift.mean()), "or": mh(g, "drift").get("or")} for i, g in s.groupby("insertion")}
        dow = s[s.task == "day_of_week"]
        T[lang]["drift_share_dow"] = round(float(dow.drift.sum() / s.drift.sum()), 3)
    if lang == "en_US":
        T[lang]["verif_cluster_ci"] = boot_mh(s, "verif")
        T[lang]["verif_mh_new"] = mh(s[~s.qid.isin(MID)], "verif")
R["trace"] = T

# agreement
pairs = A.pivot_table(index=["qid", "task", "level", "insertion", "cond", "q"], columns="lang", values="acc").dropna().reset_index()
AG = {}
for cond in ("direct", "cot"):
    p = pairs[pairs.cond == cond]
    en, hi = p.en_US == 1, p.hi_IN == 1
    phis, adj, ors, wgt = [], [], [], []
    rec = []
    for (lv, t), g in p.groupby(["level", "task"]):
        e, h = g.en_US == 1, g.hi_IN == 1
        pe, ph = e.mean(), h.mean()
        den = np.sqrt(pe * (1 - pe) * ph * (1 - ph))
        if den:
            ph_ = ((e & h).mean() - pe * ph) / den
            a, b = sorted([pe, ph])
            mx = np.sqrt(a * (1 - b) / ((1 - a) * b))
            phis.append(ph_)
            adj.append(ph_ / mx)
            rec.append({"cond": cond, "level": lv, "task": t, "phi": round(float(ph_), 3), "phi_max": round(float(mx), 3), "n": len(g), "acc_en": round(float(pe), 3), "acc_hi": round(float(ph), 3)})
    m = mh(p.assign(ex=~en), "ex", y="hi_IN")
    w_e = (~en)
    AG[cond] = {"pairs": len(p), "both_right": int((en & hi).sum()), "both_wrong": int((~en & ~hi).sum()), "en_only": int((en & ~hi).sum()), "hi_only": int((~en & hi).sum()), "sign_p": float(binomtest(int((en & ~hi).sum()), int((en ^ hi).sum()), 0.5).pvalue), "median_phi": round(float(np.median(phis)), 3), "phi_iqr": [round(float(x), 3) for x in np.percentile(phis, [25, 75])], "cells": len(phis), "median_phi_over_max": round(float(np.median(adj)), 3), "mh_or_hindi_right_given_english_wrong": m}
    AG[cond]["p_hi_wrong_given_en_wrong"] = pct((~hi)[~en].mean())
    AG[cond]["p_hi_wrong_given_en_right"] = pct((~hi)[en].mean())
    AG[f"{cond}_phi_cells"] = rec
    qp = p.groupby(["q", "level", "task"])[["en_US", "hi_IN"]].mean().reset_index()
    cs = []
    for _, g in qp.groupby(["level", "task"]):
        if g.en_US.std() and g.hi_IN.std():
            cs.append(np.corrcoef(g.en_US, g.hi_IN)[0, 1])
    AG[cond]["question_level_median_r"] = round(float(np.median(cs)), 3)
    AG[cond]["question_level_r_cells"] = len(cs)
    AG[cond]["question_level_positive_cells"] = int(sum(c > 0 for c in cs))
R["agreement"] = {k: v for k, v in AG.items() if not k.endswith("cells")}
pd.DataFrame(AG["direct_phi_cells"] + AG["cot_phi_cells"]).to_csv(FIG / "phi_by_cell.csv", index=False)

# recurrence
rc = F[(F.task == "date_recurrence") & F.rec.notna()]
rows = []
for (lang, cond, k), g in rc.groupby(["lang", "cond", "k"]):
    vc = g.rec.value_counts(normalize=True)
    rows.append({"lang": lang, "cond": cond, "k": int(k), "n": len(g), **{c: round(100 * float(vc.get(c, 0)), 1) for c in ("correct", "first_step", "mirror", "other")}})
RK = pd.DataFrame(rows)
RK.to_csv(FIG / "recurrence_by_k.csv", index=False)
rows = []
for (lang, cond, lv, k), g in rc[rc.k <= 4].groupby(["lang", "cond", "level", "k"]):
    vc = g.rec.value_counts(normalize=True)
    rows.append({"lang": lang, "cond": cond, "level": lv, "k": int(k), "n": len(g), **{c: round(100 * float(vc.get(c, 0)), 1) for c in ("correct", "first_step", "mirror", "other")}})
pd.DataFrame(rows).to_csv(FIG / "recurrence_by_level_k.csv", index=False)
R["recurrence_overall"] = {f"{l}/{c}": {**{k: pct(v) for k, v in g.rec.value_counts(normalize=True).items()}, "n": len(g)} for (l, c), g in rc.groupby(["lang", "cond"])}
R["recurrence_level_share"] = {f"{l}/{c}/{lv}": {**{k: pct(v) for k, v in g.rec.value_counts(normalize=True).items()}, "n": len(g)} for (l, c, lv), g in rc.groupby(["lang", "cond", "level"])}
base = F[mask(task="date_recurrence")]
lowk = {}
for lang in LANGS:
    for cond in ("direct", "cot"):
        s = base[(base.lang == lang) & (base.cond == cond) & base.answered]
        lowk[f"{lang}/{cond}"] = {"acc_all": pct(s.acc.mean()), "acc_k1": pct(s[s.k == 1].acc.mean()), "acc_k2": pct(s[s.k == 2].acc.mean()), "acc_k3plus": pct(s[s.k >= 3].acc.mean()), "share_errors_k1": pct((s.k == 1)[s.acc == 0].mean()), "share_errors_k2": pct((s.k == 2)[s.acc == 0].mean()), "mirror_share_at_k1": pct((s.k == 1)[s.rec == "mirror"].mean()) if (s.rec == "mirror").any() else None}
R["recurrence_k_summary"] = lowk

# day of week
dw = F[(F.task == "day_of_week") & F.dow_off.notna()]
R["dow_offsets"] = {f"{l}/{c}": {str(int(k)): pct(v) for k, v in g.dow_off.value_counts(normalize=True).sort_index().items()} for (l, c), g in dw.groupby(["lang", "cond"])}
R["dow_mode"] = {f"{l}/{c}": {str(int(g.dow_pred.value_counts().index[0])): pct(g.dow_pred.value_counts(normalize=True).iloc[0])} for (l, c), g in dw.groupby(["lang", "cond"])}
R["dow_cot_level"] = {f"{l}/{lv}": {"plus1": pct((g.dow_off == 1).mean()), "zero": pct((g.dow_off == 0).mean()), "minus1": pct((g.dow_off == -1).mean()), "n": len(g)} for (l, lv), g in dw[dw.cond == "cot"].groupby(["lang", "level"])}
R["dow_gold_spread"] = {str(k): pct(v) for k, v in F[(F.task == "day_of_week") & (F.lang == "en_US") & (F.cond == "direct") & (F.insertion == "no_insertion")].gold.value_counts(normalize=True).items()}
R["dow_lang_mismatch"] = {f"{l}/{c}": int(((g.lang == "hi_IN") & g.p_ans.fillna("").str.fullmatch("[A-Za-z]+") | (g.lang == "en_US") & g.p_ans.fillna("").str.contains("[ऀ-ॿ]")).sum()) for (l, c), g in F[F.task == "day_of_week"].groupby(["lang", "cond"])}

# error types
EXPECT = {}


def classify(row):
    t, a, g = row.task, row.p_ans, row.gold
    k = {"date_addition": "d", "date_subtraction": "d", "date_recurrence": "d", "interval_date": "i", "time_addition": "t", "time_subtraction": "t", "date_duration": "n", "time_duration": "n", "day_of_week": "w"}[t]
    if k == "w":
        return "off_by_one" if row.dow_off in (1, -1) else "other"
    if k == "n":
        m = re.fullmatch(r"-?\d+", a)
        if not m:
            return "other"
        return "off_by_one" if abs(int(a) - int(g)) == 1 else "other"
    if k == "t":
        if not re.fullmatch(r"\d{1,2}:\d{2}", a):
            return "other"
        am, gm = int(a[:-3]) * 60 + int(a[-2:]), int(g[:2]) * 60 + int(g[3:])
        e = (am - gm + 720) % 1440 - 720
        return "off_by_one" if abs(e) == 1 else "other"
    if k == "i":
        ds = re.findall(r"\d{4}-\d{2}-\d{2}", a)
        gs = g.split(" to ")
        if len(ds) < 2:
            return "other"
        try:
            s = [(date.fromisoformat(x) - date.fromisoformat(y)).days for x, y in zip(ds, gs)]
        except ValueError:
            return "other"
        if s[0] == s[1] and s[0] % 7 == 0:
            return "week_shift"
        return "off_by_one" if all(abs(x) <= 1 for x in s) else "other"
    try:
        d = (date.fromisoformat(a) - date.fromisoformat(g)).days
    except ValueError:
        return "other"
    return "off_by_one" if abs(d) == 1 else "other"


E_ = F[(F.cond == "cot") & (F.acc == 0)].copy()
E_["etype"] = [classify(r) for r in E_.itertuples()]
R["errors_cot"] = {l: {"n": len(g), "off_by_one": pct((g.etype == "off_by_one").mean())} for l, g in E_.groupby("lang")}
R["errors_cot_task"] = {f"{l}/{t}": {"n": len(g), "off_by_one": pct((g.etype == "off_by_one").mean())} for (l, t), g in E_.groupby(["lang", "task"])}

# time 12 hour
tm = lambda s: int(s[:2]) * 60 + int(s[3:5])
TT = F[F.task.isin(["time_addition", "time_subtraction"]) & F.p_ans.fillna("").str.fullmatch(r"\d{2}:\d{2}")].copy()
TT["off"] = (TT.p_ans.map(tm) - TT.gold.map(tm)) % 1440
R["twelve_hour"] = {f"{l}/{c}": {"answers": len(g), "wrong": int((g.acc == 0).sum()), "off_12h": int((g.off == 720).sum()), "share_of_wrong": pct((g.off == 720).sum() / max((g.acc == 0).sum(), 1)), "acc": pct(g.acc.mean()), "acc_if_12h_accepted": pct(((g.acc == 1) | (g.off == 720)).mean())} for (l, c), g in TT.groupby(["lang", "cond"])}

# interval taxonomy
IV = F[(F.task == "interval_date") & F.answered].copy()


def ivshift(r):
    ds = re.findall(r"\d{4}-\d{2}-\d{2}", r.p_ans)
    gs = r.gold.split(" to ")
    if len(ds) != 2:
        return "unparsed"
    try:
        a, b = date.fromisoformat(ds[0]), date.fromisoformat(ds[1])
    except ValueError:
        return "invalid_date"
    s0, s1 = (a - date.fromisoformat(gs[0])).days, (b - date.fromisoformat(gs[1])).days
    if s0 == 0 and s1 == 0:
        return "correct"
    if (b - a).days != 6:
        return "span_not_7_days"
    if s0 == -1:
        return "sunday_start"
    if s0 % 7 == 0:
        return "week_shift"
    if a.weekday() == 0:
        return "monday_other"
    return "not_monday"


IV["kind"] = [ivshift(r) for r in IV.itertuples()]
R["interval_kinds"] = {f"{l}/{c}": {k: pct(v) for k, v in g.kind.value_counts(normalize=True).items()} for (l, c), g in IV.groupby(["lang", "cond"])}
pd.DataFrame([{"key": k, **v} for k, v in R["interval_kinds"].items()]).to_csv(FIG / "interval_error_kinds.csv", index=False)

# direct compliance
D_ = F[F.cond == "direct"].copy()
D_["words"] = D_.hi_w + D_.en_w
D_["reasons"] = D_.words > 12
R["direct_compliance"] = {f"{l}": {"pct_over_12_words": pct(g.reasons.mean()), "pct_over_50_tokens": pct((g.ctok > 50).mean()), "median_tok": float(g.ctok.median()), "acc_compliant": pct(g[~g.reasons].acc.mean()), "acc_reasoning": pct(g[g.reasons].acc.mean())} for l, g in D_.groupby("lang")}
rows = []
for (l, t), g in D_.groupby(["lang", "task"]):
    rows.append({"lang": l, "task": t, "pct_over_12_words": pct(g.reasons.mean()), "acc_compliant": pct(g[~g.reasons].acc.mean()), "acc_reasoning": pct(g[g.reasons].acc.mean()) if g.reasons.any() else None, "n_reasoning": int(g.reasons.sum())})
pd.DataFrame(rows).to_csv(FIG / "direct_compliance_by_task.csv", index=False)
D_c = D_[~D_.reasons]
R["cot_delta_vs_compliant_direct"] = {}
for l in LANGS:
    cot_ = F[mask(lang=l, cond="cot")].acc.mean()
    R["cot_delta_vs_compliant_direct"][l] = {"direct_compliant_acc": pct(D_c[D_c.lang == l].acc.mean()), "cot_acc": pct(cot_), "delta": pct(cot_ - D_c[D_c.lang == l].acc.mean())}
    R["cot_delta_vs_compliant_direct"][l]["by_task"] = {t: pct(F[mask(lang=l, cond="cot", task=t)].acc.mean() - g.acc.mean()) for t, g in D_c[D_c.lang == l].groupby("task")}

# logit
d = A.copy()
d["cot"] = (d.cond == "cot").astype(int)
d["hindi"] = (d.lang == "hi_IN").astype(int)
d["sim"] = (d.insertion == "similar_insertion").astype(int)
d["dis"] = (d.insertion == "dissimilar_insertion").astype(int)
d["lvl"] = d.level.map({l: i for i, l in enumerate(LEVELS)})
d["cell"] = d.task + "/" + d.level + "/" + d.lang + "/" + d.cond
d["y"] = d.acc
s = F.copy()
s["cot"] = (s.cond == "cot").astype(int)
s["hindi"] = (s.lang == "hi_IN").astype(int)
s["sim"] = (s.insertion == "similar_insertion").astype(int)
s["dis"] = (s.insertion == "dissimilar_insertion").astype(int)
s["lvl"] = s.level.map({l: i for i, l in enumerate(LEVELS)})
s["cell"] = s.task + "/" + s.level + "/" + s.lang + "/" + s.cond
s["y"] = s.strict
CON = {"en_cot_x_sim": "cot:sim = 0", "hi_cot_x_sim": "cot:sim + cot:sim:hindi = 0", "hi_vs_en_cot_x_sim": "cot:sim:hindi = 0", "en_cot_x_dis": "cot:dis = 0", "hi_cot_x_dis": "cot:dis + cot:dis:hindi = 0", "hi_vs_en_cot_x_dis": "cot:dis:hindi = 0", "en_sim_direct": "sim = 0", "hi_sim_direct": "sim + sim:hindi = 0"}


def fit(fm, data):
    return smf.glm(fm, data, family=sm.families.Binomial()).fit(cov_type="cluster", cov_kwds={"groups": data["q"]})


def od(m, e):
    t = m.t_test(e)
    lo, hi = t.conf_int()[0]
    return {"or": round(float(np.exp(t.effect[0])), 3), "lo": round(float(np.exp(lo)), 3), "hi": round(float(np.exp(hi)), 3), "p": round(float(t.pvalue), 4)}


LG = {}
SPEC = {"task_level_fe": "y ~ cot * sim * hindi + cot * dis * hindi + C(task) + C(level)", "cell_fe": "y ~ C(cell) + cot * sim * hindi + cot * dis * hindi - cot - hindi - cot:hindi"}
QJAN = (F.task == "date_recurrence") & (F.sim_idx == 4)
for nm, fm in SPEC.items():
    for sc, data in (("answered", d), ("strict", s)):
        m = fit(fm, data)
        LG[f"{nm}/{sc}"] = {"n": int(m.nobs), "converged": bool(m.converged), **{k: od(m, v) for k, v in CON.items()}}
        del m
for sc, data in (("answered", d), ("strict", s)):
    keep = data[~((data.task == "date_recurrence") & (data.sim_idx == 4))]
    m = fit(SPEC["cell_fe"], keep)
    LG[f"cell_fe/{sc}/drop_recurrence_january_sentence"] = {"n": int(m.nobs), **{k: od(m, v) for k, v in CON.items()}}
    del m
    keep = data[data.task != "date_recurrence"]
    m = fit(SPEC["cell_fe"], keep)
    LG[f"cell_fe/{sc}/drop_recurrence"] = {"n": int(m.nobs), **{k: od(m, v) for k, v in CON.items()}}
    del m
tr = fit("y ~ C(task) + lvl * cot * hindi", d)
LG["difficulty_trend"] = {"n": int(tr.nobs), "gap_per_level_direct": od(tr, "lvl:hindi = 0"), "gap_per_level_cot": od(tr, "lvl:hindi + lvl:cot:hindi = 0"), "cot_per_level_en": od(tr, "lvl:cot = 0"), "cot_per_level_hi": od(tr, "lvl:cot + lvl:cot:hindi = 0")}
hi_ = d[d.hindi == 1]
tr2 = fit("y ~ C(task) * cot + C(level) * cot + cot * sim * lvl + cot * dis * lvl - lvl - cot:lvl", hi_)
LG["hindi_penalty_trend"] = {"n": int(tr2.nobs), "cot_x_sim_per_level": od(tr2, "cot:sim:lvl = 0"), "cot_x_dis_per_level": od(tr2, "cot:dis:lvl = 0")}
R["logit"] = LG

# LPM check for points
for sc, data in (("answered", d), ("strict", s)):
    m = smf.ols("y ~ C(cell) + cot * sim * hindi + cot * dis * hindi - cot - hindi - cot:hindi", data).fit(cov_type="cluster", cov_kwds={"groups": data["q"]})
    out = {}
    for k, v in (("en_sim", "cot:sim = 0"), ("hi_sim", "cot:sim + cot:sim:hindi = 0"), ("hi_vs_en_sim", "cot:sim:hindi = 0"), ("en_dis", "cot:dis = 0"), ("hi_dis", "cot:dis + cot:dis:hindi = 0"), ("hi_vs_en_dis", "cot:dis:hindi = 0")):
        t = m.t_test(v)
        lo, hi = t.conf_int()[0]
        out[k] = {"pts": round(float(-100 * t.effect[0]), 2), "lo": round(float(-100 * hi), 2), "hi": round(float(-100 * lo), 2), "p": round(float(t.pvalue), 4)}
    R[f"lpm_penalty/{sc}"] = out
    del m

# sentence-level inference
SL = {}
L = pd.read_csv(FIG / "rq2_loso.csv")
for (sc, ins, lang), g in L.groupby(["scoring", "ins", "lang"]):
    v = g.sent_penalty.to_numpy()
    rng = np.random.default_rng(3)
    b = np.array([v[rng.integers(0, len(v), len(v))].mean() for _ in range(5000)])
    SL[f"{sc}/{ins}/{lang}"] = {"k": len(v), "mean": round(float(v.mean()), 2), "boot_ci": [round(float(x), 2) for x in np.percentile(b, [2.5, 97.5])], "t_p": round(float(ttest_1samp(v, 0).pvalue), 4), "positive": int((v > 0).sum()), "min_loso": round(float(g.loo_all_tasks.min()), 2), "max_loso": round(float(g.loo_all_tasks.max()), 2), "min_loso_lo": round(float(g.loo_all_lo.min()), 2), "max_loso_hi": round(float(g.loo_all_hi.max()), 2)}
    wide = g.set_index(["task", "sent_idx"]).sent_penalty
R["sentence_level"] = SL
wide = L[L.scoring == "strict"].pivot_table(index=["ins", "task", "sent_idx"], columns="lang", values="sent_penalty").reset_index()
SI = {}
for ins, g in wide.groupby("ins"):
    v = (g.hi_IN - g.en_US).to_numpy()
    rng = np.random.default_rng(4)
    b = np.array([v[rng.integers(0, len(v), len(v))].mean() for _ in range(5000)])
    SI[ins] = {"mean": round(float(v.mean()), 2), "boot_ci": [round(float(x), 2) for x in np.percentile(b, [2.5, 97.5])], "t_p": round(float(ttest_1samp(v, 0).pvalue), 4)}
R["sentence_level_interaction_strict"] = SI

# replication groups
RP = {}
newq = ~F.qid.isin(MID).to_numpy()
vvl = mask(level="very_very_long")
for lang in LANGS:
    for ins in INS[1:]:
        for g, m_ in (("mid", ~newq), ("new", newq), ("new_first4", newq & ~vvl), ("new_vvl", newq & vvl)):
            RP[f"{lang}/{ins}/{g}"] = {k: penalty(mask(lang=lang) & m_, ins)[k] for k in ("v", "lo", "hi", "n_q")}
    for t in ("date_duration", "time_duration", "date_recurrence", "day_of_week"):
        RP[f"{lang}/similar_insertion/{t}/new"] = {k: penalty(mask(lang=lang, task=t) & newq, "similar_insertion")[k] for k in ("v", "lo", "hi", "n_q")}
        RP[f"{lang}/similar_insertion/{t}/mid"] = {k: penalty(mask(lang=lang, task=t) & ~newq, "similar_insertion")[k] for k in ("v", "lo", "hi", "n_q")}
    RP[f"{lang}/cot_delta/new"] = {k: cot_delta(mask(lang=lang) & newq)[k] for k in ("direct", "cot", "v", "lo", "hi")}
    RP[f"{lang}/cot_delta/mid"] = {k: cot_delta(mask(lang=lang) & ~newq)[k] for k in ("direct", "cot", "v", "lo", "hi")}
R["replication"] = RP
R["robust_no_recurrence"] = {f"{l}/{i}": {k: penalty(mask(lang=l) & ~mask(task="date_recurrence"), i)[k] for k in ("v", "lo", "hi")} for l in LANGS for i in INS[1:]}

# other
c = F[~F.answered]
R["cutoffs"] = {"unanswered": len(c), "unanswered_finish": c.finish.value_counts().to_dict(), "by_cell": {f"{a}/{b}": int(v) for (a, b), v in c.groupby(["lang", "cond"]).size().items()}, "finish_length_total": int((F.finish == "length").sum()), "answered_with_length": int(((F.finish == "length") & F.answered).sum()), "answered_with_length_correct": int(((F.finish == "length") & (F.acc == 1)).sum()), "scored": int(F.answered.sum())}
R["cutoffs"]["pct_by_cell"] = {f"{a}/{b}": pct(g.answered.eq(False).mean()) for (a, b), g in F.groupby(["lang", "cond"])}
R["jan_sentence"] = {}
J = F[mask(task="date_recurrence", cond="cot", insertion="similar_insertion") & (F.sim_idx == 4)]
R["jan_sentence"] = {l: {"questions": len(g), "finish_length": int((g.finish == "length").sum()), "unanswered": int((~g.answered).sum()), "acc_answered": pct(g.acc.mean()), "strict": pct(g.strict.mean()), "median_tokens": float(g.ctok.median())} for l, g in J.groupby("lang")}
dump(R, "results_secondary.json")
print("ok")
