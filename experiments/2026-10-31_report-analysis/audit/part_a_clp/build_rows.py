import json
import pickle
import re
import sys
from datetime import date
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / "tools" / "temporal-reasoning-dataset" / "src"))
from trd.utils.locale import DAY_NAMES

CACHE = HERE / "cache"
LEVELS = ["short", "medium", "long", "very_long", "very_very_long"]
TASKS = ["date_addition", "date_subtraction", "date_duration", "date_recurrence", "day_of_week",
         "interval_date", "time_addition", "time_subtraction", "time_duration"]
INS = ["no_insertion", "similar_insertion", "dissimilar_insertion"]
COND = {("en_US", "direct"): "en_direct", ("en_US", "cot"): "en_cot", ("hi_IN", "direct"): "hi_direct", ("hi_IN", "cot"): "hi_cot"}
DIGITS = str.maketrans("०१२३४५६७८९", "0123456789")
LABEL = re.compile(r"(?:Answer|उत्तर(?:\s*है)?|जवाब)\s*\**\s*[:：]")
WEEKDAY = {n.casefold(): d for names in DAY_NAMES.values() for d, n in names.items()}
MONTH_LIST = {1: ["january", "जनवरी"], 2: ["february", "फरवरी"], 3: ["march", "मार्च"], 4: ["april", "अप्रैल"], 5: ["may", "मई"],
              6: ["june", "जून"], 7: ["july", "जुलाई"], 8: ["august", "अगस्त"], 9: ["september", "सितंबर", "सितम्बर"],
              10: ["october", "अक्टूबर", "अक्तूबर"], 11: ["november", "नवंबर", "नवम्बर"], 12: ["december", "दिसंबर", "दिसम्बर"]}
MONTH = {n: m for m, ns in MONTH_LIST.items() for n in ns}
MALT = "|".join(sorted(MONTH, key=len, reverse=True))
ISO = re.compile(r"(?<!\d)(\d{4})-(\d{2})-(\d{2})(?!\d)")
DMY = re.compile(rf"(?<!\d)(\d{{1,2}})(?:st|nd|rd|th)?\s+(?:of\s+)?({MALT})(?:,?\s+(\d{{4}})(?!\d))?", re.I)
MDY = re.compile(rf"({MALT})\s+(\d{{1,2}})(?!\d)(?:st|nd|rd|th)?(?:,?\s+(\d{{4}})(?!\d))?", re.I)
TIME = re.compile(r"(?<!\d)(\d{1,2}):(\d{2})(?!\d)")
VER = re.compile(r"verif|double.?check|let me check|check (?:this|by|again)|sanity|alternatively|another way|cross.?check|सत्यापित|जांच|जाँच|पुष्टि|दोबारा|वैकल्पिक|दूसरे तरीके", re.I)
TOK = re.compile(r"[^\s.,!?।'\"():;]+")
STOP = set("""the a an and of to in on at is was for with my i he she it they his her their this that be by as from or are
have has had will would not but you your we our me always many each every how what which there some very just
day days month months year years time times date dates week weeks today hour hours minute minutes
है हैं में की के का को से ने पर और भी यह वह इस उस मैं मुझे मेरा मेरी मेरे हम हमें हमारा था थी थे हूं हूँ हो होता होती
होते जाता जाती जाते रहता रहती रहते करता करती करते कि कितने कैसे हर नहीं चाहिए गया गई लिए साथ बहुत सबसे वाले वाली
रही रहा दिन दिनों महीना महीने महीनों साल वर्ष समय तारीख तारीखें तिथि सप्ताह हफ्ते आज घंटे मिनट""".split())
HI_W = re.compile(r"[ऀ-ॣॱ-ॿ]+")
EN_W = re.compile(r"[A-Za-z]+")
KIND = {"date_addition": "date", "date_subtraction": "date", "date_recurrence": "date", "date_duration": "n", "time_duration": "n",
        "day_of_week": "wd", "interval_date": "iv", "time_addition": "t", "time_subtraction": "t"}


def norm(s):
    return (s or "").translate(DIGITS)


def answer(text):
    text = text or ""
    spans = [m for m in LABEL.finditer(text)]
    good = []
    for m in spans:
        rest = text[m.end():].lstrip()
        if LABEL.match(rest) or rest.startswith(("Answer", "उत्तर", "जवाब")):
            continue
        good.append((m.start(), rest.split("\n")[0]))
    if not good:
        return None, None
    a = re.sub(r"\s+से\s+", " to ", good[-1][1].strip().strip("*`.। ").translate(DIGITS))
    return a, good[-1][0]


def correct(a, gold, task):
    if task == "day_of_week":
        return WEEKDAY.get(a.casefold()) == WEEKDAY[gold.casefold()]
    return a == gold


def d(y, m, dd):
    try:
        return date(int(y), int(m), int(dd))
    except ValueError:
        return None


def parse(kind, s):
    s = norm(s)
    if kind == "date":
        m = ISO.search(s)
        return d(*m.groups()) if m else None
    if kind == "iv":
        ds = [d(*m) for m in ISO.findall(s)]
        return tuple(ds[:2]) if len(ds) >= 2 and None not in ds[:2] else None
    if kind == "n":
        m = re.search(r"-?\d+", s)
        return int(m.group()) if m else None
    if kind == "wd":
        return WEEKDAY.get(s.strip().casefold())
    m = TIME.search(s)
    return int(m[1]) * 60 + int(m[2]) if m else None


def mentions(text):
    text = norm(text)
    f = [(m.start(), m.end(), (int(m[1]), int(m[2]), int(m[3]))) for m in ISO.finditer(text)]
    f += [(m.start(), m.end(), (int(m[3]) if m[3] else None, MONTH[m[2].casefold()], int(m[1]))) for m in DMY.finditer(text)]
    f += [(m.start(), m.end(), (int(m[3]) if m[3] else None, MONTH[m[1].casefold()], int(m[2]))) for m in MDY.finditer(text)]
    out, end = [], -1
    for s, e, v in sorted(f):
        if s >= end:
            out.append((s, v))
            end = e
    return out


def same_date(v, x):
    return (v[1], v[2]) == (x.month, x.day) and v[0] in (None, x.year)


def words(text):
    return {t for t in TOK.findall(norm(text).casefold()) if len(t) >= 3 and t not in STOP and not t.isdigit()}


def toks(text):
    return set(TOK.findall(norm(text).casefold()))


def load_questions(level):
    out = {}
    for task in TASKS:
        en = json.load(open(ROOT / "dataset" / level / f"{task}_en_US.json", encoding="utf-8"))
        hi = json.load(open(ROOT / "dataset" / level / f"{task}_hi_IN.json", encoding="utf-8"))
        for q in en:
            rec = {"answer_en": en[q]["answer"], "answer_hi": hi[q]["answer"]}
            for lang, src in (("en", en[q]), ("hi", hi[q])):
                base = src["no_insertion"]
                rec[lang] = base
                for ins in INS[1:]:
                    rec[f"{lang}_{ins[:3]}"] = src[ins][:-len(base)].strip()
                    rec[f"{lang}_{ins[:3]}_full"] = src[ins]
            out[task, int(q)] = rec
    return out


def distractor_words(qr, kind, langs):
    w = set()
    for lang in langs:
        w |= words(qr[f"{lang}_{kind}"]) - words(qr[lang])
    return w


def mention_flags(body, qr, ins, row, prefix):
    t = toks(body)
    for kind in ("sim", "dis"):
        if ins[:3] not in ("no_", kind):
            continue
        for lang, langs in (("en", ["en"]), ("hi", ["hi"])):
            w = distractor_words(qr, kind, langs)
            row[f"{prefix}m_{kind}_{lang}"] = bool(w & t) if w else None
            row[f"{prefix}w_{kind}_{lang}"] = "|".join(sorted(w & t)) if w else None


def row_for(rec_id, m, content, finish, usage, qr, cond, body_text=None, target="en"):
    task, ins = m["task"], m["insertion"]
    a, pos = answer(content)
    kind = KIND[task]
    gold = m["answer"]
    row = {"level": m["difficulty"], "task": task, "q": int(m["question_id"]), "ins": ins, "cond": cond, "id": rec_id,
           "answer": a, "scored": a is not None, "correct": correct(a, gold, task) if a is not None else None,
           "cutoff": finish == "length", "tokens": (usage or {}).get("completion_tokens")}
    body = (content or "")[:pos] if pos is not None else (content or "")
    row["ver"] = bool(VER.search(body))
    hw, ew = len(HI_W.findall(LABEL.sub("", content or ""))), len(EN_W.findall(LABEL.sub("", content or "")))
    row["hi_words"], row["en_words"] = hw, ew
    if a is not None:
        ga, pa = parse(kind, gold), parse(kind, a)
        row["lenient"] = (pa == ga) if pa is not None else False
        row["parsed"] = pa
        row["gold"] = ga
    if cond.endswith("_cot") or cond in ("clp", "encot"):
        mention_flags(body, qr, ins, row, "")
    return row, body


def stage1_row(rec, qr):
    m = rec["meta"]
    text = rec["stage1"]["content"] or ""
    kind = KIND[m["task"]]
    q_full = qr["hi"] if m["insertion"] == "no_insertion" else qr[f"hi_{m['insertion'][:3]}_full"]
    asked = [d(y or 2000, mo, dd) for _, (y, mo, dd) in mentions(q_full)]
    asked = [a for a in asked if a]
    cand = [(p, v) for p, v in mentions(text) if not any(same_date(v, a) for a in asked)]
    a2, _ = answer(text)
    row = {"s1_tokens": (rec["stage1"].get("usage") or {}).get("completion_tokens"), "s1_cutoff": rec["stage1"]["finish_reason"] == "length",
           "s1_has_date": bool(cand), "s1_last": cand[-1][1] if cand else None, "s1_label_answer": a2,
           "s1_ver": bool(VER.search(text)), "s1_hi_words": len(HI_W.findall(LABEL.sub("", text))), "s1_en_words": len(EN_W.findall(LABEL.sub("", text))),
           "s1_chars": len(text)}
    gold = parse(kind, m["answer"]) if kind == "date" else None
    row["s1_gold"] = bool(cand and gold and same_date(cand[-1][1], gold)) if kind == "date" else None
    row["s1_any_gold"] = bool(gold and any(same_date(v, gold) for _, v in cand)) if kind == "date" else None
    return row, text


def main():
    CACHE.mkdir(exist_ok=True)
    rows, texts, check = [], {}, {"clp_question_match": 0, "clp_question_mismatch": 0, "clp_gold_match": 0, "clp_gold_mismatch": 0,
                                  "std_prompt_has_question": 0, "std_prompt_missing_question": 0, "encot_prompt_has_question": 0, "encot_prompt_missing_question": 0}
    feats = []
    for level in LEVELS:
        qs = load_questions(level)
        for (task, q), r in qs.items():
            feats.append({"level": level, "task": task, "q": q, "en": r["en"], "hi": r["hi"], "en_sim": r["en_sim"], "en_dis": r["en_dis"],
                          "hi_sim": r["hi_sim"], "hi_dis": r["hi_dis"], "answer_en": r["answer_en"], "answer_hi": r["answer_hi"]})
        std = json.load(open(ROOT / "responses" / "standard" / f"{level}.json", encoding="utf-8"))
        for rec in std:
            m = rec["meta"]
            qr = qs[m["task"], int(m["question_id"])]
            cond = COND[m["language"], rec["condition"]]
            row, body = row_for(rec["id"], m, rec["content"], rec["finish_reason"], rec.get("usage"), qr, cond)
            prompt = rec["request"]["messages"][0]["content"]
            lang = m["language"][:2]
            want = qr[lang] if m["insertion"] == "no_insertion" else qr[f"{lang}_{m['insertion'][:3]}_full"]
            check["std_prompt_has_question" if want in prompt else "std_prompt_missing_question"] += 1
            rows.append(row)
            if int(m["question_id"]) < 50 and cond in ("en_cot", "hi_cot", "hi_direct", "en_direct"):
                texts[cond, level, m["task"], int(m["question_id"]), m["insertion"]] = rec["content"]
        del std
        clp = json.load(open(ROOT / "responses" / "clp" / f"{level}.json", encoding="utf-8"))
        for rec in clp:
            m = rec["meta"]
            qr = qs[m["task"], int(m["question_id"])]
            want = qr["hi"] if m["insertion"] == "no_insertion" else qr[f"hi_{m['insertion'][:3]}_full"]
            check["clp_question_match" if want in rec["stage1"]["message"] else "clp_question_mismatch"] += 1
            check["clp_gold_match" if m["answer"] == qr["answer_hi"] else "clp_gold_mismatch"] += 1
            row, body = row_for(rec["id"], m, rec["stage2"]["content"], rec["stage2"]["finish_reason"], rec["stage2"].get("usage"), qr, "clp")
            s1, text = stage1_row(rec, qr)
            row.update(s1)
            for kind in ("sim", "dis"):
                if m["insertion"][:3] in ("no_", kind):
                    t = toks(text)
                    a, pos = answer(text)
                    t_body = toks(text[:pos] if pos is not None else text)
                    for lang in ("en", "hi"):
                        w = distractor_words(qr, kind, [lang])
                        row[f"s1m_{kind}_{lang}"] = bool(w & t) if w else None
                        row[f"s1bm_{kind}_{lang}"] = bool(w & t_body) if w else None
                        row[f"s1w_{kind}_{lang}"] = "|".join(sorted(w & t)) if w else None
            rows.append(row)
            texts["s1", level, m["task"], int(m["question_id"]), m["insertion"]] = text
            texts["s2", level, m["task"], int(m["question_id"]), m["insertion"]] = rec["stage2"]["content"]
        del clp
        enc = json.load(open(ROOT / "responses" / "en-cot" / f"{level}.json", encoding="utf-8"))
        for rec in enc:
            m = rec["meta"]
            qr = qs[m["task"], int(m["question_id"])]
            want = qr["hi"] if m["insertion"] == "no_insertion" else qr[f"hi_{m['insertion'][:3]}_full"]
            check["encot_prompt_has_question" if want in rec["request"]["messages"][0]["content"] else "encot_prompt_missing_question"] += 1
            row, body = row_for(rec["id"], m, rec["content"], rec["finish_reason"], rec.get("usage"), qr, "encot")
            rows.append(row)
            texts["encot", level, m["task"], int(m["question_id"]), m["insertion"]] = rec["content"]
        del enc
        print(level, len(rows), flush=True)
    with open(CACHE / "rows.pkl", "wb") as f:
        pickle.dump(rows, f)
    with open(CACHE / "texts.pkl", "wb") as f:
        pickle.dump(texts, f)
    with open(CACHE / "feats.pkl", "wb") as f:
        pickle.dump(feats, f)
    json.dump(check, open(HERE / "data_checks.json", "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    print(check)


if __name__ == "__main__":
    main()
