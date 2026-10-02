import json
import re
import sys
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "tools" / "temporal-reasoning-dataset" / "src"))
sys.path.insert(0, str(HERE))

import metrics as M

KIND = {
    "date_addition": "date",
    "date_subtraction": "date",
    "date_recurrence": "date",
    "date_duration": "days",
    "time_duration": "minutes",
    "day_of_week": "weekday",
    "interval_date": "interval",
    "time_addition": "time",
    "time_subtraction": "time",
}
MONTH_NAMES = {
    1: ["january", "जनवरी"],
    2: ["february", "फरवरी"],
    3: ["march", "मार्च"],
    4: ["april", "अप्रैल"],
    5: ["may", "मई"],
    6: ["june", "जून"],
    7: ["july", "जुलाई"],
    8: ["august", "अगस्त"],
    9: ["september", "सितंबर", "सितम्बर"],
    10: ["october", "अक्टूबर", "अक्तूबर"],
    11: ["november", "नवंबर", "नवम्बर"],
    12: ["december", "दिसंबर", "दिसम्बर"],
}
MONTHS = {name: number for number, names in MONTH_NAMES.items() for name in names}
NUMBER_WORDS = {"seven": 7, "सात": 7}
MONTH_ALT = "|".join(sorted(MONTHS, key=len, reverse=True))
WEEKDAY_ALT = "|".join(sorted(map(re.escape, M.WEEKDAYS), key=len, reverse=True))
ISO = re.compile(r"(?<!\d)(\d{4})-(\d{2})-(\d{2})(?!\d)")
TIME = re.compile(r"(?<!\d)(\d{1,2}):(\d{2})(?!\d)")
DAY_FIRST = re.compile(rf"(?<!\d)(\d{{1,2}})(?:st|nd|rd|th)?\s+(?:of\s+)?({MONTH_ALT})(?:,?\s+(\d{{4}})(?!\d))?", re.I)
MONTH_FIRST = re.compile(rf"({MONTH_ALT})\s+(\d{{1,2}})(?!\d)(?:st|nd|rd|th)?(?:,?\s+(\d{{4}})(?!\d))?", re.I)
WEEKDAY = re.compile(WEEKDAY_ALT, re.I)
VERIFICATION = re.compile(r"verif|double.?check|let me check|check (?:this|by|again)|sanity|alternatively|another way|cross.?check|सत्यापित|जांच|जाँच|पुष्टि|दोबारा|वैकल्पिक|दूसरे तरीके", re.I)
TOKEN = re.compile(r"[^\s.,!?।'\"():;]+")
FEATURE_OF = {
    "year": "numbers",
    "day": "numbers",
    "number": "numbers",
    "minute": "numbers",
    "hour": "hours",
    "month": "months",
    "weekday": "weekdays",
}


def load_records():
    return json.load(open(HERE.parent / "1-10-26_analysis_rahul" / "merged_results.json", encoding="utf-8"))


def normalise(text):
    return (text or "").translate(M.DIGITS)


def tail(record):
    return record["request"]["messages"][0]["content"].split("\n\n")[-1]


def question_key(record):
    m = record["meta"]
    return m["difficulty"], m["task"], m["language"], m["question_id"]


def question_texts(records):
    return {question_key(r): tail(r) for r in records if r["meta"]["insertion"] == "no_insertion"}


def distractor_texts(records):
    base = question_texts(records)
    return {
        (question_key(r), r["meta"]["insertion"]): tail(r)[: -len(base[question_key(r)])].strip()
        for r in records
        if r["meta"]["insertion"] != "no_insertion"
    }


def to_date(year, month, day):
    try:
        return date(int(year), int(month), int(day))
    except ValueError:
        return None


def parse(kind, text):
    text = normalise(text)
    if kind == "date":
        m = ISO.search(text)
        return to_date(*m.groups()) if m else None
    if kind == "interval":
        dates = [to_date(*m) for m in ISO.findall(text)]
        return tuple(dates[:2]) if len(dates) >= 2 and None not in dates[:2] else None
    if kind in ("days", "minutes"):
        m = re.search(r"-?\d+", text)
        return int(m.group()) if m else None
    if kind == "weekday":
        return M.WEEKDAYS.get(text.strip().casefold())
    m = TIME.search(text)
    return int(m.group(1)) * 60 + int(m.group(2)) if m else None


def pivot(kind, question):
    question = normalise(question)
    if kind == "time":
        m = TIME.search(question)
        return int(m.group(1)) * 60 + int(m.group(2)) if m else None
    m = ISO.search(question)
    return to_date(*m.groups()) if m else None


def judged(records):
    for r in M.answered(records):
        kind = KIND[r["meta"]["task"]]
        yield r, kind, parse(kind, M.extract_answer(r["content"])), parse(kind, r["meta"]["answer"])


def distractor_features(text):
    text = normalise(text).casefold()
    tokens = TOKEN.findall(text)
    numbers = {int(n) for n in re.findall(r"\d+", text)} | {NUMBER_WORDS[t] for t in tokens if t in NUMBER_WORDS}
    return {
        "numbers": numbers,
        "hours": numbers | {n + 12 for n in numbers if n < 12},
        "months": {MONTHS[t] for t in tokens if t in MONTHS},
        "weekdays": {M.WEEKDAYS[t] for t in tokens if t in M.WEEKDAYS},
    }


def components(kind, value):
    if kind == "date":
        return [("year", value.year), ("month", value.month), ("day", value.day)]
    if kind == "interval":
        return [(f"{side}_{name}", v) for side, d in zip(("start", "end"), value) for name, v in components("date", d)]
    if kind == "time":
        return [("hour", value // 60), ("minute", value % 60)]
    return [({"days": "number", "minutes": "number", "weekday": "weekday"}[kind], value)]


def reuses_distractor(kind, answer, gold, features):
    return any(
        a != g and a in features[FEATURE_OF[name.rsplit("_", 1)[-1]]]
        for (name, a), (_, g) in zip(components(kind, answer), components(kind, gold))
    )


def date_mentions(text):
    text = normalise(text)
    found = [(m.start(), m.end(), (int(m[1]), int(m[2]), int(m[3]))) for m in ISO.finditer(text)]
    found += [
        (m.start(), m.end(), (int(m[3]) if m[3] else None, MONTHS[m[2].casefold()], int(m[1])))
        for m in DAY_FIRST.finditer(text)
    ]
    found += [
        (m.start(), m.end(), (int(m[3]) if m[3] else None, MONTHS[m[1].casefold()], int(m[2])))
        for m in MONTH_FIRST.finditer(text)
    ]
    mentions, end = [], -1
    for start, stop, value in sorted(found):
        if start >= end:
            mentions.append(value)
            end = stop
    return mentions


def strip_dates_and_times(text):
    text = DAY_FIRST.sub(" ", MONTH_FIRST.sub(" ", TIME.sub(" ", ISO.sub(" ", text))))
    return text


def reasoning_candidates(kind, body, question):
    body = normalise(body)
    if kind == "weekday":
        return [M.WEEKDAYS[m.group().casefold()] for m in WEEKDAY.finditer(body)]
    if kind in ("days", "minutes"):
        return [int(n) for n in re.findall(r"\d+", strip_dates_and_times(body))]
    if kind == "time":
        candidates = [int(m[1]) * 60 + int(m[2]) for m in TIME.finditer(body)]
        return [c for c in candidates if c not in {int(m[1]) * 60 + int(m[2]) for m in TIME.finditer(normalise(question))}]
    asked = [to_date(*(y or 2000, m, d)) for y, m, d in date_mentions(question)]
    return [c for c in date_mentions(body) if not any(a and mention_matches(c, a) for a in asked)]


def mention_matches(mention, value):
    year, month, day = mention
    return (month, day) == (value.month, value.day) and year in (None, value.year)


def candidate_matches(kind, candidate, value):
    if kind == "date":
        return mention_matches(candidate, value)
    if kind == "interval":
        return all(mention_matches(c, v) for c, v in zip(candidate, value))
    return candidate == value


def last_candidate(kind, candidates):
    if kind == "interval":
        return tuple(candidates[-2:]) if len(candidates) >= 2 else None
    return candidates[-1] if candidates else None


def reasoning_body(record):
    content = record["content"] or ""
    matches = list(M.ANSWER.finditer(content))
    return content[: matches[-1].start()] if matches else content
