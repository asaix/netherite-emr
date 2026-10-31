import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT))
import metrics as M

CACHE = HERE / "cache"
FIG = HERE / "fig_data"
DIFFS = ["short", "medium", "long", "very_long", "very_very_long"]
EXP1 = ROOT / "experiments/2026-10-27_trace-deletion-selfhost/outputs"
EXP2 = ROOT / "experiments/2026-10-29_distractor-resampling/outputs"
STOP = set(re.search(r'STOP = set\(\s*"""(.*?)"""', (ROOT / "experiments/2026-10-02_mid-report-analysis/build_responses.py").read_text(encoding="utf-8"), re.S).group(1).split())
TOKEN = re.compile(r"[^\s.,!?।'\"():;]+")
SENT = re.compile(r"[^\n]+?(?:[।!?]|\.(?=\s|$)|$)", re.M)
MONTHS = "january february march april may june july august september october november december जनवरी फरवरी मार्च अप्रैल मई जून जुलाई अगस्त सितंबर सितम्बर अक्टूबर अक्तूबर नवंबर नवम्बर दिसंबर दिसम्बर".split()
CAL = set(MONTHS) | set(M.WEEKDAYS)
BOOT, PERM, SEED = 5000, 20000, 20261031


def norm(t):
    return (t or "").translate(M.DIGITS)


def words(t):
    return {w for w in TOKEN.findall(norm(t).casefold()) if len(w) >= 3 and w not in STOP and not w.isdigit()}


def sentences(t):
    return [m.group().strip() for m in SENT.finditer(t) if m.group().strip()]


def body(c):
    return c[: list(M.ANSWER.finditer(c))[-1].start()]


def answer_pos(task, ans, sents):
    vals = ans.split(" to ") if task == "interval_date" else [ans]
    pats = [re.compile(r"(?<![\w:.-])" + re.escape(norm(v).casefold()) + r"(?![\w:-])(?!\.\d)") for v in vals]
    for i, s in enumerate(sents):
        if any(p.search(norm(s).casefold()) for p in pats):
            return i
    return len(sents) - 1


def q_text(r):
    return r["request"]["messages"][0]["content"].split("\n\n")[-1]


def correct(rec, meta):
    a = M.extract_answer(rec.get("content") or "")
    return a is not None and M.is_correct({"content": rec["content"], "meta": meta})


def loop_stats(text, tail=20000, maxp=4000):
    s = (text or "")[-tail:][::-1]
    n = len(s)
    if n < 4:
        return 0, 0, 0
    z = [0] * n
    l = r = 0
    best = (0, 0, 0)
    for i in range(1, n):
        v = min(r - i, z[i - l]) if i < r else 0
        while i + v < n and s[v] == s[i + v]:
            v += 1
        z[i] = v
        if i + v > r:
            l, r = i, i + v
    for p in range(1, min(n, maxp)):
        reps = z[p] / p + 1
        if reps >= 2 and z[p] + p > best[2]:
            best = (p, reps, z[p] + p)
    return best


def stage_api():
    df = defaultdict(Counter)
    tot = Counter()
    for d in DIFFS:
        for r in json.load(open(ROOT / f"responses/standard/{d}.json", encoding="utf-8")):
            if r["condition"] == "cot" and r["meta"]["insertion"] == "no_insertion" and r["content"]:
                lang = r["meta"]["language"]
                tot[lang] += 1
                df[lang].update(words(r["content"]))
    rows = []
    for d in DIFFS:
        recs = [r for r in json.load(open(ROOT / f"responses/standard/{d}.json", encoding="utf-8")) if r["condition"] == "cot"]
        by = {r["id"]: r for r in recs}
        for r in recs:
            m = r["meta"]
            lang = m["language"]
            c = r["content"] or ""
            a = M.extract_answer(c)
            row = {"id": r["id"], "difficulty": d, "task": m["task"], "language": lang, "qid": m["question_id"], "insertion": m["insertion"],
                   "has_answer": a is not None, "cutoff": r.get("finish_reason") == "length", "correct": correct(r, m),
                   "tokens": (r.get("usage") or {}).get("completion_tokens"), "reasoning_null": not r.get("reasoning_content"),
                   "answer": a, "gold": m["answer"], "n_messages": len(r["request"]["messages"]), "temperature": r["request"].get("temperature")}
            base = by.get(r["id"].replace(m["insertion"], "no_insertion"))
            if m["insertion"] != "no_insertion" and base is not None:
                q, bq = q_text(r), q_text(base)
                row["suffix_ok"] = q.endswith(bq)
                dis = q[: len(q) - len(bq)]
                w = words(dis) - words(bq)
                strict = w - CAL
                cal = w & CAL
                rare = {x for x in strict if df[lang][x] / tot[lang] < 0.02}
                row["distractor"] = dis.strip()
                if a is not None:
                    b = body(c)
                    ss = sentences(b)
                    cw = [words(s) for s in ss]
                    found = [i for i, x in enumerate(cw) if len(x & strict) >= 2 or x & rare]
                    loose = [i for i, x in enumerate(cw) if x & w]
                    calhit = [i for i, x in enumerate(cw) if x & cal]
                    ap = answer_pos(m["task"], a, ss) if ss else 0
                    row.update({"n_sent": len(ss), "answer_pos": ap, "any_mention": bool(found), "k": found[0] if found else -1, "loose_any": bool(loose), "cal_any": bool(calhit), "cal_first": calhit[0] if calhit else -1})
                    if found:
                        k = found[0]
                        dt = TOKEN.findall(norm(dis).casefold())
                        st = set(TOKEN.findall(norm(ss[k]).casefold()))
                        row["mention_cover"] = sum(t in st for t in dt) / max(1, len(dt))
                        row["mention_digits"] = bool(re.search(r"\d", norm(ss[k])))
                        row["cal_before_k"] = any(x & cal for x in cw[:k])
                        row["loose_before_k"] = any(x & w for x in cw[:k])
            rows.append(row)
        del recs, by
    pd.DataFrame(rows).to_csv(CACHE / "api_cot.csv.gz", index=False)


def m_words(meta):
    return set(meta["distractor_words_strict"]), set(meta["distractor_words_rare"])


def rollout_row(r, meta):
    c = r.get("content") or ""
    strict, rare = m_words(meta)
    cw = [words(s) for s in sentences(c)]
    a = M.extract_answer(c)
    cut = r.get("finish_reason") == "length"
    cor = correct(r, meta) and not cut
    whole = words(c)
    row = {"has_answer": a is not None, "cutoff": cut, "answered": a is not None and not cut, "correct": cor, "tokens": (r.get("usage") or {}).get("completion_tokens"),
           "mention": any(len(x & strict) >= 2 or x & rare for x in cw), "whole_mention": len(whole & strict) >= 2 or bool(whole & rare),
           "same_as_original": a is not None and not cut and a == meta["original_answer"], "chars": len(c)}
    if cut or a is None:
        p, reps, cov = loop_stats(c)
        row.update({"loop_period": p, "loop_reps": reps, "loop_cover": cov})
    return row


def stage_rollouts():
    rows = []
    for n in range(1, 8):
        for r in json.load(open(EXP2 / f"resample/round_{n:02d}/results.json", encoding="utf-8")):
            m = r["meta"]
            rows.append({"round": n, "source_id": m["source_id"], "arm": m["arm"], "language": m["language"], "task": m["task"], "difficulty": m["difficulty"], "k": m["first_mention"],
                         "opening": m["opening_mention"], "in_del": m["in_trace_deletion"], "empty_prefix": m["empty_prefix"], "seed": r["decoding"]["seed"], "time": r["time"], "prefix_chars": m["prefix_chars"], **rollout_row(r, m)})
    pd.DataFrame(rows).to_csv(CACHE / "rollouts.csv.gz", index=False)


def stage_exp1():
    rows = []
    for run in "GS":
        for kind, f in [("main", "results.json"), ("repeat", "results_repeat.json")]:
            for r in json.load(open(EXP1 / f"selfhost_{run}/{f}", encoding="utf-8")):
                m = r["meta"]
                rows.append({"run": run, "kind": kind, "source_id": m["source_id"], "version": m["version"], "language": m["language"], "task": m["task"], "difficulty": m["difficulty"], "k": m["first_mention"],
                             "window_end": m["window_end"], "answer_sentence": m["answer_sentence"], "n_del": len(m["deleted_b"]), "mention_has_digits": m["mention_has_digits"], "answer": M.extract_answer(r.get("content") or ""), "time": r["time"], **rollout_row(r, m)})
    pd.DataFrame(rows).to_csv(CACHE / "exp1.csv.gz", index=False)


def stage_prefix():
    e1 = {r["id"]: r for r in json.load(open(EXP1 / "requests_cap1000.json", encoding="utf-8"))}
    e2 = {r["id"]: r for r in json.load(open(EXP2 / "requests_resample.json", encoding="utf-8"))}
    rows = []
    for sid in sorted({r["meta"]["source_id"] for r in e1.values()}):
        g = lambda d, a: d[f"{sid}/{a}"]["messages"][-1]["content"].strip()
        rows.append({"source_id": sid, "language": e1[f"{sid}/A"]["meta"]["language"], "A_eq_M": g(e1, "A") == g(e2, "M"), "B_eq_P": g(e1, "B") == g(e2, "P"),
                     "k": e1[f"{sid}/A"]["meta"]["first_mention"], "window_end": e1[f"{sid}/A"]["meta"]["window_end"], "answer_sentence": e1[f"{sid}/A"]["meta"]["answer_sentence"],
                     "n_del": len(e1[f"{sid}/A"]["meta"]["deleted_b"]), "C_keeps_mention": True})
    pd.DataFrame(rows).to_csv(CACHE / "exp1_prefix_map.csv", index=False)
    req = [{"source_id": r["meta"]["source_id"], "arm": r["meta"]["arm"], "prefix_chars": r["meta"]["prefix_chars"], "empty": r["meta"]["empty_prefix"], "mention_digits": bool(re.search(r"\d", norm(r["meta"]["mention_text"]))),
            "mention_chars": len(r["meta"]["mention_text"])} for r in e2.values() if r["meta"]["arm"] == "P"]
    pd.DataFrame(req).to_csv(CACHE / "exp2_trace_meta.csv", index=False)
    ids = sorted({r["meta"]["source_id"] for r in e2.values()})
    (CACHE / "exp2_source_ids.json").write_text(json.dumps(ids, indent=2, ensure_ascii=False), encoding="utf-8")


def stage_calibration():
    rows = []
    for tag in "GS":
        d = json.load(open(EXP1 / f"selfhost/calibration_redhat_v031_triton_mla_{tag}.json", encoding="utf-8"))
        for r in d["rows"]:
            rows.append({"run": tag, "id": r["id"], "language": r["language"], "task": r["task"], "difficulty": r["difficulty"], "self": r["correct"], "api": r["api_correct"], "finished": r["finished"], "tokens": r["tokens"]})
    pd.DataFrame(rows).to_csv(CACHE / "calibration.csv", index=False)


def trace_means(ro):
    return ro.pivot_table(index=["source_id", "language", "opening", "in_del", "task", "difficulty", "k"], columns="arm", values="correct", aggfunc="mean").reset_index()


def boot_ci(v, rng, b=BOOT):
    v = np.asarray(v, float)
    v = v[~np.isnan(v)]
    idx = rng.integers(0, len(v), size=(b, len(v)))
    return [float(x) for x in np.quantile(v[idx].mean(axis=1), [0.025, 0.975])]


def perm_p(v, rng, n=PERM):
    v = np.asarray(v, float)
    v = v[~np.isnan(v)]
    flips = (v * rng.choice([-1.0, 1.0], size=(n, len(v)))).mean(axis=1)
    return float(((np.abs(flips) >= abs(v.mean()) - 1e-12).sum() + 1) / (n + 1))


def test(v, rng):
    v = np.asarray(v, float)
    v = v[~np.isnan(v)]
    return {"n": int(len(v)), "mean": 100 * float(v.mean()), "ci": [100 * x for x in boot_ci(v, rng)], "p": perm_p(v, rng)}


def mcnemar_exact(b, c):
    from math import comb
    n = b + c
    return 1.0 if n == 0 else min(1.0, 2 * sum(comb(n, i) for i in range(min(b, c) + 1)) / 2 ** n)


def contrasts(t, rng):
    out = {"n": len(t), "acc": {a: 100 * float(t[a].mean()) for a in ["Q", "P", "M", "P1"] if t[a].notna().any()}}
    out["Q-P"] = test(t.Q - t.P, rng)
    out["M-P"] = test(t.M - t.P, rng)
    s = t[t.P1.notna()]
    if len(s) > 1:
        out["P-P1"] = test(s.P - s.P1, rng)
        out["DiD"] = test((s.M - s.P) - (s.P - s.P1), rng)
    return out


def groups(t):
    return {"Hindi, all": t[t.language == "hi_IN"], "Hindi, opening": t[(t.language == "hi_IN") & t.opening], "Hindi, later": t[(t.language == "hi_IN") & ~t.opening],
            "English, all": t[t.language == "en_US"], "English, opening": t[(t.language == "en_US") & t.opening], "English, later": t[(t.language == "en_US") & ~t.opening],
            "Hindi, trace-deletion 222": t[(t.language == "hi_IN") & t.in_del], "Hindi, not in deletion 304": t[(t.language == "hi_IN") & ~t.in_del]}


def analyse():
    rng = np.random.default_rng(SEED)
    res = {}
    api = pd.read_csv(CACHE / "api_cot.csv.gz", low_memory=False)
    ro = pd.read_csv(CACHE / "rollouts.csv.gz")
    e1 = pd.read_csv(CACHE / "exp1.csv.gz")
    cal = pd.read_csv(CACHE / "calibration.csv")
    pm = pd.read_csv(CACHE / "exp1_prefix_map.csv")
    tm = pd.read_csv(CACHE / "exp2_trace_meta.csv")
    ids = set(json.load(open(CACHE / "exp2_source_ids.json", encoding="utf-8")))

    api["answered"] = api.has_answer & ~api.cutoff
    pop = {}
    for (lang, ins), g in api.groupby(["language", "insertion"]):
        pop[f"{lang}|{ins}"] = {"responses": len(g), "cutoff": int(g.cutoff.sum()), "no_answer": int((~g.has_answer).sum()), "answered": int(g.answered.sum()), "right": int((g.answered & g.correct).sum()), "wrong": int((g.answered & ~g.correct).sum()),
                                "acc_answered_pct": 100 * float((g.answered & g.correct).sum() / g.answered.sum()), "acc_strict_pct": 100 * float((g.answered & g.correct).sum() / len(g)), "unanswered_pct": 100 * float((~g.answered).mean())}
    res["api_population"] = pop
    res["api_checks"] = {"temperatures": {str(k): int(v) for k, v in api.temperature.value_counts().items()}, "n_messages": {str(k): int(v) for k, v in api.n_messages.value_counts().items()}, "reasoning_null_share": float(api.reasoning_null.mean()), "suffix_ok": float(api.suffix_ok.dropna().astype(bool).mean())}

    sim = api[api.insertion != "no_insertion"].copy()
    for c in ["any_mention", "cal_any", "loose_any", "cal_before_k", "loose_before_k", "mention_digits"]:
        sim[c] = sim[c].map({True: True, False: False, "True": True, "False": False}).astype("boolean")
    sim["pre_mention"] = sim.any_mention.fillna(False).astype(bool) & (sim.k >= 0) & (sim.k < sim.answer_pos) & sim.answered
    fun = {}
    for (lang, ins), g in sim.groupby(["language", "insertion"]):
        wrong = g[g.answered & ~g.correct]
        right = g[g.answered & g.correct]
        fun[f"{lang}|{ins}"] = {"responses": len(g), "unscored_or_cut": int((~g.answered).sum()), "right": len(right), "wrong": len(wrong), "wrong_mention_any": int(wrong.any_mention.fillna(False).sum()), "wrong_pre_answer": int(wrong.pre_mention.sum()),
                                "wrong_opening": int((wrong.pre_mention & (wrong.k == 0)).sum()), "wrong_later": int((wrong.pre_mention & (wrong.k > 0)).sum()), "eligible_share_of_wrong_pct": 100 * float(wrong.pre_mention.mean()),
                                "right_pre_answer": int(right.pre_mention.sum()), "right_pre_answer_pct": 100 * float(right.pre_mention.mean()), "wrong_loose_any": int(wrong.loose_any.fillna(False).sum()), "wrong_calendar_only": int((wrong.cal_any.fillna(False) & ~wrong.any_mention.fillna(False)).sum()),
                                "wrong_no_mention_any_rule": int((~wrong.any_mention.fillna(False) & ~wrong.loose_any.fillna(False) & ~wrong.cal_any.fillna(False)).sum())}
    res["funnel"] = fun
    mine = set(sim[(sim.insertion == "similar_insertion") & sim.answered & ~sim.correct & sim.pre_mention].id)
    res["funnel_set_check"] = {"mine": len(mine), "resample_ids": len(ids), "only_mine": len(mine - ids), "only_resample": len(ids - mine), "examples": sorted(mine ^ ids)[:6]}

    q = {}
    for lang in ["hi_IN", "en_US"]:
        s = sim[(sim.language == lang) & (sim.insertion == "similar_insertion") & sim.pre_mention]
        for name, g in [("right", s[s.correct]), ("wrong", s[~s.correct]), ("wrong_opening", s[(~s.correct) & (s.k == 0)]), ("wrong_later", s[(~s.correct) & (s.k > 0)]), ("right_opening", s[s.correct & (s.k == 0)]), ("right_later", s[s.correct & (s.k > 0)])]:
            q[f"{lang}|{name}"] = {"n": len(g), "mention_has_digits_pct": 100 * float(g.mention_digits.fillna(False).astype(bool).mean()) if len(g) else None, "restates_distractor_80pct": 100 * float((g.mention_cover >= 0.8).mean()) if len(g) else None, "cal_before_k_pct": 100 * float(g.cal_before_k.fillna(False).astype(bool).mean()) if len(g) else None, "loose_before_k_pct": 100 * float(g.loose_before_k.fillna(False).astype(bool).mean()) if len(g) else None}
    res["mention_quality"] = q

    wide = []
    for (lang, task, d, qid), g in api.groupby(["language", "task", "difficulty", "qid"]):
        x = {r.insertion: r for r in g.itertuples()}
        if {"no_insertion", "similar_insertion", "dissimilar_insertion"} <= set(x):
            wide.append({"language": lang, "task": task, "difficulty": d, "qid": qid, **{f"{i[:3]}_ok": bool(x[i].answered and x[i].correct) for i in x}, **{f"{i[:3]}_ans": bool(x[i].answered) for i in x}, "sim_id": x["similar_insertion"].id})
    wide = pd.DataFrame(wide)
    pen = {}
    for lang in ["hi_IN", "en_US"]:
        w = wide[wide.language == lang]
        for tag in ["sim", "dis"]:
            v = (w.no__ok.astype(float) - w[f"{tag}_ok"].astype(float)).values
            b, c = int((w.no__ok & ~w[f"{tag}_ok"]).sum()), int((~w.no__ok & w[f"{tag}_ok"]).sum())
            acc = float(w[f"{tag}_ok"].mean())
            pen[f"{lang}|{tag}"] = {"n": len(w), "strict_none": 100 * float(w.no__ok.mean()), "strict_cond": 100 * acc, "penalty_strict": 100 * float(v.mean()), "ci": [100 * x for x in boot_ci(v, rng, 2000)], "mcnemar_p": mcnemar_exact(b, c), "excess_fraction_of_errors_pct": 100 * float(v.mean()) / (100 * (1 - acc)) * 100,
                                    "unanswered_none_pct": 100 * float((~w.no__ans).mean()), "unanswered_cond_pct": 100 * float((~w[f"{tag}_ans"]).mean())}
    res["api_penalty_strict"] = pen

    sel = wide[wide.sim_id.isin(ids)]
    t = trace_means(ro).merge(sel[["sim_id", "no__ok", "no__ans"]], left_on="source_id", right_on="sim_id", how="left")
    res["table_b3_b4"] = {g: contrasts(x, rng) for g, x in groups(t).items()}
    res["trace_counts"] = {"traces": int(t.source_id.nunique()), "hi": int((t.language == "hi_IN").sum()), "en": int((t.language == "en_US").sum()), "opening_hi": int(((t.language == "hi_IN") & t.opening).sum()), "opening_en": int(((t.language == "en_US") & t.opening).sum()), "rollouts": len(ro),
                           "per_round": {int(k): int(v) for k, v in ro.groupby("round").size().items()}, "seeds_equal_round": bool((ro["round"] == ro.seed).all()), "time_min": ro.time.min(), "time_max": ro.time.max(), "unique_ids_per_round": bool(ro.groupby("round").apply(lambda g: g.duplicated(["source_id", "arm"]).sum() == 0, include_groups=False).all())}

    ef = {}
    for g, x in groups(t).items():
        v = np.c_[x.P.values, x.Q.values]
        idx = rng.integers(0, len(v), size=(BOOT, len(v)))
        bs = (v[idx, 1].mean(1) - v[idx, 0].mean(1)) / (1 - v[idx, 0].mean(1))
        ef[g] = {"wrong_P": 100 * float(1 - x.P.mean()), "wrong_Q": 100 * float(1 - x.Q.mean()), "excess_fraction_pct": 100 * float((x.Q.mean() - x.P.mean()) / (1 - x.P.mean())), "ci": [100 * float(a) for a in np.quantile(bs, [0.025, 0.975])], "one_in": float((1 - x.P.mean()) / (x.Q.mean() - x.P.mean()))}
    res["excess_fraction"] = ef

    dec = {}
    for g, x in groups(t).items():
        r = ro[ro.source_id.isin(x.source_id)]
        a = {arm: r[r.arm == arm] for arm in ["Q", "P", "M"]}
        Uq, Up, Um = [float((~a[k].answered).mean()) for k in "QPM"]
        Aq, Ap, Am = [float(a[k][a[k].answered].correct.mean()) for k in "QPM"]
        dec[g] = {"unanswered_Q": 100 * Uq, "unanswered_P": 100 * Up, "unanswered_M": 100 * Um, "acc_answered_Q": 100 * Aq, "acc_answered_P": 100 * Ap, "acc_answered_M": 100 * Am, "completion_part_midpoint": 100 * (Up - Uq) * (Aq + Ap) / 2, "quality_part_midpoint": 100 * (Aq - Ap) * ((1 - Uq) + (1 - Up)) / 2, "total_Q_P": 100 * ((1 - Uq) * Aq - (1 - Up) * Ap)}
        dec[g]["completion_share_pct"] = 100 * dec[g]["completion_part_midpoint"] / dec[g]["total_Q_P"]
    res["decomposition"] = dec

    ans = ro[ro.answered].groupby(["source_id", "arm"]).correct.mean().unstack()
    tt = t.set_index("source_id")
    uq = ro.assign(un=~ro.answered).groupby(["source_id", "arm"]).un.mean().unstack()
    sens = {}
    for g, x in groups(t).items():
        i = x.source_id
        z = ans.loc[i]
        sens[g] = {"answered_only_Q-P": test((z.Q - z.P).values, rng), "answered_only_M-P": test((z.M - z.P).values, rng), "unanswered_P-Q": test((uq.loc[i].P - uq.loc[i].Q).values, rng), "unanswered_M-P": test((uq.loc[i].M - uq.loc[i].P).values, rng)}
    res["sensitivity"] = sens
    res["unanswered_by_group_pct"] = {g: {a: 100 * float((~ro[ro.source_id.isin(x.source_id) & (ro.arm == a)].answered).mean()) for a in ["Q", "P", "M", "P1"] if len(ro[ro.source_id.isin(x.source_id) & (ro.arm == a)])} for g, x in groups(t).items()}

    cut = ro.groupby("round").cutoff.mean() * 100
    res["cutoff"] = {"per_round_pct": {int(k): float(v) for k, v in cut.items()}, "min": float(cut.min()), "max": float(cut.max()), "hi": int((ro.cutoff & (ro.language == "hi_IN")).sum()), "en": int((ro.cutoff & (ro.language == "en_US")).sum()), "no_answer_line_per_round": {int(k): int(v) for k, v in ro[ro.cutoff & ~ro.has_answer].groupby("round").size().items()},
                     "stop_no_answer": int((~ro.has_answer & ~ro.cutoff).sum()), "cut_with_answer": int((ro.has_answer & ro.cutoff).sum())}
    grid = {}
    for mr in [2, 3, 5, 10, 20]:
        for mc in [0, 100, 200, 500, 1000]:
            c = ro[ro.cutoff]
            l = (c.loop_reps >= mr) & (c.loop_cover >= mc)
            grid[f"reps>={mr},cover>={mc}"] = {"hi": int((l & (c.language == "hi_IN")).sum()), "en": int((l & (c.language == "en_US")).sum())}
    res["loop_grid_exp2"] = grid
    a_tok = ro[ro.answered].tokens
    res["answered_tokens"] = {"p99": float(np.percentile(a_tok, 99)), "gt3500_pct": 100 * float((a_tok > 3500).mean()), "max": int(a_tok.max()), "n": int(len(a_tok))}
    res["all_tokens"] = {"p50": float(a_tok.median()), "cutoff_tokens_min": int(ro[ro.cutoff].tokens.min()), "cutoff_tokens_max": int(ro[ro.cutoff].tokens.max())}
    res["noise_P"] = {}
    for lang in ["hi_IN", "en_US"]:
        p = t[t.language == lang].P
        res["noise_P"][lang] = {"mixed": int(((p > 0) & (p < 1)).sum()), "all_right": int((p == 1).sum()), "all_wrong": int((p == 0).sum()), "n": int(len(p))}
    res["mention_rate"] = {}
    for g, x in groups(t).items():
        r = ro[ro.source_id.isin(x.source_id)]
        res["mention_rate"][g] = {a: 100 * float(r[r.arm == a].mention.mean()) for a in ["Q", "P", "M", "P1"] if (r.arm == a).any()}

    within = {}
    for g in ["Hindi, all", "Hindi, opening", "Hindi, later", "English, all"]:
        x = groups(t)[g]
        r = ro[ro.source_id.isin(x.source_id)]
        pp = r[(r.arm == "P") & r.answered]
        d = pp.groupby(["source_id", "mention"]).correct.mean().unstack().dropna()
        pall = r[r.arm == "P"]
        ds = pall.groupby(["source_id", "mention"]).correct.mean().unstack().dropna()
        qm = r[r.arm == "Q"].groupby("source_id").correct.mean()
        ann = pp.groupby("mention").correct.mean()
        cnt = pall.groupby("mention").agg(n=("correct", "size"), acc=("correct", "mean"), un=("answered", lambda s: 1 - s.mean()))
        within[g] = {"answered_acc_mention": 100 * float(ann.get(True, np.nan)), "answered_acc_no_mention": 100 * float(ann.get(False, np.nan)), "within_answered_mention_minus_not": test((d[True] - d[False]).values, rng) if len(d) > 1 else None,
                     "within_strict_mention_minus_not": test((ds[True] - ds[False]).values, rng) if len(ds) > 1 else None, "strict_acc_mention": 100 * float(cnt.acc.get(True, np.nan)), "strict_acc_no_mention": 100 * float(cnt.acc.get(False, np.nan)), "unanswered_mention_pct": 100 * float(cnt.un.get(True, np.nan)), "unanswered_no_mention_pct": 100 * float(cnt.un.get(False, np.nan)), "rollouts_mention": int(cnt.n.get(True, 0)), "rollouts_no_mention": int(cnt.n.get(False, 0))}
        nm = ds[False].index
        within[g]["Q_minus_P_no_mention_rollouts"] = test((qm.loc[nm] - ds[False]).values, rng)
        within[g]["Q_minus_P_mention_rollouts"] = test((qm.loc[nm] - ds[True]).values, rng)
    res["P_mention_within"] = within

    same = {}
    for g, x in groups(t).items():
        r = ro[ro.source_id.isin(x.source_id)]
        same[g] = {a: 100 * float(r[r.arm == a].same_as_original.mean()) for a in ["Q", "P", "M", "P1"] if (r.arm == a).any()}
    res["repeat_original_wrong_answer_pct"] = same

    meta = t.merge(tm[["source_id", "mention_digits"]], on="source_id")
    apix = api[api.id.isin(ids)][["id", "mention_cover", "cal_before_k", "loose_before_k"]].rename(columns={"id": "source_id"})
    meta = meta.merge(apix, on="source_id")
    meta["cal_before_k"] = meta.cal_before_k.map({True: True, False: False, "True": True, "False": False}).fillna(False).astype(bool)
    meta["loose_before_k"] = meta.loose_before_k.map({True: True, False: False, "True": True, "False": False}).fillna(False).astype(bool)
    sub = {}
    hi = meta[meta.language == "hi_IN"]
    for name, x in [("later,mention has digits", hi[~hi.opening & hi.mention_digits]), ("later,mention no digits", hi[~hi.opening & ~hi.mention_digits]), ("opening,mention has digits", hi[hi.opening & hi.mention_digits]), ("opening,mention no digits", hi[hi.opening & ~hi.mention_digits]),
                    ("later,calendar word already in prefix", hi[~hi.opening & hi.cal_before_k]), ("later,no calendar word in prefix", hi[~hi.opening & ~hi.cal_before_k]), ("later,any distractor word in prefix", hi[~hi.opening & (hi.cal_before_k | hi.loose_before_k)]), ("later,clean prefix", hi[~hi.opening & ~(hi.cal_before_k | hi.loose_before_k)]),
                    ("opening,restates distractor (>=80% tokens)", hi[hi.opening & (hi.mention_cover >= 0.8)]), ("opening,other", hi[hi.opening & (hi.mention_cover < 0.8)]), ("later,restates distractor", hi[~hi.opening & (hi.mention_cover >= 0.8)]), ("later,other", hi[~hi.opening & (hi.mention_cover < 0.8)])]:
        sub[name] = {"n": len(x), "Q-P": test(x.Q - x.P, rng), "M-P": test(x.M - x.P, rng), "acc": {a: 100 * float(x[a].mean()) for a in "QPM"}}
    res["subgroups_exploratory"] = sub
    tasks = {}
    for lang in ["hi_IN", "en_US"]:
        for task, x in t[t.language == lang].groupby("task"):
            tasks[f"{lang}|{task}"] = {"n": len(x), "Q-P": 100 * float((x.Q - x.P).mean()), "M-P": 100 * float((x.M - x.P).mean())}
    res["by_task"] = tasks

    h, e = t[t.language == "hi_IN"], t[t.language == "en_US"]
    gap = {}
    for name, f in [("Q-P", lambda x: x.Q - x.P), ("M-P", lambda x: x.M - x.P)]:
        vh, ve = f(h).values, f(e).values
        bs = vh[rng.integers(0, len(vh), (BOOT, len(vh)))].mean(1) - ve[rng.integers(0, len(ve), (BOOT, len(ve)))].mean(1)
        gap[name] = {"hi_minus_en": 100 * float(vh.mean() - ve.mean()), "ci": [100 * float(a) for a in np.quantile(bs, [0.025, 0.975])]}
        wt = e.task.value_counts(normalize=True)
        hs = {k: f(h[h.task == k]).mean() for k in wt.index if (h.task == k).any()}
        gap[name]["hi_standardised_to_en_task_mix"] = 100 * float(sum(wt[k] * hs[k] for k in hs) / sum(wt[k] for k in hs))
        wo = e.opening.value_counts(normalize=True)
        gap[name]["en_opening_only_hi_opening_only"] = [100 * float(f(e[e.opening]).mean()), 100 * float(f(h[h.opening]).mean())]
    res["hindi_english_gap"] = gap
    res["english_task_mix"] = {k: int(v) for k, v in e.task.value_counts().items()}
    res["leave_one_task_out_en_QP"] = {k: 100 * float((e[e.task != k].Q - e[e.task != k].P).mean()) for k in e.task.unique()}

    op = t[t.opening]
    fp8 = {}
    for lang in ["hi_IN", "en_US"]:
        x = op[op.language == lang].dropna(subset=["no__ok"])
        d = x.Q - x.no__ok.astype(float)
        fp8[lang] = {"n": len(x), "api_no_insertion_strict": 100 * float(x.no__ok.astype(float).mean()), "fp8_Q_strict": 100 * float(x.Q.mean()), "fp8_minus_api": test(d.values, rng)}
        y = op[(op.language == lang)]
        r = ro[ro.source_id.isin(y.source_id) & (ro.arm == "Q")]
        fp8[lang]["fp8_Q_unanswered_pct"] = 100 * float((~r.answered).mean())
        fp8[lang]["api_no_ins_unanswered_pct"] = 100 * float((~x.no__ans).mean())
    res["calibration_large_opening_traces"] = fp8
    lat = t[~t.opening]
    res["api_no_insertion_on_selected"] = {g: {"n": int(x.no__ok.notna().sum()), "api_no_insertion_right_pct": 100 * float(x.no__ok.astype(float).mean())} for g, x in groups(t).items()}

    cals = {}
    for run, g in cal.groupby("run"):
        for lang, x in list(g.groupby("language")) + [("all", g)]:
            d = x["self"].astype(float).values - x["api"].astype(float).values
            b, c = int((x["self"] & ~x["api"]).sum()), int((~x["self"] & x["api"]).sum())
            n = len(x)
            se = float(np.std(d, ddof=1) / np.sqrt(n))
            cals[f"{run}|{lang}"] = {"n": n, "self": 100 * float(x["self"].mean()), "api": 100 * float(x["api"].mean()), "finished": int(x.finished.sum()), "only_self": b, "only_api": c, "diff": 100 * float(d.mean()), "wald_ci": [100 * float(d.mean() - 1.96 * se), 100 * float(d.mean() + 1.96 * se)], "boot_ci": [100 * a for a in boot_ci(d, rng)], "mcnemar_p": mcnemar_exact(b, c), "tost_margin_needed_pts": 100 * float(abs(d.mean()) + 1.645 * se), "max_tokens_seen": int(x.tokens.max())}
    res["calibration_90"] = cals

    m = e1[e1.kind == "main"]
    w = m.pivot_table(index=["run", "source_id", "language"], columns="version", values="correct", aggfunc="first").reset_index()
    t1 = {}
    for (run, lang), g in w.groupby(["run", "language"]):
        b, c = int((g.B & ~g.C).sum()), int((~g.B & g.C).sum())
        d = (g.B.astype(float) - g.C.astype(float)).values
        t1[f"{run}|{lang}"] = {"n": len(g), "A": 100 * float(g.A.mean()), "B": 100 * float(g.B.mean()), "C": 100 * float(g.C.mean()), "B-C": 100 * float(d.mean()), "ci": [100 * a for a in boot_ci(d, rng)], "only_B": b, "only_C": c, "p": mcnemar_exact(b, c)}
    res["table_b1"] = t1

    rem = {}
    for (run, lang, v), g in m.groupby(["run", "language", "version"]):
        rem[f"{run}|{lang}|{v}"] = {"whole_text_rule_pct": 100 * float(g.whole_mention.mean()), "sentence_rule_pct": 100 * float(g.mention.mean()), "unanswered": int((~g.answered).sum()), "cutoff": int(g.cutoff.sum()), "no_answer_line": int((~g.has_answer).sum())}
    res["exp1_remention"] = rem
    rep = {}
    for run in "GS":
        a = m[(m.run == run) & (m.version == "A")].set_index("source_id")
        r = e1[(e1.run == run) & (e1.kind == "repeat")].set_index("source_id")
        for lang in ["hi_IN", "en_US", "all"]:
            idx = a.index if lang == "all" else a[a.language == lang].index
            rep[f"{run}|{lang}"] = {"n": len(idx), "flip_right_wrong": int((a.loc[idx].correct.values != r.loc[idx].correct.values).sum()), "same_answer": int(sum(x == y or (pd.isna(x) and pd.isna(y)) for x, y in zip(a.loc[idx].answer, r.loc[idx].answer)))}
    res["exp1_repeat"] = rep
    ru = {}
    for run in "GS":
        g = m[m.run == run]
        cg = g[g.cutoff]
        ug = g[~g.answered]
        ru[run] = {"n": len(g), "unanswered": len(ug), "unanswered_pct": 100 * len(ug) / len(g), "cutoff": len(cg), "no_answer_line": int((~g.has_answer).sum()), "cut_without_answer": int((g.cutoff & ~g.has_answer).sum()), "cut_with_answer": int((g.cutoff & g.has_answer).sum()), "stop_no_answer": int((~g.cutoff & ~g.has_answer).sum())}
        ru[run]["loops"] = {f"reps>={r},cover>={c}": int(((cg.loop_reps >= r) & (cg.loop_cover >= c)).sum()) for r in [2, 3, 5, 10, 20] for c in [0, 100, 200, 500, 1000]}
        ru[run]["loops_on_unanswered"] = {f"reps>={r},cover>={c}": int(((ug.loop_reps >= r) & (ug.loop_cover >= c)).sum()) for r in [2, 3, 5, 10, 20] for c in [0, 100, 200, 500, 1000]}
    res["exp1_runaways"] = ru
    s = m[m.run == "S"]
    res["exp1_tokens_S"] = {"answered_over_4096": int((s.answered & (s.tokens > 4096)).sum()), "answered_over_4096_correct": int((s.correct & (s.tokens > 4096)).sum()), "n": len(s), "cut_at_12288": int(s.cutoff.sum()), "exceed_4096_any": int((s.tokens > 4096).sum())}

    hw = w[w.language == "hi_IN"]
    pow1 = {}
    for run, g in hw.groupby("run"):
        d = (g.B.astype(float) - g.C.astype(float)).values
        n = len(d)
        disc = (d != 0).mean()
        se = float(np.std(d, ddof=1) / np.sqrt(n))
        sim_rng = np.random.default_rng(SEED)
        pw = {}
        for eff in [0.02, 0.033, 0.05, 0.075, 0.10, 0.15]:
            pb = (disc + eff) / 2
            pc = (disc - eff) / 2
            draws = sim_rng.multinomial(n, [pb, pc, 1 - pb - pc], size=4000)
            ps = np.array([mcnemar_exact(int(x), int(y)) for x, y in draws[:, :2]])
            pw[f"{100 * eff:.1f}"] = float((ps < 0.05).mean())
        pow1[run] = {"n": n, "discordant_share": float(disc), "se_pts": 100 * se, "mde80_pts": 100 * 2.8 * se, "mde_at_ci_halfwidth_pts": 196 * se, "power_at_effect_pts": pw}
    ps = hw.pivot_table(index="source_id", columns="run", values=["B", "C", "A"], aggfunc="first")
    dg = ps["B"]["G"].astype(float) - ps["C"]["G"].astype(float)
    ds = ps["B"]["S"].astype(float) - ps["C"]["S"].astype(float)
    res["exp1_pooled_G_S_B_C"] = test(((dg + ds) / 2).values, rng)
    pow1["pooled_se_pts"] = 100 * float(((dg + ds) / 2).std(ddof=1) / np.sqrt(len(dg)))
    res["exp1_power"] = pow1
    res["exp1_A_vs_B_hi"] = {run: test((g.A.astype(float) - g.B.astype(float)).values, rng) for run, g in hw.groupby("run")}
    res["exp1_A_vs_C_hi"] = {run: test((g.A.astype(float) - g.C.astype(float)).values, rng) for run, g in hw.groupby("run")}

    pm_h = pm[pm.language == "hi_IN"]
    res["exp1_exp2_prefix_map"] = {"traces": len(pm), "A_eq_M": int(pm.A_eq_M.sum()), "B_eq_P": int(pm.B_eq_P.sum()), "hi_A_eq_M": int(pm_h.A_eq_M.sum()), "hi_B_eq_P": int(pm_h.B_eq_P.sum()), "window_ends_at_k": int((pm.window_end == pm.k).sum()), "window_after_k": int((pm.window_end > pm.k).sum()),
                                   "sentences_cut_before_answer_median": float((pm.answer_sentence - pm.window_end).median()), "cut_immediately_before_answer": int((pm.answer_sentence - pm.window_end == 1).sum()), "hi_opening": int((pm_h.k == 0).sum()), "multi_deleted": int((pm.n_del > 1).sum())}
    tb = t[t.source_id.isin(pm_h[pm_h.window_end == pm_h.k].source_id)]
    res["exp2_on_window_at_k"] = contrasts(tb, rng)

    res["hindi_del_vs_rest"] = {}
    a, b = t[(t.language == "hi_IN") & t.in_del], t[(t.language == "hi_IN") & ~t.in_del]
    for name, f in [("Q-P", lambda x: x.Q - x.P), ("M-P", lambda x: x.M - x.P)]:
        va, vb = f(a).values, f(b).values
        bs = va[rng.integers(0, len(va), (BOOT, len(va)))].mean(1) - vb[rng.integers(0, len(vb), (BOOT, len(vb)))].mean(1)
        res["hindi_del_vs_rest"][name] = {"in_222": 100 * float(va.mean()), "other_304": 100 * float(vb.mean()), "diff": 100 * float(va.mean() - vb.mean()), "ci": [100 * float(x) for x in np.quantile(bs, [0.025, 0.975])]}
    res["composition_222"] = {"opening": int((a.opening).sum()), "later": int((~a.opening).sum()), "opening_other": int((b.opening).sum()), "later_other": int((~b.opening).sum())}
    ol = t[(t.language == "hi_IN")]
    va, vb = (ol[ol.opening].M - ol[ol.opening].P).values, (ol[~ol.opening].M - ol[~ol.opening].P).values
    bs = vb[rng.integers(0, len(vb), (BOOT, len(vb)))].mean(1) - va[rng.integers(0, len(va), (BOOT, len(va)))].mean(1)
    res["hi_MP_later_minus_opening"] = {"diff": 100 * float(vb.mean() - va.mean()), "ci": [100 * float(x) for x in np.quantile(bs, [0.025, 0.975])]}

    pv = sorted([("Hindi Q-P", res["table_b3_b4"]["Hindi, all"]["Q-P"]["p"]), ("Hindi M-P", res["table_b3_b4"]["Hindi, all"]["M-P"]["p"]), ("Hindi DiD", res["table_b3_b4"]["Hindi, all"]["DiD"]["p"]), ("English Q-P", res["table_b3_b4"]["English, all"]["Q-P"]["p"]), ("English M-P", res["table_b3_b4"]["English, all"]["M-P"]["p"]), ("English DiD", res["table_b3_b4"]["English, all"]["DiD"]["p"])], key=lambda x: x[1])
    res["multiplicity"] = {"tests": [{"name": n, "p": p, "holm_threshold": 0.05 / (6 - i), "bonferroni": 0.05 / 6} for i, (n, p) in enumerate(pv)]}

    ex = "long/date_recurrence_hi_IN/12/similar_insertion/cot"
    res["example_b2"] = {a: int(ro[(ro.source_id == ex) & (ro.arm == a)].correct.sum()) for a in ["Q", "P", "M", "P1"]}

    fig_b1 = []
    for g, x in res["table_b3_b4"].items():
        if g in ["Hindi, all", "Hindi, opening", "Hindi, later", "English, all", "English, opening", "English, later"]:
            for c, lab in [("Q-P", "a"), ("M-P", "b"), ("P-P1", "c")]:
                if c in x:
                    fig_b1.append({"panel": lab, "contrast": c, "group": g, "n": x[c]["n"], "mean_pts": x[c]["mean"], "ci_low": x[c]["ci"][0], "ci_high": x[c]["ci"][1], "p": x[c]["p"]})
    pd.DataFrame(fig_b1).to_csv(FIG / "fig_b1_contrasts.csv", index=False)
    pd.DataFrame([{"group": g, "arm": a, "accuracy_pct": v} for g, x in res["table_b3_b4"].items() for a, v in x["acc"].items()]).to_csv(FIG / "table_b3_arm_accuracy.csv", index=False)
    pd.DataFrame([{"group": g, "metric": k, "mean_pts": v["mean"], "ci_low": v["ci"][0], "ci_high": v["ci"][1], "n": v["n"], "p": v["p"]} for g, x in sens.items() for k, v in x.items()]).to_csv(FIG / "new_answered_only_and_unanswered.csv", index=False)
    pd.DataFrame([{"group": g, **{k: x[k] for k in ["unanswered_Q", "unanswered_P", "acc_answered_Q", "acc_answered_P", "completion_part_midpoint", "quality_part_midpoint", "total_Q_P", "completion_share_pct"]}} for g, x in dec.items()]).to_csv(FIG / "new_decomposition_completion_quality.csv", index=False)
    pd.DataFrame([{"effect_pts": e, "run": r, "power": p} for r in "GS" for e, p in pow1[r]["power_at_effect_pts"].items()]).to_csv(FIG / "new_exp1_power_curve.csv", index=False)
    pd.DataFrame([{"group": g, "excess_fraction_pct": x["excess_fraction_pct"], "ci_low": x["ci"][0], "ci_high": x["ci"][1], "wrong_P": x["wrong_P"], "wrong_Q": x["wrong_Q"]} for g, x in ef.items()]).to_csv(FIG / "new_excess_fraction.csv", index=False)
    pd.DataFrame([{"language": k.split("|")[0], "condition": k.split("|")[1], **{a: b for a, b in v.items() if a != "ci"}, "ci_low": v["ci"][0], "ci_high": v["ci"][1]} for k, v in pen.items()]).to_csv(FIG / "new_api_population_penalty.csv", index=False)
    pd.DataFrame([{"group": g, "arm": a, "unanswered_pct": v} for g, x in res["unanswered_by_group_pct"].items() for a, v in x.items()]).to_csv(FIG / "new_unanswered_by_arm.csv", index=False)
    pd.DataFrame([{"run": k.split("|")[0], "language": k.split("|")[1], "n": v["n"], "self": v["self"], "api": v["api"], "diff": v["diff"], "ci_low": v["boot_ci"][0], "ci_high": v["boot_ci"][1], "only_self": v["only_self"], "only_api": v["only_api"], "mcnemar_p": v["mcnemar_p"]} for k, v in cals.items()]).to_csv(FIG / "new_calibration_ci.csv", index=False)
    pd.DataFrame([{"group": k, "arm": a, "repeats_original_wrong_answer_pct": v} for k, x in same.items() for a, v in x.items()]).to_csv(FIG / "new_repeat_original_answer.csv", index=False)
    (HERE / "verify_results.json").write_text(json.dumps(res, indent=2, ensure_ascii=False, default=float), encoding="utf-8")
    print(json.dumps(res, indent=1, ensure_ascii=False, default=float)[:200])


def extra():
    import statsmodels.api as sm
    rng = np.random.default_rng(SEED + 1)
    res = {}
    api = pd.read_csv(CACHE / "api_cot.csv.gz", low_memory=False)
    ro = pd.read_csv(CACHE / "rollouts.csv.gz")
    e1 = pd.read_csv(CACHE / "exp1.csv.gz")
    pm = pd.read_csv(CACHE / "exp1_prefix_map.csv")
    ids = set(json.load(open(CACHE / "exp2_source_ids.json", encoding="utf-8")))
    api["answered"] = api.has_answer & ~api.cutoff
    t = trace_means(ro)

    wide = api.pivot_table(index=["language", "task", "difficulty", "qid"], columns="insertion", values="answered", aggfunc="first")
    un = {}
    for lang in ["hi_IN", "en_US"]:
        w = wide.loc[lang].dropna()
        for ins in ["similar_insertion", "dissimilar_insertion"]:
            v = (~w[ins].astype(bool)).astype(float).values - (~w["no_insertion"].astype(bool)).astype(float).values
            un[f"{lang}|{ins}"] = {"n": len(v), "unanswered_none_pct": 100 * float((~w["no_insertion"].astype(bool)).mean()), "unanswered_cond_pct": 100 * float((~w[ins].astype(bool)).mean()), "diff_pts": 100 * float(v.mean()), "ci": [100 * x for x in boot_ci(v, rng, 2000)]}
    res["api_unanswered_paired"] = un

    sim = api[api.insertion != "no_insertion"].copy()
    for c in ["any_mention", "loose_any"]:
        sim[c] = sim[c].map({True: True, False: False, "True": True, "False": False}).fillna(False).astype(bool)
    sim = sim[sim.answered]
    sim["pre"] = sim.any_mention & (sim.k >= 0) & (sim.k < sim.answer_pos)
    mh = {}
    for (lang, ins), g in sim.groupby(["language", "insertion"]):
        for col in ["pre", "any_mention", "loose_any"]:
            tabs = []
            for _, x in g.groupby(["task", "difficulty"]):
                a, b, c, d = int((x[col] & ~x.correct).sum()), int((x[col] & x.correct).sum()), int((~x[col] & ~x.correct).sum()), int((~x[col] & x.correct).sum())
                tabs.append(np.array([[a, b], [c, d]]))
            st = sm.stats.StratifiedTable(tabs)
            lo, hi = st.oddsratio_pooled_confint()
            mh[f"{lang}|{ins}|{col}"] = {"wrong_given_mention_pct": 100 * float((~g[g[col]].correct).mean()), "wrong_given_no_mention_pct": 100 * float((~g[~g[col]].correct).mean()), "n_mention": int(g[col].sum()), "mh_or_wrong": float(st.oddsratio_pooled), "ci": [float(lo), float(hi)], "p": float(st.test_null_odds().pvalue)}
    res["mention_vs_error_mh"] = mh

    d = api[api.id.isin(ids)][["id", "distractor"]].rename(columns={"id": "source_id"})
    x = t.merge(d, on="source_id")
    dist = {}
    for lang in ["hi_IN", "en_US"]:
        h = x[x.language == lang]
        g = h.groupby("distractor")
        tab = g.agg(n=("Q", "size"), Q=("Q", "mean"), P=("P", "mean"), M=("M", "mean"), task=("task", "first"))
        tab["Q-P"] = 100 * (tab.Q - tab.P)
        tab["M-P"] = 100 * (tab.M - tab.P)
        tab = tab.sort_values("n", ascending=False)
        dist[lang] = {"distinct_distractors": len(tab), "top10": [{"distractor": i, **{k: (float(v) if k != "task" else v) for k, v in r.items()}} for i, r in tab.head(10).iterrows()]}
        keys = list(g.groups)
        arr = {k: (g.get_group(k).Q - g.get_group(k).P).values for k in keys}
        arm = {k: (g.get_group(k).M - g.get_group(k).P).values for k in keys}
        qs, ms = [], []
        for _ in range(BOOT):
            pick = rng.integers(0, len(keys), len(keys))
            qs.append(np.concatenate([arr[keys[i]] for i in pick]).mean())
            ms.append(np.concatenate([arm[keys[i]] for i in pick]).mean())
        dist[lang]["cluster_boot_QP_ci"] = [100 * float(a) for a in np.quantile(qs, [0.025, 0.975])]
        dist[lang]["cluster_boot_MP_ci"] = [100 * float(a) for a in np.quantile(ms, [0.025, 0.975])]
        top = tab.index[0]
        rest = h[h.distractor != top]
        dist[lang]["excluding_top_distractor"] = {"top": top, "n_top": int(tab.n.iloc[0]), "Q-P": test(rest.Q - rest.P, rng), "M-P": test(rest.M - rest.P, rng)}
        tab.reset_index().to_csv(FIG / f"new_by_distractor_{lang}.csv", index=False)
    res["by_distractor"] = dist

    h = t[t.language == "hi_IN"]
    res["hindi_excl_recurrence"] = {"Q-P": test((h[h.task != "date_recurrence"].Q - h[h.task != "date_recurrence"].P), rng), "M-P": test((h[h.task != "date_recurrence"].M - h[h.task != "date_recurrence"].P), rng), "recurrence_share_of_QP_pct": 100 * float((h[h.task == "date_recurrence"].Q - h[h.task == "date_recurrence"].P).sum() / (h.Q - h.P).sum())}
    res["hindi_recurrence_only"] = {"Q-P": test((h[h.task == "date_recurrence"].Q - h[h.task == "date_recurrence"].P), rng)}
    base = api[(api.language == "hi_IN")].pivot_table(index=["task", "difficulty", "qid"], columns="insertion", values="correct", aggfunc="first")
    ans = api[(api.language == "hi_IN")].pivot_table(index=["task", "difficulty", "qid"], columns="insertion", values="answered", aggfunc="first")
    ok = base.astype(bool) & ans.astype(bool)
    res["api_penalty_by_task_hi"] = {k: {"n": len(v), "sim": 100 * float(v.no_insertion.mean() - v.similar_insertion.mean()), "dis": 100 * float(v.no_insertion.mean() - v.dissimilar_insertion.mean())} for k, v in ok.groupby(level="task")}

    def both(g):
        x = t[g]
        s = ro[ro.source_id.isin(x.source_id)]
        a = s[s.answered].groupby(["source_id", "arm"]).correct.mean().unstack()
        pm_rate = s.groupby("arm").mention.mean()
        out = {"sum_QP_plus_MP_strict": test((x.Q - x.P) + (x.M - x.P), rng), "sum_QP_plus_MP_answered": test(((a.Q - a.P) + (a.M - a.P)).values, rng), "mention_rate_Q": 100 * float(pm_rate["Q"]), "mention_rate_P": 100 * float(pm_rate["P"]), "mention_rate_M": 100 * float(pm_rate["M"])}
        v = x[["Q", "P", "M"]].values
        idx = rng.integers(0, len(v), size=(BOOT, len(v)))
        pp = s[s.arm == "P"].groupby("source_id").mention.mean().reindex(x.source_id).values
        qq = s[s.arm == "Q"].groupby("source_id").mention.mean().reindex(x.source_id).values
        w1 = (v[idx, 0].mean(1) - v[idx, 1].mean(1)) / (pp[idx].mean(1) - qq[idx].mean(1))
        w2 = (v[idx, 2].mean(1) - v[idx, 1].mean(1)) / (1 - pp[idx].mean(1))
        out["QP_per_unit_mention"] = {"est": 100 * float((v[:, 0].mean() - v[:, 1].mean()) / (pp.mean() - qq.mean())), "ci": [100 * float(q) for q in np.quantile(w1, [0.025, 0.975])]}
        out["MP_per_unit_mention"] = {"est": 100 * float((v[:, 2].mean() - v[:, 1].mean()) / (1 - pp.mean())), "ci": [100 * float(q) for q in np.quantile(w2, [0.025, 0.975])]}
        u = s.assign(un=~s.answered).groupby(["source_id", "arm"]).un.mean().unstack().reindex(x.source_id)
        aq = s[s.answered & (s.arm == "Q")]
        vv = np.c_[x.P.values, x.Q.values, u.P.values, u.Q.values, ]
        share = []
        for i in idx[:2000]:
            up, uq = vv[i, 2].mean(), vv[i, 3].mean()
            pq, pp2 = vv[i, 1].mean(), vv[i, 0].mean()
            ap, aq2 = pp2 / (1 - up), pq / (1 - uq)
            share.append((up - uq) * (ap + aq2) / 2 / (pq - pp2))
        out["completion_share_ci_pct"] = [100 * float(q) for q in np.quantile(share, [0.025, 0.975])]
        return out
    res["comparability"] = {"Hindi, all": both(t.language == "hi_IN"), "Hindi, later": both((t.language == "hi_IN") & ~t.opening), "Hindi, opening": both((t.language == "hi_IN") & t.opening), "English, all": both(t.language == "en_US")}

    p_m = ro[ro.arm == "P"].groupby(["source_id", "mention"]).correct.mean().unstack()
    res["M_minus_P_no_mention_rollouts"] = {}
    for name, g in [("Hindi, all", t.language == "hi_IN"), ("Hindi, later", (t.language == "hi_IN") & ~t.opening), ("Hindi, opening", (t.language == "hi_IN") & t.opening), ("English, all", t.language == "en_US")]:
        x = t[g].set_index("source_id")
        nm = p_m.reindex(x.index)[False]
        res["M_minus_P_no_mention_rollouts"][name] = test((x.M - nm).dropna().values, rng)
        res["M_minus_P_no_mention_rollouts"][name + " (Q minus same)"] = test((x.Q - nm).dropna().values, rng)

    lat = t[(t.language == "hi_IN") & ~t.opening]
    res["P_minus_P1_by_k"] = {"k=1 (P1 is empty prefix)": test(lat[lat.k == 1].P - lat[lat.k == 1].P1, rng), "k>=2": test(lat[lat.k >= 2].P - lat[lat.k >= 2].P1, rng), "M-P k=1": test(lat[lat.k == 1].M - lat[lat.k == 1].P, rng), "M-P k>=2": test(lat[lat.k >= 2].M - lat[lat.k >= 2].P, rng), "DiD k=1": test((lat[lat.k == 1].M - lat[lat.k == 1].P) - (lat[lat.k == 1].P - lat[lat.k == 1].P1), rng), "DiD k>=2": test((lat[lat.k >= 2].M - lat[lat.k >= 2].P) - (lat[lat.k >= 2].P - lat[lat.k >= 2].P1), rng)}

    s1 = e1[(e1.run == "S") & (e1.kind == "main")].pivot_table(index="source_id", columns="version", values="correct", aggfunc="first")
    g1 = e1[(e1.run == "G") & (e1.kind == "main")].pivot_table(index="source_id", columns="version", values="correct", aggfunc="first")
    same = pm[(pm.language == "hi_IN") & pm.A_eq_M].source_id
    other = pm[(pm.language == "hi_IN") & ~pm.A_eq_M].source_id
    tt = t.set_index("source_id")
    res["exp1_vs_exp2_identical_prefix"] = {"n": len(same), "S_A_minus_B": test(s1.loc[same].A.astype(float) - s1.loc[same].B.astype(float), rng), "G_A_minus_B": test(g1.loc[same].A.astype(float) - g1.loc[same].B.astype(float), rng), "exp2_M_minus_P": test(tt.loc[same].M - tt.loc[same].P, rng), "S_B_minus_C": test(s1.loc[same].B.astype(float) - s1.loc[same].C.astype(float), rng), "G_B_minus_C": test(g1.loc[same].B.astype(float) - g1.loc[same].C.astype(float), rng),
                                            "S_B_acc": 100 * float(s1.loc[same].B.mean()), "exp2_P_acc": 100 * float(tt.loc[same].P.mean()), "S_A_acc": 100 * float(s1.loc[same].A.mean()), "exp2_M_acc": 100 * float(tt.loc[same].M.mean())}
    res["exp1_other_107"] = {"n": len(other), "S_B_minus_C": test(s1.loc[other].B.astype(float) - s1.loc[other].C.astype(float), rng), "G_B_minus_C": test(g1.loc[other].B.astype(float) - g1.loc[other].C.astype(float), rng), "opening": int((pm[pm.source_id.isin(other)].k == 0).sum())}

    v = (tt[tt.language == "en_US"].M - tt[tt.language == "en_US"].P).values
    extreme = 0
    total = 0
    r2 = np.random.default_rng(SEED + 2)
    for _ in range(40):
        f = (v * r2.choice([-1.0, 1.0], size=(100000, len(v)))).mean(axis=1)
        extreme += int((np.abs(f) >= abs(v.mean()) - 1e-12).sum())
        total += 100000
    res["english_MP_perm_4M"] = {"p": (extreme + 1) / (total + 1), "holm_threshold": 0.05 / 3, "se": float(np.sqrt(extreme / total * (1 - extreme / total) / total))}

    chk = Counter()
    loops = defaultdict(Counter)
    for n in range(1, 8):
        for r in json.load(open(EXP2 / f"resample/round_{n:02d}/results.json", encoding="utf-8")):
            d = r["decoding"]
            chk[f"temp{d['temperature']}|top_p{d['top_p']}|max{d['max_tokens']}|cont{d['continue_final_message']}|gen{d['add_generation_prompt']}|think{d['chat_template_kwargs']['enable_thinking']}"] += 1
            chk["reasoning_content_nonnull"] += bool(r.get("reasoning_content"))
            chk["content_has_think_tag"] += "<think" in (r.get("content") or "") or "</think" in (r.get("content") or "")
            if r.get("finish_reason") == "length":
                c = r["content"] or ""
                lang = r["meta"]["language"]
                for w in [40, 50, 60, 80, 100]:
                    for off in [0, 20, 50]:
                        tail = c[-w - off:-off] if off else c[-w:]
                        loops[f"tail{w}_offset{off}_count>=3"][lang] += c.count(tail) >= 3
                        loops[f"tail{w}_offset{off}_count>=2"][lang] += c.count(tail) >= 2
    res["decoding_checks_exp2"] = dict(chk)
    res["loop_tail_grid_exp2"] = {k: dict(v) for k, v in loops.items()}
    e2req = json.load(open(EXP2 / "requests_resample.json", encoding="utf-8"))
    src = {}
    for dn in DIFFS:
        for r in json.load(open(ROOT / f"responses/standard/{dn}.json", encoding="utf-8")):
            if r["condition"] == "cot" and r["meta"]["insertion"] in ("similar_insertion", "no_insertion"):
                src[r["id"]] = (r["request"]["messages"][0]["content"], r["content"])
    match = Counter()
    for q in e2req:
        sid = q["meta"]["source_id"]
        target = sid.replace("similar_insertion", "no_insertion") if q["meta"]["arm"] == "Q" else sid
        match[f"user_prompt_equal_{q['meta']['arm']}"] += q["messages"][0]["content"] == src[target][0]
        pre = q["messages"][1]["content"]
        match["prefix_is_substring_of_api_text"] += pre == "<think></think>" or pre.strip() in src[sid][1]
    res["request_checks_exp2"] = dict(match)
    res["request_checks_total"] = len(e2req)
    lg = {}
    for run in "GS":
        r = [x for x in json.load(open(EXP1 / f"selfhost_{run}/results.json", encoding="utf-8")) if x["finish_reason"] == "length"]
        lg[run] = {"cutoff": len(r), "last60_seen_3x": sum((x["content"] or "").count((x["content"] or "")[-60:]) >= 3 for x in r)}
    res["loop_exp1_last60"] = lg
    cs = json.load(open(EXP1 / "selfhost/calibration_redhat_v031_triton_mla_S.json", encoding="utf-8"))
    res["calibration_S_over_4096"] = [{"language": x["language"], "tokens": x["tokens"], "correct": x["correct"]} for x in cs["rows"] if (x["tokens"] or 0) > 4096]
    res["calibration_G_checks"] = json.load(open(EXP1 / "selfhost/calibration_redhat_v031_triton_mla_G.json", encoding="utf-8"))["summary"]["checks"]
    fp = {}
    for lang in ["hi_IN", "en_US"]:
        x = api[api.language == lang]
        p = x.pivot_table(index=["task", "difficulty", "qid"], columns="insertion", values=["answered", "correct"], aggfunc="first")
        for ins in ["similar_insertion", "dissimilar_insertion"]:
            a0, a1 = p["answered"]["no_insertion"].astype(bool), p["answered"][ins].astype(bool)
            ok = a0 & a1
            v = (p["correct"]["no_insertion"][ok].astype(float) - p["correct"][ins][ok].astype(float)).values
            st = ((a0 & p["correct"]["no_insertion"].astype(bool)).astype(float) - (a1 & p["correct"][ins].astype(bool)).astype(float)).values
            cd = (a1 & p["correct"][ins].astype(bool)).astype(float).values
            idx = rng.integers(0, len(st), (2000, len(st)))
            ef = st[idx].mean(1) / (1 - cd[idx].mean(1))
            fp[f"{lang}|{ins}"] = {"both_answered_n": len(v), "both_answered_penalty": 100 * float(v.mean()), "both_answered_ci": [100 * q for q in boot_ci(v, rng, 2000)], "strict_penalty": 100 * float(st.mean()), "strict_excess_fraction_pct": 100 * float(st.mean() / (1 - cd.mean())), "strict_excess_fraction_ci": [100 * float(q) for q in np.quantile(ef, [0.025, 0.975])]}
    res["api_population_attribution"] = fp
    pd.DataFrame([{"language": k.split("|")[0], "condition": k.split("|")[1], **{a: b for a, b in v.items() if not a.endswith("ci")}, "ef_low": v["strict_excess_fraction_ci"][0], "ef_high": v["strict_excess_fraction_ci"][1]} for k, v in fp.items()]).to_csv(FIG / "new_api_population_attribution.csv", index=False)
    lt = t[t.language == "hi_IN"]
    res["split_by_recurrence"] = {f"{'later' if not o else 'opening'}|{'recurrence' if r else 'other tasks'}": {"n": int(((lt.opening == o) & ((lt.task == "date_recurrence") == r)).sum()), "M-P": test((lt[(lt.opening == o) & ((lt.task == "date_recurrence") == r)].M - lt[(lt.opening == o) & ((lt.task == "date_recurrence") == r)].P), rng), "Q-P": test((lt[(lt.opening == o) & ((lt.task == "date_recurrence") == r)].Q - lt[(lt.opening == o) & ((lt.task == "date_recurrence") == r)].P), rng)} for o in [True, False] for r in [True, False]}
    pt = []
    for g, cond in [("Hindi, all", t.language == "hi_IN"), ("Hindi, opening", (t.language == "hi_IN") & t.opening), ("Hindi, later", (t.language == "hi_IN") & ~t.opening), ("English, all", t.language == "en_US")]:
        i = t[cond].source_id
        s = ro[ro.source_id.isin(i)]
        for arm, label in [("Q", "Q arm"), ("M", "M arm")]:
            pt.append({"group": g, "series": label, "accuracy_pct": 100 * float(s[s.arm == arm].correct.mean()), "n_rollouts": int((s.arm == arm).sum())})
        for flag, label in [(True, "P arm, rollout mentions"), (False, "P arm, rollout does not mention")]:
            z = s[(s.arm == "P") & (s.mention == flag)]
            pt.append({"group": g, "series": label, "accuracy_pct": 100 * float(z.correct.mean()), "n_rollouts": len(z)})
    pd.DataFrame(pt).to_csv(FIG / "new_p_rollouts_by_mention.csv", index=False)
    (HERE / "verify_extra.json").write_text(json.dumps(res, indent=2, ensure_ascii=False, default=float), encoding="utf-8")


if __name__ == "__main__":
    CACHE.mkdir(exist_ok=True)
    FIG.mkdir(exist_ok=True)
    stages = {"api": stage_api, "rollouts": stage_rollouts, "exp1": stage_exp1, "prefix": stage_prefix, "calibration": stage_calibration, "analyse": analyse, "extra": extra}
    for s in sys.argv[1:] or stages:
        stages[s]()
