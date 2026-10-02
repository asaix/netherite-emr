import json
from pathlib import Path

import matplotlib

matplotlib.use("pdf")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from statsmodels.stats.contingency_tables import StratifiedTable
from scipy.stats import binomtest, fisher_exact
from statsmodels.stats.multitest import multipletests

HERE = Path(__file__).resolve().parent
OUT = HERE / "outputs"
TAB, FIG, DATA = OUT / "tables", OUT / "figures", OUT / "data"
for d in (TAB, FIG, DATA):
    d.mkdir(parents=True, exist_ok=True)

B = 2000
RNG = np.random.default_rng(0)
TASKS = ["date_addition", "date_subtraction", "date_duration", "date_recurrence", "day_of_week",
         "interval_date", "time_addition", "time_subtraction", "time_duration"]
LABEL = {"date_addition": "Date addition", "date_subtraction": "Date subtraction", "date_duration": "Date duration",
         "date_recurrence": "Date recurrence", "day_of_week": "Day of week", "interval_date": "Interval date",
         "time_addition": "Time addition", "time_subtraction": "Time subtraction", "time_duration": "Time duration"}
DIFFS = ["short", "medium", "long", "very_long"]
DIFF_LABEL = {"short": "Short", "medium": "Medium", "long": "Long", "very_long": "Very long"}
LANGS = ["en_US", "hi_IN"]
LANG = {"en_US": "English", "hi_IN": "Hindi"}

plt.rcParams.update({
    "font.family": "serif", "font.serif": ["Times New Roman"], "font.size": 9, "axes.titlesize": 9,
    "axes.labelsize": 9, "legend.fontsize": 8, "xtick.labelsize": 8, "ytick.labelsize": 8,
    "pdf.fonttype": 42, "ps.fonttype": 42, "axes.spines.top": False, "axes.spines.right": False,
})

df = pd.read_pickle(DATA / "responses.pkl")
df["correct"] = df["correct"].astype(float)
qids = df["qid"].unique()
df["qi"] = df["qid"].map({q: i for i, q in enumerate(qids)})
Q = len(qids)
WEIGHTS = np.stack([np.bincount(RNG.integers(0, Q, Q), minlength=Q) for _ in range(B)])
numbers, macros = {}, {}


def macro(name, value):
    macros[name] = value
    return value


def pval(p):
    return r"\(p<0.001\)" if p < 0.001 else rf"\(p={p:.3f}\)" if p < 0.01 else rf"\(p={p:.2f}\)"


def pct(x):
    return f"{100 * x:.1f}"


def signed(x):
    return f"{100 * x:+.1f}".replace("-", "$-$")


def counts(mask, strict=False):
    sub = df[mask] if strict else df[mask & df["scored"]]
    c = np.bincount(sub["qi"], weights=sub["correct"], minlength=Q)
    n = np.bincount(sub["qi"], minlength=Q).astype(float)
    return c, n


def acc(mask, strict=False):
    c, n = counts(mask, strict)
    return c.sum() / n.sum()


def boot_acc(mask, strict=False):
    c, n = counts(mask, strict)
    return (WEIGHTS @ c) / (WEIGHTS @ n)


def ci(samples):
    lo, hi = np.percentile(samples, [2.5, 97.5])
    return float(lo), float(hi)


def sel(**kw):
    mask = np.ones(len(df), dtype=bool)
    for k, v in kw.items():
        mask &= df[k].isin(v).to_numpy() if isinstance(v, (list, tuple, set)) else (df[k] == v).to_numpy()
    return mask


def mantel_haenszel(sub, exposure):
    tables = []
    for _, g in sub.groupby(["task", "difficulty"]):
        e, c = g[exposure].astype(bool), g["correct"] == 1
        t = np.array([[(e & c).sum(), (e & ~c).sum()], [(~e & c).sum(), (~e & ~c).sum()]], dtype=float)
        if t[0].sum() and t[1].sum():
            tables.append(t)
    st = StratifiedTable(tables)
    lo, hi = st.oddsratio_pooled_confint()
    return {"odds_ratio": float(st.oddsratio_pooled), "or_ci": [float(lo), float(hi)],
            "p": float(st.test_null_odds().pvalue), "strata": len(tables)}


def mcnemar(mask):
    sub = df[mask & df["scored"]]
    wide = sub.pivot_table(index=["qid", "insertion"], columns="condition", values="correct").dropna()
    b = int(((wide["cot"] == 1) & (wide["direct"] == 0)).sum())
    c = int(((wide["cot"] == 0) & (wide["direct"] == 1)).sum())
    return b, c, binomtest(b, b + c, 0.5).pvalue if b + c else 1.0


# 1. Overview
numbers["records"] = macro("NRecords", f"{len(df):,}")
numbers["questions"] = macro("NQuestions", f"{Q:,}")
numbers["scored"] = macro("NScored", f"{int(df['scored'].sum()):,}")
numbers["cutoff"] = macro("NCutoff", f"{int((~df['scored']).sum()):,}")
macro("NCutoffPct", pct((~df["scored"]).mean()))
numbers["cutoff_all_length"] = bool(df.loc[~df["scored"], "cutoff"].all())
cut = df[~df["scored"]].groupby(["language", "condition"]).size().to_dict()
numbers["cutoff_by_cell"] = {f"{k[0]}/{k[1]}": int(v) for k, v in cut.items()}
macro("NCutoffEnCot", str(cut.get(("en_US", "cot"), 0)))
macro("NCutoffHiCot", str(cut.get(("hi_IN", "cot"), 0)))

# 2. CoT delta (Table 1)
tests, cells = [], {}
for lang in LANGS:
    for task in TASKS + ["all"]:
        base = sel(language=lang) & (sel(task=task) if task != "all" else True)
        d, c = acc(base & sel(condition="direct")), acc(base & sel(condition="cot"))
        bd, bc = boot_acc(base & sel(condition="direct")), boot_acc(base & sel(condition="cot"))
        b, cc, p = mcnemar(base)
        cells[lang, task] = {"direct": d, "cot": c, "delta": c - d, "ci": ci(bc - bd), "cot_wins": b, "direct_wins": cc, "p": p}
        if task != "all":
            tests.append((lang, task))
reject, p_holm, _, _ = multipletests([cells[k]["p"] for k in tests], alpha=0.05, method="holm")
for k, r, ph in zip(tests, reject, p_holm):
    cells[k]["p_holm"], cells[k]["sig"] = float(ph), bool(r)
for lang in LANGS:
    cells[lang, "all"]["sig"] = cells[lang, "all"]["p"] < 0.05
numbers["cot_delta"] = {f"{k[0]}/{k[1]}": v for k, v in cells.items()}
nq = df.drop_duplicates("qid").groupby("task").size()

lines = [r"\begin{table*}[t]", r"\centering", r"\begin{tabular}{lrrrrrrr}", r"\toprule",
         r" & & \multicolumn{3}{c}{English} & \multicolumn{3}{c}{Hindi} \\",
         r"\cmidrule(lr){3-5}\cmidrule(lr){6-8}",
         r"Task & $Q$ & Direct & CoT & $\Delta$ & Direct & CoT & $\Delta$ \\", r"\midrule"]


def delta_cell(v):
    s = signed(v["delta"]) + (r"$^{*}$" if v["sig"] else r"\phantom{$^{*}$}")
    return r"\textbf{" + s + "}" if v["delta"] < 0 and v["sig"] else s


for task in TASKS + ["all"]:
    name = LABEL.get(task, "All tasks")
    q = int(nq[task]) if task != "all" else Q
    row = [name, f"{q:,}"]
    for lang in LANGS:
        v = cells[lang, task]
        row += [pct(v["direct"]), pct(v["cot"]), delta_cell(v)]
    if task == "all":
        lines.append(r"\midrule")
    lines.append(" & ".join(row) + r" \\")
lines += [r"\bottomrule", r"\end{tabular}",
          r"\caption{Accuracy (\%) with direct answers and chain-of-thought (CoT), pooled over difficulty levels and "
          r"distractor conditions. $Q$ is the number of questions; each question contributes three responses per language "
          r"and condition. $\Delta$ is CoT minus direct in percentage points; $^{*}$ marks $p<0.05$ in an exact McNemar "
          r"test on paired responses, Holm-corrected over the 18 task--language tests (uncorrected for the pooled row). "
          r"Significant negative deltas are in bold. Chance for day of week is 14.3\%.}",
          r"\label{tab:cot-delta}", r"\end{table*}"]
(TAB / "cot_delta.tex").write_text("\n".join(lines) + "\n")

for lang, p in (("en_US", "En"), ("hi_IN", "Hi")):
    v = cells[lang, "all"]
    macro(f"{p}DirectAcc", pct(v["direct"]))
    macro(f"{p}CotAcc", pct(v["cot"]))
    macro(f"{p}CotDelta", signed(v["delta"]))
    macro(f"{p}CotDeltaLo", signed(v["ci"][0]))
    macro(f"{p}CotDeltaHi", signed(v["ci"][1]))
    macro(f"{p}CotWins", f"{v['cot_wins']:,}")
    macro(f"{p}DirectWins", f"{v['direct_wins']:,}")
for task, name in (("interval_date", "Interval"), ("date_subtraction", "Subtraction"), ("day_of_week", "Dow"),
                   ("date_recurrence", "Recurrence"), ("time_duration", "TimeDuration")):
    for lang, p in (("en_US", "En"), ("hi_IN", "Hi")):
        v = cells[lang, task]
        macro(f"{p}{name}Direct", pct(v["direct"]))
        macro(f"{p}{name}Cot", pct(v["cot"]))
        macro(f"{p}{name}Delta", signed(v["delta"]))
neg = [t for t in TASKS if cells["hi_IN", t]["delta"] < 0 and cells["hi_IN", t]["sig"]]
numbers["hindi_significant_negative"] = neg
numbers["english_any_negative"] = [t for t in TASKS if cells["en_US", t]["delta"] < 0]
numbers["hindi_significant_positive"] = [t for t in TASKS if cells["hi_IN", t]["delta"] > 0 and cells["hi_IN", t]["sig"]]
numbers["english_significant_positive"] = [t for t in TASKS if cells["en_US", t]["delta"] > 0 and cells["en_US", t]["sig"]]
macro("NHiSigPos", str(len(numbers["hindi_significant_positive"])))
macro("NEnSigPos", str(len(numbers["english_significant_positive"])))
cutoff_rate = {f"{l}/{c}": float((~df[sel(language=l, condition=c)]["scored"]).mean()) for l in LANGS for c in ("direct", "cot")}
numbers["unscored_rate"] = cutoff_rate

# Strict accuracy robustness
for lang, p in (("en_US", "En"), ("hi_IN", "Hi")):
    d = acc(sel(language=lang, condition="direct"), strict=True)
    c = acc(sel(language=lang, condition="cot"), strict=True)
    numbers[f"strict/{lang}"] = {"direct": d, "cot": c, "delta": c - d}
    macro(f"{p}StrictDelta", signed(c - d))

# 3. Difficulty (Figure 1)
panels = [("date_addition date_duration".split(), DIFFS, "(a) Date addition and duration"),
          ("date_addition date_subtraction date_duration date_recurrence day_of_week".split(),
           ["short", "medium", "very_long"], "(b) Five date tasks")]
styles = {("en_US", "direct"): ("o", "-", "0.0", "English direct"), ("en_US", "cot"): ("s", "-", "0.0", "English CoT"),
          ("hi_IN", "direct"): ("o", "--", "0.45", "Hindi direct"), ("hi_IN", "cot"): ("s", "--", "0.45", "Hindi CoT")}
fig, axes = plt.subplots(1, 2, figsize=(6.3, 2.2), sharey=False)
diff_numbers = {}
for ax, (tasks, levels, title) in zip(axes, panels):
    for (lang, cond), (marker, ls, color, label) in styles.items():
        ys, los, his = [], [], []
        for lvl in levels:
            mask = sel(language=lang, condition=cond, difficulty=lvl, task=tasks)
            a, b = acc(mask), boot_acc(mask)
            ys.append(100 * a)
            lo, hi = ci(b)
            los.append(100 * (a - lo))
            his.append(100 * (hi - a))
            diff_numbers[f"{title[:3]}/{lvl}/{lang}/{cond}"] = a
        filled = "white" if cond == "direct" else color
        ax.errorbar(range(len(levels)), ys, yerr=[los, his], marker=marker, linestyle=ls, color=color,
                    markerfacecolor=filled, markersize=4.5, linewidth=1.1, capsize=2, label=label)
    for lvl in levels:
        for cond in ("direct", "cot"):
            mask = sel(condition=cond, difficulty=lvl, task=tasks)
            gap = acc(mask & sel(language="en_US")) - acc(mask & sel(language="hi_IN"))
            gap_b = boot_acc(mask & sel(language="en_US")) - boot_acc(mask & sel(language="hi_IN"))
            diff_numbers[f"gap/{title[:3]}/{lvl}/{cond}"] = {"gap": gap, "ci": ci(gap_b)}
    ax.set_xticks(range(len(levels)), [DIFF_LABEL[l] for l in levels])
    ax.set_title(title)
    ax.set_xlabel("TRD difficulty level")
    ax.grid(axis="y", color="0.85", linewidth=0.5)
axes[0].set_ylabel("Accuracy (%)")
handles, labels = axes[0].get_legend_handles_labels()
fig.legend(handles, labels, loc="lower center", ncol=4, frameon=False, bbox_to_anchor=(0.5, -0.04))
fig.tight_layout(rect=(0, 0.1, 1, 1))
fig.savefig(FIG / "difficulty.pdf")
plt.close(fig)
numbers["difficulty"] = diff_numbers
for cond, p in (("direct", "Direct"), ("cot", "Cot")):
    for lvl, lp in (("short", "Short"), ("very_long", "VeryLong")):
        g = diff_numbers[f"gap/(b)/{lvl}/{cond}"]
        macro(f"Gap{p}{lp}", pct(g["gap"]))
    for lvl, lp in (("short", "Short"), ("long", "Long"), ("very_long", "VeryLong")):
        g = diff_numbers[f"gap/(a)/{lvl}/{cond}"]
        macro(f"GapA{p}{lp}", pct(g["gap"]))
for lang, p in (("en_US", "En"), ("hi_IN", "Hi")):
    for cond, c in (("direct", "Direct"), ("cot", "Cot")):
        for lvl, lp in (("short", "Short"), ("very_long", "VeryLong")):
            macro(f"A{p}{c}{lp}", pct(diff_numbers[f"(a)/{lvl}/{lang}/{cond}"]))

# 4. Distractors (Table 2)
INS = ["no_insertion", "similar_insertion", "dissimilar_insertion"]
dist = {}
for lang in LANGS:
    for cond in ("direct", "cot"):
        for ins in INS:
            m = sel(language=lang, condition=cond, insertion=ins)
            dist[lang, cond, ins] = (acc(m), boot_acc(m))
    for ins in INS[1:]:
        drops = {}
        for cond in ("direct", "cot"):
            a0, b0 = dist[lang, cond, "no_insertion"]
            a1, b1 = dist[lang, cond, ins]
            drops[cond] = (a0 - a1, b0 - b1)
        did, did_b = drops["cot"][0] - drops["direct"][0], drops["cot"][1] - drops["direct"][1]
        dist[lang, "did", ins] = (did, did_b)
        for cond in ("direct", "cot"):
            dist[lang, f"drop_{cond}", ins] = drops[cond]
numbers["distractor"] = {"/".join(k): {"value": v[0], "ci": ci(v[1])} for k, v in dist.items()}
lines = [r"\begin{table}[t]", r"\centering", r"\small", r"\setlength{\tabcolsep}{4pt}", r"\begin{tabular}{lrrrrr}",
         r"\toprule", r" & \multicolumn{3}{c}{Accuracy} & \multicolumn{2}{c}{Drop} \\",
         r"\cmidrule(lr){2-4}\cmidrule(lr){5-6}", r" & None & Sim. & Dis. & Sim. & Dis. \\", r"\midrule"]


def did_cell(v):
    lo, hi = ci(v[1])
    s = signed(v[0])
    return r"\textbf{" + s + "}" if lo > 0 or hi < 0 else s


for i, lang in enumerate(LANGS):
    if i:
        lines.append(r"\midrule")
    lines.append(r"\multicolumn{6}{l}{\textit{" + LANG[lang] + r"}} \\")
    for cond, name in (("direct", "Direct"), ("cot", "CoT")):
        row = [r"\quad " + name] + [pct(dist[lang, cond, ins][0]) for ins in INS]
        row += [signed(dist[lang, f"drop_{cond}", ins][0]) for ins in INS[1:]]
        lines.append(" & ".join(row) + r" \\")
    row = [r"\quad CoT $-$ direct", "", "", ""] + [did_cell(dist[lang, "did", ins]) for ins in INS[1:]]
    lines.append(" & ".join(row) + r" \\")
lines += [r"\bottomrule", r"\end{tabular}",
          r"\caption{Accuracy (\%) with no distractor (None), a time-related (Sim.) or an unrelated (Dis.) distractor. "
          r"Drop is accuracy without the distractor minus accuracy with it (points; positive means the distractor hurt). "
          r"CoT $-$ direct is the CoT drop minus the direct drop (the CoT distraction penalty); bold marks a 95\% cluster-bootstrap interval that excludes zero.}",
          r"\label{tab:distractor}", r"\end{table}"]
(TAB / "distractor.tex").write_text("\n".join(lines) + "\n")
for lang, p in (("en_US", "En"), ("hi_IN", "Hi")):
    for ins, ip in (("similar_insertion", "Sim"), ("dissimilar_insertion", "Dis")):
        v, b = dist[lang, "did", ins]
        lo, hi = ci(b)
        macro(f"{p}Did{ip}", signed(v))
        macro(f"{p}Did{ip}Lo", signed(lo))
        macro(f"{p}Did{ip}Hi", signed(hi))
        for cond, c in (("direct", "Direct"), ("cot", "Cot")):
            macro(f"{p}Drop{c}{ip}", signed(dist[lang, f"drop_{cond}", ins][0]))

task_did = {}
for lang in LANGS:
    for task in TASKS:
        for ins in INS[1:]:
            vals = {}
            for cond in ("direct", "cot"):
                m0 = sel(language=lang, condition=cond, insertion="no_insertion", task=task)
                m1 = sel(language=lang, condition=cond, insertion=ins, task=task)
                vals[cond] = (acc(m0) - acc(m1), boot_acc(m0) - boot_acc(m1))
            d = vals["cot"][0] - vals["direct"][0]
            task_did[f"{lang}/{task}/{ins}"] = {"drop_cot": vals["cot"][0], "drop_direct": vals["direct"][0], "did": d,
                                                "ci": ci(vals["cot"][1] - vals["direct"][1])}
numbers["distractor_by_task"] = task_did
pd.DataFrame(task_did).T.to_csv(DATA / "distractor_by_task.csv")
for t, tp in (("date_duration", "Duration"), ("day_of_week", "Dow"), ("time_duration", "TimeDuration"), ("date_recurrence", "Rec")):
    v = task_did[f"hi_IN/{t}/similar_insertion"]
    macro(f"HiDidSim{tp}", signed(v["did"]))
    macro(f"HiDidSim{tp}Lo", signed(v["ci"][0]))
    macro(f"HiDidSim{tp}Hi", signed(v["ci"][1]))
macro("EnMaxDrop", f"{100 * max(dist['en_US', f'drop_{c}', i][0] for c in ('direct', 'cot') for i in INS[1:]):.1f}")
macro("HiDropCotSimAbs", f"{100 * abs(dist['hi_IN', 'drop_cot', 'similar_insertion'][0]):.1f}")
macro("HiDidSimAbs", f"{100 * abs(dist['hi_IN', 'did', 'similar_insertion'][0]):.1f}")
rec = task_did["hi_IN/date_recurrence/similar_insertion"]
macro("HiRecSimDropCot", signed(rec["drop_cot"]))
macro("HiRecSimDropDirect", signed(rec["drop_direct"]))
rec = task_did["en_US/date_recurrence/similar_insertion"]
macro("EnRecSimDropCot", signed(rec["drop_cot"]))

# Distractor reuse in wrong answers
reuse = {}
for lang in LANGS:
    for cond in ("direct", "cot"):
        ins_rows = df[sel(language=lang, condition=cond, insertion="similar_insertion") & df["reuse_similar"].notna()]
        plc_rows = df[sel(language=lang, condition=cond, insertion="no_insertion") & df["reuse_similar"].notna()]
        a, n1 = int(ins_rows["reuse_similar"].sum()), len(ins_rows)
        b, n2 = int(plc_rows["reuse_similar"].sum()), len(plc_rows)
        p = fisher_exact([[a, n1 - a], [b, n2 - b]])[1] if n1 and n2 else float("nan")
        reuse[f"{lang}/{cond}"] = {"inserted": a, "inserted_n": n1, "placebo": b, "placebo_n": n2, "p": p}
numbers["reuse_similar"] = reuse
for lang, p in (("en_US", "En"), ("hi_IN", "Hi")):
    for cond, c in (("direct", "Direct"), ("cot", "Cot")):
        r = reuse[f"{lang}/{cond}"]
        macro(f"{p}Reuse{c}", pct(r["inserted"] / r["inserted_n"]) if r["inserted_n"] else "--")
        macro(f"{p}Reuse{c}N", f"{r['inserted']} of {r['inserted_n']:,}")
        macro(f"{p}Reuse{c}Placebo", pct(r["placebo"] / r["placebo_n"]) if r["placebo_n"] else "--")
        macro(f"{p}Reuse{c}PlaceboN", f"{r['placebo']} of {r['placebo_n']:,}")
        macro(f"{p}Reuse{c}P", pval(r["p"]))

# Distractor mention in the trace
mention = {}
for lang in LANGS:
    for kind in ("similar", "dissimilar"):
        col = f"mentions_{kind}"
        ins_mask = sel(language=lang, condition="cot", insertion=f"{kind}_insertion") & df[col].notna()
        plc_mask = sel(language=lang, condition="cot", insertion="no_insertion") & df[col].notna()
        sub = df[ins_mask].copy()
        sub["mention"] = sub[col].astype(bool)
        mention[f"{lang}/{kind}"] = {
            "inserted_rate": float(df.loc[ins_mask, col].mean()), "placebo_rate": float(df.loc[plc_mask, col].mean()),
            "n": int(ins_mask.sum()), "acc_mention": float(sub.loc[sub["mention"], "correct"].mean()),
            "acc_no_mention": float(sub.loc[~sub["mention"], "correct"].mean()),
            **mantel_haenszel(sub, "mention"),
        }
numbers["mention"] = mention
for lang, p in (("en_US", "En"), ("hi_IN", "Hi")):
    for kind, k in (("similar", "Sim"), ("dissimilar", "Dis")):
        v = mention[f"{lang}/{kind}"]
        macro(f"{p}Mention{k}", pct(v["inserted_rate"]))
        macro(f"{p}Mention{k}Placebo", pct(v["placebo_rate"]))
        macro(f"{p}Mention{k}OR", f"{v['odds_ratio']:.2f}")
        macro(f"{p}Mention{k}ORLo", f"{v['or_ci'][0]:.2f}")
        macro(f"{p}Mention{k}ORHi", f"{v['or_ci'][1]:.2f}")
        macro(f"{p}Mention{k}P", pval(v["p"]))
        macro(f"{p}Mention{k}OddsDrop", f"{100 * (1 - v['odds_ratio']):.0f}")
lines = [r"\begin{table}[ht]", r"\centering", r"\small", r"\begin{tabular}{llrr}", r"\toprule",
         r"Distractor & Language & Traces & OR [95\% CI] \\", r"\midrule"]
for i, (kind, name) in enumerate((("similar", "Time-related"), ("dissimilar", "Unrelated"))):
    if i:
        lines.append(r"\midrule")
    for lang in LANGS:
        v = mention[f"{lang}/{kind}"]
        lines.append(f"{name if lang == 'en_US' else ''} & {LANG[lang]} & {v['n']:,} & "
                     f"{v['odds_ratio']:.2f} [{v['or_ci'][0]:.2f}, {v['or_ci'][1]:.2f}]" + r" \\")
lines += [r"\bottomrule", r"\end{tabular}",
          r"\caption{Odds ratio (OR) of a correct answer for CoT traces that mention the distractor versus traces that "
          r"do not, stratified by task and difficulty (Mantel--Haenszel). Traces is the number of CoT responses whose prompt "
          r"contained that distractor.}",
          r"\label{tab:mention-or}", r"\end{table}"]
(TAB / "mention_or.tex").write_text("\n".join(lines) + "\n")

# 5. Trace properties (Table 3)
props = {}
for lang in LANGS:
    cot = df[sel(language=lang, condition="cot")]
    sc = cot[cot["scored"]]
    ratio = sc["target_words"] / sc["words"].where(sc["words"] > 0)
    props[lang] = {
        "unscored": float((~cot["scored"]).mean()),
        "median_words": float(sc["words"].median()),
        "median_tokens": float(sc["completion_tokens"].median()),
        "ratio_pooled": float(sc["target_words"].sum() / sc["words"].sum()),
        "ratio_below_09": float((ratio < 0.9).mean()),
        "verification": float(sc["verification"].mean()),
        "answer_in_reasoning": float(sc["answer_in_reasoning"].dropna().mean()),
        "wrong": int((sc["correct"] == 0).sum()),
        "wrong_ends_at_gold": int(((sc["correct"] == 0) & (sc["reasoning_ends_at_gold"] == True)).sum()),
        "acc_ratio_below_09": float(sc.loc[ratio < 0.9, "correct"].mean()) if (ratio < 0.9).any() else float("nan"),
        "acc_ratio_atleast_09": float(sc.loc[ratio >= 0.9, "correct"].mean()),
        "n_ratio_below_09": int((ratio < 0.9).sum()),
    }
numbers["trace"] = props
rows = [("Cut off before answering", lambda v: pct(v["unscored"]) + r"\%"),
        ("Median length (words)", lambda v: f"{v['median_words']:.0f}"),
        ("Median completion tokens", lambda v: f"{v['median_tokens']:.0f}"),
        ("Target-language ratio", lambda v: f"{v['ratio_pooled']:.3f}"),
        ("Ratio below 0.9", lambda v: pct(v["ratio_below_09"]) + r"\%"),
        ("Has a verification step", lambda v: pct(v["verification"]) + r"\%"),
        ("Answer value in trace", lambda v: pct(v["answer_in_reasoning"]) + r"\%"),
        (r"Mentions sim.\ distractor", lambda v: v["sim"]),
        (r"Mentions dis.\ distractor", lambda v: v["dis"])]
for lang in LANGS:
    for kind, k in (("similar", "sim"), ("dissimilar", "dis")):
        m = mention[f"{lang}/{kind}"]
        props[lang][k] = pct(m["inserted_rate"]) + r"\% (" + pct(m["placebo_rate"]) + ")"
lines = [r"\begin{table}[t]", r"\centering", r"\small", r"\setlength{\tabcolsep}{4pt}", r"\begin{tabular}{lrr}", r"\toprule",
         r" & English & Hindi \\", r"\midrule"]
for name, f in rows:
    lines.append(f"{name} & {f(props['en_US'])} & {f(props['hi_IN'])}" + r" \\")
lines += [r"\bottomrule", r"\end{tabular}",
          r"\caption{Properties of CoT responses. All rows except the first are computed over graded responses. The "
          r"target-language ratio is the number of target-language words divided by the number of Hindi plus English "
          r"words, with both counts summed over all responses before dividing, so longer traces weigh more. Distractor "
          r"mention rates are for traces whose prompt contained that distractor; the value in parentheses is the "
          r"placebo rate for the same questions without it.}",
          r"\label{tab:trace}", r"\end{table}"]
(TAB / "trace.tex").write_text("\n".join(lines) + "\n")
for lang, p in (("en_US", "En"), ("hi_IN", "Hi")):
    v = props[lang]
    macro(f"{p}MedianWords", f"{v['median_words']:.0f}")
    macro(f"{p}MedianTokens", f"{v['median_tokens']:.0f}")
    macro(f"{p}Verification", pct(v["verification"]))
    macro(f"{p}RatioPooled", f"{v['ratio_pooled']:.3f}")
    macro(f"{p}RatioBelow", pct(v["ratio_below_09"]))
    macro(f"{p}Wrong", f"{v['wrong']:,}")
    macro(f"{p}WrongEndsGold", str(v["wrong_ends_at_gold"]))
    macro(f"{p}AnswerInTrace", pct(v["answer_in_reasoning"]))
macro("HiAccRatioBelow", pct(props["hi_IN"]["acc_ratio_below_09"]))
macro("HiAccRatioAbove", pct(props["hi_IN"]["acc_ratio_atleast_09"]))
macro("HiNRatioBelow", f"{props['hi_IN']['n_ratio_below_09']:,}")

en_cot = df[sel(language="en_US", condition="cot") & df["scored"]].copy()
numbers["verification_en"] = {**mantel_haenszel(en_cot, "verification"),
                              "acc_with": float(en_cot.loc[en_cot["verification"], "correct"].mean()),
                              "acc_without": float(en_cot.loc[~en_cot["verification"], "correct"].mean())}
macro("VerOR", f"{numbers['verification_en']['odds_ratio']:.2f}")
macro("VerORLo", f"{numbers['verification_en']['or_ci'][0]:.2f}")
macro("VerORHi", f"{numbers['verification_en']['or_ci'][1]:.2f}")
macro("VerP", pval(numbers["verification_en"]["p"]))
ver_dow = en_cot[en_cot["task"] == "day_of_week"]["verification"]
macro("VerDowN", f"{int(ver_dow.sum()):,}")
macro("VerDowTotal", f"{len(ver_dow):,}")
hi_cot = df[sel(language="hi_IN", condition="cot") & df["scored"]].copy()
hi_cot["drift"] = (hi_cot["target_words"] / hi_cot["words"].where(hi_cot["words"] > 0)) < 0.9
drift = mantel_haenszel(hi_cot, "drift")
drift["by_task"] = hi_cot[hi_cot["drift"]].groupby("task").size().to_dict()
drift["acc_by_task"] = {t: {"drift": float(g.loc[g["drift"], "correct"].mean()) if g["drift"].any() else None,
                            "no_drift": float(g.loc[~g["drift"], "correct"].mean())} for t, g in hi_cot.groupby("task")}
numbers["hindi_drift"] = drift
macro("DriftOR", f"{drift['odds_ratio']:.2f}")
macro("DriftORLo", f"{drift['or_ci'][0]:.2f}")
macro("DriftORHi", f"{drift['or_ci'][1]:.2f}")
macro("DriftP", pval(drift["p"]))
macro("DriftStrata", str(drift["strata"]))
macro("DriftDow", str(drift["by_task"].get("day_of_week", 0)))
macro("DriftRec", str(drift["by_task"].get("date_recurrence", 0)))
for t, tp in (("day_of_week", "Dow"), ("date_recurrence", "Rec")):
    macro(f"Drift{tp}Acc", pct(drift["acc_by_task"][t]["drift"]))
    macro(f"Drift{tp}AccNo", pct(drift["acc_by_task"][t]["no_drift"]))
macro("VerAccWith", pct(numbers["verification_en"]["acc_with"]))
macro("VerAccWithout", pct(numbers["verification_en"]["acc_without"]))

# 6. Cross-lingual agreement
pairs = df[df["scored"]].pivot_table(index=["qid", "task", "difficulty", "insertion", "condition"], columns="language",
                                     values="correct").dropna().reset_index()
agree = {}
for cond in ("direct", "cot"):
    p = pairs[pairs["condition"] == cond]
    en, hi = p["en_US"] == 1, p["hi_IN"] == 1
    eo, ho = int((en & ~hi).sum()), int((~en & hi).sum())
    phis, splits, indep = [], [], []
    for _, g in p.groupby(["difficulty", "task"]):
        e, h = g["en_US"] == 1, g["hi_IN"] == 1
        pe, ph = e.mean(), h.mean()
        den = np.sqrt(pe * (1 - pe) * ph * (1 - ph))
        if den:
            phis.append(((e & h).mean() - pe * ph) / den)
    agree[cond] = {"pairs": len(p), "both_right": int((en & hi).sum()), "both_wrong": int((~en & ~hi).sum()),
                   "en_only": eo, "hi_only": ho, "p": binomtest(eo, eo + ho, 0.5).pvalue,
                   "median_phi": float(np.median(phis)), "phi_iqr": [float(x) for x in np.percentile(phis, [25, 75])]}
numbers["agreement"] = agree
for cond, c in (("direct", "Direct"), ("cot", "Cot")):
    v = agree[cond]
    macro(f"Agree{c}Pairs", f"{v['pairs']:,}")
    macro(f"Agree{c}EnOnly", f"{v['en_only']:,}")
    macro(f"Agree{c}HiOnly", f"{v['hi_only']:,}")
    macro(f"Agree{c}Phi", f"{v['median_phi']:.2f}")
    macro(f"Agree{c}BothRight", f"{v['both_right']:,}")
    macro(f"Agree{c}BothWrong", f"{v['both_wrong']:,}")

# 7. Day of week (Figure 2)
dow = df[sel(task="day_of_week") & df["scored"]]
fig, ax = plt.subplots(figsize=(3.03, 1.8))
offsets = list(range(-3, 4))
series = [("en_US", "direct", "white", ""), ("hi_IN", "direct", "white", "////"),
          ("en_US", "cot", "0.25", ""), ("hi_IN", "cot", "0.7", "////")]
width = 0.2
dow_numbers = {}
for i, (lang, cond, color, hatch) in enumerate(series):
    s = dow[(dow["language"] == lang) & (dow["condition"] == cond)]["weekday_offset"].dropna().astype(int)
    share = [100 * (s == o).mean() for o in offsets]
    dow_numbers[f"{lang}/{cond}"] = dict(zip(map(str, offsets), share))
    ax.bar([o + (i - 1.5) * width for o in offsets], share, width, color=color, edgecolor="black", linewidth=0.5,
           hatch=hatch, label=f"{LANG[lang]} {'CoT' if cond == 'cot' else 'direct'}")
ax.axhline(100 / 7, color="black", linestyle=":", linewidth=0.8)
ax.text(3.45, 100 / 7 + 1.5, "chance", ha="right", fontsize=7)
ax.set_xticks(offsets, [f"{o:+d}" if o else "0" for o in offsets])
ax.set_xlabel("Predicted minus correct weekday (days)")
ax.set_ylabel("Responses (%)")
ax.legend(frameon=False, ncol=2, loc="lower center", bbox_to_anchor=(0.5, 1.0), fontsize=7, handlelength=1.5, columnspacing=0.8)
ax.set_ylim(0, 80)
ax.grid(axis="y", color="0.85", linewidth=0.5)
fig.tight_layout()
fig.savefig(FIG / "day_of_week.pdf")
plt.close(fig)
pred = {}
for lang in LANGS:
    s = dow[(dow["language"] == lang) & (dow["condition"] == "direct")]["predicted_weekday"].dropna().astype(int)
    vc = s.value_counts(normalize=True)
    pred[lang] = {"mode": int(vc.index[0]), "share": float(vc.iloc[0])}
numbers["day_of_week"] = {"offsets": dow_numbers, "direct_mode": pred}
DAY = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
macro("EnDowModeDay", DAY[pred["en_US"]["mode"]])
macro("EnDowModeShare", pct(pred["en_US"]["share"]))
macro("HiDowModeDay", DAY[pred["hi_IN"]["mode"]])
macro("HiDowModeShare", pct(pred["hi_IN"]["share"]))
macro("HiDowCotZero", pct(dow_numbers["hi_IN/cot"]["0"] / 100))
macro("HiDowCotPlusOne", pct(dow_numbers["hi_IN/cot"]["1"] / 100))
macro("EnDowCotPlusOne", pct(dow_numbers["en_US/cot"]["1"] / 100))
macro("EnDowCotMinusOne", pct(dow_numbers["en_US/cot"]["-1"] / 100))
for lang, p in (("en_US", "En"), ("hi_IN", "Hi")):
    v = list(dow_numbers[f"{lang}/direct"].values())
    macro(f"{p}DowDirectMin", pct(min(v) / 100))
    macro(f"{p}DowDirectMax", pct(max(v) / 100))

# Date recurrence answer patterns
recur = {}
for lang in LANGS:
    for cond in ("direct", "cot"):
        s = df[sel(task="date_recurrence", language=lang, condition=cond) & df["recurrence_pattern"].notna()]["recurrence_pattern"]
        recur[f"{lang}/{cond}"] = s.value_counts(normalize=True).to_dict()
        recur[f"{lang}/{cond}"]["n"] = int(len(s))
numbers["recurrence"] = recur
for lang, p in (("en_US", "En"), ("hi_IN", "Hi")):
    for cond, c in (("direct", "Direct"), ("cot", "Cot")):
        v = recur[f"{lang}/{cond}"]
        macro(f"{p}Rec{c}FirstStep", pct(v.get("first_step", 0)))
        macro(f"{p}Rec{c}Mirror", pct(v.get("mirror", 0)))

# 8. Error composition (Figure 3)
GROUPS = {"off_by_one": "Off by one", "wrong_direction": "Wrong direction", "month_slip": "Month slip"}
errs = df[(df["condition"] == "cot") & df["error_type"].notna()].copy()
errs["group"] = errs["error_type"].map(lambda e: GROUPS.get(e, "Other"))
show = [t for t in TASKS if all(((errs["task"] == t) & (errs["language"] == l)).sum() >= 25 for l in LANGS)]
order = ["Off by one", "Wrong direction", "Month slip", "Other"]
fill = {"Off by one": ("0.2", ""), "Wrong direction": ("white", "xxxx"), "Month slip": ("0.75", ""), "Other": ("white", "")}
labels, data = [], []
comp = {}
for t in show:
    for l in LANGS:
        g = errs[(errs["task"] == t) & (errs["language"] == l)]["group"].value_counts(normalize=True)
        labels.append(f"{LABEL[t]} ({'En' if l == 'en_US' else 'Hi'}, n={int(((errs['task'] == t) & (errs['language'] == l)).sum())})")
        data.append([g.get(k, 0.0) for k in order])
        comp[f"{l}/{t}"] = dict(zip(order, [float(x) for x in data[-1]]))
for l in LANGS:
    g = errs[errs["language"] == l]["group"].value_counts(normalize=True)
    comp[f"{l}/all"] = {k: float(g.get(k, 0.0)) for k in order}
    comp[f"{l}/all"]["n"] = int((errs["language"] == l).sum())
numbers["error_composition_cot"] = comp
numbers["error_tasks_shown"] = show
data = np.array(data)
fig, ax = plt.subplots(figsize=(3.03, 0.2 * len(labels) + 0.8))
left = np.zeros(len(labels))
ypos = np.arange(len(labels))[::-1]
for j, k in enumerate(order):
    color, hatch = fill[k]
    ax.barh(ypos, 100 * data[:, j], left=left, color=color, hatch=hatch, edgecolor="black", linewidth=0.5, label=k)
    left += 100 * data[:, j]
ax.set_yticks(ypos, labels, fontsize=7)
ax.tick_params(axis="y", length=0)
ax.set_xlim(0, 100)
ax.set_xlabel("Share of wrong CoT answers (%)")
ax.legend(frameon=False, ncol=2, loc="lower center", bbox_to_anchor=(0.35, 1.0), fontsize=7, handlelength=1.5)
fig.tight_layout()
fig.savefig(FIG / "error_types.pdf")
plt.close(fig)
for t, tp in (("date_addition", "Add"), ("date_subtraction", "Sub"), ("day_of_week", "Dow")):
    for l, p in (("en_US", "En"), ("hi_IN", "Hi")):
        if f"{l}/{t}" in comp:
            macro(f"{p}Err{tp}OffByOne", pct(comp[f"{l}/{t}"]["Off by one"]))
            macro(f"{p}Err{tp}MonthSlip", pct(comp[f"{l}/{t}"]["Month slip"]))
for l, p in (("en_US", "En"), ("hi_IN", "Hi")):
    macro(f"{p}ErrAllOffByOne", pct(comp[f"{l}/all"]["Off by one"]))
    macro(f"{p}ErrAllN", f"{comp[f'{l}/all']['n']:,}")
invalid = df[df["error_type"] == "invalid_answer"]
numbers["invalid_answers"] = {"total": int(len(invalid)), "direct": int((invalid["condition"] == "direct").sum())}
macro("NInvalid", str(len(invalid)))
macro("NInvalidDirect", str(int((invalid["condition"] == "direct").sum())))


cov = df.drop_duplicates("qid").groupby(["task", "difficulty"]).size()
ALL_DIFFS = DIFFS + ["very_very_long"]
lines = [r"\begin{table}[t]", r"\centering", r"\small", r"\setlength{\tabcolsep}{3.5pt}", r"\begin{tabular}{@{}lrrrrr@{}}",
         r"\toprule", r"Task & Short & Med. & Long & V.\ long & V.V.\ long \\", r"\midrule"]
for task in TASKS:
    cells = [str(int(cov[task, d])) if (task, d) in cov.index else "--" for d in ALL_DIFFS]
    lines.append(f"{LABEL[task]} & " + " & ".join(cells) + r" \\")
tot = [str(int(cov.xs(d, level="difficulty").sum())) if d in cov.index.get_level_values("difficulty") else "--" for d in ALL_DIFFS]
lines += [r"\midrule", "Total & " + " & ".join(tot) + r" \\", r"\bottomrule", r"\end{tabular}",
          r"\caption{Questions answered in all 12 conditions, by task and difficulty level, out of 150 generated per cell. "
          r"Cells marked -- were not run, or only partly run, before the API credit ran out and are left out of the analysis.}",
          r"\label{tab:coverage}", r"\end{table}"]
(TAB / "coverage.tex").write_text("\n".join(lines) + "\n")
macro("NPlannedQuestions", f"{len(TASKS) * len(ALL_DIFFS) * 150:,}")
macro("CoveragePct", f"{100 * Q / (len(TASKS) * len(ALL_DIFFS) * 150):.0f}")

with open(DATA / "numbers.json", "w", encoding="utf-8") as f:
    json.dump(numbers, f, ensure_ascii=False, indent=2, default=float)
(TAB / "macros.tex").write_text("".join(f"\\newcommand{{\\{k}}}{{{v}}}\n" for k, v in sorted(macros.items())))
print(len(macros), "macros")
