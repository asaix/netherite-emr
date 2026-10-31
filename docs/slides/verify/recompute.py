import json
import re
import sys
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
LEVELS = ["short", "medium", "long", "very_long", "very_very_long"]
DIG = str.maketrans("०१२३४५६७८९", "0123456789")
LABEL = re.compile(r"(?:\banswer\b|उत्तर|जवाब)(?:\s*है)?\s*\**\s*[:：]", re.I)
ISO = re.compile(r"\d{4}-\d{1,2}-\d{1,2}")
DAYS = {"monday": 0, "सोमवार": 0, "tuesday": 1, "मंगलवार": 1, "wednesday": 2, "बुधवार": 2, "thursday": 3, "गुरुवार": 3, "गुरूवार": 3, "बृहस्पतिवार": 3, "friday": 4, "शुक्रवार": 4, "saturday": 5, "शनिवार": 5, "sunday": 6, "रविवार": 6}
JANUARY = ("The last time I had a weekly commitment was in January", "आखिरी साप्ताहिक प्रतिबद्धता जनवरी")


def answer_text(text):
    t = (text or "").translate(DIG)
    hits = list(LABEL.finditer(t))
    if not hits:
        return None
    rest = t[hits[-1].end():].strip(" *`_\t\n")
    return rest.split("\n")[0].strip(" *`_.।,\"'\t") or None


def iso(s):
    y, m, d = map(int, s.split("-"))
    try:
        return date(y, m, d).isoformat()
    except ValueError:
        return None


def correct(task, raw, gold):
    if raw is None:
        return False
    if task in ("date_addition", "date_subtraction", "date_recurrence"):
        m = ISO.search(raw)
        return bool(m) and iso(m.group()) == gold
    if task == "interval_date":
        got = [iso(x) for x in ISO.findall(raw)]
        return len(got) >= 2 and f"{got[0]} to {got[1]}" == gold
    if task == "day_of_week":
        low = raw.lower()
        found = [v for k, v in DAYS.items() if k in low]
        return bool(found) and found[0] == DAYS.get(gold.lower(), DAYS.get(gold))
    if task in ("time_addition", "time_subtraction"):
        m = re.search(r"(\d{1,2})[:.](\d{2})", raw)
        return bool(m) and f"{int(m[1]):02d}:{m[2]}" == gold
    h = re.search(r"(\d+)\s*(?:hours?|hrs?|घंटे|घंटा)\s*(?:and|और|,)?\s*(\d+)\s*(?:minutes?|mins?|मिनट)", raw, re.I)
    if h and task == "time_duration":
        return str(int(h[1]) * 60 + int(h[2])) == str(gold)
    m = re.search(r"-?\d+", raw)
    return bool(m) and m.group() == str(gold)


def question(r):
    return r["request"]["messages"][-1]["content"] if "request" in r else ""


rows = []
for source in ["standard", "en-cot", "clp", "hinglish"]:
    for level in LEVELS:
        for r in json.loads((ROOT / "responses" / source / f"{level}.json").read_text()):
            m = r["meta"]
            if source == "clp":
                stage = r["stage2"]
                text, q, cond = stage["content"], r["stage1"]["message"] if isinstance(r["stage1"].get("message"), str) else json.dumps(r["stage1"]["request"], ensure_ascii=False), "clp"
            else:
                text, q, cond = r["content"], question(r), r["condition"]
            raw = answer_text(text)
            rows.append(dict(source=source, cond=cond, level=m["difficulty"], task=m["task"], lang=m["language"], q=int(m["question_id"]), ins=m["insertion"], scored=raw is not None, correct=correct(m["task"], raw, m["answer"]), january=any(j in q for j in JANUARY)))
d = pd.DataFrame(rows)


def acc(x, strict=False):
    x = x if strict else x[x.scored]
    return round(100 * x.correct.mean(), 2)


s = d[d.source == "standard"]
sub = s[s.q < 50]
res = {"counts": d.groupby(["source", "lang", "cond"]).size().rename(lambda x: x).reset_index().astype(str).values.tolist()}
for name, frame in [("full", s), ("subset", sub)]:
    res[name] = {f"{l} {c}": {"answered": acc(frame[(frame.lang == l) & (frame.cond == c)]), "strict": acc(frame[(frame.lang == l) & (frame.cond == c)], True)} for l in ["en_US", "hi_IN"] for c in ["direct", "cot"]}
res["subset"]["en-cot"] = {"answered": acc(d[d.source == "en-cot"]), "strict": acc(d[d.source == "en-cot"], True)}
res["subset"]["clp"] = {"answered": acc(d[d.source == "clp"]), "strict": acc(d[d.source == "clp"], True)}
for l in ["en_US", "hi_IN"]:
    x = d[(d.source == "hinglish") & (d.lang == l)]
    res["subset"][f"hinglish {l}"] = {"answered": acc(x), "strict": acc(x, True)}


def cell(frame, **f):
    for k, v in f.items():
        frame = frame[frame[k] == v]
    return frame


res["tasks_subset"] = {t: {f"{l} {c}": acc(cell(sub, task=t, lang=l, cond=c)) for l in ["en_US", "hi_IN"] for c in ["direct", "cot"]} for t in s.task.unique()}
res["hindi_no_distractor_full"] = {t: round(acc(cell(s, task=t, lang="hi_IN", cond="cot", ins="no_insertion")) - acc(cell(s, task=t, lang="hi_IN", cond="direct", ins="no_insertion")), 2) for t in ["date_subtraction", "interval_date"]}
res["hindi_pooled_full"] = {t: round(acc(cell(s, task=t, lang="hi_IN", cond="cot")) - acc(cell(s, task=t, lang="hi_IN", cond="direct")), 2) for t in ["date_subtraction", "interval_date"]}
res["gap_by_level_full"] = {l: round(acc(cell(s, level=l, lang="en_US", cond="cot")) - acc(cell(s, level=l, lang="hi_IN", cond="cot")), 2) for l in LEVELS}
drop = lambda lang, cond: round(acc(cell(s, lang=lang, cond=cond, ins="no_insertion")) - acc(cell(s, lang=lang, cond=cond, ins="similar_insertion")), 2)
res["time_distractor_drop_full"] = {"hi cot": drop("hi_IN", "cot"), "hi direct": drop("hi_IN", "direct"), "en cot": drop("en_US", "cot"), "en direct": drop("en_US", "direct")}
j = s[(s.task == "date_recurrence") & (s.cond == "cot") & s.january]
base = s[(s.task == "date_recurrence") & (s.cond == "cot") & (s.ins == "no_insertion")].set_index(["level", "q", "lang"])
keys = j[["level", "q", "lang"]].drop_duplicates()
res["january"] = {"questions_per_lang": keys.groupby("lang").size().to_dict()}
for l in ["en_US", "hi_IN"]:
    with_j = j[j.lang == l]
    ref = base.loc[[(a, b, l) for a, b in zip(with_j.level, with_j.q)]]
    res["january"][l] = {"n": len(with_j), "strict_with": acc(with_j, True), "strict_without": acc(ref.reset_index(), True), "cutoffs_with": int((~with_j.scored).sum()), "cutoffs_without": int((~ref.scored).sum())}
(OUT / "recomputed.json").write_text(json.dumps(res, indent=2, ensure_ascii=False))
print(json.dumps(res, indent=1, ensure_ascii=False)[:6000])
