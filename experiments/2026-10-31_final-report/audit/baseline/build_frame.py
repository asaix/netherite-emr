import gc
import hashlib
import importlib.util
import re
import sys

from common import *
from trd.templates.insertions import get_all_insertions

STOP = set("""the a an and of to in on at is was for with my i he she it they his her their this that be by as from or are
have has had will would not but you your we our me always many each every how what which there some very just
day days month months year years time times date dates week weeks today hour hours minute minutes
है हैं में की के का को से ने पर और भी यह वह इस उस मैं मुझे मेरा मेरी मेरे हम हमें हमारा था थी थे हूं हूँ हो होता होती
होते जाता जाती जाते रहता रहती रहते करता करती करते कि कितने कैसे हर नहीं चाहिए गया गई लिए साथ बहुत सबसे वाले वाली
रही रहा दिन दिनों महीना महीने महीनों साल वर्ष समय तारीख तारीखें तिथि सप्ताह हफ्ते आज घंटे मिनट""".split())
TOK = re.compile(r"[^\s.,!?।'\"():;]+")
VERIF = re.compile(r"verif|double.?check|let me check|check (?:this|by|again)|sanity|alternatively|another way|cross.?check|सत्यापित|जांच|जाँच|पुष्टि|दोबारा|वैकल्पिक|दूसरे तरीके", re.I)
P_CUR = re.compile(r"(?:Answer|उत्तर(?:\s*है)?|जवाब)\s*\**\s*[:：]\s*(?!Answer|उत्तर|जवाब)(.*)")
P_ROOT = re.compile(r"(?:Answer|उत्तर(?:\s*है)?|जवाब)\s*\**\s*[:：]\s*(.*)")
P_MID = re.compile(r"(?:Answer|उत्तर)\s*\**\s*[:：]\s*(.*)")
HI_TO = re.compile(r"\s+से\s+")
WD = {"monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3, "friday": 4, "saturday": 5, "sunday": 6}
spec = importlib.util.spec_from_file_location("trd_locale", ROOT / "tools/temporal-reasoning-dataset/src/trd/utils/locale.py")
loc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(loc)
ALLDAYS = {n.casefold(): d for names in loc.DAY_NAMES.values() for d, n in names.items()}


def ext(rx, content, mid=False):
    m = rx.findall(content or "")
    if not m:
        return None
    s = m[-1].strip().strip("*`.। ").translate(DIG)
    return s if mid else HI_TO.sub(" to ", s)


def proj_correct(task, ans, gold):
    if ans is None:
        return None
    if task == "day_of_week":
        return ALLDAYS.get(ans.casefold()) == ALLDAYS[gold.casefold()]
    return ans == gold


def content_words(t):
    return {w for w in TOK.findall(t.translate(DIG).casefold()) if len(w) >= 3 and w not in STOP and not w.isdigit()}


def reuse_feats(s):
    s = s.translate(DIG).casefold()
    toks = TOK.findall(s)
    nums = {int(n) for n in re.findall(r"\d+", s)} | ({7} if ("seven" in toks or "सात" in toks) else set())
    mon = {MONTHS[t] for t in toks if t in MONTHS}
    wk = {ALLDAYS[t] for t in toks if t in ALLDAYS}
    return nums, nums | {n + 12 for n in nums if n < 12}, mon, wk


def comps(task, v):
    if task in ("date_addition", "date_subtraction", "date_recurrence"):
        d = date.fromisoformat(v)
        return [("n", d.year), ("mon", d.month), ("n", d.day)]
    if task == "interval_date":
        a, b = v.split(" to ")
        return comps("date_addition", a) + comps("date_addition", b)
    if task in ("time_addition", "time_subtraction"):
        h, m = v.split(":")
        return [("hr", int(h)), ("n", int(m))]
    if task == "day_of_week":
        return [("wk", v)]
    return [("n", int(v))]


def reuse(task, a, g, feats):
    n, hr, mon, wk = feats
    if not (n or mon or wk):
        return None
    pool = {"n": n, "hr": hr, "mon": mon, "wk": wk}
    return any(x != y and x in pool[k] for (k, x), (_, y) in zip(comps(task, a), comps(task, g)))


DATA = {}
for lvl in LEVELS:
    for task in TASKS:
        for lang in LANGS:
            DATA[lvl, task, lang] = json.load(open(ROOT / "dataset" / lvl / f"{task}_{lang}.json", encoding="utf-8"))

qrows = []
for (lvl, task, lang), qs in DATA.items():
    sim = get_all_insertions(lang, TPL_KEY[task], True)
    dis = get_all_insertions(lang, TPL_KEY[task], False)
    for qn, q in qs.items():
        s = q["similar_insertion"][: -len(q["no_insertion"])].strip()
        d = q["dissimilar_insertion"][: -len(q["no_insertion"])].strip()
        p = parse_question(task, q["no_insertion"])
        qrows.append({"level": lvl, "task": task, "lang": lang, "qnum": int(qn), "qtext": q["no_insertion"], "gold": q["answer"], "sim_text": s, "dis_text": d, "sim_idx": sim.index(s), "dis_idx": dis.index(d), "params": json.dumps(p), "gold_computed": compute_gold(task, p)})
Q = pd.DataFrame(qrows)
Q["gold_check"] = [gold_typed(t, g) == c for t, g, c in zip(Q.task, Q.gold, Q.gold_computed)]
Q.to_pickle(CACHE / "questions.pkl")

rows, rawhash = [], {}
for lvl in LEVELS:
    R = json.load(open(ROOT / "responses" / "standard" / f"{lvl}.json", encoding="utf-8"))
    for r in R:
        m, c = r["meta"], r["content"] or ""
        task, lang, ins, qn = m["task"], m["language"], m["insertion"], m["question_id"]
        q = DATA[lvl, task, lang][qn]
        gold = m["answer"]
        pc = ext(P_CUR, c)
        pr, pm = ext(P_ROOT, c), ext(P_MID, c, True)
        mine, on_last = my_extract(c)
        tv = typed(task, mine)
        g = gold_typed(task, gold)
        ok_p, ok_r, ok_m = proj_correct(task, pc, gold), proj_correct(task, pr, gold), proj_correct(task, pm, gold)
        hits = list(P_CUR.finditer(c))
        body = c[: hits[-1].start()] if hits else c
        nolabel = P_CUR.sub("", c)
        hi, en = len(DEV_WORD.findall(nolabel)), len(LAT_WORD.findall(nolabel))
        qparam = parse_question(task, q["no_insertion"])
        s_txt = q["similar_insertion"][: -len(q["no_insertion"])].strip()
        d_txt = q["dissimilar_insertion"][: -len(q["no_insertion"])].strip()
        row = {"id": r["id"], "level": lvl, "task": task, "lang": lang, "insertion": ins, "cond": r["condition"], "qnum": int(qn), "qid": f"{lvl}/{task}/{qn}", "gold": gold, "finish": r["finish_reason"], "ctok": (r.get("usage") or {}).get("completion_tokens"), "ptok": (r.get("usage") or {}).get("prompt_tokens"), "time": r.get("time"), "p_ans": pc, "p_ok": ok_p, "r_ans": pr, "r_ok": ok_r, "m_ans": pm, "m_ok": ok_m, "my_raw": mine, "my_val": None if tv is None else str(tv), "my_ok": None if mine is None else tv == g, "on_last": on_last, "hi_w": hi, "en_w": en, "verif": bool(VERIF.search(body)), "chars": len(c), "prompt_ok": r["request"]["messages"][0]["content"].rstrip().endswith(q[ins].rstrip()), "gold_ds": q["answer"] == gold, "last_val": None}
        norm_body = body.translate(DIG)
        toks = set(TOK.findall(norm_body.casefold()))
        base = content_words(q["no_insertion"])
        for kind, txt in (("sim", s_txt), ("dis", d_txt)):
            insname = {"sim": "similar_insertion", "dis": "dissimilar_insertion"}[kind]
            if ins in ("no_insertion", insname):
                w = content_words(txt) - base
                row[f"men_{kind}"] = bool(w & toks) if w and r["condition"] == "cot" and pc is not None else None
                row[f"quote_{kind}"] = txt.translate(DIG).rstrip(".।?").casefold() in norm_body.casefold() if r["condition"] == "cot" else None
                nq = norm_body.casefold().replace(txt.translate(DIG).rstrip(".।?").casefold(), " ")
                row[f"men_nq_{kind}"] = bool(w & set(TOK.findall(nq))) if w and r["condition"] == "cot" and pc is not None else None
            else:
                row[f"men_{kind}"] = row[f"quote_{kind}"] = row[f"men_nq_{kind}"] = None
            if pc is not None and ok_p is False and typed(task, pc) is not None and ins in ("no_insertion", insname):
                val = typed(task, pc)
                ans_str = val if task != "day_of_week" else val
                gv = g
                try:
                    row[f"reuse_{kind}"] = reuse(task, ans_str, gv, reuse_feats(txt))
                except Exception:
                    row[f"reuse_{kind}"] = None
            else:
                row[f"reuse_{kind}"] = None
        if task == "date_recurrence" and pc is not None:
            ad = mkdate(*pc.split("-")) if re.fullmatch(r"\d{4}-\d{2}-\d{2}", pc) else None
            today = date.fromisoformat(qparam["today"])
            off = (ad - today).days if ad else None
            row["k"], row["every"] = qparam["k"], qparam["every"]
            row["rec"] = None if off is None else "correct" if off == qparam["every"] * qparam["k"] else "mirror" if off == -qparam["every"] * qparam["k"] else "first_step" if off == qparam["every"] else "other"
        if task == "day_of_week" and pc is not None and pc.casefold() in ALLDAYS:
            row["dow_pred"] = ALLDAYS[pc.casefold()]
            row["dow_off"] = (ALLDAYS[pc.casefold()] - ALLDAYS[gold.casefold()] + 3) % 7 - 3
        rows.append(row)
    del R
    gc.collect()
F = pd.DataFrame(rows)
idx = Q[Q.lang == "en_US"].set_index(["level", "task", "qnum"])
hi = Q[Q.lang == "hi_IN"].set_index(["level", "task", "qnum"])
F = F.merge(idx[["sim_idx", "dis_idx"]].reset_index(), on=["level", "task", "qnum"], how="left")
F["answered"] = F.p_ans.notna()
F["acc"] = F.p_ok.astype(float)
F["strict"] = F.acc.fillna(0.0)
F["my_acc"] = F.my_ok.astype(float)
F["my_strict"] = F.my_acc.fillna(0.0)
F.to_pickle(CACHE / "frame.pkl")
print(len(F), F.answered.sum(), len(Q), Q.gold_check.mean(), (idx.sim_idx == hi.sim_idx).all(), (idx.dis_idx == hi.dis_idx).all())
print(F.groupby(["lang", "cond"])[["acc", "strict", "my_acc", "my_strict"]].mean().round(4))
print((F.acc != F.my_acc).sum(), "acc vs my_acc mismatches incl nan", (F.prompt_ok).mean(), F.gold_ds.mean())
