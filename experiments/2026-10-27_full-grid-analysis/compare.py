import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
OUT = HERE / "outputs"
ap = argparse.ArgumentParser()
ap.add_argument("--pair", choices=["full", "reasoning"], default="full")
args = ap.parse_args()
if args.pair == "full":
    SCOPES = {"mid-midparser": "Mid report", "new": "New questions only", "full4": "Full grid, 4 levels", "full": "Full grid, 5 levels"}
else:
    SCOPES = {"ron-off": "Thinking off", "ron": "Thinking on"}
N = {s: json.load(open(OUT / s / "numbers.json", encoding="utf-8")) for s in SCOPES}


def diff(get):
    def f(n):
        v = get(n)
        return None if v is None else ("diff", v[0], v[1][0], v[1][1])
    return f


def ratio(get):
    def f(n):
        v = get(n)
        return None if v is None else ("or", v["odds_ratio"], v["or_ci"][0], v["or_ci"][1])
    return f


def test(get):
    def f(n):
        v = get(n)
        return None if v is None else ("p", v[0], v[1], None)
    return f


def share(get):
    def f(n):
        v = get(n)
        return None if v is None else ("share", v, None, None)
    return f


def count(get):
    def f(n):
        v = get(n)
        return None if v is None else ("count", v, None, None)
    return f


def find(path):
    def f(n):
        for k in path.split("|"):
            if n is None or k not in n:
                return None
            n = n[k]
        return n
    return f


def pattern(key, name):
    return share(lambda n: (lambda v: v and v.get(name, 0.0))(find(f"recurrence|{key}")(n)))


def cot(lang, task):
    return diff(lambda n: (lambda v: v and (v["delta"], v["ci"]))(find(f"cot_delta|{lang}/{task}")(n)))


def dist(lang, ins):
    return diff(lambda n: (lambda v: v and (v["value"], v["ci"]))(find(f"distractor|{lang}/did/{ins}")(n)))


def dist_task(lang, task, ins="similar_insertion"):
    return diff(lambda n: (lambda v: v and (v["did"], v["ci"]))(find(f"distractor_by_task|{lang}/{task}/{ins}")(n)))


def gap(panel, lvl, cond):
    return diff(lambda n: (lambda v: v and (v["gap"], v["ci"]))(find(f"difficulty|gap/({panel})/{lvl}/{cond}")(n)))


def reuse(lang, cond):
    def get(n):
        v = find(f"reuse_similar|{lang}/{cond}")(n)
        return v and (v["inserted"] / v["inserted_n"] - v["placebo"] / v["placebo_n"], v["p"])
    return test(get)


def agree(cond):
    def get(n):
        v = find(f"agreement|{cond}")(n)
        return v and ((v["en_only"] - v["hi_only"]) / v["pairs"], v["p"])
    return test(get)


ROWS = [
    ("1 CoT delta", "English, all tasks", cot("en_US", "all")),
    ("1 CoT delta", "Hindi, all tasks", cot("hi_IN", "all")),
    ("1 CoT delta", "Hindi, date subtraction", cot("hi_IN", "date_subtraction")),
    ("1 CoT delta", "Hindi, interval date", cot("hi_IN", "interval_date")),
    ("1 CoT delta", "Hindi, day of week", cot("hi_IN", "day_of_week")),
    ("1 CoT delta", "Hindi, date recurrence", cot("hi_IN", "date_recurrence")),
    ("1 CoT delta", "Hindi, time duration", cot("hi_IN", "time_duration")),
    ("1 CoT delta", "English, time duration", cot("en_US", "time_duration")),
    ("1 CoT delta", "English, interval date", cot("en_US", "interval_date")),
    ("2 Day of week", "Hindi CoT +1 day minus correct (share)", share(lambda n: (lambda v: v and (v["1"] - v["0"]) / 100)(find("day_of_week|offsets|hi_IN/cot")(n)))),
    ("2 Day of week", "English direct modal weekday share", share(find("day_of_week|direct_mode|en_US|share"))),
    ("2 Day of week", "Hindi direct modal weekday share", share(find("day_of_week|direct_mode|hi_IN|share"))),
    ("3 Recurrence", "Hindi CoT first-step shortcut", pattern("hi_IN/cot", "first_step")),
    ("3 Recurrence", "Hindi CoT mirror (backwards)", pattern("hi_IN/cot", "mirror")),
    ("3 Recurrence", "Hindi direct mirror (backwards)", pattern("hi_IN/direct", "mirror")),
    ("3 Recurrence", "English direct first-step shortcut", pattern("en_US/direct", "first_step")),
    ("4 EN-HI gap", "Five date tasks, short, CoT", gap("b", "short", "cot")),
    ("4 EN-HI gap", "Five date tasks, very long, CoT", gap("b", "very_long", "cot")),
    ("4 EN-HI gap", "Five date tasks, short, direct", gap("b", "short", "direct")),
    ("4 EN-HI gap", "Five date tasks, very long, direct", gap("b", "very_long", "direct")),
    ("5 Distraction penalty", "English, time-related", dist("en_US", "similar_insertion")),
    ("5 Distraction penalty", "English, unrelated", dist("en_US", "dissimilar_insertion")),
    ("5 Distraction penalty", "Hindi, time-related", dist("hi_IN", "similar_insertion")),
    ("5 Distraction penalty", "Hindi, unrelated", dist("hi_IN", "dissimilar_insertion")),
    ("5 Distraction penalty", "Hindi time-related, date duration", dist_task("hi_IN", "date_duration")),
    ("5 Distraction penalty", "Hindi time-related, day of week", dist_task("hi_IN", "day_of_week")),
    ("5 Distraction penalty", "Hindi time-related, time duration", dist_task("hi_IN", "time_duration")),
    ("5 Distraction penalty", "Hindi time-related, date recurrence", dist_task("hi_IN", "date_recurrence")),
    ("6 Distractor mention", "English time-related: mention rate minus placebo", share(lambda n: (lambda v: v and v["inserted_rate"] - v["placebo_rate"])(find("mention|en_US/similar")(n)))),
    ("6 Distractor mention", "Hindi time-related: mention rate minus placebo", share(lambda n: (lambda v: v and v["inserted_rate"] - v["placebo_rate"])(find("mention|hi_IN/similar")(n)))),
    ("6 Distractor mention", "Hindi unrelated: mention rate minus placebo", share(lambda n: (lambda v: v and v["inserted_rate"] - v["placebo_rate"])(find("mention|hi_IN/dissimilar")(n)))),
    ("6 Distractor mention", "OR correct | mention, English time-related", ratio(find("mention|en_US/similar"))),
    ("6 Distractor mention", "OR correct | mention, Hindi time-related", ratio(find("mention|hi_IN/similar"))),
    ("6 Distractor mention", "OR correct | mention, English unrelated", ratio(find("mention|en_US/dissimilar"))),
    ("6 Distractor mention", "OR correct | mention, Hindi unrelated", ratio(find("mention|hi_IN/dissimilar"))),
    ("7 Distractor reuse", "Hindi direct: reuse minus placebo", reuse("hi_IN", "direct")),
    ("7 Distractor reuse", "Hindi CoT: reuse minus placebo", reuse("hi_IN", "cot")),
    ("7 Distractor reuse", "English direct: reuse minus placebo", reuse("en_US", "direct")),
    ("8 Language drift", "OR correct | Hindi trace drifts (TLR < 0.9)", ratio(find("hindi_drift"))),
    ("9 Verification", "OR correct | English trace verifies", ratio(find("verification_en"))),
    ("10 Trace length", "English median words", count(find("trace|en_US|median_words"))),
    ("10 Trace length", "Hindi median words", count(find("trace|hi_IN|median_words"))),
    ("10 Trace length", "English median completion tokens", count(find("trace|en_US|median_tokens"))),
    ("10 Trace length", "Hindi median completion tokens", count(find("trace|hi_IN|median_tokens"))),
    ("11 Agreement", "CoT: English-only minus Hindi-only right (share of pairs)", agree("cot")),
    ("11 Agreement", "Direct: English-only minus Hindi-only right (share of pairs)", agree("direct")),
]


def significant(kind, v, lo, hi):
    if kind == "diff":
        return lo > 0 or hi < 0
    if kind == "or":
        return lo > 1 or hi < 1
    if kind == "p":
        return lo < 0.05
    return None


def effect(kind, v):
    return np.log(v) if kind == "or" else v


def verdict(old, new):
    if old is None or new is None or not all(np.isfinite(x) for x in (old[1], new[1])):
        return "not computable"
    kind, v0, lo0, hi0 = old
    _, v1, lo1, hi1 = new
    if kind == "count":
        change = 100 * (v1 - v0) / v0
        return "about the same" if abs(change) < 10 else f"{'up' if change > 0 else 'down'} {abs(change):.0f}%"
    if kind == "share":
        change = 100 * (v1 - v0)
        return "about the same" if abs(change) < 2 else f"{'up' if change > 0 else 'down'} {abs(change):.1f} pts"
    s0, s1 = significant(kind, v0, lo0, hi0), significant(kind, v1, lo1, hi1)
    e0, e1 = effect(kind, v0), effect(kind, v1 if kind != "p" else v1)
    if s0 and s1 and np.sign(e0) != np.sign(e1):
        return "reversed"
    if s0 and not s1:
        return "no longer significant"
    if not s0 and s1:
        return "newly significant"
    if not s0 and not s1:
        return "null in both"
    if kind != "p" and lo0 <= v1 <= hi0:
        return "holds, inside old CI"
    return "stronger" if abs(e1) > abs(e0) else "weaker, still significant"


def replicates(old, new):
    if old is None or new is None:
        return "-"
    kind, v0, lo0, hi0 = old
    _, v1, lo1, hi1 = new
    if kind in ("share", "count"):
        return "-"
    s0, s1 = significant(kind, v0, lo0, hi0), significant(kind, v1, lo1, hi1)
    if s0:
        return "yes" if s1 and np.sign(effect(kind, v0)) == np.sign(effect(kind, v1)) else "no"
    return "yes (null)" if not s1 else "no (now an effect)"


def fmt(x):
    if x is None:
        return "-"
    kind, v, lo, hi = x
    if kind == "diff":
        return f"{100 * v:+.1f} [{100 * lo:+.1f}, {100 * hi:+.1f}]"
    if kind == "or":
        return f"{v:.2f} [{lo:.2f}, {hi:.2f}]"
    if kind == "p":
        return f"{100 * v:+.1f} (p={lo:.2g})"
    if kind == "count":
        return f"{v:.0f}"
    return f"{100 * v:.1f}"


records = []
for section, name, get in ROWS:
    vals = {s: get(N[s]) for s in SCOPES}
    row = {"section": section, "finding": name, **{SCOPES[s]: fmt(v) for s, v in vals.items()}}
    if args.pair == "full":
        row["verdict (full vs mid)"] = verdict(vals["mid-midparser"], vals["full"])
        row["replicates on new questions"] = replicates(vals["mid-midparser"], vals["new"])
    else:
        row["verdict (on vs off)"] = verdict(vals["ron-off"], vals["ron"])
    records.append(row)
table = pd.DataFrame(records)
name = "comparison" if args.pair == "full" else "comparison_reasoning"
table.to_csv(OUT / f"{name}.csv", index=False)
lines = ["| " + " | ".join(table.columns) + " |", "|" + "---|" * len(table.columns)]
lines += ["| " + " | ".join(str(v) for v in row) + " |" for row in table.itertuples(index=False)]
note = ("Differences are percentage points with 95% cluster-bootstrap intervals; OR = Mantel-Haenszel odds ratio within task x "
        "difficulty; reuse and agreement rows give the difference in points with Fisher / sign-test p; plain numbers are shares "
        "(%), and trace lengths are medians. Mid report = the mid-report pipeline and parser on its 3,089 questions "
        "(reproduces the submitted tables exactly).")
if args.pair == "reasoning":
    note = ("Same pipeline on the 449 questions answered with thinking on (reasoning_effort: low, 16k tokens) and with thinking "
            "off (main runs, 4k tokens). Differences are percentage points with 95% cluster-bootstrap intervals; OR = "
            "Mantel-Haenszel odds ratio within task x difficulty; reuse and agreement rows give the difference in points with "
            "Fisher / sign-test p; plain numbers are shares (%), and trace lengths are medians of the visible CoT.")
title = "Mid report vs full grid" if args.pair == "full" else "Thinking off vs thinking on (same questions)"
(OUT / f"{name}.md").write_text(f"# {title}\n\n" + note + "\n\n" + "\n".join(lines) + "\n")
print(table.drop(columns=["section"]).to_string(index=False))
