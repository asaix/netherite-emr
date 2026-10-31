import re

from stats_core import *
from scipy.stats import chi2

STOP = set("""the a an and of to in on at is was for with my i he she it they his her their this that be by as from or are
have has had will would not but you your we our me always many each every how what which there some very just
day days month months year years time times date dates week weeks today hour hours minute minutes
है हैं में की के का को से ने पर और भी यह वह इस उस मैं मुझे मेरा मेरी मेरे हम हमें हमारा था थी थे हूं हूँ हो होता होती
होते जाता जाती जाते रहता रहती रहते करता करती करते कि कितने कैसे हर नहीं चाहिए गया गई लिए साथ बहुत सबसे वाले वाली
रही रहा दिन दिनों महीना महीने महीनों साल वर्ष समय तारीख तारीखें तिथि सप्ताह हफ्ते आज घंटे मिनट""".split())
TOK = re.compile(r"[^\s.,!?।'\"():;]+")
DISMISS = re.compile(r"irrelevant|not relevant|not needed|unrelated|doesn't affect|does not affect|no bearing|extra information|distract|flavor|अप्रासंगिक|जरूरी नहीं|ज़रूरी नहीं|असर नहीं|प्रभाव नहीं|संबंध नहीं|संबंधित नहीं|नहीं जुड़|भटका|अतिरिक्त जानकारी|प्रासंगिक नहीं|आवश्यक नहीं|कोई लेना", re.I)
BROAD = re.compile(r"सत्यापित|सत्यापन|जांच|जाँच|पुष्टि|दोबारा|दुबारा|पुनः|फिर से|वैकल्पिक|दूसरे तरीके|दूसरी विधि|अन्य विधि|और तरीके|चेक|verif|double.?check|let me check|check (?:this|by|again)|sanity|alternatively|another way|cross.?check|recheck|re-check|let me re", re.I)
Q = pd.read_pickle(CACHE / "questions.pkl").set_index(["level", "task", "lang", "qnum"])


def cw(t):
    return {w for w in TOK.findall(t.translate(DIG).casefold()) if len(w) >= 3 and w not in STOP and not w.isdigit()}


rec = {}
placebo_hits = {}
placebo_n = {}
for lvl in LEVELS:
    for r in json.load(open(ROOT / "responses/standard" / f"{lvl}.json", encoding="utf-8")):
        if r["condition"] != "cot":
            continue
        m = r["meta"]
        c = (r["content"] or "").translate(DIG)
        h = list(re.finditer(r"(?:Answer|उत्तर(?:\s*है)?|जवाब)\s*\**\s*[:：]\s*(?!Answer|उत्तर|जवाब)(.*)", c))
        if not h:
            continue
        body = c[: h[-1].start()]
        low = body.casefold()
        toks = set(TOK.findall(low))
        q = Q.loc[(lvl, m["task"], m["language"], int(m["question_id"]))]
        base = cw(q.qtext)
        for kind, txt in (("sim", q.sim_text), ("dis", q.dis_text)):
            name = {"sim": "similar_insertion", "dis": "dissimilar_insertion"}[kind]
            if m["insertion"] not in ("no_insertion", name):
                continue
            w = cw(txt) - base
            if m["insertion"] == "no_insertion":
                for x in w:
                    k = (m["language"], m["task"], kind, x)
                    placebo_n[k] = placebo_n.get(k, 0) + 1
                    placebo_hits[k] = placebo_hits.get(k, 0) + (x in toks)
            rec[r["id"], kind] = {"w": w, "toks": toks, "dismiss": bool(DISMISS.search(low)), "quote": txt.translate(DIG).rstrip(".।?").casefold() in low, "lang": m["language"], "task": m["task"], "kind": kind, "ins": m["insertion"]}
        rec[r["id"], "broad"] = bool(BROAD.search(body))
rate = {k: placebo_hits[k] / placebo_n[k] for k in placebo_n}
rows = []
for (i, kind), v in rec.items():
    if kind == "broad":
        continue
    good = {x for x in v["w"] if rate.get((v["lang"], v["task"], kind, x), 0) < 0.02}
    rows.append({"id": i, "kind": kind, "lang": v["lang"], "task": v["task"], "ins": v["ins"], "has_words": bool(good), "strict_mention": bool(good & v["toks"]), "dismiss": v["dismiss"], "quote": v["quote"]})
M = pd.DataFrame(rows).merge(F[["id", "acc", "level", "q", "cond", "sim_idx", "dis_idx"]], on="id")
M = M[M.has_words]
R = {}


def mh(sub, exp):
    r, s, pr, psq, qs, num, var = 0, 0, 0, 0, 0, 0, 0
    for _, g in sub.groupby(["task", "level"]):
        e, c = g[exp].to_numpy(), (g.acc == 1).to_numpy()
        a, b, cc, d = (e & c).sum(), (e & ~c).sum(), (~e & c).sum(), (~e & ~c).sum()
        n = a + b + cc + d
        if not (a + b) or not (cc + d):
            continue
        Ri, Si, Pi, Qi = a * d / n, b * cc / n, (a + d) / n, (b + cc) / n
        r += Ri
        s += Si
        pr += Pi * Ri
        psq += Pi * Si + Qi * Ri
        qs += Qi * Si
        num += a - (a + b) * (a + cc) / n
        var += (a + b) * (cc + d) * (a + cc) * (b + d) / (n * n * (n - 1))
    if not r or not s:
        return None
    o = r / s
    se = np.sqrt(pr / (2 * r * r) + psq / (2 * r * s) + qs / (2 * s * s))
    return {"or": round(float(o), 3), "lo": round(float(np.exp(np.log(o) - 1.96 * se)), 3), "hi": round(float(np.exp(np.log(o) + 1.96 * se)), 3), "p": float(chi2.sf(num * num / var, 1))}


for lang in LANGS:
    for kind, name in (("sim", "similar_insertion"), ("dis", "dissimilar_insertion")):
        a = M[(M.lang == lang) & (M.kind == kind) & (M.ins == name)].copy()
        b = M[(M.lang == lang) & (M.kind == kind) & (M.ins == "no_insertion")]
        a["dismissed"] = a.strict_mention & a.dismiss
        a["engaged"] = a.strict_mention & ~a.dismiss
        a["quoted"] = a.quote
        none = a[~a.strict_mention]
        R[f"{lang}/{kind}"] = {"n": len(a), "rate": pct(a.strict_mention.mean()), "placebo": pct(b.strict_mention.mean()), "excess": pct(a.strict_mention.mean() - b.strict_mention.mean()), "share_of_mentions_with_dismissal_cue": pct(a[a.strict_mention].dismiss.mean()), "share_of_mentions_verbatim": pct(a[a.strict_mention].quote.mean()), "acc_no_mention": pct(none.acc.mean()), "acc_dismissed": pct(a[a.dismissed].acc.mean()), "acc_engaged": pct(a[a.engaged].acc.mean()), "or_mention": mh(a, "strict_mention"), "or_engaged_vs_no_mention": mh(a[a.engaged | ~a.strict_mention], "engaged"), "or_dismissed_vs_no_mention": mh(a[a.dismissed | ~a.strict_mention], "dismissed")}
br = pd.DataFrame([{"id": i, "broad": v} for (i, k), v in rec.items() if k == "broad"]).merge(F[["id", "lang", "task"]], on="id")
R["broad_verification"] = {l: pct(g.broad.mean()) for l, g in br.groupby("lang")}
R["broad_verification_task"] = {f"{l}/{t}": pct(g.broad.mean()) for (l, t), g in br.groupby(["lang", "task"])}
dump(R, "results_mentions.json")
print(json.dumps(R, indent=0, ensure_ascii=False))
