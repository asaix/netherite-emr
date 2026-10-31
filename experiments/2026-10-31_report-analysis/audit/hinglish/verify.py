import json
import re
import warnings
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy.stats import binomtest, spearmanr
from statsmodels.stats.contingency_tables import StratifiedTable
from statsmodels.stats.multitest import multipletests

from features import DIFFS, ROOT, SCRIPT_DAY, TASKS, answer_of, build, score

warnings.filterwarnings("ignore")
OUT = Path(__file__).resolve().parent
RES, FIG = OUT / "results", OUT / "fig_data"
RES.mkdir(exist_ok=True)
FIG.mkdir(exist_ok=True)
INS = ["no_insertion", "similar_insertion", "dissimilar_insertion"]
LANGS = ["en_US", "hi_IN"]
FIVE = ["date_addition", "date_subtraction", "date_duration", "date_recurrence", "day_of_week"]
KEY = ["qid", "difficulty", "task", "qnum", "language", "insertion"]
B = 2000
N = {}

df = build().reset_index(drop=True)
df["dshare"] = (df.n_deva / (df.n_deva + df.n_latin).replace(0, np.nan)).fillna(0)
df["fshare"] = (df.fn_wide / df.n_latin.replace(0, np.nan)).fillna(0)
df["style"] = np.where(df.dshare >= 0.10, "devanagari", np.where(df.fshare >= 0.05, "roman", "plain"))
df["style_text"] = np.where(df.dshare >= 0.10, "devanagari", np.where((df.n_deva == 0) & (df.fshare >= 0.05), "roman", "plain"))
order = df[df.condition.isin(["direct", "cot"])].qid.drop_duplicates().tolist()
QI = {q: i for i, q in enumerate(order)}
df["qi"] = df.qid.map(QI)
Q = len(order)
RNG = np.random.default_rng(0)
W = np.stack([np.bincount(RNG.integers(0, Q, Q), minlength=Q) for _ in range(B)])


def sel(**kw):
    m = np.ones(len(df), bool)
    for k, v in kw.items():
        m &= df[k].isin(v).to_numpy() if isinstance(v, (list, tuple, set)) else (df[k] == v).to_numpy()
    return m


def stat(mask, strict=False):
    s = df[mask] if strict else df[mask & df.answered.to_numpy()]
    c = np.bincount(s.qi, weights=s.correct.astype(float), minlength=Q)
    n = np.bincount(s.qi, minlength=Q).astype(float)
    return c.sum() / n.sum(), (W @ c) / (W @ n)


def ci(b):
    lo, hi = np.percentile(b, [2.5, 97.5])
    return float(lo), float(hi)


def pts(x):
    return round(100 * float(x), 2)


def contrast(ma, mb, strict=False):
    a, ba = stat(ma, strict)
    b, bb = stat(mb, strict)
    lo, hi = ci(ba - bb)
    return {"a": pts(a), "b": pts(b), "diff": pts(a - b), "lo": pts(lo), "hi": pts(hi)}


wide = df[df.condition == "hinglish"][KEY + ["qi", "answered", "correct", "correct_lenient", "tokens", "finish", "style", "style_text", "dshare", "fshare", "verif_orig", "verif_ext", "after_first_ans", "n_steps", "n_dates", "n_clock", "n_nums", "n_latin", "n_deva", "chars", "answer", "gold"]].rename(columns={"answered": "ans_h", "correct": "ok_h", "tokens": "tok_h", "verif_orig": "vo_h", "verif_ext": "ve_h", "after_first_ans": "afa_h", "answer": "a_h", "n_steps": "steps_h"})
for c, s in (("cot", "s"), ("direct", "d"), ("en-cot", "e")):
    t = df[df.condition == c][["qid", "language", "insertion", "answered", "correct", "tokens", "verif_orig", "verif_ext", "after_first_ans", "answer", "n_deva", "n_latin", "n_steps"]].rename(columns={"answered": f"ans_{s}", "correct": f"ok_{s}", "tokens": f"tok_{s}", "verif_orig": f"vo_{s}", "verif_ext": f"ve_{s}", "after_first_ans": f"afa_{s}", "answer": f"a_{s}", "n_deva": f"deva_{s}", "n_latin": f"lat_{s}", "n_steps": f"steps_{s}"})
    wide = wide.merge(t, on=["qid", "language", "insertion"], how="left")
for col in ("ok_e", "ans_e"):
    wide[col] = wide[col].astype(object)


def flip_p(d, qi, flips=10000, seed=1):
    rng = np.random.default_rng(seed)
    v = pd.Series(np.asarray(d, float)).groupby(np.asarray(qi)).sum().to_numpy()
    obs = abs(v.sum())
    hits = 0
    for _ in range(flips // 1000):
        s = rng.integers(0, 2, (1000, len(v)), dtype=np.int8) * 2 - 1
        hits += (np.abs(s @ v) >= obs - 1e-9).sum()
    return float((hits + 1) / (flips + 1))


def mcn(a, b):
    x, y = int((a & ~b).sum()), int((~a & b).sum())
    return x, y, float(binomtest(x, x + y, 0.5).pvalue) if x + y else 1.0


def paired(w, a, b, sa, sb, qi="qi"):
    both = w[w[sa].astype(bool) & w[sb].astype(bool)]
    x, y, p = mcn(both[a].astype(bool).to_numpy(), both[b].astype(bool).to_numpy())
    xs, ys, ps = mcn((w[a].astype(bool) & w[sa].astype(bool)).to_numpy(), (w[b].astype(bool) & w[sb].astype(bool)).to_numpy())
    d = both[a].astype(float) - both[b].astype(float)
    ds = (w[a].astype(bool) & w[sa].astype(bool)).astype(float) - (w[b].astype(bool) & w[sb].astype(bool)).astype(float)
    return {"n_both": len(both), "a_only": x, "b_only": y, "p_mcnemar": p, "diff_pairs": pts(d.mean()) if len(both) else None,
            "a_only_strict": xs, "b_only_strict": ys, "p_mcnemar_strict": ps, "diff_strict": pts(ds.mean()),
            "p_cluster_flip": flip_p(d, both[qi]), "p_cluster_flip_strict": flip_p(ds, w[qi])}


def boot_pair(w, a, b, sa, sb):
    both = w[w[sa].astype(bool) & w[sb].astype(bool)]
    d = both[a].astype(float) - both[b].astype(float)
    c = np.bincount(both.qi, weights=d, minlength=Q)
    n = np.bincount(both.qi, minlength=Q).astype(float)
    return ci((W @ c) / (W @ n))


def holm(rows, key, out):
    idx = [i for i, r in enumerate(rows)]
    adj = multipletests([rows[i][key] for i in idx], method="holm")[1]
    for i, p in zip(idx, adj):
        rows[i][out] = float(p)


def fe_ols(w, y, xs, fe, cluster="qi"):
    d = w[[y] + xs + [fe, cluster]].dropna().copy()
    d[[y] + xs] = d[[y] + xs].astype(float)
    g = d.groupby(fe)
    z = d[[y] + xs] - g[[y] + xs].transform("mean")
    k = z[xs].std() > 0
    use = [x for x in xs if k[x]]
    m = sm.OLS(z[y], z[use]).fit(cov_type="cluster", cov_kwds={"groups": d[cluster]})
    return {x: {"b": pts(m.params[x]) if x in ("hinglish", "roman", "plain", "devanagari", "script_roman", "script_deva") or set(d[x].unique()) <= {0.0, 1.0} else round(float(m.params[x]) * 100, 3), "lo": round(float(m.conf_int().loc[x, 0]) * 100, 2), "hi": round(float(m.conf_int().loc[x, 1]) * 100, 2), "p": float(m.pvalues[x])} for x in use} | {"n": len(d), "groups": int(g.ngroups)}


def save(name, rows, fig=False):
    (FIG if fig else RES).joinpath(f"{name}.csv").write_text(pd.DataFrame(rows).to_csv(index=False), encoding="utf-8")


A = wide.ans_h.astype(bool)
wide["cell"] = wide.task + "|" + wide.difficulty + "|" + wide.insertion
wide["pair"] = wide.qid + "|" + wide.language + "|" + wide.insertion
wide["qlang"] = wide.qid + "|" + wide.language

N["integrity"] = json.loads((OUT / "_cache/integrity.json").read_text(encoding="utf-8"))
N["counts"] = {f"{c}/{l}": int(n) for (c, l), n in df.groupby(["condition", "language"]).size().items()}
N["questions"] = int(df.qid.nunique())
N["unanswered"] = {f"{c}/{l}": {"n": int((~g.answered).sum()), "pct": pts((~g.answered).mean()), "length_pct": pts((g.finish == "length").mean()), "unanswered_not_length": int(((~g.answered) & (g.finish != "length")).sum())} for (c, l), g in df.groupby(["condition", "language"])}
N["run_times"] = {c: {"min": g.time.min()[:10], "max": g.time.max()[:10]} for c, g in df.groupby("condition")}
N["lenient_weekday_changes"] = int((df.correct != df.correct_lenient).sum())
t1 = df[(df.condition == "hinglish") & (df.language == "hi_IN") & (df.task == "day_of_week")]
N["lenient_hi_dow"] = {"strict_answered": pts(t1[t1.answered].correct.mean()), "lenient_answered": pts(t1[t1.answered].correct_lenient.mean()), "romanised_or_english_answers": int(t1.answer.fillna("").str.contains("[A-Za-z]").sum())}

rows = []
for lang in LANGS:
    for task in TASKS + ["all"]:
        base = sel(language=lang) if task == "all" else sel(language=lang, task=task)
        w = wide[(wide.language == lang) & ((wide.task == task) | (task == "all"))]
        r = {"language": lang, "task": task}
        for c, s in (("direct", "direct"), ("cot", "std"), ("hinglish", "hing"), ("en-cot", "encot")):
            if c == "en-cot" and lang == "en_US":
                continue
            m = base & sel(condition=c)
            r[f"{s}_answered"] = pts(stat(m)[0])
            r[f"{s}_strict"] = pts(stat(m, True)[0])
        r["dhing_answered"] = round(r["hing_answered"] - r["direct_answered"], 2)
        r["dstd_answered"] = round(r["std_answered"] - r["direct_answered"], 2)
        p = paired(w, "ok_h", "ok_d", "ans_h", "ans_d")
        r |= {f"hd_{k}": v for k, v in p.items()}
        p = paired(w, "ok_s", "ok_d", "ans_s", "ans_d")
        r |= {"sd_a_only": p["a_only"], "sd_b_only": p["b_only"], "sd_p_mcnemar": p["p_mcnemar"]}
        p = paired(w, "ok_h", "ok_s", "ans_h", "ans_s")
        lo, hi = boot_pair(w, "ok_h", "ok_s", "ans_h", "ans_s")
        r |= {f"hs_{k}": v for k, v in p.items()} | {"hs_lo": pts(lo), "hs_hi": pts(hi)}
        rows.append(r)
tasks_only = [r for r in rows if r["task"] != "all"]
holm(tasks_only, "hd_p_mcnemar", "hd_p_holm18")
holm(tasks_only, "sd_p_mcnemar", "sd_p_holm18")
holm(tasks_only, "hs_p_mcnemar", "hs_p_holm18")
holm(tasks_only, "hs_p_mcnemar_strict", "hs_p_strict_holm18")
holm(tasks_only, "hs_p_cluster_flip", "hs_p_flip_holm18")
holm(tasks_only, "hs_p_cluster_flip_strict", "hs_p_flip_strict_holm18")
for lang in LANGS:
    sub = [r for r in tasks_only if r["language"] == lang]
    holm(sub, "hs_p_mcnemar", "hs_p_holm9")
    holm(sub, "hs_p_cluster_flip", "hs_p_flip_holm9")
save("table1", rows)
N["table1"] = {f"{r['language']}/{r['task']}": r for r in rows}

gains = {}
for lang in LANGS:
    for c, s in (("cot", "std"), ("hinglish", "hing"), ("en-cot", "encot")):
        if c == "en-cot" and lang == "en_US":
            continue
        for strict in (False, True):
            gains[f"{lang}/{s}/{'strict' if strict else 'answered'}"] = contrast(sel(language=lang, condition=c), sel(language=lang, condition="direct"), strict)
N["gains"] = gains
gap = {}
for c, s in (("cot", "std"), ("hinglish", "hing"), ("direct", "direct")):
    for name, tasks in (("five", FIVE), ("all9", TASKS)):
        for lvl in DIFFS + ["all"]:
            for strict in (False, True):
                base = sel(task=tasks) if lvl == "all" else sel(task=tasks, difficulty=lvl)
                gap[f"{s}/{name}/{lvl}/{'strict' if strict else 'answered'}"] = contrast(base & sel(language="en_US", condition=c), base & sel(language="hi_IN", condition=c), strict)
for name, tasks in (("five", FIVE), ("all9", TASKS)):
    for lvl in DIFFS + ["all"]:
        for strict in (False, True):
            base = sel(task=tasks) if lvl == "all" else sel(task=tasks, difficulty=lvl)
            gap[f"encot/{name}/{lvl}/{'strict' if strict else 'answered'}"] = contrast(base & sel(language="en_US", condition="cot"), base & sel(language="hi_IN", condition="en-cot"), strict)
N["gap"] = gap


def penalty(lang, c, ins, strict=False):
    a0, b0 = stat(sel(language=lang, condition=c, insertion="no_insertion"), strict)
    a1, b1 = stat(sel(language=lang, condition=c, insertion=ins), strict)
    d0, bd0 = stat(sel(language=lang, condition="direct", insertion="no_insertion"), strict)
    d1, bd1 = stat(sel(language=lang, condition="direct", insertion=ins), strict)
    lo, hi = ci((b0 - b1) - (bd0 - bd1))
    return {"cot_drop": pts(a0 - a1), "direct_drop": pts(d0 - d1), "did": pts((a0 - a1) - (d0 - d1)), "lo": pts(lo), "hi": pts(hi)}


N["penalty"] = {f"{l}/{s}/{i}/{'strict' if st else 'answered'}": penalty(l, c, i, st) for l in LANGS for c, s in (("cot", "std"), ("hinglish", "hing")) for i in INS[1:] for st in (False, True)}
N["penalty"] |= {f"hi_IN/encot/{i}/answered": penalty("hi_IN", "en-cot", i) for i in INS[1:]}
N["tokens"] = {f"{c}/{l}": {"median_answered": float(g[g.answered].tokens.median()), "median_all": float(g.tokens.median())} for (c, l), g in df[df.condition != "direct"].groupby(["condition", "language"])}

fig2 = []
for lang in LANGS:
    for lvl in DIFFS:
        for c, s in (("direct", "Direct"), ("cot", "Standard CoT"), ("hinglish", "Hinglish CoT")):
            for strict in (False, True):
                a, b = stat(sel(language=lang, difficulty=lvl, condition=c), strict)
                lo, hi = ci(b)
                fig2.append({"language": lang, "difficulty": lvl, "condition": s, "convention": "strict" if strict else "answered", "accuracy": pts(a), "lo": pts(lo), "hi": pts(hi)})
save("fig2_accuracy_by_level", fig2, True)
lvlrows = []
for lang in LANGS:
    for lvl in DIFFS:
        w = wide[(wide.language == lang) & (wide.difficulty == lvl)]
        a = contrast(sel(language=lang, difficulty=lvl, condition="hinglish"), sel(language=lang, difficulty=lvl, condition="cot"))
        s = contrast(sel(language=lang, difficulty=lvl, condition="hinglish"), sel(language=lang, difficulty=lvl, condition="cot"), True)
        lvlrows.append({"language": lang, "difficulty": lvl, "hing": a["a"], "std": a["b"], "diff": a["diff"], "lo": a["lo"], "hi": a["hi"], "diff_strict": s["diff"], "lo_strict": s["lo"], "hi_strict": s["hi"]} | {k: v for k, v in paired(w, "ok_h", "ok_s", "ans_h", "ans_s").items() if k in ("a_only", "b_only", "p_mcnemar", "p_cluster_flip", "p_mcnemar_strict")})
holm(lvlrows, "p_mcnemar", "p_holm10")
save("level_hing_vs_std", lvlrows)
N["level_diff"] = lvlrows
ix = {d: i for i, d in enumerate(DIFFS)}
tr = {}
for lang in LANGS:
    for strict in (False, True):
        ests, boots = [], []
        for lvl in DIFFS:
            a, ba = stat(sel(language=lang, difficulty=lvl, condition="hinglish"), strict)
            b, bb = stat(sel(language=lang, difficulty=lvl, condition="cot"), strict)
            ests.append(a - b)
            boots.append(ba - bb)
        x = np.arange(5) - 2
        sl = (x @ np.array(ests)) / (x @ x)
        bs = (x @ np.stack(boots)) / (x @ x)
        lo, hi = ci(bs)
        tr[f"{lang}/{'strict' if strict else 'answered'}"] = {"slope_per_level": pts(sl), "lo": pts(lo), "hi": pts(hi), "short": pts(ests[0]), "vvl": pts(ests[-1])}
N["level_trend"] = tr

split = []
for ins in INS + ["all"]:
    i = {} if ins == "all" else {"insertion": ins}
    for lang in LANGS:
        for strict in (False, True):
            lab = {"insertion": ins, "language": lang, "convention": "strict" if strict else "answered"}
            d = stat(sel(language=lang, condition="direct", **i), strict)[0]
            s = stat(sel(language=lang, condition="cot", **i), strict)[0]
            h = stat(sel(language=lang, condition="hinglish", **i), strict)[0]
            c = contrast(sel(language=lang, condition="hinglish", **i), sel(language=lang, condition="cot", **i), strict)
            g = contrast(sel(language=lang, condition="hinglish", **i), sel(language=lang, condition="direct", **i), strict)
            gs = contrast(sel(language=lang, condition="cot", **i), sel(language=lang, condition="direct", **i), strict)
            row = lab | {"direct": pts(d), "std": pts(s), "hing": pts(h), "hing_minus_std": c["diff"], "hs_lo": c["lo"], "hs_hi": c["hi"], "gain_std": gs["diff"], "gain_std_lo": gs["lo"], "gain_std_hi": gs["hi"], "gain_hing": g["diff"], "gain_hing_lo": g["lo"], "gain_hing_hi": g["hi"]}
            if lang == "hi_IN":
                e = contrast(sel(language=lang, condition="en-cot", **i), sel(language=lang, condition="hinglish", **i), strict)
                row |= {"encot": e["a"], "encot_minus_hing": e["diff"], "eh_lo": e["lo"], "eh_hi": e["hi"]}
            split.append(row)
save("split_by_distractor_headline", split)
N["split_headline"] = split
sgap = []
for ins in INS:
    for c, s in (("cot", "std"), ("hinglish", "hing")):
        for name, tasks, lvl in (("five_short", FIVE, "short"), ("five_very_long", FIVE, "very_long"), ("all9_all", TASKS, None)):
            base = sel(task=tasks, insertion=ins) if lvl is None else sel(task=tasks, insertion=ins, difficulty=lvl)
            sgap.append({"insertion": ins, "condition": s, "measure": name} | contrast(base & sel(language="en_US", condition=c), base & sel(language="hi_IN", condition=c)))
save("split_gap", sgap)
N["split_gap"] = sgap
stask = []
for ins in INS:
    for lang in LANGS:
        for task in TASKS:
            w = wide[(wide.insertion == ins) & (wide.language == lang) & (wide.task == task)]
            m = sel(insertion=ins, language=lang, task=task)
            c = contrast(m & sel(condition="hinglish"), m & sel(condition="cot"))
            d = contrast(m & sel(condition="hinglish"), m & sel(condition="direct"))
            p = paired(w, "ok_h", "ok_s", "ans_h", "ans_s")
            q = paired(w, "ok_h", "ok_d", "ans_h", "ans_d")
            stask.append({"insertion": ins, "language": lang, "task": task, "hing": c["a"], "std": c["b"], "direct": d["b"], "hing_minus_std": c["diff"], "h_only": p["a_only"], "s_only": p["b_only"], "p": p["p_mcnemar"], "hing_minus_direct": d["diff"], "p_hd": q["p_mcnemar"]})
for ins in INS:
    sub = [r for r in stask if r["insertion"] == ins]
    holm(sub, "p", "p_holm18")
    holm(sub, "p_hd", "p_hd_holm18")
save("split_by_distractor_task", stask)
N["split_task"] = stask

hg = df[df.condition == "hinglish"]
N["style"] = {
    l: {"roman_pct": pts((g.style == "roman").mean()), "plain_pct": pts((g.style == "plain").mean()), "devanagari_pct": pts((g.style == "devanagari").mean()),
        "roman_text_pct": pts((g.style_text == "roman").mean()), "plain_text_pct": pts((g.style_text == "plain").mean()),
        "no_deva_pct": pts((g.n_deva == 0).mean()), "any_deva": int((g.n_deva > 0).sum()), "deva_ge50_pct": pts((g.dshare >= 0.5).mean()), "deva_ge75_pct": pts((g.dshare >= 0.75).mean()), "median_dshare_all": pts(g.dshare.median()), "median_dshare_devmix": pts(g[g.style == "devanagari"].dshare.median()) if (g.style == "devanagari").any() else None,
        "low_deva_in_roman": int(((g.style == "roman") & (g.n_deva > 0)).sum()), "low_deva_in_plain": int(((g.style == "plain") & (g.n_deva > 0)).sum()), "median_fshare_roman": pts(g[g.style == "roman"].fshare.median())}
    for l, g in hg.groupby("language")}
sh = hg.groupby(["language", "style"]).size().rename("n").reset_index()
sh["pct_of_traces"] = (100 * sh.n / 6750).round(2)
save("fig3_style_shares", sh, True)
shares = []
for f in ("task", "difficulty", "insertion"):
    for (l, v), g in hg.groupby(["language", f]):
        shares.append({"language": l, "by": f, "value": v, "roman": pts((g.style == "roman").mean()), "plain": pts((g.style == "plain").mean()), "devanagari": pts((g.style == "devanagari").mean()), "median_tokens": float(g.tokens.median())})
save("style_shares_by", shares)
N["style_shares_by"] = shares

w3 = wide[wide.ans_h.astype(bool) & wide.ans_s.astype(bool)]
t3 = []
for (l, s), g in w3.groupby(["language", "style"]):
    t3.append({"language": l, "style": s, "n": len(g), "hing": pts(g.ok_h.mean()), "std": pts(g.ok_s.mean()), "direct": pts(g[g.ans_d.astype(bool)].ok_d.mean()), "h_only": int((g.ok_h & ~g.ok_s).sum()), "s_only": int((~g.ok_h & g.ok_s).sum()), "median_tokens_hing": float(g.tok_h.median()), "median_tokens_std": float(g.tok_s.median())})
save("table3", t3)
N["table3"] = t3
sx = wide[wide.ans_h.astype(bool)]
N["table3_all_answered_hinglish"] = [{"language": l, "style": s, "n": len(g), "hing": pts(g.ok_h.mean()), "std_strict": pts((g.ok_s.astype(bool) & g.ans_s.astype(bool)).mean()), "std_cutoff_pct": pts((~g.ans_s.astype(bool)).mean())} for (l, s), g in sx.groupby(["language", "style"])]
wx = w3[w3.language == "en_US"]
f4 = []
for task in TASKS:
    g = wx[wx.task == task]
    r = {"task": task}
    for s in ("roman", "plain"):
        k = g[g["style"] == s]
        r[f"{s}_n"] = len(k)
        r[f"{s}_hing"] = pts(k.ok_h.mean())
        r[f"{s}_std"] = pts(k.ok_s.mean())
        r[f"{s}_diff"] = pts(k.ok_h.mean() - k.ok_s.mean())
    g2 = g.assign(d=g.ok_h.astype(float) - g.ok_s.astype(float), rom=(g["style"] == "roman").astype(float))
    c1 = np.bincount(g2[g2.rom == 1].qi, weights=g2[g2.rom == 1].d, minlength=Q)
    n1 = np.bincount(g2[g2.rom == 1].qi, minlength=Q).astype(float)
    c0 = np.bincount(g2[g2.rom == 0].qi, weights=g2[g2.rom == 0].d, minlength=Q)
    n0 = np.bincount(g2[g2.rom == 0].qi, minlength=Q).astype(float)
    with np.errstate(all="ignore"):
        bs = (W @ c1) / (W @ n1) - (W @ c0) / (W @ n0)
    lo, hi = np.nanpercentile(bs, [2.5, 97.5])
    r |= {"did": round(r["roman_diff"] - r["plain_diff"], 2), "did_lo": pts(lo), "did_hi": pts(hi)}
    cells = []
    for _, h in g2.groupby("difficulty"):
        a, b = h[h.rom == 1], h[h.rom == 0]
        if len(a) and len(b):
            cells.append((len(a) * len(b) / (len(a) + len(b)), a.d.mean() - b.d.mean()))
    r["did_within_level"] = pts(sum(x * y for x, y in cells) / sum(x for x, _ in cells))
    m = fe_ols(g2.assign(roman=g2.rom), "d", ["roman"], "cell")
    r |= {"did_cellfe": m["roman"]["b"], "did_cellfe_lo": m["roman"]["lo"], "did_cellfe_hi": m["roman"]["hi"], "did_cellfe_p": m["roman"]["p"]}
    f4.append(r)
adj = multipletests([r["did_cellfe_p"] for r in f4], method="holm")[1]
for r, p in zip(f4, adj):
    r["did_cellfe_p_holm"] = float(p)
save("fig4_style_by_task", f4, True)
N["fig4"] = f4
save("fig1_accuracy_by_task", [{"language": r["language"], "task": r["task"], "direct": r["direct_answered"], "std": r["std_answered"], "hing": r["hing_answered"], "direct_strict": r["direct_strict"], "std_strict": r["std_strict"], "hing_strict": r["hing_strict"]} for r in rows], True)

def by_style(g, y="ok_h"):
    return {s: pts(g[g["style"] == s][y].astype(float).mean()) for s in g["style"].unique()}


sel_rows = {}
en = wx.copy()
en["roman"] = (en["style"] == "roman").astype(float)
en["d"] = en.ok_h.astype(float) - en.ok_s.astype(float)
en["h"] = en.ok_h.astype(float)
en["s"] = en.ok_s.astype(float)
sel_rows["marginal"] = {"hing": by_style(en), "std": by_style(en, "ok_s"), "direct": by_style(en[en.ans_d.astype(bool)], "ok_d")}
plain_mix = en[en["style"] == "plain"].groupby("cell").size()
rom = en[en["style"] == "roman"].groupby("cell").agg(n=("s", "size"), s=("s", "mean"), h=("h", "mean"))
pl = en[en["style"] == "plain"].groupby("cell").agg(n=("s", "size"), s=("s", "mean"), h=("h", "mean"))
both = rom.join(pl, lsuffix="_r", rsuffix="_p", how="inner")
wgt = both.n_r * both.n_p / (both.n_r + both.n_p)
sel_rows["standardised_within_task_level_insertion"] = {"cells": len(both), "std_roman_minus_plain": pts(((both.s_r - both.s_p) * wgt).sum() / wgt.sum()), "hing_roman_minus_plain": pts(((both.h_r - both.h_p) * wgt).sum() / wgt.sum())}
tl = en.assign(tl=en.task + "|" + en.difficulty)
sel_rows["expected_std_from_composition"] = {}
cellstd = en.groupby("cell").s.mean()
for s in ("roman", "plain"):
    sel_rows["expected_std_from_composition"][s] = pts(en[en["style"] == s].cell.map(cellstd).mean())
cellacc = en.groupby("cell").ok_d.apply(lambda x: x.astype(float).mean())
for s in ("roman", "plain"):
    sel_rows["expected_std_from_composition"][f"direct_{s}"] = pts(en[en["style"] == s].cell.map(cellacc).mean())
sel_rows["raw_gap"] = {"hing_roman_minus_plain": round(by_style(en)["roman"] - by_style(en)["plain"], 2), "loss_did": round((by_style(en)["roman"] - by_style(en, "ok_s")["roman"]) - (by_style(en)["plain"] - by_style(en, "ok_s")["plain"]), 2)}
sel_rows["cell_fe_hing"] = fe_ols(en, "h", ["roman"], "cell")
sel_rows["cell_fe_std"] = fe_ols(en, "s", ["roman"], "cell")
sel_rows["cell_fe_did"] = fe_ols(en, "d", ["roman"], "cell")
sel_rows["cell_fe_hing_ctrl_std"] = fe_ols(en, "h", ["roman", "s"], "cell")
sel_rows["question_fe_hing"] = fe_ols(en, "h", ["roman"], "qlang")
disc = en.groupby("qid").roman.transform(lambda x: x.nunique() > 1)
sel_rows["question_fe_discordant"] = {"questions": int(en[disc].qid.nunique()), "responses": int(disc.sum()), "roman_acc": pts(en[disc & (en.roman == 1)].h.mean()), "plain_acc": pts(en[disc & (en.roman == 0)].h.mean()), "std_roman": pts(en[disc & (en.roman == 1)].s.mean()), "std_plain": pts(en[disc & (en.roman == 0)].s.mean())}
for v, name in ((1, "std_right"), (0, "std_wrong")):
    k = en[en.s == v]
    sel_rows[name] = {"roman": pts(k[k.roman == 1].h.mean()), "plain": pts(k[k.roman == 0].h.mean()), "n_roman": int((k.roman == 1).sum()), "n_plain": int((k.roman == 0).sum()), "cell_fe": fe_ols(k, "h", ["roman"], "cell")["roman"]}
tabs = []
for _, g in en.groupby("cell"):
    t = np.array([[((g.roman == 1) & (g.h == 1)).sum(), ((g.roman == 1) & (g.h == 0)).sum()], [((g.roman == 0) & (g.h == 1)).sum(), ((g.roman == 0) & (g.h == 0)).sum()]], float)
    if t[0].sum() and t[1].sum():
        tabs.append(t)
st = StratifiedTable(tabs)
sel_rows["mh_or_hing_roman_vs_plain_cell"] = {"or": round(float(st.oddsratio_pooled), 3), "lo": round(float(st.oddsratio_pooled_confint()[0]), 3), "hi": round(float(st.oddsratio_pooled_confint()[1]), 3), "strata": len(tabs)}
sel_rows["structure"] = {s: {"tokens": float(g.tok_h.median()), "dates_per_100w": round(float((100 * (g.n_dates + g.n_clock) / (g.n_latin + 1)).median()), 2), "nums_per_100w": round(float((100 * g.n_nums / (g.n_latin + 1)).median()), 2), "steps": float(g.steps_h.median()), "verif_orig": pts(g.vo_h.mean()), "verif_ext": pts(g.ve_h.mean()), "afa": round(float(g.afa_h.mean()), 3)} for s, g in en.groupby("style")}
en["numdens"] = (en.n_dates + en.n_clock + en.n_nums) / (en.n_latin + 1)
en["logtok"] = np.log(en.tok_h.astype(float))
en["verif"] = en.ve_h.astype(float)
sel_rows["cell_fe_hing_ctrl_structure"] = fe_ols(en, "h", ["roman", "s", "logtok", "numdens", "verif"], "cell")
N["selection"] = sel_rows
save("selection_task_level_share", [{"task": t, "difficulty": d, "roman_pct": pts((g["style"] == "roman").mean()), "n": len(g), "std": pts(g.ok_s.mean()), "direct": pts(g.ok_d.astype(float).mean())} for (t, d), g in wx.groupby(["task", "difficulty"])])
for ins in INS:
    k = en[en.insertion == ins]
    N.setdefault("selection_by_insertion", {})[ins] = {"n_roman": int((k.roman == 1).sum()), "n_plain": int((k.roman == 0).sum()), "hing_roman": pts(k[k.roman == 1].h.mean()), "hing_plain": pts(k[k.roman == 0].h.mean()), "std_roman": pts(k[k.roman == 1].s.mean()), "std_plain": pts(k[k.roman == 0].s.mean()), "cell_fe_hing": fe_ols(k, "h", ["roman"], "cell")["roman"], "cell_fe_did": fe_ols(k, "d", ["roman"], "cell")["roman"]}

sens = []
for dt in (0.01, 0.05, 0.10, 0.20, 0.30, 0.50):
    for ft in (0.01, 0.02, 0.03, 0.05, 0.075, 0.10, 0.15, 0.20):
        st_ = np.where(wide.dshare >= dt, "devanagari", np.where(wide.fshare >= ft, "roman", "plain"))
        t = wide.assign(s2=st_)
        e = t[(t.language == "en_US") & t.ans_h.astype(bool) & t.ans_s.astype(bool)].copy()
        h = t[(t.language == "hi_IN")]
        hb = h[h.ans_h.astype(bool) & h.ans_s.astype(bool)]
        r = {"deva_thr": dt, "fn_thr": ft, "en_roman_pct": pts((t[t.language == "en_US"].s2 == "roman").mean()), "hi_dev_pct": pts((h.s2 == "devanagari").mean()), "hi_roman_pct": pts((h.s2 == "roman").mean())}
        for s in ("roman", "plain"):
            k = e[e.s2 == s]
            r[f"en_{s}_n"] = len(k)
            r[f"en_{s}_hing"] = pts(k.ok_h.mean()) if len(k) else None
            r[f"en_{s}_std"] = pts(k.ok_s.mean()) if len(k) else None
        for s in ("devanagari", "roman", "plain"):
            k = hb[hb.s2 == s]
            r[f"hi_{s}_hing"] = pts(k.ok_h.mean()) if len(k) else None
            r[f"hi_{s}_std"] = pts(k.ok_s.mean()) if len(k) else None
        e = e.assign(roman=(e.s2 == "roman").astype(float), h=e.ok_h.astype(float), d=e.ok_h.astype(float) - e.ok_s.astype(float))
        m = fe_ols(e, "d", ["roman"], "cell")["roman"]
        r |= {"en_did_cellfe": m["b"], "en_did_lo": m["lo"], "en_did_hi": m["hi"]}
        tk = [t2 for t2 in TASKS if (e[(e.task == t2) & (e.roman == 1)].d.mean() < e[(e.task == t2) & (e.roman == 0)].d.mean())]
        r["tasks_roman_worse"] = len(tk)
        sens.append(r)
save("threshold_sensitivity", sens, True)
N["sensitivity_summary"] = {"en_roman_pct_range": [min(r["en_roman_pct"] for r in sens), max(r["en_roman_pct"] for r in sens)], "en_did_range": [min(r["en_did_cellfe"] for r in sens), max(r["en_did_cellfe"] for r in sens)], "hi_dev_pct_range": [min(r["hi_dev_pct"] for r in sens), max(r["hi_dev_pct"] for r in sens)], "tasks_worse_range": [min(r["tasks_roman_worse"] for r in sens), max(r["tasks_roman_worse"] for r in sens)]}

edges = [-0.001, 0, 0.01, 0.03, 0.05, 0.10, 0.15, 0.20, 0.25, 1.01]
dose = []
ed = en.assign(bin=pd.cut(en.fshare, edges))
for b, g in ed.groupby("bin", observed=True):
    dose.append({"fn_share_bin": str(b), "n": len(g), "hing": pts(g.h.mean()), "std": pts(g.s.mean()), "loss": pts(g.d.mean()), "median_tokens": float(g.tok_h.median())})
save("dose_response_english", dose, True)
N["dose_bins"] = dose
ed["f10"] = ed.fshare * 10
nz = ed[ed.fshare > 0]
N["dose"] = {
    "spearman_fshare_d": round(float(spearmanr(ed.fshare, ed.d)[0]), 3),
    "cell_fe_d_per_10pt": fe_ols(ed, "d", ["f10"], "cell")["f10"],
    "cell_fe_h_per_10pt": fe_ols(ed, "h", ["f10"], "cell")["f10"],
    "cell_fe_h_per_10pt_within_roman": fe_ols(ed[ed.roman == 1], "h", ["f10"], "cell")["f10"],
    "cell_fe_d_per_10pt_within_roman": fe_ols(ed[ed.roman == 1], "d", ["f10"], "cell")["f10"],
    "qfe_h_per_10pt": fe_ols(ed, "h", ["f10"], "qlang")["f10"],
    "cell_fe_h_ctrl_len": fe_ols(ed, "h", ["f10", "logtok"], "cell"),
}
for lo, hi, nm in ((0.05, 0.15, "fs05_15"), (0.15, 0.25, "fs15_25"), (0.25, 1.01, "fs25up")):
    k = ed[(ed.fshare >= lo) & (ed.fshare < hi)]
    N["dose"][nm] = {"n": len(k), "hing": pts(k.h.mean()), "std": pts(k.s.mean()), "loss": pts(k.d.mean())}

en_long = []
for c, tag in (("h", 1.0), ("s", 0.0)):
    t = wide[(wide.language == "en_US") & wide[f"ans_{c}"].astype(bool)][["pair", "qid", "qi", "task", "difficulty", "insertion", "cell", "style"]].copy()
    src = wide[(wide.language == "en_US") & wide[f"ans_{c}"].astype(bool)]
    t["y"] = src[f"ok_{c}"].astype(float).to_numpy()
    t["tok"] = src[f"tok_{c}"].astype(float).to_numpy()
    t["ve"] = src[f"ve_{c}"].astype(float).to_numpy()
    t["vo"] = src[f"vo_{c}"].astype(float).to_numpy()
    t["afa"] = src[f"afa_{c}"].astype(float).fillna(0).to_numpy()
    t["hinglish"] = tag
    en_long.append(t)
L = pd.concat(en_long)
keep = L.groupby("pair").hinglish.transform("nunique") == 2
L = L[keep].copy()
L["logtok"] = np.log(L.tok)
L["plain_h"] = ((L.hinglish == 1) & (L["style"] == "plain")).astype(float)
L["roman_h"] = ((L.hinglish == 1) & (L["style"] == "roman")).astype(float)
cov = {}
cov["m0_no_ctrl"] = fe_ols(L, "y", ["hinglish"], "pair")
cov["m1_logtok"] = fe_ols(L, "y", ["hinglish", "logtok"], "pair")
cov["m2_verif_ext"] = fe_ols(L, "y", ["hinglish", "ve"], "pair")
cov["m3_afa"] = fe_ols(L, "y", ["hinglish", "afa"], "pair")
cov["m4_all"] = fe_ols(L, "y", ["hinglish", "logtok", "ve", "afa"], "pair")
cov["s0_style"] = fe_ols(L, "y", ["roman_h", "plain_h"], "pair")
cov["s1_style_all"] = fe_ols(L, "y", ["roman_h", "plain_h", "logtok", "ve", "afa"], "pair")
N["covariate_models_english"] = cov
L["tl"] = L.task + "|" + L.difficulty
L["tq"] = L.groupby("tl").tok.transform(lambda x: pd.qcut(x, 10, labels=False, duplicates="drop"))
cem = []
for (tl, q), g in L.groupby(["tl", "tq"]):
    a, b = g[g.hinglish == 1], g[g.hinglish == 0]
    if len(a) and len(b):
        cem.append((len(a), a.y.mean() - b.y.mean(), a.tok.median(), b.tok.median()))
cem = np.array(cem, float)
N["length_matched"] = {"strata": len(cem), "diff_hing_weighted": round(float(100 * (cem[:, 0] * cem[:, 1]).sum() / cem[:, 0].sum()), 2), "raw": round(float(100 * (L[L.hinglish == 1].y.mean() - L[L.hinglish == 0].y.mean())), 2)}
for s in ("roman", "plain"):
    M = L[(L.hinglish == 0) | (L["style"] == s)]
    M = M[M.pair.isin(M[M.hinglish == 1].pair)]
    c2 = []
    for (tl, q), g in M.groupby(["tl", "tq"]):
        a, b = g[g.hinglish == 1], g[g.hinglish == 0]
        if len(a) and len(b):
            c2.append((len(a), a.y.mean() - b.y.mean()))
    c2 = np.array(c2)
    N["length_matched"][s] = round(float(100 * (c2[:, 0] * c2[:, 1]).sum() / c2[:, 0].sum()), 2)
tok_rows = []
for name, g in (("hing_roman", wx[wx["style"] == "roman"]), ("hing_plain", wx[wx["style"] == "plain"])):
    tok_rows.append({"group": name, "n": len(g), "tok_hing": float(g.tok_h.median()), "tok_std_same_items": float(g.tok_s.median()), "ve_hing": pts(g.ve_h.mean()), "ve_std": pts(g.ve_s.mean()), "vo_hing": pts(g.vo_h.mean()), "vo_std": pts(g.vo_s.mean()), "afa_hing": round(float(g.afa_h.astype(float).mean()), 3), "afa_std": round(float(g.afa_s.astype(float).mean()), 3)})
N["verification_by_group"] = tok_rows
hx = df[df.answered & df.condition.isin(["cot", "hinglish", "en-cot"])]
N["verification_condition"] = {f"{c}/{l}": {"orig": pts(g.verif_orig.mean()), "ext": pts(g.verif_ext.mean()), "afa": round(float(g.after_first_ans.astype(float).mean()), 3), "afa_gt_20pct": pts((g.after_first_ans.astype(float) > 0.2).mean())} for (c, l), g in hx.groupby(["condition", "language"])}
vstrata = []
for cond, c in (("hing", "h"), ("std", "s")):
    for ve in (True, False):
        k = wx[wx[f"ve_{c}"].astype(bool) == ve]
        vstrata.append({"condition": cond, "verif_ext": ve, "n": len(k), "acc": pts(k[f"ok_{c}"].mean())})
N["accuracy_by_verif"] = vstrata
tbin = []
for name, g in (("std", wx.assign(t=wx.tok_s.astype(float), y=wx.ok_s.astype(float))), ("hing_plain", wx[wx["style"] == "plain"].assign(t=lambda x: x.tok_h.astype(float), y=lambda x: x.ok_h.astype(float))), ("hing_roman", wx[wx["style"] == "roman"].assign(t=lambda x: x.tok_h.astype(float), y=lambda x: x.ok_h.astype(float)))):
    for lo, hi in ((0, 100), (100, 200), (200, 300), (300, 500), (500, 1000), (1000, 5000)):
        k = g[(g.t >= lo) & (g.t < hi)]
        tbin.append({"group": name, "token_bin": f"{lo}-{hi}", "n": len(k), "acc": pts(k.y.mean()) if len(k) else None})
save("length_bins_english", tbin, True)
N["length_bins"] = tbin

hq = wide[wide.language == "hi_IN"].copy()
for col in ("ok_e", "ans_e"):
    hq[col] = hq[col].astype(bool)
for col in ("ok_h", "ans_h", "ok_s", "ans_s", "ok_d", "ans_d"):
    hq[col] = hq[col].astype(bool)
te = []
for s in ("devanagari", "roman", "plain", "all"):
    g = hq if s == "all" else hq[hq["style"] == s]
    b = g[g.ans_h & g.ans_e]
    c = g[g.ans_h & g.ans_s & g.ans_e]
    x, y, p = mcn(b.ok_e.to_numpy(), b.ok_h.to_numpy())
    lo, hi = boot_pair(g, "ok_e", "ok_h", "ans_e", "ans_h")
    te.append({"style": s, "n_pairs": len(b), "hing": pts(b.ok_h.mean()), "encot": pts(b.ok_e.mean()), "diff": pts(b.ok_e.mean() - b.ok_h.mean()), "lo": pts(lo), "hi": pts(hi), "encot_only": x, "hing_only": y, "p": p, "std_same_items": pts(c.ok_s.mean()), "n_triple": len(c), "encot_triple": pts(c.ok_e.mean()), "hing_triple": pts(c.ok_h.mean())})
save("takeaway2_encot_by_style", te, True)
N["encot_by_style"] = te
hq["script_roman"] = (hq["style"] == "roman").astype(float)
hq["plain"] = (hq["style"] == "plain").astype(float)
hq["h"] = hq.ok_h.astype(float)
b = hq[hq.ans_h & hq.ans_e & hq.ans_s].copy()
b["de"] = b.ok_e.astype(float) - b.ok_h.astype(float)
b["ds"] = b.ok_h.astype(float) - b.ok_s.astype(float)
b["dse"] = b.ok_e.astype(float) - b.ok_s.astype(float)
N["hindi_script_models"] = {
    "raw_cell_fe_hing": fe_ols(b, "h", ["script_roman", "plain"], "cell"),
    "cell_fe_encot_loss": fe_ols(b, "de", ["script_roman", "plain"], "cell"),
    "question_fe_hing": fe_ols(b, "h", ["script_roman", "plain"], "qlang"),
    "question_fe_encot_loss": fe_ols(b, "de", ["script_roman", "plain"], "qlang"),
    "cell_fe_vs_std": fe_ols(b, "ds", ["script_roman", "plain"], "cell"),
}
disc = b[b.groupby("qid").script_roman.transform("nunique") > 1]
N["hindi_script_discordant"] = {"questions": int(disc.qid.nunique()), "responses": len(disc), "roman_acc": pts(disc[disc.script_roman == 1].ok_h.mean()), "dev_acc": pts(disc[(disc["style"] == "devanagari")].ok_h.mean())}
ta2 = []
for task in TASKS + ["all"]:
    g = hq if task == "all" else hq[hq.task == task]
    r = {"task": task}
    for s in ("devanagari", "roman"):
        k = g[(g["style"] == s) & g.ans_h & g.ans_e]
        r[f"{s}_n"] = len(k)
        r[f"{s}_hing"] = pts(k.ok_h.mean())
        r[f"{s}_encot"] = pts(k.ok_e.mean())
    e2 = wx[wx.task == task] if task != "all" else wx
    ro = e2[e2["style"] == "roman"]
    r |= {"enq_roman_hing": pts(ro.ok_h.mean()), "enq_roman_std": pts(ro.ok_s.mean())}
    ta2.append(r)
save("takeaway2_script_by_task", ta2, True)
N["script_by_task"] = ta2
g2 = df[df.answered]
four = {"EN_q_EN_reason_std": sel(language="en_US", condition="cot"), "EN_q_hinglish_prompt": sel(language="en_US", condition="hinglish"), "HI_q_EN_reason_encot": sel(language="hi_IN", condition="en-cot"), "HI_q_hinglish_prompt": sel(language="hi_IN", condition="hinglish"), "HI_q_HI_reason_std": sel(language="hi_IN", condition="cot")}
N["reading_vs_reasoning"] = {"cells": {k: {"answered": pts(stat(v)[0]), "strict": pts(stat(v, True)[0])} for k, v in four.items()}}
for name, a, b_ in (("reading_cost_en_reasoning", "EN_q_EN_reason_std", "HI_q_EN_reason_encot"), ("reasoning_cost_on_hi_q", "HI_q_EN_reason_encot", "HI_q_HI_reason_std"), ("hinglish_cost_on_en_q", "EN_q_EN_reason_std", "EN_q_hinglish_prompt"), ("hinglish_cost_on_hi_q_vs_encot", "HI_q_EN_reason_encot", "HI_q_hinglish_prompt"), ("encot_hi_vs_hinglish_en", "HI_q_EN_reason_encot", "EN_q_hinglish_prompt")):
    N["reading_vs_reasoning"][name] = {"answered": contrast(four[a], four[b_]), "strict": contrast(four[a], four[b_], True)}
gs = stat(four["EN_q_EN_reason_std"])
N["gap_recovered"] = {"std_gap": pts(gs[0] - stat(four["HI_q_HI_reason_std"])[0]), "encot_gap": pts(gs[0] - stat(four["HI_q_EN_reason_encot"])[0]), "hing_gap": pts(stat(four["EN_q_hinglish_prompt"])[0] - stat(four["HI_q_hinglish_prompt"])[0])}
N["gap_recovered"]["recovered_pct"] = round(100 * (1 - N["gap_recovered"]["encot_gap"] / N["gap_recovered"]["std_gap"]), 1)
N["encot_compliance"] = {"any_deva_pct": pts((df[df.condition == "en-cot"].n_deva > 0).mean()), "dshare_ge10_pct": pts((df[df.condition == "en-cot"].dshare >= 0.1).mean())}
N["cross_lang_same_style"] = {}
for s in ("roman", "plain"):
    a = wide[(wide["style"] == s) & wide.ans_h.astype(bool)]
    p = a.pivot_table(index=["qid", "insertion"], columns="language", values="ok_h", aggfunc="first").dropna()
    p = p.astype(bool)
    x, y, pp = mcn(p.en_US.to_numpy(), p.hi_IN.to_numpy())
    N["cross_lang_same_style"][s] = {"pairs": len(p), "en": pts(p.en_US.mean()), "hi": pts(p.hi_IN.mean()), "en_only": x, "hi_only": y, "p": pp}
c_en = wide[(wide.language == "en_US") & (wide["style"] == "plain") & wide.ans_h.astype(bool)]
c_hi = wide[(wide.language == "hi_IN") & (wide["style"] == "plain") & wide.ans_h.astype(bool) & wide.ans_e.astype(bool)]
N["prompt_effect_no_hindi"] = {"english_q_plain_vs_std": {"n": int((c_en.ans_s.astype(bool)).sum()), "hing": pts(c_en[c_en.ans_s.astype(bool)].ok_h.mean()), "std": pts(c_en[c_en.ans_s.astype(bool)].ok_s.mean()), "ci": [pts(x) for x in boot_pair(c_en, "ok_h", "ok_s", "ans_h", "ans_s")]}, "hindi_q_plain_vs_encot": {"n": len(c_hi), "hing": pts(c_hi.ok_h.astype(bool).mean()), "encot": pts(c_hi.ok_e.astype(bool).mean())}}
pur = wx[(wx["style"] == "plain") & (wx.fshare == 0)]
N["prompt_effect_no_hindi"]["english_q_zero_fn_words"] = {"n": len(pur), "hing": pts(pur.ok_h.mean()), "std": pts(pur.ok_s.mean()), "tok_h": float(pur.tok_h.median()), "tok_s": float(pur.tok_s.median()), "ci": [pts(x) for x in boot_pair(pur, "ok_h", "ok_s", "ans_h", "ans_s")], "by_insertion": {i: {"n": int((pur.insertion == i).sum()), "hing": pts(pur[pur.insertion == i].ok_h.mean()), "std": pts(pur[pur.insertion == i].ok_s.mean())} for i in INS}}
tot = wx.ok_h.astype(float).mean() - wx.ok_s.astype(float).mean()
rshare = (wx["style"] == "roman").mean()
rl = wx[wx["style"] == "roman"]
pl_ = wx[wx["style"] == "plain"]
rd = rl.ok_h.astype(float).mean() - rl.ok_s.astype(float).mean()
pd_ = pl_.ok_h.astype(float).mean() - pl_.ok_s.astype(float).mean()
N["decomposition"] = {"total": pts(tot), "roman_share": pts(rshare), "roman_loss": pts(rd), "plain_loss": pts(pd_), "if_all_loss_were_plain_rate": pts(pd_), "share_of_total_at_plain_rate_pct": round(100 * pd_ / tot, 1)}

data = {}
for d in DIFFS:
    for t in ("date_subtraction", "date_addition", "date_recurrence"):
        data[(d, t)] = json.load(open(ROOT / "dataset" / d / f"{t}_en_US.json", encoding="utf-8"))
ISO = re.compile(r"(\d{4})-(\d{2})-(\d{2})")


def to_d(s):
    m = ISO.search(s or "")
    try:
        return date(*map(int, m.groups())) if m else None
    except ValueError:
        return None


err = []
subs = df[(df.task == "date_subtraction") & df.condition.isin(["cot", "hinglish", "en-cot"]) & df.answered].copy()
piv = {(d, q): to_d(v["no_insertion"]) for (d, t), f in data.items() if t == "date_subtraction" for q, v in f.items()}
subs["pivot"] = [piv[(d, str(q))] for d, q in zip(subs.difficulty, subs.qnum)]
subs["ad"] = subs.answer.map(to_d)
subs["gd"] = subs.gold.map(to_d)


def etype(r):
    if r.correct:
        return "correct"
    if r.ad is None:
        return "invalid"
    if (r.ad - r.pivot).days == -(r.gd - r.pivot).days:
        return "wrong_direction"
    dd = abs((r.ad - r.gd).days)
    if dd == 1:
        return "off_by_one"
    if r.ad.year == r.gd.year and r.ad.day == r.gd.day:
        return "month_slip"
    if dd <= 3:
        return "off_by_2_3"
    return "other"


subs["etype"] = [etype(r) for r in subs.itertuples()]
subs["cross"] = [r.gd.month != r.pivot.month for r in subs.itertuples()]
for (c, l), g in subs.groupby(["condition", "language"]):
    wrong = g[~g.correct]
    err.append({"condition": c, "language": l, "n": len(g), "acc": pts(g.correct.mean()), "wrong": len(wrong)} | {k: pts((wrong.etype == k).mean()) for k in ("off_by_one", "wrong_direction", "month_slip", "off_by_2_3", "other", "invalid")} | {"acc_cross_month": pts(g[g.cross].correct.mean()), "acc_same_month": pts(g[~g.cross].correct.mean()), "n_cross": int(g.cross.sum())})
save("subtraction_error_types", err, True)
N["subtraction_errors"] = err
dow = df[(df.task == "day_of_week") & df.condition.isin(["cot", "hinglish", "en-cot"]) & df.answered].copy()
ALL_DAY = {k.casefold(): v for k, v in SCRIPT_DAY.items()}
dow["ad"] = dow.answer.str.casefold().map(ALL_DAY)
dow["gd"] = dow.gold.str.casefold().map(ALL_DAY)
dow["off"] = (dow.ad - dow.gd + 3) % 7 - 3
dr = []
for (c, l), g in dow.groupby(["condition", "language"]):
    dr.append({"condition": c, "language": l, "n": len(g), "correct": pts((g.off == 0).mean()), "plus1": pts((g.off == 1).mean()), "minus1": pts((g.off == -1).mean()), "other": pts((g.off.abs() > 1).mean())})
save("dow_offsets", dr, True)
N["dow_offsets"] = dr
ag = []
for task in TASKS + ["all"]:
    g = wide[(wide.task == task) | (task == "all")]
    e = g[(g.language == "en_US") & g.ans_h.astype(bool) & g.ans_s.astype(bool)].set_index(["qid", "insertion"])
    hi = g[(g.language == "hi_IN") & g.ans_s.astype(bool)].set_index(["qid", "insertion"])
    j = e[["ok_h", "ok_s"]].astype(float).join(hi[["ok_s"]].astype(float).rename(columns={"ok_s": "hi_std"}), how="inner")
    if task == "all":
        cellm = g[["qid", "task", "difficulty"]].drop_duplicates().set_index("qid")
        j = j.reset_index().merge(cellm, on="qid")
        for c in ("ok_h", "ok_s", "hi_std"):
            j[c] = j[c] - j.groupby(["task", "difficulty"])[c].transform("mean")
    ag.append({"task": task, "n": len(j), "phi_enHing_hiStd": round(float(j.ok_h.corr(j.hi_std)), 3), "phi_enStd_hiStd": round(float(j.ok_s.corr(j.hi_std)), 3), "phi_enHing_enStd": round(float(j.ok_h.corr(j.ok_s)), 3)})
save("failure_agreement", ag, True)
N["failure_agreement"] = ag
wi = wide[(wide.language == "en_US") & (wide.task == "date_subtraction")]
N["subtraction_std_wrong_vs_right"] = {}
N["english_vs_direct_negatives"] = {s: [r["task"] for r in rows if r["language"] == "en_US" and r["task"] != "all" and r[f"d{s}_answered"] < 0] for s in ("hing", "std")}

full = {}
for d in DIFFS:
    recs = json.load(open(ROOT / "responses/standard" / f"{d}.json", encoding="utf-8"))
    for r in recs:
        m = r["meta"]
        a = answer_of(r["content"])
        if a is None:
            continue
        full.setdefault((m["task"], m["language"], r["condition"]), [0, 0])
        full[(m["task"], m["language"], r["condition"])][0] += score(m["task"], a, m["answer"], SCRIPT_DAY)
        full[(m["task"], m["language"], r["condition"])][1] += 1
    del recs
frows = []
for (t, l, c), (x, n) in sorted(full.items()):
    sub = df[(df.task == t) & (df.language == l) & (df.condition == c) & df.answered]
    frows.append({"task": t, "language": l, "condition": c, "full_grid": pts(x / n), "n_full": n, "first50": pts(sub.correct.mean()), "n_first50": len(sub)})
for (l, c) in {(l, c) for (_, l, c) in full}:
    x = sum(v[0] for k, v in full.items() if k[1] == l and k[2] == c)
    n = sum(v[1] for k, v in full.items() if k[1] == l and k[2] == c)
    sub = df[(df.language == l) & (df.condition == c) & df.answered]
    frows.append({"task": "all", "language": l, "condition": c, "full_grid": pts(x / n), "n_full": n, "first50": pts(sub.correct.mean()), "n_first50": len(sub)})
save("first50_vs_full_grid", frows)
N["first50_vs_full"] = frows
uq = []
for d in DIFFS:
    for t in TASKS:
        f = json.load(open(ROOT / "dataset" / d / f"{t}_en_US.json", encoding="utf-8"))
        ks = list(f)[:50]
        uq.append({"difficulty": d, "task": t, "n": len(ks), "unique": len({f[k]["no_insertion"] for k in ks}), "first_50_ids_match": sorted(map(int, ks)) == sorted(df[(df.difficulty == d) & (df.task == t)].qnum.unique().tolist())})
save("unique_questions", uq)
N["unique_questions"] = {"min_unique": min(u["unique"] for u in uq), "total_unique": sum(u["unique"] for u in uq), "all_ids_match": all(u["first_50_ids_match"] for u in uq)}


ivw = wide[(wide.language == "en_US") & wide.ans_h.astype(bool) & wide.ans_s.astype(bool)].copy()
ivw["R"] = (ivw["style"] == "roman").astype(float)
ivw["H"] = ivw.ok_h.astype(float)
ivw["S"] = ivw.ok_s.astype(float)
ivw["D"] = ivw.H - ivw.S
ivw["Z"] = (ivw.insertion == "dissimilar_insertion").astype(int)
gr = ivw.groupby(["qi", "Z"])[["R", "H", "S", "D"]].mean().unstack("Z").dropna()
iv = {"questions": len(gr)}
dR = (gr["R"][1] - gr["R"][0])
idx = gr.index.to_numpy()


def boot_mean(v):
    a = np.zeros(Q)
    n = np.zeros(Q)
    a[idx] = v.to_numpy()
    n[idx] = 1
    return (W @ a) / (W @ n)


bR = boot_mean(dR)
iv["first_stage_dR"] = {"est": pts(dR.mean()), "lo": pts(ci(bR)[0]), "hi": pts(ci(bR)[1])}
for y in ("H", "S", "D"):
    dy = gr[y][1] - gr[y][0]
    by = boot_mean(dy)
    w_ = by / bR
    iv[f"reduced_{y}"] = {"est": pts(dy.mean()), "lo": pts(ci(by)[0]), "hi": pts(ci(by)[1])}
    iv[f"wald_{y}"] = {"est": pts(dy.mean() / dR.mean()), "lo": pts(ci(w_)[0]), "hi": pts(ci(w_)[1])}
N["iv_distractor_shifts_style"] = iv
sh0 = {}
for ins in INS:
    g = wide[(wide.language == "en_US") & (wide.insertion == ins) & wide.ans_h.astype(bool)]
    sh0[ins] = {"roman_share": float((g["style"] == "roman").mean()), "roman_acc": float(g[g["style"] == "roman"].ok_h.astype(float).mean()), "plain_acc": float(g[g["style"] == "plain"].ok_h.astype(float).mean()), "acc": float(g.ok_h.astype(float).mean())}
base = sh0["no_insertion"]
d0 = stat(sel(language="en_US", condition="direct", insertion="no_insertion"))[0]
d1 = stat(sel(language="en_US", condition="direct", insertion="dissimilar_insertion"))[0]
x = sh0["dissimilar_insertion"]
std_acc = base["roman_share"] * x["roman_acc"] + (1 - base["roman_share"]) * x["plain_acc"]
N["penalty_style_decomposition"] = {"by_insertion": {k: {a: pts(b) for a, b in v.items()} for k, v in sh0.items()}, "did_observed": pts((base["acc"] - x["acc"]) - (d0 - d1)), "did_at_no_insertion_style_mix": pts((base["acc"] - std_acc) - (d0 - d1)), "composition_part": pts(std_acc - x["acc"]), "direct_drop": pts(d0 - d1)}
fi = []
for ins in INS:
    for task in TASKS:
        g = wx[(wx.task == task) & (wx.insertion == ins)]
        r_ = g[g["style"] == "roman"]
        p_ = g[g["style"] == "plain"]
        fi.append({"insertion": ins, "task": task, "n_roman": len(r_), "n_plain": len(p_), "roman_loss": pts(r_.ok_h.astype(float).mean() - r_.ok_s.astype(float).mean()), "plain_loss": pts(p_.ok_h.astype(float).mean() - p_.ok_s.astype(float).mean())})
for r in fi:
    r["roman_worse"] = r["roman_loss"] < r["plain_loss"]
save("fig4_by_distractor", fi, True)
N["fig4_by_distractor"] = {i: sum(r["roman_worse"] for r in fi if r["insertion"] == i) for i in INS}
N["fig4_by_distractor_exceptions"] = [r for r in fi if not r["roman_worse"]]
words = []
base_df = wide.merge(df[df.condition == "hinglish"][["qid", "language", "insertion", "fn_listed5", "fn_core"]], on=["qid", "language", "insertion"])
for name, col in (("listed5", "fn_listed5"), ("core", "fn_core"), ("wide", None)):
    fs = base_df.fshare if col is None else (base_df[col] / base_df.n_latin.replace(0, np.nan)).fillna(0)
    s2 = np.where(base_df.dshare >= 0.1, "devanagari", np.where(fs >= 0.05, "roman", "plain"))
    t = base_df.assign(s2=s2)
    e = t[(t.language == "en_US") & t.ans_h.astype(bool) & t.ans_s.astype(bool)]
    words.append({"list": name, "en_roman_n": int((e.s2 == "roman").sum()), "en_plain_n": int((e.s2 == "plain").sum()), "en_roman_hing": pts(e[e.s2 == "roman"].ok_h.astype(float).mean()), "en_plain_hing": pts(e[e.s2 == "plain"].ok_h.astype(float).mean()), "en_roman_std": pts(e[e.s2 == "roman"].ok_s.astype(float).mean()), "en_plain_std": pts(e[e.s2 == "plain"].ok_s.astype(float).mean())})
save("wordlist_sensitivity", words, True)
N["wordlist_sensitivity"] = words
fsm = ed[ed.fshare >= 0.15]
N["dose"]["slope_within_fshare_ge15"] = fe_ols(fsm, "h", ["f10"], "cell")["f10"]
N["dose"]["slope_loss_within_fshare_ge15"] = fe_ols(fsm, "d", ["f10"], "cell")["f10"]
N["dose"]["share_zero"] = pts((ed.fshare == 0).mean())
N["dose"]["share_ge25"] = pts((ed.fshare >= 0.25).mean())
N["dose"]["share_between_3_and_15"] = pts(((ed.fshare > 0.03) & (ed.fshare < 0.15)).mean())
qt = ed[ed.fshare >= 0.15].fshare.quantile([0.25, 0.5, 0.75]).tolist()
N["dose"]["quartiles_ge15"] = [pts(v) for v in qt]
qb = []
for lo, hi in zip([0.15] + qt, qt + [1.01]):
    k = ed[(ed.fshare >= lo) & (ed.fshare < hi)]
    qb.append({"lo": pts(lo), "hi": pts(hi), "n": len(k), "hing": pts(k.h.mean()), "std": pts(k.s.mean()), "loss": pts(k.d.mean())})
N["dose"]["quartile_bins_ge15"] = qb
cv = {}
for nm, c in (("hing", "h"), ("std", "s")):
    k = wide[(wide.language == "en_US") & wide[f"ans_{c}"].astype(bool)].copy()
    k["y"] = k[f"ok_{c}"].astype(float)
    k["v"] = k[f"vo_{c}"].astype(float)
    k["ve_"] = k[f"ve_{c}"].astype(float)
    k["lt"] = np.log(k[f"tok_{c}"].astype(float))
    cv[nm] = {"cell_fe_orig": fe_ols(k, "y", ["v"], "cell"), "cell_fe_ext": fe_ols(k, "y", ["ve_"], "cell"), "question_fe_ext": fe_ols(k, "y", ["ve_"], "qlang"), "cell_fe_len": fe_ols(k, "y", ["lt"], "cell"), "question_fe_len": fe_ols(k, "y", ["lt"], "qlang")}
    if nm == "hing":
        for s in ("roman", "plain"):
            kk = k[k["style"] == s]
            cv[f"hing_{s}"] = {"cell_fe_ext": fe_ols(kk, "y", ["ve_"], "cell"), "cell_fe_len": fe_ols(kk, "y", ["lt"], "cell"), "acc_verified": pts(kk[kk.ve_ == 1].y.mean()), "acc_unverified": pts(kk[kk.ve_ == 0].y.mean()), "n_verified": int((kk.ve_ == 1).sum())}
N["within_condition_verif_length"] = cv
pure = wx[(wx["style"] == "plain") & (wx.fshare == 0)]
N["pure_english_verification"] = {"n": len(pure), "orig_hing": pts(pure.vo_h.mean()), "orig_std": pts(pure.vo_s.mean()), "afa_hing": round(float(pure.afa_h.astype(float).mean()), 3), "afa_std": round(float(pure.afa_s.astype(float).mean()), 3)}
subw = subs[(subs.condition == "hinglish")].merge(wide[["qid", "language", "insertion", "style"]], on=["qid", "language", "insertion"], suffixes=("", "_w"))
cr = []
for (l, s), g in subw.groupby(["language", "style_w" if "style_w" in subw else "style"]):
    cr.append({"language": l, "style": s, "n_cross": int(g.cross.sum()), "acc_cross": pts(g[g.cross].correct.mean()), "n_same": int((~g.cross).sum()), "acc_same": pts(g[~g.cross].correct.mean())})
save("subtraction_month_cross_by_style", cr, True)
N["subtraction_cross_by_style"] = cr
sw = subs[subs.condition == "cot"].groupby(["language", "cross"]).correct.mean().mul(100).round(2).to_dict()
N["subtraction_cross_std"] = {f"{a}/{b}": v for (a, b), v in sw.items()}
hid = df[(df.language == "hi_IN") & (df.condition == "cot")]
N["hindi_std_vs_devmix"] = {"std_median_dshare": pts(hid.dshare.median()), "std_ge10_pct": pts((hid.dshare >= 0.1).mean()), "std_ge50_pct": pts((hid.dshare >= 0.5).mean()), "devmix_median_dshare": pts(df[(df.language == "hi_IN") & (df.condition == "hinglish") & (df["style"] == "devanagari")].dshare.median())}
dm = w3[(w3.language == "hi_IN") & (w3["style"] == "devanagari")]
N["hindi_std_vs_devmix"]["discordant_pct"] = pts((dm.ok_h != dm.ok_s).mean())
N["hindi_std_vs_devmix"]["answers_identical_pct"] = pts((dm.a_h == dm.a_s).mean())
ee = w3[w3.language == "en_US"]
N["english_answer_identical_pct"] = {s: pts((g.a_h == g.a_s).mean()) for s, g in ee.groupby("style")}
hl = []
for lvl in DIFFS:
    for ins in INS:
        g = wide[(wide.language == "en_US") & (wide.difficulty == lvl) & (wide.insertion == ins) & wide.ans_h.astype(bool) & wide.ans_s.astype(bool)]
        hl.append({"difficulty": lvl, "insertion": ins, "hing": pts(g.ok_h.astype(float).mean()), "std": pts(g.ok_s.astype(float).mean()), "loss": pts(g.ok_h.astype(float).mean() - g.ok_s.astype(float).mean())})
save("level_by_distractor_english", hl, True)
N["level_by_distractor_english"] = hl
tp = {}
for ins in INS:
    ests, boots = [], []
    for lvl in DIFFS:
        a, ba = stat(sel(language="en_US", difficulty=lvl, condition="hinglish", insertion=ins))
        b_, bb = stat(sel(language="en_US", difficulty=lvl, condition="cot", insertion=ins))
        ests.append(a - b_)
        boots.append(ba - bb)
    x_ = np.arange(5) - 2
    lo, hi = ci((x_ @ np.stack(boots)) / (x_ @ x_))
    tp[ins] = {"slope": pts((x_ @ np.array(ests)) / (x_ @ x_)), "lo": pts(lo), "hi": pts(hi)}
N["level_trend_by_insertion"] = tp
te2 = []
for ins in INS:
    for s in ("devanagari", "roman", "plain"):
        g = hq[(hq.insertion == ins) & (hq["style"] == s) & hq.ans_h & hq.ans_e]
        te2.append({"insertion": ins, "style": s, "n": len(g), "hing": pts(g.ok_h.mean()), "encot": pts(g.ok_e.mean()), "diff": pts(g.ok_e.mean() - g.ok_h.mean())})
save("takeaway2_encot_by_style_distractor", te2, True)
N["encot_style_by_insertion"] = te2
sty = {}
for ins in INS:
    g = wx[wx.insertion == ins]
    sty[ins] = {s: {"n": int((g["style"] == s).sum()), "hing": pts(g[g["style"] == s].ok_h.astype(float).mean()), "std": pts(g[g["style"] == s].ok_s.astype(float).mean())} for s in ("roman", "plain")}
N["table3_by_insertion_english"] = sty
h3 = {}
for ins in INS:
    g = w3[(w3.language == "hi_IN") & (w3.insertion == ins)]
    h3[ins] = {s: {"n": int((g["style"] == s).sum()), "hing": pts(g[g["style"] == s].ok_h.astype(float).mean()), "std": pts(g[g["style"] == s].ok_s.astype(float).mean())} for s in ("devanagari", "roman", "plain")}
N["table3_by_insertion_hindi"] = h3
b2 = {}
for label, ord_ in (("direct_first", df[df.condition == "direct"].qid.drop_duplicates().tolist()), ("hinglish_first", df[df.condition == "hinglish"].qid.drop_duplicates().tolist())):
    qi2 = {q: i for i, q in enumerate(ord_)}
    rng = np.random.default_rng(0)
    w2 = np.stack([np.bincount(rng.integers(0, Q, Q), minlength=Q) for _ in range(B)])


    def st2(m):
        s = df[m & df.answered.to_numpy()]
        qq = s.qid.map(qi2).to_numpy()
        return (w2 @ np.bincount(qq, weights=s.correct.astype(float), minlength=Q)) / (w2 @ np.bincount(qq, minlength=Q).astype(float))


    gh = st2(sel(language="en_US", condition="hinglish")) - st2(sel(language="en_US", condition="direct"))
    gsh = st2(sel(language="en_US", condition="hinglish", task=FIVE, difficulty="short")) - st2(sel(language="hi_IN", condition="hinglish", task=FIVE, difficulty="short"))
    gvl = st2(sel(language="en_US", condition="hinglish", task=FIVE, difficulty="very_long")) - st2(sel(language="hi_IN", condition="hinglish", task=FIVE, difficulty="very_long"))
    b2[label] = {"gain_en": [pts(x) for x in ci(gh)], "gap_short": [pts(x) for x in ci(gsh)], "gap_very_long": [pts(x) for x in ci(gvl)]}
    if label == "hinglish_first":
        hg_ci = {"gain_hi": [pts(x) for x in ci(st2(sel(language="hi_IN", condition="hinglish")) - st2(sel(language="hi_IN", condition="direct")))]}
        for l_ in LANGS:
            for i_ in INS[1:]:
                bb_ = (st2(sel(language=l_, condition="hinglish", insertion="no_insertion")) - st2(sel(language=l_, condition="hinglish", insertion=i_))) - (st2(sel(language=l_, condition="direct", insertion="no_insertion")) - st2(sel(language=l_, condition="direct", insertion=i_)))
                hg_ci[f"{l_}/{i_}"] = [pts(x) for x in ci(bb_)]
        b2[label] |= hg_ci
    del w2
N["ci_seed_order_check"] = b2

ex = {}
sh = json.load(open(ROOT / "responses/hinglish/short.json", encoding="utf-8"))
sd = json.load(open(ROOT / "responses/standard/short.json", encoding="utf-8"))
stdmap = {(r["meta"]["task"], r["meta"]["language"], r["meta"]["question_id"], r["meta"]["insertion"]): r for r in sd if r["condition"] == "cot"}
for name, needle in (("subtraction", "01 minus 3 karne par hum 31 April"), ("recurrence", "toh kal 2025-06-28 hoga pehla occurrence"), ("hindi", "19:52")):
    hits = [r for r in sh if needle in (r["content"] or "") and (name != "hindi" or (r["meta"]["language"] == "hi_IN" and "20:17" in r["content"] and "सबसे पहले" in r["content"]))]
    ex[name] = [{"id": r["id"], "answer": answer_of(r["content"]), "gold": r["meta"]["answer"], "std_answer": answer_of(stdmap[(r["meta"]["task"], r["meta"]["language"], r["meta"]["question_id"], r["meta"]["insertion"])]["content"]), "excerpt": r["content"][:500]} for r in hits]
del sd
N["examples"] = ex
del sh



cm = {(d, str(q)): (to_d(v["no_insertion"]), to_d(v["answer"])) for (d, t), f in data.items() if t == "date_subtraction" for q, v in f.items()}
ws = wide[wide.task == "date_subtraction"].copy()
ws["cross"] = [cm[(d, str(q))][0].month != cm[(d, str(q))][1].month for d, q in zip(ws.difficulty, ws.qnum)]
cmo = {}
for lang in LANGS:
    for flag in (True, False):
        g_ = ws[(ws.language == lang) & (ws.cross == flag)]
        b_ = g_[g_.ans_h.astype(bool) & g_.ans_s.astype(bool)]
        lo, hi = boot_pair(g_, "ok_h", "ok_s", "ans_h", "ans_s")
        cmo[f"{lang}/{'cross' if flag else 'same'}"] = {"n": len(b_), "hing": pts(b_.ok_h.astype(float).mean()), "std": pts(b_.ok_s.astype(float).mean()), "diff": pts(b_.ok_h.astype(float).mean() - b_.ok_s.astype(float).mean()), "lo": pts(lo), "hi": pts(hi)}
N["subtraction_cross_paired"] = cmo
pv_ = wx[(wx["style"] == "plain") & (wx.fshare == 0)]
lo, hi = boot_pair(pv_, "vo_h", "vo_s", "ans_h", "ans_s")
N["pure_english_verification"]["diff_ci"] = [pts(lo), pts(hi)]
N["pure_english_verification"]["diff"] = pts(pv_.vo_h.astype(float).mean() - pv_.vo_s.astype(float).mean())
sty_ins = []
for ins in INS:
    g_ = wide[(wide.language == "en_US") & (wide.insertion == ins)]
    b_ = np.bincount(g_.qi, weights=(g_["style"] == "roman").astype(float), minlength=Q)
    n_ = np.bincount(g_.qi, minlength=Q).astype(float)
    lo, hi = ci((W @ b_) / (W @ n_))
    sty_ins.append({"insertion": ins, "roman_pct": pts((g_["style"] == "roman").mean()), "lo": pts(lo), "hi": pts(hi)})
N["roman_share_by_insertion_ci"] = sty_ins
save("new_roman_share_by_distractor", sty_ins, True)

save("table2_penalties", [{"key": k} | v for k, v in N["penalty"].items()], True)
save("table2_gaps", [{"key": k} | v for k, v in N["gap"].items() if "/five/" in k and ("/short/" in k or "/very_long/" in k)], True)
save("new_task_hing_minus_std", [{"language": r["language"], "task": r["task"], "diff_pairs": r["hs_diff_pairs"], "lo": r["hs_lo"], "hi": r["hs_hi"], "hing_only": r["hs_a_only"], "std_only": r["hs_b_only"], "p_holm18": r.get("hs_p_holm18"), "p_cluster_flip_holm9": r.get("hs_p_flip_holm9"), "diff_strict": r["hs_diff_strict"]} for r in rows], True)
save("new_split_headline", split, True)
save("new_verification_rates", [{"condition_language": k} | v for k, v in N["verification_condition"].items()], True)
save("new_length_verification_models", [{"model": m, "term": t} | v for m, d in N["covariate_models_english"].items() for t, v in d.items() if isinstance(v, dict)], True)
subx = []
for r in err:
    subx.append({"group": f"{r['condition']}/{r['language']}", "acc_cross_month": r["acc_cross_month"], "acc_same_month": r["acc_same_month"], "n_cross": r["n_cross"]})
for r in cr:
    subx.append({"group": f"hinglish/{r['language']}/{r['style']}", "acc_cross_month": r["acc_cross"], "acc_same_month": r["acc_same"], "n_cross": r["n_cross"]})
save("new_subtraction_month_cross", subx, True)
qtxt = {}
for t_, q_ in (("date_subtraction", "33"), ("date_recurrence", "17")):
    f_ = json.load(open(ROOT / "dataset/short" / f"{t_}_en_US.json", encoding="utf-8"))
    qtxt[t_] = f_[q_]["no_insertion"]
N["example_questions"] = qtxt

(OUT / "numbers.json").write_text(json.dumps(N, indent=2, ensure_ascii=False, default=lambda o: o.item() if hasattr(o, "item") else str(o)), encoding="utf-8")
print("ok", len(N))

exec(compile((OUT / "claims.py").read_text(encoding="utf-8"), "claims.py", "exec"))
