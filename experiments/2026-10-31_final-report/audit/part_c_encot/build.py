import gc
import json
import re
import sys
from datetime import date
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent
DIFFS = ["short", "medium", "long", "very_long", "very_very_long"]
TASKS = ["date_addition", "date_subtraction", "date_duration", "date_recurrence", "day_of_week",
         "interval_date", "time_addition", "time_subtraction", "time_duration"]
KIND = {"date_addition": "date", "date_subtraction": "date", "date_recurrence": "date", "date_duration": "days",
        "time_duration": "minutes", "day_of_week": "weekday", "interval_date": "interval",
        "time_addition": "time", "time_subtraction": "time"}
ANSWER = re.compile(r"(?:Answer|उत्तर(?:\s*है)?|जवाब)\s*\**\s*[:：]\s*(?!Answer|उत्तर|जवाब)(.*)")
DIGITS = str.maketrans("०१२३४५६७८९٠١٢٣٤٥٦٧٨٩", "0123456789" * 2)
WEEK = {"monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3, "friday": 4, "saturday": 5, "sunday": 6,
        "सोमवार": 0, "मंगलवार": 1, "बुधवार": 2, "गुरुवार": 3, "शुक्रवार": 4, "शनिवार": 5, "रविवार": 6}
ISO = re.compile(r"(?<!\d)(\d{4})-(\d{2})-(\d{2})(?!\d)")
TIME = re.compile(r"(?<!\d)(\d{1,2}):(\d{2})(?!\d)")
VERIF = re.compile(r"verif|double.?check|let me check|check (?:this|by|again)|sanity|alternatively|another way|cross.?check|सत्यापित|जांच|जाँच|पुष्टि|दोबारा|वैकल्पिक|दूसरे तरीके", re.I)
VERIF_WIDE = re.compile(VERIF.pattern + r"|सत्यापन|फिर से|चेक|पुनः|वेरिफ", re.I)
TOKEN = re.compile(r"[^\s.,!?।'\"():;]+")
DEV = re.compile(r"[ऀ-ॣॱ-ॿ]")
LAT = re.compile(r"[A-Za-z]")
HIW = re.compile(r"[ऀ-ॣॱ-ॿ]+")
ENW = re.compile(r"[A-Za-z]+")
STOP = set("""the a an and of to in on at is was for with my i he she it they his her their this that be by as from or are
have has had will would not but you your we our me always many each every how what which there some very just
day days month months year years time times date dates week weeks today hour hours minute minutes
है हैं में की के का को से ने पर और भी यह वह इस उस मैं मुझे मेरा मेरी मेरे हम हमें हमारा था थी थे हूं हूँ हो होता होती
होते जाता जाती जाते रहता रहती रहते करता करती करते कि कितने कैसे हर नहीं चाहिए गया गई लिए साथ बहुत सबसे वाले वाली
रही रहा दिन दिनों महीना महीने महीनों साल वर्ष समय तारीख तारीखें तिथि सप्ताह हफ्ते आज घंटे मिनट""".split())


def norm(t):
    return (t or "").translate(DIGITS)


def extract(content):
    m = ANSWER.findall(content or "")
    return re.sub(r"\s+से\s+", " to ", m[-1].strip().strip("*`.। ").translate(DIGITS)) if m else None


def body_of(content):
    content = content or ""
    m = list(ANSWER.finditer(content))
    return content[:m[-1].start()] if m else content


def words(text):
    return {t for t in TOKEN.findall(norm(text).casefold()) if len(t) >= 3 and t not in STOP and not t.isdigit()}


def d_(s):
    try:
        return date(*map(int, s))
    except ValueError:
        return None


def parse(kind, text):
    text = norm(text)
    if kind == "date":
        m = ISO.search(text)
        return d_(m.groups()) if m else None
    if kind == "interval":
        x = [d_(m) for m in ISO.findall(text)]
        return tuple(x[:2]) if len(x) >= 2 and None not in x[:2] else None
    if kind in ("days", "minutes"):
        m = re.search(r"-?\d+", text)
        return int(m.group()) if m else None
    if kind == "weekday":
        return WEEK.get(text.strip().casefold())
    m = TIME.search(text)
    return int(m[1]) * 60 + int(m[2]) if m else None


def classify(kind, a, g, q):
    if a is None:
        return "invalid"
    if a == g:
        return "format_only"
    if kind == "date":
        p = ISO.search(norm(q))
        t = d_(p.groups())
        if (a - t).days == -(g - t).days:
            return "wrong_direction"
        return "off_by_one" if abs((a - g).days) == 1 else "other"
    if kind == "interval":
        s = [(x - y).days for x, y in zip(a, g)]
        if s[0] == s[1] and s[0] % 7 == 0:
            return "week_shift"
        return "off_by_one" if all(abs(v) <= 1 for v in s) else "other"
    if kind == "weekday":
        return "off_by_one" if abs((a - g + 3) % 7 - 3) == 1 else "other"
    if kind == "time":
        p = TIME.search(norm(q))
        t = int(p[1]) * 60 + int(p[2])
        if (a - t) % 1440 == (t - g) % 1440:
            return "wrong_direction"
        e = (a - g + 720) % 1440 - 720
        return "off_by_one" if abs(e) == 1 else "off_by_one_hour" if abs(e) == 60 else "other"
    if kind == "minutes" and a and (a * 60 == g or a == g * 60):
        return "unit_confusion"
    if abs(a - g) == 1:
        return "off_by_one"
    return "off_by_one_hour" if kind == "minutes" and abs(a - g) == 60 else "other"


def load_dataset(diff):
    out = {}
    for task in TASKS:
        for lang in ("en_US", "hi_IN"):
            out[task, lang] = json.load(open(ROOT / "dataset" / diff / f"{task}_{lang}.json", encoding="utf-8"))
    return out


def row(r, ds, source, content, reasoning, usage, finish, request, time):
    m = r["meta"]
    task, lang, ins, qn = m["task"], m["language"], m["insertion"], m["question_id"]
    q = ds[task, lang][str(qn)]
    base = q["no_insertion"]
    kind = KIND[task]
    ans = extract(content)
    scored = ans is not None
    gold = m["answer"]
    if task == "day_of_week":
        correct = scored and WEEK.get(ans.casefold()) == WEEK[gold.casefold()]
    else:
        correct = scored and ans == gold
    a, g = (parse(kind, ans), parse(kind, gold)) if scored else (None, None)
    body = body_of(content)
    rec = {"source": source, "id": r["id"], "difficulty": m["difficulty"], "task": task, "qn": int(qn), "lang": lang, "ins": ins,
           "cond": r["condition"], "finish": finish, "ctok": (usage or {}).get("completion_tokens"),
           "rtok": ((usage or {}).get("completion_tokens_details") or {}).get("reasoning_tokens"),
           "scored": scored, "correct": bool(correct), "answer": ans, "date": (time or "")[:10],
           "n_answers": len(ANSWER.findall(content or "")), "prompt_match": norm(q[ins]).strip() in norm(request).strip() if request else None,
           "gold_match": gold == q["answer"], "verif": bool(VERIF.search(body)), "verif_wide": bool(VERIF_WIDE.search(body)),
           "c_dev": len(DEV.findall(body)), "c_lat": len(LAT.findall(body)), "c_hiw": len(HIW.findall(body)), "c_enw": len(ENW.findall(body)),
           "r_dev": len(DEV.findall(reasoning or "")), "r_lat": len(LAT.findall(reasoning or "")),
           "r_hiw": len(HIW.findall(reasoning or "")), "r_enw": len(ENW.findall(reasoning or "")), "r_verif": bool(VERIF.search(reasoning or "")),
           "err": None, "wk_off": None, "wk_ans": None, "wk_gold": None, "rec_k": None, "rec_every": None, "rec_pattern": None, "rec_offset": None}
    if scored and not correct:
        rec["err"] = classify(kind, a, g, base)
    if task == "day_of_week" and scored and a is not None:
        rec["wk_off"] = (a - g + 3) % 7 - 3
        rec["wk_ans"], rec["wk_gold"] = a, g
    if task == "date_recurrence":
        n = norm(base)
        k = re.search(r"the (\d+) occurrence|(\d+)वीं", n)
        ev = re.search(r"every (\d+) day|हर (\d+) दिन", n)
        rec["rec_k"] = int(next(x for x in k.groups() if x))
        rec["rec_every"] = int(next(x for x in ev.groups() if x))
        if scored and a is not None:
            off = (a - d_(ISO.search(n).groups())).days
            rec["rec_offset"] = off
            full = rec["rec_k"] * rec["rec_every"]
            rec["rec_pattern"] = "correct" if off == full else "mirror" if off == -full else "first_step" if off == rec["rec_every"] else "other"
    tokens = set(TOKEN.findall(norm(body).casefold()))
    for name, key in (("similar", "similar_insertion"), ("dissimilar", "dissimilar_insertion")):
        if ins not in ("no_insertion", key):
            continue
        hq = ds[task, "hi_IN"][str(qn)]
        eq = ds[task, "en_US"][str(qn)]
        hd = hq[key][:-len(hq["no_insertion"])] if hq[key].endswith(hq["no_insertion"]) else hq[key]
        ed = eq[key][:-len(eq["no_insertion"])] if eq[key].endswith(eq["no_insertion"]) else eq[key]
        hw = words(hd) - words(hq["no_insertion"])
        ew = words(ed) - words(eq["no_insertion"])
        own = hw if lang == "hi_IN" else ew
        rec[f"m_{name}_own"] = bool(own & tokens) if own else None
        hw2 = hw - words(eq["no_insertion"])
        ew2 = ew - words(hq["no_insertion"])
        rec[f"m_{name}_hi"] = bool(hw2 & tokens) if hw2 else None
        rec[f"m_{name}_en"] = bool(ew2 & tokens) if ew2 else None
        u = hw2 | ew2
        rec[f"m_{name}_both"] = bool(u & tokens) if u else None
        rec[f"m_{name}_hw"] = len(hw2)
        rec[f"m_{name}_ew"] = len(ew2)
    if ins != "no_insertion":
        tail = q[ins]
        rec["sentence"] = tail[:-len(base)].strip() if tail.endswith(base) else tail
    return rec


def run():
    rows = []
    for diff in DIFFS:
        ds = load_dataset(diff)
        for source in ("standard", "en-cot", "clp", "ron", "hinglish"):
            for r in json.load(open(ROOT / "responses" / source / f"{diff}.json", encoding="utf-8")):
                if source == "clp":
                    s1, s2 = r["stage1"], r["stage2"]
                    x = row(r, ds, source, s2["content"], s2.get("reasoning_content"), s2.get("usage"), s2.get("finish_reason"),
                            s1["request"]["messages"][0]["content"], s2.get("time"))
                    x["ctok"] = ((s1.get("usage") or {}).get("completion_tokens") or 0) + ((s2.get("usage") or {}).get("completion_tokens") or 0)
                    x["verif_s1"] = bool(VERIF.search(s1.get("content") or ""))
                else:
                    x = row(r, ds, source, r["content"], r.get("reasoning_content"), r.get("usage"), r.get("finish_reason"),
                            r["request"]["messages"][-1]["content"], r.get("time"))
                rows.append(x)
            gc.collect()
        print(diff, len(rows), flush=True)
    df = pd.DataFrame(rows)
    (OUT / "cache").mkdir(exist_ok=True)
    df.to_pickle(OUT / "cache" / "tidy.pkl")
    print(df.groupby(["source", "lang", "cond"]).size())


if __name__ == "__main__":
    run()
