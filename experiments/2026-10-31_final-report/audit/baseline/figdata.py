from common import *

D = pd.read_csv(FIG / "rq1_cot_delta_by_scope_split.csv")
D[D.scope.isin(LEVELS)][["scoring", "split", "lang", "scope", "direct", "cot", "v", "lo", "hi"]].rename(columns={"scope": "level", "v": "delta"}).to_csv(FIG / "fig_difficulty.csv", index=False)
D[D.scope.isin(TASKS)][["scoring", "split", "lang", "scope", "direct", "cot", "v", "lo", "hi", "mcnemar_holm", "q_t_holm"]].rename(columns={"scope": "task", "v": "delta"}).to_csv(FIG / "fig_cot_delta_task_split.csv", index=False)
G = pd.read_csv(FIG / "rq1_cot_delta_task_level.csv")
G[(G.scoring == "answered")][["split", "lang", "task", "level", "direct", "cot", "v", "lo", "hi"]].rename(columns={"v": "delta"}).to_csv(FIG / "fig_cot_delta_heatmap.csv", index=False)
P = pd.read_csv(FIG / "rq2_penalty_by_scope.csv")
for c in ("drop_direct", "drop_cot"):
    P[c] = P[c].map(lambda x: eval(x)["v"] if isinstance(x, str) else x)
P = P[["scoring", "ins", "scope", "lang", "drop_direct", "drop_cot", "v", "lo", "hi", "q_t_p", "q_t_holm", "n_q"]].rename(columns={"v": "penalty"})
P.to_csv(FIG / "fig_penalty_forest.csv", index=False)
P[P.scope.isin(LEVELS)].rename(columns={"scope": "level"}).to_csv(FIG / "fig_penalty_by_difficulty.csv", index=False)
L = pd.read_csv(FIG / "rq2_loso.csv")
L.sort_values(["scoring", "ins", "lang", "sent_penalty"]).to_csv(FIG / "fig_sentence_penalty.csv", index=False)
R = json.load(open(HERE / "results_secondary.json", encoding="utf-8"))
rows = []
for k, v in R["dow_offsets"].items():
    l, c = k.split("/")
    rows += [{"lang": l, "cond": c, "offset": int(o), "share_pct": s} for o, s in v.items()]
pd.DataFrame(rows).to_csv(FIG / "fig_dow_offsets.csv", index=False)
pd.DataFrame([{"lang": k.split("/")[0], "task": k.split("/")[1], **v} for k, v in R["errors_cot_task"].items()]).to_csv(FIG / "fig_error_off_by_one.csv", index=False)
O = json.load(open(HERE / "results_ron.json", encoding="utf-8"))
rows = []
for k, v in O["on_vs_off"].items():
    l, c = k.split("/")
    for s in ("answered", "strict", "cap4k_strict"):
        rows.append({"lang": l, "cond": c, "scoring": s, "off": v[s]["off"], "on": v[s]["on"], "delta": v[s]["v"], "lo": v[s]["lo"], "hi": v[s]["hi"], "n": v[s]["n"]})
pd.DataFrame(rows).to_csv(FIG / "fig_thinking_budget.csv", index=False)
M = json.load(open(HERE / "results_mentions.json", encoding="utf-8"))
rows = []
for k, v in R["mention"].items():
    l, kind = k.split("/")
    rows.append({"lang": l, "distractor": kind, "measure": "project", "rate": v["rate"], "placebo": v["placebo"], "or": v["mh"]["or"], "or_lo": v["mh_cluster_ci"][0], "or_hi": v["mh_cluster_ci"][1]})
    w = M[f"{l}/{'sim' if kind == 'similar' else 'dis'}"]
    rows.append({"lang": l, "distractor": kind, "measure": "low_placebo_words", "rate": w["rate"], "placebo": w["placebo"], "or": w["or_mention"]["or"], "or_lo": w["or_mention"]["lo"], "or_hi": w["or_mention"]["hi"]})
pd.DataFrame(rows).to_csv(FIG / "fig_mention.csv", index=False)
