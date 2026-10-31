import re
import warnings

from scipy.stats import binomtest

from common import *

warnings.simplefilter("ignore")
P = re.compile(r"(?:Answer|उत्तर(?:\s*है)?|जवाब)\s*\**\s*[:：]\s*(?!Answer|उत्तर|जवाब)(.*)")
HI_TO = re.compile(r"\s+से\s+")
VERIF = re.compile(r"verif|double.?check|let me check|check (?:this|by|again)|sanity|alternatively|another way|cross.?check|सत्यापित|जांच|जाँच|पुष्टि|दोबारा|वैकल्पिक|दूसरे तरीके", re.I)
ALL = {**EN_DAYS, **{k: v for k, v in HI_DAYS.items() if k in ("सोमवार", "मंगलवार", "बुधवार", "गुरुवार", "शुक्रवार", "शनिवार", "रविवार")}}


def ext(c):
    m = P.findall(c or "")
    return HI_TO.sub(" to ", m[-1].strip().strip("*`.। ").translate(DIG)) if m else None


def ok(task, a, g):
    if a is None:
        return None
    return ALL.get(a.casefold()) == ALL[g.casefold()] if task == "day_of_week" else a == g


rows = []
for lvl in LEVELS:
    for r in json.load(open(ROOT / "responses/ron" / f"{lvl}.json", encoding="utf-8")):
        m, c, h = r["meta"], r["content"] or "", r.get("reasoning_content") or ""
        u = r.get("usage") or {}
        a = ext(c)
        v = P.sub("", c)
        vh, ve = len(DEV_WORD.findall(v)), len(LAT_WORD.findall(v))
        hh, he = len(DEV_WORD.findall(h)), len(LAT_WORD.findall(h))
        rec = None
        if m["task"] == "date_recurrence" and a and re.fullmatch(r"\d{4}-\d{2}-\d{2}", a):
            p = parse_question("date_recurrence", r["request"]["messages"][0]["content"].rstrip().split("\n")[-1])
            ad = mkdate(*a.split("-"))
            off = (ad - date.fromisoformat(p["today"])).days if ad else None
            rec = (p["k"], None if off is None else "correct" if off == p["every"] * p["k"] else "mirror" if off == -p["every"] * p["k"] else "first_step" if off == p["every"] else "other")
        rows.append({"id": r["id"], "level": lvl, "task": m["task"], "lang": m["language"], "insertion": m["insertion"], "cond": r["condition"], "qnum": int(m["question_id"]), "qid": f"{lvl}/{m['task']}/{m['question_id']}", "gold": m["answer"], "finish": r["finish_reason"], "max_tokens": r["request"].get("max_tokens"), "effort": r["request"].get("reasoning_effort"), "temperature": r["request"].get("temperature"), "ctok": u.get("completion_tokens"), "rtok": (u.get("completion_tokens_details") or {}).get("reasoning_tokens"), "acc_on": None if ok(m["task"], a, m["answer"]) is None else float(ok(m["task"], a, m["answer"])), "vis_hi": vh, "vis_en": ve, "hid_hi": hh, "hid_en": he, "hid_lang_mentions": len(re.findall(r"\bHindi\b|हिंदी|हिन्दी", h)), "vis_verif": bool(VERIF.search(c)), "hid_verif": bool(VERIF.search(h)), "has_hidden": bool(h), "rec_k": rec[0] if rec else None, "rec": rec[1] if rec else None})
ON = pd.DataFrame(rows)
OFF = frame()[["id", "acc", "strict", "ctok", "finish", "answered", "hi_w", "en_w", "verif"]].rename(columns={"acc": "acc_off", "strict": "strict_off", "ctok": "ctok_off", "finish": "finish_off", "answered": "answered_off", "hi_w": "off_hi", "en_w": "off_en", "verif": "off_verif"})
D = ON.merge(OFF, on="id", how="left", validate="one_to_one")
D["strict_on"] = D.acc_on.fillna(0.0)
D["ans_on_4k"] = D.acc_on.notna() & (D.ctok <= 4096)
D["acc_on_4k"] = D.acc_on.where(D.ans_on_4k)
D["strict_on_4k"] = D.acc_on_4k.fillna(0.0)
D.to_pickle(CACHE / "ron.pkl")
D["q"] = D.groupby("qid", sort=False).ngroup()
NQ = D.q.max() + 1
rng = np.random.default_rng(20261032)
W = np.stack([np.bincount(rng.integers(0, NQ, NQ), minlength=NQ) for _ in range(2000)]).astype(np.float32)


def est(s, col):
    s = s[s[col].notna()]
    c = np.bincount(s.q, weights=s[col], minlength=NQ).astype(np.float32)
    n = np.bincount(s.q, minlength=NQ).astype(np.float32)
    return c.sum() / n.sum(), (W @ c) / (W @ n), int(n.sum())


def ci(v, b):
    lo, hi = np.nanpercentile(b, [2.5, 97.5])
    return {"v": round(100 * float(v), 2), "lo": round(100 * float(lo), 2), "hi": round(100 * float(hi), 2)}


R = {"meta": {"rows": len(D), "questions": D.qid.nunique(), "matched_off": int(D.acc_off.notna().sum() + D.answered_off.eq(False).sum()), "effort": D.effort.value_counts().to_dict(), "max_tokens": D.max_tokens.value_counts().to_dict(), "temperature": D.temperature.value_counts().to_dict(), "hidden_present": round(float(D.has_hidden.mean()), 4)}}
T = {}
for l in LANGS:
    for c in ("direct", "cot"):
        s = D[(D.lang == l) & (D.cond == c)]
        e = {}
        for name, a, b in (("answered", "acc_on", "acc_off"), ("strict", "strict_on", "strict_off"), ("cap4k_strict", "strict_on_4k", "strict_off"), ("cap4k_answered", "acc_on_4k", "acc_off")):
            both = s[s[a].notna() & s[b].notna()]
            v1, b1, n = est(both, a)
            v0, b0, _ = est(both, b)
            up, dn = int(((both[a] == 1) & (both[b] == 0)).sum()), int(((both[a] == 0) & (both[b] == 1)).sum())
            e[name] = {"off": round(100 * float(v0), 2), "on": round(100 * float(v1), 2), "n": n, **ci(v1 - v0, b1 - b0), "on_only": up, "off_only": dn, "p": float(binomtest(up, up + dn, 0.5).pvalue) if up + dn else 1.0}
        e["unanswered_on_pct"] = round(100 * float(s.acc_on.isna().mean()), 2)
        e["finish_length_on_pct"] = round(100 * float((s.finish == "length").mean()), 2)
        e["over_4096_pct"] = round(100 * float((s.ctok > 4096).mean()), 2)
        e["unanswered_off_pct"] = round(100 * float((~s.answered_off).mean()), 2)
        e["median_ctok_on"] = float(s.ctok.median())
        e["median_ctok_off"] = float(s.ctok_off.median())
        e["median_rtok"] = float(s.rtok.median())
        tot = s.hid_hi + s.hid_en
        e["hidden_devanagari_pooled"] = round(100 * float(s.hid_hi.sum() / tot.sum()), 2)
        e["hidden_devanagari_mean"] = round(100 * float((s.hid_hi / tot.where(tot > 0)).mean()), 2)
        e["hidden_mostly_devanagari"] = round(100 * float(((s.hid_hi / tot.where(tot > 0)) > 0.5).mean()), 2)
        vt = s.vis_hi + s.vis_en
        e["visible_devanagari_pooled"] = round(100 * float(s.vis_hi.sum() / vt.sum()), 2)
        e["visible_target_pooled"] = round(100 * float((s.vis_hi if l == "hi_IN" else s.vis_en).sum() / vt.sum()), 2)
        e["median_lang_mentions"] = float(s.hid_lang_mentions.median())
        e["median_hidden_words"] = float(tot.median())
        e["median_visible_words"] = float(vt.median())
        e["vis_verif"] = round(100 * float(s.vis_verif.mean()), 2)
        e["hid_verif"] = round(100 * float(s.hid_verif.mean()), 2)
        e["off_verif"] = round(100 * float(s.off_verif.mean()), 2)
        T[f"{l}/{c}"] = e
R["on_vs_off"] = T
CD = {}
for mode, col in (("on_answered", "acc_on"), ("on_strict", "strict_on"), ("off_answered", "acc_off"), ("off_strict", "strict_off"), ("on_4k_strict", "strict_on_4k")):
    for l in LANGS:
        s = D[D.lang == l]
        a1, b1, _ = est(s[s.cond == "cot"], col)
        a0, b0, _ = est(s[s.cond == "direct"], col)
        CD[f"{mode}/{l}"] = {"direct": round(100 * float(a0), 2), "cot": round(100 * float(a1), 2), **ci(a1 - a0, b1 - b0)}
        for ins in INS:
            ss = s[s.insertion == ins]
            a1, b1, _ = est(ss[ss.cond == "cot"], col)
            a0, b0, _ = est(ss[ss.cond == "direct"], col)
            CD[f"{mode}/{l}/{ins}"] = {"direct": round(100 * float(a0), 2), "cot": round(100 * float(a1), 2), **ci(a1 - a0, b1 - b0)}
R["cot_delta"] = CD
G = {}
for lvl in LEVELS:
    for c in ("cot", "direct"):
        for mode, col in (("on", "acc_on"), ("off", "acc_off"), ("on_strict", "strict_on"), ("off_strict", "strict_off")):
            s = D[(D.level == lvl) & (D.cond == c)]
            e, be, _ = est(s[s.lang == "en_US"], col)
            h, bh, _ = est(s[s.lang == "hi_IN"], col)
            G[f"{mode}/{c}/{lvl}"] = {"en": round(100 * float(e), 2), "hi": round(100 * float(h), 2), "gap": ci(e - h, be - bh)}
for c in ("cot", "direct"):
    for mode, col in (("on", "acc_on"), ("off", "acc_off"), ("on_strict", "strict_on"), ("off_strict", "strict_off")):
        s = D[D.cond == c]
        e, be, _ = est(s[s.lang == "en_US"], col)
        h, bh, _ = est(s[s.lang == "hi_IN"], col)
        G[f"{mode}/{c}/all"] = {"en": round(100 * float(e), 2), "hi": round(100 * float(h), 2), "gap": ci(e - h, be - bh)}
R["gap"] = G
TK = []
for (l, t, c), s in D.groupby(["lang", "task", "cond"]):
    TK.append({"lang": l, "task": t, "cond": c, "off": round(100 * s.acc_off.mean(), 1), "on": round(100 * s.acc_on.mean(), 1), "off_strict": round(100 * s.strict_off.mean(), 1), "on_strict": round(100 * s.strict_on.mean(), 1), "on_4k_strict": round(100 * s.strict_on_4k.mean(), 1), "unanswered_on": round(100 * s.acc_on.isna().mean(), 1), "over_4096": round(100 * (s.ctok > 4096).mean(), 1)})
pd.DataFrame(TK).to_csv(FIG / "ron_by_task.csv", index=False)
LV = []
for (l, lv, c), s in D.groupby(["lang", "level", "cond"]):
    LV.append({"lang": l, "level": lv, "cond": c, "off": round(100 * s.acc_off.mean(), 1), "on": round(100 * s.acc_on.mean(), 1), "off_strict": round(100 * s.strict_off.mean(), 1), "on_strict": round(100 * s.strict_on.mean(), 1), "on_4k_strict": round(100 * s.strict_on_4k.mean(), 1)})
pd.DataFrame(LV).to_csv(FIG / "ron_by_level.csv", index=False)
AG = {}
for mode, col in (("off", "acc_off"), ("on", "acc_on")):
    p = D.pivot_table(index=["qid", "insertion", "cond"], columns="lang", values=col).dropna().reset_index()
    for c in ("direct", "cot"):
        x = p[p.cond == c]
        en, hi = x.en_US == 1, x.hi_IN == 1
        eo, ho = int((en & ~hi).sum()), int((~en & hi).sum())
        AG[f"{mode}/{c}"] = {"pairs": len(x), "en_only": eo, "hi_only": ho, "both_wrong": int((~en & ~hi).sum()), "p": float(binomtest(eo, eo + ho, 0.5).pvalue) if eo + ho else 1.0}
R["agreement"] = AG
PN = {}
for mode, col in (("on", "acc_on"), ("off", "acc_off"), ("on_strict", "strict_on"), ("off_strict", "strict_off")):
    for l in LANGS:
        for ins in INS[1:]:
            dr = {}
            for c in ("direct", "cot"):
                s = D[(D.lang == l) & (D.cond == c)]
                a0, b0, _ = est(s[s.insertion == "no_insertion"], col)
                a1, b1, _ = est(s[s.insertion == ins], col)
                dr[c] = (a0 - a1, b0 - b1)
            PN[f"{mode}/{l}/{ins}"] = {"drop_direct": round(100 * float(dr["direct"][0]), 2), "drop_cot": round(100 * float(dr["cot"][0]), 2), **ci(dr["cot"][0] - dr["direct"][0], dr["cot"][1] - dr["direct"][1])}
R["penalty"] = PN
rc = D[D.rec.notna()]
R["recurrence_on"] = {f"{l}/{c}": {**{k: round(100 * float(v), 1) for k, v in g.rec.value_counts(normalize=True).items()}, "n": len(g), "mirror_n": int((g.rec == "mirror").sum())} for (l, c), g in rc.groupby(["lang", "cond"])}
R["recurrence_on_k1"] = {f"{l}/{c}": {"n": len(g), "correct": round(100 * float((g.rec == "correct").mean()), 1), "mirror": round(100 * float((g.rec == "mirror").mean()), 1)} for (l, c), g in rc[rc.rec_k == 1].groupby(["lang", "cond"])}
R["recurrence_on_mirror_k"] = {f"{l}": g[g.rec == "mirror"].rec_k.value_counts().to_dict() for l, g in rc.groupby("lang")}
dw = D[(D.task == "day_of_week") & D.acc_on.notna()]
R["dow_on"] = {f"{l}/{c}": round(100 * float(g.acc_on.mean()), 1) for (l, c), g in dw.groupby(["lang", "cond"])}
F = frame()
sub = F[F.qnum < 10]
rest = F[F.qnum >= 10]
R["subset_representativeness"] = {f"{l}/{c}": {"q0_9": round(100 * float(sub[(sub.lang == l) & (sub.cond == c)].acc.mean()), 2), "q10_149": round(100 * float(rest[(rest.lang == l) & (rest.cond == c)].acc.mean()), 2)} for l in LANGS for c in ("direct", "cot")}
long_off = F[(F.cond == "cot") & (~F.answered)]
R["budget"] = {"off_cutoffs_cot_total": len(long_off), "off_cot_strict_if_all_cutoffs_right": {l: round(100 * float((F[(F.lang == l) & (F.cond == "cot")].strict + (~F[(F.lang == l) & (F.cond == "cot")].answered)).mean()), 2) for l in LANGS}, "off_tok_p99": {l: float(F[(F.lang == l) & (F.cond == "cot")].ctok.quantile(0.99)) for l in LANGS}}
dump(R, "results_ron.json")
print(json.dumps({k: R[k] for k in ("meta", "subset_representativeness", "budget")}, indent=1, ensure_ascii=False))
for k, v in T.items():
    print(k, {a: {x: v[a][x] for x in ("off", "on", "v", "lo", "hi", "n")} for a in ("answered", "strict", "cap4k_strict")}, {a: v[a] for a in v if not isinstance(v[a], dict)})
print(json.dumps(CD, indent=0)[:1800])
print(json.dumps(R["agreement"]), json.dumps(PN)[:1500])
print(json.dumps(G["on/cot/short"]), json.dumps(R["recurrence_on_k1"]), json.dumps(R["recurrence_on"]), R["dow_on"], R["recurrence_on_mirror_k"])
