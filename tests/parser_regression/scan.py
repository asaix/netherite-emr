import calendar
import datetime
import json
import re
import sys
from collections import Counter, defaultdict
from multiprocessing import Pool
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
DATA = ROOT / "experiments" / "2026-10-29_ed-analysis"
sys.path.insert(0, str(ROOT))

from ed import partial
from parser import ARITHMETIC, KIND, VALUE, WEEKDAYS, find_distractor, fold, parse_sentences, segments, values

SETS = ["standard", "ron"]
DIFFICULTIES = ["short", "medium", "long", "very_long", "very_very_long"]
FIELDS = ["content", "reasoning_content"]
OUT = HERE / "outputs" / (sys.argv[1] if len(sys.argv) > 1 else "scan")
EXAMPLES = 3
TOP = 400
DAYNAMES = list(calendar.day_name)


def shape(segment):
    s = VALUE.sub(lambda m: f"<{KIND[m.lastgroup]}>", segment).lower()
    return re.sub(r"\s+", " ", s).strip()


def prefix(s, n=6):
    return " ".join(s.split()[:n])


def note(counter, examples, key, example):
    counter[key] += 1
    if len(examples[key]) < EXAMPLES:
        examples[key].append(example)


def checks(token, segment, prompt_values):
    op, *args = token.split()
    found = []
    if op == "GIVEN" and args:
        if not any(args[0] == v or partial(args[0], v) for v in prompt_values):
            found.append("GIVEN value not in question")
    if op == "ANCHOR" and len(args) == 2 and re.fullmatch(r"\d{4}-\d{2}-\d{2}", args[0]):
        try:
            if DAYNAMES[datetime.date.fromisoformat(args[0]).weekday()] != args[1]:
                found.append("ANCHOR weekday does not match date")
        except ValueError:
            found.append("ANCHOR invalid date")
    if op == "MONTHLEN" and args:
        lengths = {int(n) for n in re.findall(r"(?<!\d)(2[89]|3[01])(?!\d)", segment)}
        month = int(args[0][-2:])
        expected = {calendar.monthrange(int(args[0][:4]), month)[1]} if len(args[0]) == 7 else ({28, 29} if month == 2 else {calendar.monthrange(2025, month)[1]})
        if lengths and not lengths & expected:
            found.append("MONTHLEN length does not match month")
    if op in ARITHMETIC:
        if len(args) < 2:
            found.append(f"{op} missing operand")
        elif args[0] == args[1] and args[0] != "()":
            found.append(f"{op} identical operands")
        if any(a in DAYNAMES for a in args[1:]) and op not in ("SUB", "CMP"):
            found.append(f"{op} weekday as second operand")
    return found


def run(job):
    s, d = job
    records = json.load(open(DATA / "parsed" / s / f"{d}.json", encoding="utf-8"))["records"]
    counts = Counter()
    uncovered, uncovered_ex = Counter(), defaultdict(list)
    tokens, tokens_ex = Counter(), defaultdict(list)
    flags, flags_ex = Counter(), defaultdict(list)
    ops = Counter()
    for record in records:
        lang, task = record["meta"]["language"], record["meta"]["task"]
        prompt_values = {v for _, _, v in values(fold(record["request"]["messages"][-1]["content"]))}
        distractor = find_distractor(record)
        for field in FIELDS:
            text = record[field]["original"]
            if text is None:
                continue
            key = (s, field, lang)
            counts[key + ("texts",)] += 1
            for segment, toks in zip(segments(text), parse_sentences(text, distractor, record["request"]["messages"][-1]["content"])):
                counts[key + ("segments",)] += 1
                sh = shape(segment)
                example = {"id": record["id"], "segment": segment[:240], "tokens": toks}
                if not toks:
                    counts[key + ("uncovered",)] += 1
                    note(uncovered, uncovered_ex, (field, lang, prefix(sh)), example)
                for token in toks:
                    op = token.split()[0]
                    ops[(s, field, lang, task, op)] += 1
                    note(tokens, tokens_ex, (field, lang, op, prefix(sh)), example)
                    for f in checks(token, segment, prompt_values):
                        counts[key + ("flag", f)] += 1
                        note(flags, flags_ex, (field, lang, f, prefix(sh)), {**example, "token": token})
    return counts, uncovered, dict(uncovered_ex), tokens, dict(tokens_ex), flags, dict(flags_ex), ops


def top(counter, examples, n):
    return [{"key": " | ".join(k), "count": c, "examples": examples[k]} for k, c in counter.most_common(n)]


if __name__ == "__main__":
    with Pool(4) as pool:
        results = pool.map(run, [(s, d) for s in SETS for d in DIFFICULTIES])
    counts, uncovered, tokens, flags, ops = Counter(), Counter(), Counter(), Counter(), Counter()
    uncovered_ex, tokens_ex, flags_ex = defaultdict(list), defaultdict(list), defaultdict(list)
    for c, u, ue, t, te, f, fe, o in results:
        counts.update(c)
        uncovered.update(u)
        tokens.update(t)
        flags.update(f)
        ops.update(o)
        for src, dst in ((ue, uncovered_ex), (te, tokens_ex), (fe, flags_ex)):
            for k, v in src.items():
                dst[k] = (dst[k] + v)[:EXAMPLES]
    OUT.mkdir(parents=True, exist_ok=True)
    summary = {}
    for key in sorted({k[:3] for k in counts}):
        c = {k[3]: v for k, v in counts.items() if k[:3] == key and len(k) == 4}
        summary["/".join(key)] = {
            "texts": c["texts"],
            "segments": c["segments"],
            "uncovered_pct": round(100 * c["uncovered"] / c["segments"], 2),
            "flags": {k[4]: v for k, v in sorted(counts.items(), key=lambda kv: -kv[1]) if k[:3] == key and len(k) == 5},
        }
    json.dump(summary, open(OUT / "summary.json", "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    json.dump(top(uncovered, uncovered_ex, TOP * 2), open(OUT / "uncovered.json", "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    by_op = defaultdict(Counter)
    for k, v in tokens.items():
        by_op[k[:3]][k] = v
    json.dump({" | ".join(g): top(c, tokens_ex, 40) for g, c in sorted(by_op.items())}, open(OUT / "token_shapes.json", "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    json.dump(top(flags, flags_ex, TOP), open(OUT / "flags.json", "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    texts = Counter()
    for (s, field, lang, task, op), v in ops.items():
        texts[(s, field, lang, task, op)] = v
    json.dump({" | ".join(k): v for k, v in sorted(texts.items())}, open(OUT / "op_counts.json", "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    print(json.dumps(summary, indent=2, ensure_ascii=False))
