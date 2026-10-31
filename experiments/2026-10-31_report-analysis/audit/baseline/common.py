import json
import re
import sys
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / "tools" / "temporal-reasoning-dataset" / "src"))
CACHE = HERE / "cache"
FIG = HERE / "fig_data"
HAND = HERE / "hand_review"
LEVELS = ["short", "medium", "long", "very_long", "very_very_long"]
TASKS = ["date_addition", "date_subtraction", "date_duration", "date_recurrence", "day_of_week", "interval_date", "time_addition", "time_subtraction", "time_duration"]
LANGS = ["en_US", "hi_IN"]
INS = ["no_insertion", "similar_insertion", "dissimilar_insertion"]
TPL_KEY = {"date_addition": "addition_date", "date_subtraction": "subtraction_date", "date_duration": "duration_date", "date_recurrence": "recurrence_date", "day_of_week": "day_of_week", "interval_date": "interval_date", "time_addition": "addition_time", "time_subtraction": "subtraction_time", "time_duration": "duration_time"}
DIG = str.maketrans("०१२३४५६७८९٠١٢٣٤٥٦٧٨٩", "0123456789" * 2)
HI_DAYS = {"सोमवार": 0, "मंगलवार": 1, "मंगल": 1, "बुधवार": 2, "बुध": 2, "गुरुवार": 3, "गुरूवार": 3, "बृहस्पतिवार": 3, "वीरवार": 3, "शुक्रवार": 4, "शुक्र": 4, "शनिवार": 5, "शनिचर": 5, "रविवार": 6, "इतवार": 6}
EN_DAYS = {d: i for i, d in enumerate(["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"])}
MONTHS = {"january": 1, "february": 2, "march": 3, "april": 4, "may": 5, "june": 6, "july": 7, "august": 8, "september": 9, "october": 10, "november": 11, "december": 12, "जनवरी": 1, "फरवरी": 2, "फ़रवरी": 2, "मार्च": 3, "अप्रैल": 4, "मई": 5, "जून": 6, "जुलाई": 7, "अगस्त": 8, "सितंबर": 9, "सितम्बर": 9, "अक्टूबर": 10, "अक्तूबर": 10, "नवंबर": 11, "नवम्बर": 11, "दिसंबर": 12, "दिसम्बर": 12}
MON_ALT = "|".join(sorted(MONTHS, key=len, reverse=True))
ISO = re.compile(r"(?<!\d)(\d{4})\s*[-/.]\s*(\d{1,2})\s*[-/.]\s*(\d{1,2})(?!\d)")
DMY = re.compile(r"(?<!\d)(\d{1,2})[-/.](\d{1,2})[-/.](\d{4})(?!\d)")
DMON = re.compile(rf"(?<!\d)(\d{{1,2}})(?:st|nd|rd|th)?\s+(?:of\s+)?({MON_ALT}),?\s+(\d{{4}})(?!\d)", re.I)
MOND = re.compile(rf"({MON_ALT})\s+(\d{{1,2}})(?:st|nd|rd|th)?,?\s+(\d{{4}})(?!\d)", re.I)
CLOCK = re.compile(r"(?<!\d)(\d{1,2})[:.](\d{2})(?::\d{2})?\s*(am|pm|a\.m\.?|p\.m\.?|बजे)?", re.I)
LABEL = re.compile(r"(?:\banswer\b|उत्तर|जवाब)(?:\s*है)?\s*\**\s*[:：]", re.I)
DEV_WORD = re.compile(r"[ऀ-ॣॱ-ॿ]+")
LAT_WORD = re.compile(r"[A-Za-z]+")


def mkdate(y, m, d):
    try:
        return date(int(y), int(m), int(d))
    except ValueError:
        return None


def all_dates(t):
    found = []
    for m in ISO.finditer(t):
        found.append((m.start(), mkdate(m[1], m[2], m[3])))
    for m in DMON.finditer(t):
        found.append((m.start(), mkdate(m[3], MONTHS[m[2].lower()], m[1])))
    for m in MOND.finditer(t):
        found.append((m.start(), mkdate(m[3], MONTHS[m[1].lower()], m[2])))
    for m in DMY.finditer(t):
        found.append((m.start(), mkdate(m[3], m[2], m[1])))
    return [d for _, d in sorted(found, key=lambda x: x[0]) if d]


def my_extract(content):
    text = (content or "").translate(DIG)
    hits = list(LABEL.finditer(text))
    if not hits:
        return None, False
    h = hits[-1]
    rest = text[h.end():]
    lines = rest.split("\n")
    first = lines[0].strip(" *`_\t")
    if not first:
        for ln in lines[1:]:
            if ln.strip(" *`_\t"):
                first = ln.strip(" *`_\t")
                break
    tail_lines = [ln for ln in text.split("\n") if ln.strip()]
    on_last = bool(tail_lines) and bool(LABEL.search(tail_lines[-1]))
    return first.strip(" *`_.।,\"'\t"), on_last


def typed(task, raw):
    if raw is None:
        return None
    t = raw.translate(DIG)
    if task in ("date_addition", "date_subtraction", "date_recurrence"):
        ds = all_dates(t)
        return ds[0].isoformat() if ds else None
    if task == "interval_date":
        ds = all_dates(t)
        return f"{ds[0].isoformat()} to {ds[1].isoformat()}" if len(ds) >= 2 else None
    if task in ("time_addition", "time_subtraction"):
        m = CLOCK.search(t)
        if not m:
            return None
        h, mi = int(m[1]), int(m[2])
        suf = (m[3] or "").lower().replace(".", "")
        if suf == "pm" and h < 12:
            h += 12
        if suf == "am" and h == 12:
            h = 0
        return f"{h:02d}:{mi:02d}" if h < 24 and mi < 60 else None
    if task == "time_duration":
        m = re.search(r"(\d+)\s*(?:hours?|hrs?|घंटे|घंटा)\s*(?:and|और|,)?\s*(\d+)\s*(?:minutes?|mins?|मिनट)", t, re.I)
        if m:
            return str(int(m[1]) * 60 + int(m[2]))
        m = re.search(r"-?\d+", t)
        return str(int(m.group())) if m else None
    if task == "date_duration":
        m = re.search(r"-?\d+", t)
        return str(int(m.group())) if m else None
    low = t.lower()
    for name, i in EN_DAYS.items():
        if name in low:
            return i
    for name in sorted(HI_DAYS, key=len, reverse=True):
        if name in t:
            return HI_DAYS[name]
    return None


def gold_typed(task, gold):
    if task == "day_of_week":
        return EN_DAYS.get(gold.lower(), HI_DAYS.get(gold))
    return gold


def parse_question(task, q):
    q = q.translate(DIG)
    nums = re.findall(r"\d{4}-\d{2}-\d{2}|\d{1,2}:\d{2}|\d+", q)
    if task in ("date_addition", "date_subtraction"):
        return {"today": nums[0], "n": int(nums[1])}
    if task == "date_recurrence":
        return {"today": nums[0], "every": int(nums[1]), "k": int(nums[2])}
    if task == "date_duration":
        iso = re.findall(r"\d{4}-\d{2}-\d{2}", q)
        return {"a": iso[0], "b": iso[1]}
    if task == "day_of_week":
        return {"d": nums[0]}
    if task == "interval_date":
        return {"today": nums[0]}
    if task in ("time_addition", "time_subtraction"):
        return {"t": nums[0], "h": int(nums[1]), "m": int(nums[2])}
    return {"a": nums[0], "b": nums[1]}


def compute_gold(task, p):
    if task in ("date_addition", "date_subtraction", "date_recurrence", "interval_date"):
        t = date.fromisoformat(p["today"])
    if task == "date_addition":
        return (t + timedelta(days=p["n"])).isoformat()
    if task == "date_subtraction":
        return (t - timedelta(days=p["n"])).isoformat()
    if task == "date_recurrence":
        return (t + timedelta(days=p["every"] * p["k"])).isoformat()
    if task == "date_duration":
        return str((date.fromisoformat(p["b"]) - date.fromisoformat(p["a"])).days)
    if task == "day_of_week":
        return date.fromisoformat(p["d"]).weekday()
    if task == "interval_date":
        s = t + timedelta(days=7 - t.weekday())
        return f"{s.isoformat()} to {(s + timedelta(days=6)).isoformat()}"
    h, m = map(int, (p["t"] if "t" in p else p["a"]).split(":"))
    a = h * 60 + m
    if task == "time_addition":
        v = (a + p["h"] * 60 + p["m"]) % 1440
    elif task == "time_subtraction":
        v = (a - p["h"] * 60 - p["m"]) % 1440
    else:
        h2, m2 = map(int, p["b"].split(":"))
        return str((h2 * 60 + m2 - a) % 1440)
    return f"{v // 60:02d}:{v % 60:02d}"


def frame():
    return pd.read_pickle(CACHE / "frame.pkl")


def dump(obj, name):
    with open(HERE / name, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2, default=float)
