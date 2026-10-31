import re

from common import *

F = frame()
Q = pd.read_pickle(CACHE / "questions.pkl")
rng = np.random.default_rng(61)
TOK = re.compile(r"[^\s.,!?।'\"():;]+")
VERIF = re.compile(r"verif|double.?check|let me check|check (?:this|by|again)|sanity|alternatively|another way|cross.?check|सत्यापित|जांच|जाँच|पुष्टि|दोबारा|वैकल्पिक|दूसरे तरीके", re.I)
want = {}
for lang in LANGS:
    for kind, name in (("sim", "similar"), ("dis", "dissimilar")):
        s = F[(F.lang == lang) & (F.cond == "cot") & (F.insertion == f"{name}_insertion") & (F[f"men_{kind}"] == True)]
        for i in rng.choice(s.id.to_numpy(), 15, replace=False):
            want[i] = ("mention", kind)
        p = F[(F.lang == lang) & (F.cond == "cot") & (F.insertion == "no_insertion") & (F[f"men_{kind}"] == True)]
        for i in rng.choice(p.id.to_numpy(), 5, replace=False):
            want[i] = ("placebo", kind)
    v = F[(F.lang == lang) & (F.cond == "cot") & (F.verif == True)]
    for i in rng.choice(v.id.to_numpy(), 15, replace=False):
        want[i] = ("verif", None)
rows = []
for lvl in LEVELS:
    for r in json.load(open(ROOT / "responses/standard" / f"{lvl}.json", encoding="utf-8")):
        if r["id"] not in want:
            continue
        kindtag, kind = want[r["id"]]
        m = r["meta"]
        c = r["content"] or ""
        if kindtag == "verif":
            h = VERIF.search(c)
            rows.append({"tag": "verif", "kind": "", "lang": m["language"], "id": r["id"], "sentence": "", "matched": h.group() if h else "", "context": c[max(0, h.start() - 70):h.end() + 70].replace("\n", " ") if h else ""})
            continue
        q = Q[(Q.level == lvl) & (Q.task == m["task"]) & (Q.lang == m["language"]) & (Q.qnum == int(m["question_id"]))].iloc[0]
        txt = q.sim_text if kind == "sim" else q.dis_text
        words = {w for w in TOK.findall(txt.translate(DIG).casefold()) if len(w) >= 3 and not w.isdigit()}
        low = c.translate(DIG).casefold()
        hit = next((w for w in sorted(words, key=len, reverse=True) if w in set(TOK.findall(low))), "")
        pos = low.find(hit) if hit else 0
        rows.append({"tag": kindtag, "kind": kind, "lang": m["language"], "id": r["id"], "sentence": txt, "matched": hit, "context": c[max(0, pos - 80):pos + 80].replace("\n", " ")})
D = pd.DataFrame(rows).sort_values(["lang", "tag", "kind", "id"])
D.to_csv(HAND / "mention_verification_sample.csv", index=False)
for i, r in D.iterrows():
    print(f"[{r.lang} {r.tag} {r.kind}] {r.id.split('/')[1]} | S={r.sentence} | W={r.matched} | {r.context}")
