import json
import re
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent
PARSED = ROOT / "experiments/2026-10-29_ed-analysis/parsed"
DIFFICULTIES = ["short", "medium", "long", "very_long", "very_very_long"]
PARTIAL_COST = yaml.safe_load(open(ROOT / "config/ed.yaml"))["partial_date_cost"]
WEEKDAYS = {n.casefold(): d for d, names in yaml.safe_load(open(ROOT / "config/parser.yaml"))["weekdays"].items() for n in names}

ANS = {"ANSWER", "SPITANSWER"}
META = ANS | {"GOAL", "PLAN", "RULE", "CHECK", "REVISE", "IGNORE", "FORMAT"}
ANSWER_RE = re.compile(r"(?:Answer|उत्तर(?:\s*है)?|जवाब)\s*\**\s*[:：]\s*(.*)")
HI_DIGITS = str.maketrans("०१२३४५६७८९٠١٢٣٤٥٦٧٨٩", "0123456789" * 2)
SHORT = re.compile(r"\d{1,2}(?:-\d{2})?")
LONG = re.compile(r"\d{4}-\d{2}(?:-\d{2})?")


def head(t):
    return t.split(" ")[0]


def partial(s, f):
    if not (SHORT.fullmatch(s) and LONG.fullmatch(f)):
        return False
    a = [int(x) for x in s.split("-")]
    return [int(x) for x in f.split("-")][-len(a):] == a


def value_match(a, b):
    p, q = a.split(".."), b.split("..")
    return len(p) == len(q) and all(x == y or partial(x, y) or partial(y, x) for x, y in zip(p, q))


def sub_cost(a, b):
    p, q = a.split(" "), b.split(" ")
    if len(p) == len(q) and all(value_match(x, y) for x, y in zip(p[1:], q[1:])):
        return PARTIAL_COST
    return 1.0


def norm_ed(a, b):
    if not a or not b:
        return np.nan
    ua, ub = sorted(set(a)), sorted(set(b))
    ia, ib = {t: i for i, t in enumerate(ua)}, {t: i for i, t in enumerate(ub)}
    costs = np.ones((len(ua), len(ub)))
    by_head = {}
    for j, t in enumerate(ub):
        by_head.setdefault(head(t), []).append(j)
    for i, t in enumerate(ua):
        for j in by_head.get(head(t), ()):
            costs[i, j] = 0.0 if t == ub[j] else sub_cost(t, ub[j])
    y = np.array([ib[t] for t in b])
    pos = np.arange(len(b) + 1, dtype=float)
    prev = pos.copy()
    for i, t in enumerate(a, 1):
        row = np.empty(len(b) + 1)
        row[0] = i
        row[1:] = np.minimum(prev[1:] + 1, prev[:-1] + costs[ia[t], y])
        prev = np.minimum.accumulate(row - pos) + pos
    return prev[-1] / max(len(a), len(b))


def answer_of(text):
    m = ANSWER_RE.findall(text or "")
    return re.sub(r"\s+से\s+", " to ", m[-1].strip().strip("*`.। ").translate(HI_DIGITS)) if m else None


def correct_of(ans, gold, task):
    if ans is None:
        return np.nan
    if task == "day_of_week":
        return float(WEEKDAYS.get(ans.casefold()) == WEEKDAYS[gold.casefold()])
    return float(ans == gold)


def answer_values(a, b, gold):
    vals = set(re.split(r"\s+to\s+", gold))
    for s in (a, b):
        for t in s:
            if head(t) in ANS:
                for arg in t.split(" ")[1:]:
                    vals.update(arg.split(".."))
    return vals


def drop_valued(s, vals):
    keep = []
    for t in s:
        parts = [p for arg in t.split(" ")[1:] for p in arg.split("..")]
        if not any(p == v or partial(p, v) or partial(v, p) for p in parts for v in vals):
            keep.append(t)
    return keep


def pre_check(s):
    for i, t in enumerate(s):
        if head(t) in {"CHECK", "REVISE"}:
            return s[:i]
    return s


def views(a, b, gold):
    na, nb = [t for t in a if head(t) not in ANS], [t for t in b if head(t) not in ANS]
    vals = answer_values(a, b, gold)
    return {
        "full": (a, b),
        "noans": (na, nb),
        "noansval": (drop_valued(na, vals), drop_valued(nb, vals)),
        "ops": ([head(t) for t in a], [head(t) for t in b]),
        "opsnoans": ([head(t) for t in na], [head(t) for t in nb]),
        "opscore": ([head(t) for t in a if head(t) not in META], [head(t) for t in b if head(t) not in META]),
        "prefix8": (na[:8], nb[:8]),
        "prefix8ops": ([head(t) for t in na[:8]], [head(t) for t in nb[:8]]),
        "precheck": (pre_check(na), pre_check(nb)),
        "precheckops": ([head(t) for t in pre_check(na)], [head(t) for t in pre_check(nb)]),
    }


def corrupt(s):
    return [(head(t) + " WRONGVALUE") if head(t) in ANS else t for t in s]


def build():
    rows = []
    for mode, folder in {"off": "standard", "on": "ron"}.items():
        for difficulty in DIFFICULTIES:
            records = json.load(open(PARSED / folder / f"{difficulty}.p.json", encoding="utf-8"))["records"]
            by_key = {}
            for r in records:
                if r["condition"] != "cot":
                    continue
                m = r["meta"]
                by_key.setdefault((m["task"], m["question_id"], m["insertion"]), {})[m["language"]] = r
            del records
            for (task, qid, insertion), langs in by_key.items():
                en, hi = langs["en_US"], langs["hi_IN"]
                gold = en["meta"]["answer"]
                ea, ha = answer_of(en["content"]["original"]), answer_of(hi["content"]["original"])
                row = {"mode": mode, "difficulty": difficulty, "task": task, "question_id": int(qid), "insertion": insertion,
                       "gold": gold, "en_answer": ea, "hi_answer": ha, "en_correct": correct_of(ea, gold, task), "hi_correct": correct_of(ha, gold, task),
                       "en_finish": en["finish_reason"], "hi_finish": hi["finish_reason"],
                       "en_tokens": en["usage"]["completion_tokens"], "hi_tokens": hi["usage"]["completion_tokens"],
                       "en_content_chars": len(en["content"]["original"] or ""), "hi_content_chars": len(hi["content"]["original"] or "")}
                for field, tag in (("content", "c"), ("reasoning_content", "r")):
                    a, b = en[field]["parsed"] or [], hi[field]["parsed"] or []
                    for name, (x, y) in views(a, b, gold).items():
                        row[f"{tag}_{name}"] = norm_ed(x, y)
                        row[f"{tag}_{name}_en"], row[f"{tag}_{name}_hi"] = len(x), len(y)
                    row[f"{tag}_corrupted"] = norm_ed(a, corrupt(b))
                    row[f"{tag}_en_answer_tokens"] = sum(head(t) in ANS for t in a)
                    row[f"{tag}_hi_answer_tokens"] = sum(head(t) in ANS for t in b)
                rows.append(row)
            del by_key
            print(mode, difficulty, len(rows), flush=True)
    df = pd.DataFrame(rows)
    df.to_csv(OUT / "pairs.csv.gz", index=False)


if __name__ == "__main__":
    build()
