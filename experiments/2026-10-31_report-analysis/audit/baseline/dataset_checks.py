import re

from common import *

Q = pd.read_pickle(CACHE / "questions.pkl")
F = frame()
rng = np.random.default_rng(30)
out = {"all_gold_match_python_datetime": bool(Q.gold_check.all()), "n_checked": len(Q), "by_task": {t: int(g.gold_check.sum()) for t, g in Q.groupby("task")}}
rows = []
for t in TASKS:
    s = Q[(Q.task == t) & (Q.lang == "hi_IN")]
    for i in rng.choice(s.index.to_numpy(), 30, replace=False):
        r = s.loc[i]
        e = Q[(Q.task == t) & (Q.lang == "en_US") & (Q.level == r.level) & (Q.qnum == r.qnum)].iloc[0]
        rows.append({"task": t, "level": r.level, "qnum": r.qnum, "question_en": e.qtext, "question_hi": r.qtext, "gold_en": e.gold, "gold_hi": r.gold, "independent_value": r.gold_computed, "match": bool(r.gold_check and e.gold_check)})
pd.DataFrame(rows).to_csv(FIG / "gold_spotcheck_30_per_task.csv", index=False)
out["spotcheck_n"] = len(rows)
out["spotcheck_match"] = int(sum(r["match"] for r in rows))
e = Q[Q.lang == "en_US"].set_index(["level", "task", "qnum"])
h = Q[Q.lang == "hi_IN"].set_index(["level", "task", "qnum"])
same = (e.gold_computed.astype(str) == h.gold_computed.astype(str)).mean()
out["en_hi_same_computed_gold"] = float(same)
out["en_hi_same_params"] = float((e.params == h.params).mean())
out["duplicate_questions_within_cell"] = int(Q.duplicated(["level", "task", "lang", "qtext"]).sum())
out["counts_per_cell"] = sorted(Q.groupby(["level", "task", "lang"]).size().unique().tolist())
p = {t: F[(F.task == t)].groupby("level").size().to_dict() for t in TASKS[:1]}
med = F[(F.level == "medium") & (F.cond == "direct") & (F.insertion == "no_insertion")].groupby(["task", "lang"]).strict.mean().unstack() * 100
T6 = {"claude-3-5-sonnet": {"date_addition": (1.0, 1.0), "date_duration": (1.0, 1.0), "date_recurrence": (.82, .36), "date_subtraction": (1.0, 1.0), "day_of_week": (1.0, .94), "interval_date": (.98, .97), "time_addition": (1.0, .97), "time_duration": (1.0, 1.0), "time_subtraction": (.99, .99)}, "claude-3-haiku": {"date_addition": (.99, 1.0), "date_duration": (.99, .96), "date_recurrence": (.09, 0.0), "date_subtraction": (1.0, .99), "day_of_week": (1.0, .33), "interval_date": (.60, .73), "time_addition": (.92, .94), "time_duration": (.99, .97), "time_subtraction": (.98, .93)}, "mistral-large-2402": {"date_addition": (.99, .99), "date_duration": (.96, .77), "date_recurrence": (.25, 0.0), "date_subtraction": (1.0, 1.0), "day_of_week": (.86, .25), "interval_date": (.69, .31), "time_addition": (.94, .83), "time_duration": (.68, .67), "time_subtraction": (.95, .74)}, "command-r-plus": {"date_addition": (.95, .99), "date_duration": (.97, .92), "date_recurrence": (.03, 0.0), "date_subtraction": (.94, .97), "day_of_week": (.75, .37), "interval_date": (.01, .25), "time_addition": (.91, .92), "time_duration": (.79, .69), "time_subtraction": (.81, .79)}}
rows = []
for t in TASKS:
    row = {"task": t, "sarvam105b_en": round(float(med.loc[t, "en_US"]), 1), "sarvam105b_hi": round(float(med.loc[t, "hi_IN"]), 1)}
    for m, d in T6.items():
        row[f"{m}_en"], row[f"{m}_hi"] = round(100 * d[t][0], 1), round(100 * d[t][1], 1)
    rows.append(row)
pd.DataFrame(rows).to_csv(FIG / "trd_comparison_medium_direct.csv", index=False)
out["trd_comparison"] = rows
dq = F[(F.cond == "direct") & (F.insertion == "no_insertion")].groupby(["level", "lang", "task"]).strict.mean().unstack() * 100
REASON = ["date_addition", "date_subtraction", "date_duration", "date_recurrence", "time_addition", "time_subtraction", "time_duration"]
MEM = ["day_of_week", "interval_date"]
out["trd_group_medium_direct"] = {l: {"reasoning": round(float(med.loc[REASON, l].mean()), 1), "memorization": round(float(med.loc[MEM, l].mean()), 1)} for l in LANGS}
lv = []
for lvl in LEVELS:
    for l in LANGS:
        v = dq.loc[(lvl, l)]
        lv.append({"level": lvl, "lang": l, "reasoning": round(float(v[REASON].mean()), 1), "memorization": round(float(v[MEM].mean()), 1)})
pd.DataFrame(lv).to_csv(FIG / "trd_reasoning_memorization_by_level.csv", index=False)
out["trd_group_by_level"] = lv
ins = F[(F.cond == "direct")].groupby(["lang", "insertion", "task"]).strict.mean().unstack(0) * 100
out["direct_drop_by_task"] = {f"{l}/{t}": {i: round(float(ins.loc[("no_insertion", t), l] - ins.loc[(i, t), l]), 1) for i in INS[1:]} for l in LANGS for t in TASKS}
yr = F[(F.task == "day_of_week") & (F.cond == "direct") & (F.insertion == "no_insertion")].merge(Q[Q.lang == "en_US"][["level", "task", "qnum", "params"]], on=["level", "task", "qnum"])
yr["year"] = yr.params.map(lambda s: int(json.loads(s)["d"][:4]))
out["dow_direct_by_year"] = {f"{l}/{y}": round(100 * float(g.strict.mean()), 1) for (l, y), g in yr.groupby(["lang", "year"])}
yc = F[(F.task == "day_of_week") & (F.cond == "cot") & (F.insertion == "no_insertion")].merge(Q[Q.lang == "en_US"][["level", "task", "qnum", "params"]], on=["level", "task", "qnum"])
yc["year"] = yc.params.map(lambda s: int(json.loads(s)["d"][:4]))
out["dow_cot_by_year"] = {f"{l}/{y}": round(100 * float(g.strict.mean()), 1) for (l, y), g in yc.groupby(["lang", "year"])}
rows = []
for name, s in (("direct", yr), ("cot", yc)):
    for (l, y), g in s.groupby(["lang", "year"]):
        rows.append({"cond": name, "lang": l, "year": y, "acc_strict": round(100 * float(g.strict.mean()), 1), "n": len(g)})
pd.DataFrame(rows).to_csv(FIG / "dow_accuracy_by_year.csv", index=False)
leap = F[F.qid.isin(Q[Q.qtext.str.contains("-02-29") | Q.gold.str.contains("-02-29")].apply(lambda r: f"{r.level}/{r.task}/{r.qnum}", axis=1))]
out["feb29"] = {"questions": int(leap.qid.nunique()), "ids": sorted(leap.qid.unique().tolist()), "acc_by_cell": {f"{l}/{c}": round(100 * float(g.strict.mean()), 1) for (l, c), g in leap.groupby(["lang", "cond"])}}
t = pd.to_datetime(F.time)
strad = []
cf = F.assign(day=t.dt.date.astype(str))
for (lv_, tk), g in cf.groupby(["level", "task"]):
    per_q = g.groupby("qid").day.min()
    if per_q.nunique() > 1:
        for (l, c, d), h_ in g.assign(first=g.qid.map(per_q)).groupby(["lang", "cond", "first"]):
            strad.append({"level": lv_, "task": tk, "lang": l, "cond": c, "run_day": d, "questions": h_.qid.nunique(), "acc": round(100 * float(h_.acc.mean()), 1)})
pd.DataFrame(strad).to_csv(FIG / "run_date_drift_check.csv", index=False)
d = pd.DataFrame(strad)
dr = []
for (lv_, tk, l, c), g in d.groupby(["level", "task", "lang", "cond"]):
    if len(g) >= 2 and g.questions.min() >= 20:
        g = g.sort_values("run_day")
        dr.append({"cell": f"{lv_}/{tk}/{l}/{c}", "early": g.acc.iloc[0], "late": g.acc.iloc[-1], "diff": round(g.acc.iloc[-1] - g.acc.iloc[0], 1), "n_early": int(g.questions.iloc[0]), "n_late": int(g.questions.iloc[-1])})
out["run_date_cells_ge20"] = dr
out["run_date_mean_abs_diff"] = round(float(np.mean([abs(x["diff"]) for x in dr])), 2) if dr else None
out["run_date_mean_diff"] = round(float(np.mean([x["diff"] for x in dr])), 2) if dr else None
dump(out, "results_dataset.json")
print(json.dumps({k: out[k] for k in out if k not in ("trd_comparison", "direct_drop_by_task", "dow_direct_by_year", "dow_cot_by_year", "run_date_cells_ge20")}, indent=0, ensure_ascii=False)[:3000])
print(pd.DataFrame(out["trd_comparison"]).to_string())
print(out["dow_direct_by_year"])
print(out["dow_cot_by_year"])
print(dr[:30])
