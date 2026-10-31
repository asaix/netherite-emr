from stats_core import *

R = {}
SPL = {"pooled": INS, "none": ["no_insertion"], "similar": ["similar_insertion"], "dissimilar": ["dissimilar_insertion"]}
COLS = {"answered": "acc", "strict": "strict"}
rows = []
for cname, col in COLS.items():
    for spl, ins in SPL.items():
        for lang in LANGS:
            for scope, kw in [("all", {})] + [(t, {"task": t}) for t in TASKS] + [(l, {"level": l}) for l in LEVELS]:
                r = cot_delta(mask(lang=lang, insertion=ins, **kw), col)
                rows.append({"scoring": cname, "split": spl, "lang": lang, "scope": scope, **r})
D = pd.DataFrame(rows)
for (cname, spl), g in D[D.scope.isin(TASKS)].groupby(["scoring", "split"]):
    D.loc[g.index, "mcnemar_holm"] = holm(g.mcnemar_p)
    D.loc[g.index, "q_t_holm"] = holm(g.q_t_p)
D.to_csv(FIG / "rq1_cot_delta_by_scope_split.csv", index=False)

rows = []
for cname, col in COLS.items():
    for spl, ins in SPL.items():
        for lang in LANGS:
            for t in TASKS:
                for l in LEVELS:
                    rows.append({"scoring": cname, "split": spl, "lang": lang, "task": t, "level": l, **cot_delta(mask(lang=lang, insertion=ins, task=t, level=l), col)})
G = pd.DataFrame(rows)
G.to_csv(FIG / "rq1_cot_delta_task_level.csv", index=False)

rows = []
for cname, col in COLS.items():
    for spl, ins in SPL.items():
        for cond in ("direct", "cot"):
            for scope, kw in [("all", {})] + [(t, {"task": t}) for t in TASKS] + [(l, {"level": l}) for l in LEVELS]:
                base = mask(cond=cond, insertion=ins, **kw)
                e, be = est(base & mask(lang="en_US"), col)
                h, bh = est(base & mask(lang="hi_IN"), col)
                rows.append({"scoring": cname, "split": spl, "cond": cond, "scope": scope, "en_acc": pct(e), "hi_acc": pct(h), **pct(e - h, be - bh)})
Gp = pd.DataFrame(rows)
Gp.to_csv(FIG / "rq1_gap_by_scope_split.csv", index=False)

rows = []
for cname, col in COLS.items():
    for spl, ins in SPL.items():
        for scope, kw in [("all", {})] + [(t, {"task": t}) for t in TASKS] + [(l, {"level": l}) for l in LEVELS]:
            base = mask(insertion=ins, **kw)
            eh = []
            for lang in LANGS:
                d, bd = est(base & mask(lang=lang, cond="direct"), col)
                c, bc = est(base & mask(lang=lang, cond="cot"), col)
                eh.append((c - d, bc - bd))
            rows.append({"scoring": cname, "split": spl, "scope": scope, **pct(eh[0][0] - eh[1][0], eh[0][1] - eh[1][1])})
pd.DataFrame(rows).to_csv(FIG / "rq1_gain_gap_by_scope_split.csv", index=False)

rows = []
for cname, col in COLS.items():
    for ins in INS[1:]:
        for scope, kw in [("all", {})] + [(t, {"task": t}) for t in TASKS] + [(l, {"level": l}) for l in LEVELS]:
            for lang in LANGS:
                rows.append({"scoring": cname, "ins": ins, "scope": scope, "lang": lang, **penalty(mask(lang=lang, **kw), ins, col)})
            rows.append({"scoring": cname, "ins": ins, "scope": scope, "lang": "hi_minus_en", **interaction(mask(**kw), ins, col)})
P = pd.DataFrame(rows)
for (cname, ins, lang), g in P[P.scope.isin(TASKS)].groupby(["scoring", "ins", "lang"]):
    P.loc[g.index, "q_t_holm"] = holm(g.q_t_p)
P.to_csv(FIG / "rq2_penalty_by_scope.csv", index=False)

rows = []
for cname, col in COLS.items():
    for ins in INS[1:]:
        for t in TASKS:
            for l in LEVELS:
                for lang in LANGS:
                    rows.append({"scoring": cname, "ins": ins, "task": t, "level": l, "lang": lang, **penalty(mask(lang=lang, task=t, level=l), ins, col)})
                rows.append({"scoring": cname, "ins": ins, "task": t, "level": l, "lang": "hi_minus_en", **interaction(mask(task=t, level=l), ins, col)})
PG = pd.DataFrame(rows)
PG.to_csv(FIG / "rq2_penalty_task_level.csv", index=False)

rows = []
idx = {"similar_insertion": "sim_idx", "dissimilar_insertion": "dis_idx"}
Q = pd.read_pickle(CACHE / "questions.pkl")
for ins, col_idx in idx.items():
    for t in TASKS:
        for s in range(5):
            txt = Q[(Q.task == t) & (Q.lang == "en_US")][["sim_text" if col_idx == "sim_idx" else "dis_text", col_idx]].drop_duplicates().set_index(col_idx).iloc[:, 0].to_dict()[s]
            for cname, col in COLS.items():
                for lang in LANGS:
                    drop = ~mask(task=t) | (F[col_idx].to_numpy() != s)
                    only = mask(task=t, lang=lang) & (F[col_idx].to_numpy() == s)
                    loo = penalty(mask(lang=lang) & drop, ins, col)
                    tloo = penalty(mask(lang=lang, task=t) & (F[col_idx].to_numpy() != s), ins, col)
                    sent = penalty(only, ins, col)
                    n_cut = int((~F[only & mask(cond="cot", insertion=ins)].answered).sum())
                    rows.append({"ins": ins, "task": t, "sent_idx": s, "sentence": txt, "scoring": cname, "lang": lang, "n_q": sent["n_q"], "n_q_total": int(F[only].qid.nunique()), "cot_cutoffs": n_cut, "sent_penalty": sent["v"], "sent_lo": sent["lo"], "sent_hi": sent["hi"], "loo_all_tasks": loo["v"], "loo_all_lo": loo["lo"], "loo_all_hi": loo["hi"], "loo_task": tloo["v"], "loo_task_lo": tloo["lo"], "loo_task_hi": tloo["hi"]})
pd.DataFrame(rows).to_csv(FIG / "rq2_loso.csv", index=False)
print("done")
