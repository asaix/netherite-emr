import importlib.util
import json
import random
import sys
from collections import Counter, defaultdict
from multiprocessing import Pool
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
DATA = ROOT / "experiments" / "2026-10-29_ed-analysis"
sys.path.insert(0, str(ROOT))

import parser as new


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


old = load("old_parser", DATA / "parser.py")
SETS = ["standard", "ron"]
DIFFICULTIES = ["short", "medium", "long", "very_long", "very_very_long"]
FIELDS = ["content", "reasoning_content"]
SAMPLES = 8


def ops(tokens):
    return Counter(t.split()[0] for t in tokens)


def kind(before, after):
    a, b = ops(before), ops(after)
    if a == b:
        return "args: " + " ".join(sorted({t.split()[0] for t in set(before) ^ set(after)}))
    gained, lost = b - a, a - b
    return " ".join([*(f"+{op}" for op in sorted(gained)), *(f"-{op}" for op in sorted(lost))])


def run(job):
    s, d = job
    random.seed(f"{s}/{d}")
    records = json.load(open(DATA / "parsed" / s / f"{d}.json", encoding="utf-8"))["records"]
    counts, examples = Counter(), defaultdict(list)
    for record in records:
        lang = record["meta"]["language"]
        for field in FIELDS:
            text = record[field]["original"]
            if text is None:
                continue
            o = old.parse_sentences(text, old.find_distractor(record))
            n = new.parse_sentences(text, new.find_distractor(record))
            segs = list(new.segments(text))
            key = (s, field, lang)
            counts[key + ("texts",)] += 1
            counts[key + ("segments",)] += len(segs)
            counts[key + ("covered_old",)] += sum(map(bool, o))
            counts[key + ("covered_new",)] += sum(map(bool, n))
            counts[key + ("tokens_old",)] += sum(map(len, o))
            counts[key + ("tokens_new",)] += sum(map(len, n))
            changed = False
            for seg, a, b in zip(segs, o, n):
                if a == b:
                    continue
                changed = True
                k = kind(a, b)
                counts[key + ("change", k)] += 1
                bucket = examples[(field, k)]
                if len(bucket) < SAMPLES or random.random() < 0.02:
                    entry = {"id": record["id"], "segment": seg[:300], "old": a, "new": b}
                    if len(bucket) < SAMPLES:
                        bucket.append(entry)
                    else:
                        bucket[random.randrange(SAMPLES)] = entry
            counts[key + ("texts_changed",)] += changed
    return counts, dict(examples)


if __name__ == "__main__":
    with Pool(4) as pool:
        results = pool.map(run, [(s, d) for s in SETS for d in DIFFICULTIES])
    counts, examples = Counter(), defaultdict(list)
    for c, e in results:
        counts.update(c)
        for k, v in e.items():
            examples[k].extend(v)
    summary = {}
    for key in sorted({k[:3] for k in counts}):
        c = {k[3]: v for k, v in counts.items() if k[:3] == key and len(k) == 4}
        changes = Counter({k[4]: v for k, v in counts.items() if k[:3] == key and len(k) == 5})
        summary["/".join(key)] = {
            "texts": c["texts"],
            "texts_changed_pct": round(100 * c["texts_changed"] / c["texts"], 2),
            "coverage_old_pct": round(100 * c["covered_old"] / c["segments"], 2),
            "coverage_new_pct": round(100 * c["covered_new"] / c["segments"], 2),
            "tokens_per_text_old": round(c["tokens_old"] / c["texts"], 2),
            "tokens_per_text_new": round(c["tokens_new"] / c["texts"], 2),
            "changes": dict(changes.most_common()),
        }
    out = HERE / "outputs"
    out.mkdir(exist_ok=True)
    json.dump(summary, open(out / "summary.json", "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    json.dump({f"{f} | {k}": random.sample(v, min(SAMPLES * 2, len(v))) for (f, k), v in sorted(examples.items())}, open(out / "examples.json", "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    print(json.dumps(summary, indent=2, ensure_ascii=False))
