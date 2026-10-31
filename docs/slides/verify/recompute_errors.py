import json
import re
import sys
from collections import Counter, defaultdict
from datetime import date, timedelta
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
LEVELS = ["short", "medium", "long", "very_long", "very_very_long"]
DIG = str.maketrans("०१२३४५६७८९", "0123456789")
LABEL = re.compile(r"(?:\banswer\b|उत्तर|जवाब)(?:\s*है)?\s*\**\s*[:：]", re.I)
ISO = re.compile(r"\d{4}-\d{1,2}-\d{1,2}")
CONDS = {("standard", "en_US", "direct"): "English direct", ("standard", "en_US", "cot"): "English CoT", ("standard", "hi_IN", "direct"): "Hindi direct", ("standard", "hi_IN", "cot"): "Hindi CoT", ("en-cot", "hi_IN", "en-cot"): "en-CoT"}
DATE_T = {"date_addition", "date_subtraction", "date_duration", "date_recurrence"}


def answer(text):
    t = (text or "").translate(DIG)
    hits = list(LABEL.finditer(t))
    if not hits:
        return None
    rest = t[hits[-1].end():].strip(" *`_\t\n")
    return rest.split("\n")[0].strip(" *`_.।,\"'\t") or None


def d(s):
    y, m, dd = map(int, s.split("-"))
    try:
        return date(y, m, dd)
    except ValueError:
        return None


def mins(s):
    m = re.search(r"(\d{1,2})[:.](\d{2})", s)
    return int(m[1]) * 60 + int(m[2]) if m else None


def has_feb29(a, b):
    a, b = min(a, b), max(a, b)
    return any(date(y, 2, 29) >= a and date(y, 2, 29) <= b for y in range(a.year, b.year + 1) if y % 4 == 0)


T = defaultdict(Counter)
for source in ["standard", "en-cot"]:
    for level in LEVELS:
        for r in json.loads((ROOT / "responses" / source / f"{level}.json").read_text()):
            m = r["meta"]
            key = CONDS.get((source, m["language"], r["condition"]))
            if not key:
                continue
            task, gold = m["task"], str(m["answer"])
            q = r["request"]["messages"][-1]["content"].strip().split("\n\n")[-1].translate(DIG)
            raw = answer(r["content"])
            if task in ("date_addition", "date_subtraction", "date_recurrence"):
                got = ISO.search(raw) if raw else None
                pred = d(got.group()) if got else None
                g = d(gold)
                right = pred == g
                today = d(ISO.findall(q)[-1])
                span = (today, g)
            elif task == "date_duration":
                nums = re.findall(r"-?\d+", raw) if raw else []
                pred = int(nums[0]) if nums else None
                right = str(pred) == gold
                a, z = [d(x) for x in ISO.findall(q)[-2:]]
                span = (a, z)
            elif task in ("time_addition", "time_subtraction"):
                pred = mins(raw) if raw else None
                right = pred == mins(gold)
            elif task == "time_duration":
                hm = re.search(r"(\d+)\s*(?:hours?|hrs?|घंटे|घंटा)\s*(?:and|और|,)?\s*(\d+)\s*(?:minutes?|mins?|मिनट)", raw or "", re.I)
                nums = re.findall(r"-?\d+", raw) if raw else []
                pred = int(hm[1]) * 60 + int(hm[2]) if hm else (int(nums[0]) if nums else None)
                right = str(pred) == gold
            elif task == "interval_date":
                got = [d(x) for x in ISO.findall(raw)] if raw else []
                g1, g2 = [d(x) for x in gold.split(" to ")]
                right = len(got) >= 2 and got[0] == g1 and got[1] == g2
            else:
                continue
            c = T[key]
            if task in DATE_T:
                feb = has_feb29(*span)
                month = (span[0].year, span[0].month) != (span[1].year, span[1].month)
                for name, flag in [("feb29", feb), ("month", month)]:
                    c[f"{name}|{'with' if flag else 'without'}|n"] += 1
                    c[f"{name}|{'with' if flag else 'without'}|wrong"] += not right
                if not right and pred is not None:
                    diff = abs((pred - g).days) if task != "date_duration" else abs(pred - int(gold))
                    c["tens|n"] += 1
                    c["tens|hit"] += diff in (10, 20, 30)
            if task in ("time_addition", "time_subtraction", "time_duration"):
                c["time|n"] += 1
                c["time|wrong"] += not right
                if task == "time_duration":
                    ts = re.findall(r"\d{1,2}:\d{2}", q)
                    cross = mins(ts[-1]) < mins(ts[-2])
                    goldm = int(gold)
                else:
                    cross = None
                    goldm = mins(gold)
                    start = mins(re.findall(r"\d{1,2}:\d{2}", q)[-1])
                    hm = re.search(r"(\d+)\s*(?:hours?|घंटे|घंटा)\D+?(\d+)\s*(?:minutes?|मिनट)", q)
                    delta = int(hm[1]) * 60 + int(hm[2])
                    cross = start + delta >= 1440 if task == "time_addition" else start - delta < 0
                c[f"mid|{'with' if cross else 'without'}|n"] += 1
                c[f"mid|{'with' if cross else 'without'}|wrong"] += not right
                if not right and pred is not None:
                    diff = (pred - goldm) % 1440 if task != "time_duration" else abs(pred - goldm)
                    c["time|given"] += 1
                    c["time|hours"] += diff % 60 == 0
                    c["time|twelve"] += diff == 720
            if task == "interval_date":
                c["week|n"] += 1
                c["week|wrong"] += not right
                if not right and len(got) >= 2 and got[0] and got[1]:
                    a, z = got[0], got[1]
                    c["week|given"] += 1
                    c["week|this"] += a == g1 - timedelta(7) and z == g2 - timedelta(7)
                    c["week|one"] += abs((a - g1).days) == 1 and (a - g1) == (z - g2)
                    c["week|satfri"] += a.weekday() == 5 and z.weekday() == 4 and (z - a).days == 6
                    c["week|not7"] += (z - a).days != 6
res = {k: dict(sorted(v.items())) for k, v in T.items()}
(OUT / "recomputed_errors.json").write_text(json.dumps(res, indent=2))
for k, v in res.items():
    print(k)
    print("  month", v["month|without|wrong"], v["month|without|n"], v["month|with|wrong"], v["month|with|n"], "feb", v["feb29|without|wrong"], v["feb29|without|n"], v["feb29|with|wrong"], v["feb29|with|n"], "mid", v["mid|without|wrong"], v["mid|without|n"], v["mid|with|wrong"], v["mid|with|n"])
    print("  time", v["time|wrong"], v["time|n"], "given", v["time|given"], "hours", v["time|hours"], "12", v["time|twelve"], "tens", v["tens|hit"], v["tens|n"])
    print("  week", v["week|wrong"], v["week|n"], "given", v["week|given"], "this", v["week|this"], "one", v["week|one"], "satfri", v["week|satfri"], "not7", v["week|not7"])
