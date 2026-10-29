import json
import random
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
DATA = ROOT / "experiments" / "2026-10-29_ed-analysis"
sys.path.insert(0, str(ROOT))

from ed import CONFIG, partial, substitution
from parser import find_distractor, parse_sentences, segments

SETS = ["standard", "ron"]
DIFFICULTIES = ["short", "medium", "long", "very_long", "very_very_long"]
FIELDS = ["content", "reasoning_content"]
MAX_CELLS = 2_000_000
SAMPLES = 25
UNCOVERED_RECORDS = 400
random.seed(0)


def align(a, b):
    n, m = len(a), len(b)
    dp = [[0.0] * (m + 1) for _ in range(n + 1)]
    for i in range(n + 1):
        dp[i][0] = i
    for j in range(m + 1):
        dp[0][j] = j
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            dp[i][j] = min(dp[i - 1][j] + 1, dp[i][j - 1] + 1, dp[i - 1][j - 1] + substitution(a[i - 1], b[j - 1]))
    steps, i, j = [], n, m
    while i or j:
        if i and j and dp[i][j] == dp[i - 1][j - 1] + substitution(a[i - 1], b[j - 1]):
            steps.append(("sub", a[i - 1], b[j - 1]))
            i, j = i - 1, j - 1
        elif i and dp[i][j] == dp[i - 1][j] + 1:
            steps.append(("del", a[i - 1], None))
            i -= 1
        else:
            steps.append(("ins", None, b[j - 1]))
            j -= 1
    return steps[::-1]


def arg_kind(v):
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", v):
        return "date"
    if re.fullmatch(r"\d{2}-\d{2}", v):
        return "MM-DD"
    if re.fullmatch(r"\d{4}-\d{2}", v):
        return "YYYY-MM"
    if re.fullmatch(r"\d{1,2}:\d{2}", v):
        return "time"
    if re.fullmatch(r"-?\d+(?:\.\d+)?", v):
        return "number"
    if v == "()":
        return "bracket"
    return "word"


def half_kind(a, b):
    kinds = []
    for i, (p, q) in enumerate(zip(a.split()[1:], b.split()[1:])):
        if p != q:
            short, full = (p, q) if partial(p, q) else (q, p)
            kinds.append(f"arg{i + 1}:{arg_kind(short)}~{arg_kind(full)}")
    return " ".join(kinds) or "range"


def full_kind(a, b):
    x, y = a.split(), b.split()
    if x[0] != y[0]:
        return "op"
    if len(x) != len(y):
        return "arity"
    diffs = [f"arg{i + 1}:{arg_kind(p)}/{arg_kind(q)}" for i, (p, q) in enumerate(zip(x[1:], y[1:])) if p != q]
    return " ".join(diffs)


def source(record, field, token):
    for sentence, tokens in zip(segments(record[field]["original"]), parse_sentences(record[field]["original"], find_distractor(record))):
        if token in tokens:
            return sentence
    return None


def pairs(records):
    by_question = defaultdict(dict)
    for r in records:
        if r["condition"] == "cot":
            m = r["meta"]
            by_question[(m["task"], m["question_id"], m["insertion"])][m["language"]] = r
    return [(q["en_US"], q["hi_IN"]) for q in by_question.values() if {"en_US", "hi_IN"} <= set(q)]


if __name__ == "__main__":
    report = {"partial_date_cost": CONFIG["partial_date_cost"], "alignment": {}, "half_samples": [], "same_op_samples": [], "uncovered": {}}
    half_examples = defaultdict(list)
    same_op_examples = defaultdict(list)
    uncovered = defaultdict(list)
    for s in SETS:
        for d in DIFFICULTIES:
            records = json.load(open(DATA / "parsed" / s / f"{d}.json", encoding="utf-8"))["records"]
            for field in FIELDS:
                c = Counter()
                for en, hi in pairs(records):
                    a, b = en[field]["parsed"], hi[field]["parsed"]
                    if a is None or b is None:
                        continue
                    if len(a) * len(b) > MAX_CELLS:
                        c["pairs_skipped"] += 1
                        continue
                    c["pairs"] += 1
                    for kind, x, y in align(a, b):
                        if kind != "sub":
                            c[kind] += 1
                            c[f"{kind}:{(x or y).split()[0]}"] += 1
                            continue
                        cost = substitution(x, y)
                        if cost == 0:
                            c["match"] += 1
                        elif cost < 1:
                            c["half"] += 1
                            k = half_kind(x, y)
                            c[f"half:{x.split()[0]} {k}"] += 1
                            half_examples[(field, x.split()[0], k)].append((s, d, en, hi, x, y))
                        else:
                            k = full_kind(x, y)
                            c["full"] += 1
                            c[f"full:{'op ' + x.split()[0] + '->' + y.split()[0] if k == 'op' else x.split()[0] + ' ' + k}"] += 1
                            if k not in ("op", "arity"):
                                same_op_examples[(field, x.split()[0], k)].append((s, d, en, hi, x, y))
                if c["pairs"]:
                    report["alignment"][f"{s}/{d}/{field}"] = dict(c.most_common())
            for r in random.sample(records, min(UNCOVERED_RECORDS, len(records))):
                for field in FIELDS:
                    text = r[field]["original"]
                    if text is None:
                        continue
                    for sentence, tokens in zip(segments(text), parse_sentences(text, find_distractor(r))):
                        if not tokens:
                            uncovered[(s, field, r["meta"]["language"])].append(sentence)

    for (field, op, k), rows in sorted(half_examples.items(), key=lambda kv: -len(kv[1])):
        for s, d, en, hi, x, y in random.sample(rows, min(SAMPLES, len(rows))):
            report["half_samples"].append({"group": f"{field} {op} {k}", "count": len(rows), "set": s, "difficulty": d, "id": en["id"], "en": x, "hi": y, "en_source": source(en, field, x), "hi_source": source(hi, field, y)})
    for (field, op, k), rows in sorted(same_op_examples.items(), key=lambda kv: -len(kv[1]))[:30]:
        for s, d, en, hi, x, y in random.sample(rows, min(5, len(rows))):
            report["same_op_samples"].append({"group": f"{field} {op} {k}", "count": len(rows), "set": s, "difficulty": d, "id": en["id"], "en": x, "hi": y, "en_source": source(en, field, x), "hi_source": source(hi, field, y)})
    for (s, field, lang), sentences in sorted(uncovered.items()):
        starts = Counter(" ".join(re.findall(r"[\wऀ-ॿ]+", x.lower())[:2]) for x in sentences)
        report["uncovered"][f"{s}/{field}/{lang}"] = {"segments": len(sentences), "top_openings": starts.most_common(40), "samples": random.sample(sentences, min(60, len(sentences)))}

    out = HERE / "outputs"
    out.mkdir(exist_ok=True)
    json.dump(report, open(out / "audit.json", "w", encoding="utf-8"), indent=2, ensure_ascii=False)
