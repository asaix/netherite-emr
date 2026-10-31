import json
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(HERE.parent / "baseline"))
from common import gold_typed, my_extract, typed

LEVELS = ["short", "medium", "long", "very_long", "very_very_long"]
C = Counter()


def add(key, r, content):
    task = r["meta"]["task"]
    raw, _ = my_extract(content)
    pred = typed(task, raw)
    ok = pred is not None and pred == gold_typed(task, r["meta"]["answer"])
    if raw is not None or ok:
        C[key + "|n"] += 1
        C[key + "|ok"] += ok


for lv in LEVELS:
    d = json.loads((ROOT / "responses/standard" / f"{lv}.json").read_text())
    for r in d["records"] if isinstance(d, dict) else d:
        m = r["meta"]
        k = f"{m['language']}|{r['condition']}"
        add(k + "|all", r, r.get("content"))
        add(k + "|" + m["insertion"], r, r.get("content"))
        if int(m["question_id"]) < 50:
            add("sub|" + k + "|" + m["insertion"], r, r.get("content"))
            add("sub|" + k + "|all", r, r.get("content"))
    d = json.loads((ROOT / "responses/clp" / f"{lv}.json").read_text())
    for r in d["records"] if isinstance(d, dict) else d:
        add("sub|clp|" + r["meta"]["insertion"], r, r["stage2"].get("content"))
        add("sub|clp|all", r, r["stage2"].get("content"))


def acc(k):
    return 100 * C[k + "|ok"] / C[k + "|n"]


out = {}
for i in ("all", "no_insertion", "similar_insertion", "dissimilar_insertion"):
    out[f"gap_direct_{i}"] = acc(f"en_US|direct|{i}") - acc(f"hi_IN|direct|{i}")
    out[f"gap_cot_{i}"] = acc(f"en_US|cot|{i}") - acc(f"hi_IN|cot|{i}")
    out[f"gain_en_{i}"] = acc(f"en_US|cot|{i}") - acc(f"en_US|direct|{i}")
    out[f"gain_hi_{i}"] = acc(f"hi_IN|cot|{i}") - acc(f"hi_IN|direct|{i}")
    out[f"clp_minus_hi_cot_{i}"] = acc(f"sub|clp|{i}") - acc(f"sub|hi_IN|cot|{i}")
    out[f"gap_direct_subset_{i}"] = acc(f"sub|en_US|direct|{i}") - acc(f"sub|hi_IN|direct|{i}")
out = {k: round(v, 4) for k, v in out.items()}
(HERE / "exact.json").write_text(json.dumps(out, indent=2, ensure_ascii=False))
print(json.dumps(out, indent=2))
