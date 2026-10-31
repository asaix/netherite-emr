import gc
import hashlib
import subprocess
from collections import Counter

from common import *

EXP = ROOT / "experiments"
RUNS = {"short": EXP / "2026-10-17_run-short-leftover-rahul/outputs/results.json", "medium": EXP / "2026-10-17_run-medium-leftover-rahul/output/results.json", "long": EXP / "2026-10-16_finish-run-long-adi/outputs/long/results.json", "very_long": EXP / "2026-10-18_run-very-long-leftover-aayush/output/results.json", "very_very_long": EXP / "2026-10-18-very_very_long-aayush/output/results.json"}
ON = {d: EXP / f"2026-10-25_test-reasoning-on/outputs/{d}/results.json" for d in LEVELS}
EARLY = {"short": EXP / "2026-09-29_run-short-rahul/outputs/results.json", "medium": EXP / "2026-09-29_run-medium-rahul", "long": EXP / "2026-09-29_run-long-adi", "very_long": EXP / "2026-09-30_run-very-long-aayush"}


def sig(r):
    return hashlib.md5(json.dumps({k: r.get(k) for k in ("id", "condition", "meta", "request", "content", "reasoning_content", "finish_reason", "usage", "time")}, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


out = {"levels": {}}
std = {}
for lvl in LEVELS:
    a = json.load(open(ROOT / "responses/standard" / f"{lvl}.json", encoding="utf-8"))
    b = json.load(open(RUNS[lvl], encoding="utf-8"))
    sa, sb = {r["id"]: sig(r) for r in a}, {r["id"]: sig(r) for r in b}
    std.update(sa)
    c = Counter(f"{r['meta']['task']}/{r['meta']['question_id']}" for r in a)
    out["levels"][lvl] = {"responses_standard": len(a), "unique_ids": len(sa), "responses_run": len(b), "identical_to_run": sum(sa[k] == sb.get(k) for k in sa), "only_in_run": len(set(sb) - set(sa)), "only_in_standard": len(set(sa) - set(sb)), "questions": len(c), "all_12": all(v == 12 for v in c.values()), "cut_off_finish_length": sum(r["finish_reason"] == "length" for r in a), "tasks": len({r["meta"]["task"] for r in a})}
    del a, b
    gc.collect()
out["total_responses"] = sum(v["responses_standard"] for v in out["levels"].values())
out["total_questions"] = sum(v["questions"] for v in out["levels"].values())
early = {}
for lvl, p in EARLY.items():
    fs = [p] if p.suffix == ".json" else sorted(p.rglob("results.json"))
    for f in fs:
        b = json.load(open(f, encoding="utf-8"))
        same = sum(std.get(r["id"]) == sig(r) for r in b)
        early[str(f.relative_to(ROOT))] = {"records": len(b), "identical_in_standard": same}
        del b
out["early_runs_subset"] = early
mid = json.load(open(EXP / "2026-10-01_analysis-rahul/merged_results.json", encoding="utf-8"))
midq = Counter(f"{r['meta']['difficulty']}/{r['meta']['task']}/{r['meta']['question_id']}" for r in mid)
mid_full = sorted(q for q, n in midq.items() if n == 12)
out["mid_merged"] = {"records": len(mid), "identical_in_standard": sum(std.get(r["id"]) == sig(r) for r in mid), "questions_any": len(midq), "questions_all_12": len(mid_full), "records_in_all_12": sum(midq[q] for q in mid_full)}
json.dump(mid_full, open(CACHE / "mid_qids.json", "w"), indent=2)
del mid
gc.collect()
on_ident = {}
ron = 0
for lvl in LEVELS:
    a = json.load(open(ROOT / "responses/ron" / f"{lvl}.json", encoding="utf-8"))
    b = json.load(open(ON[lvl], encoding="utf-8"))
    sb = {r["id"]: sig(r) for r in b}
    on_ident[lvl] = {"records": len(a), "identical": sum(sb.get(r["id"]) == sig(r) for r in a), "questions": len({f"{r['meta']['task']}/{r['meta']['question_id']}" for r in a}), "qnums": sorted({int(r["meta"]["question_id"]) for r in a})}
    ron += len(a)
    del a, b
out["ron"] = on_ident
out["ron_total"] = ron
F = frame()
t = pd.to_datetime(F.time)
late = F[t >= "2026-10-28"]
out["filled_in"] = {"responses_after_oct28": len(late), "questions": sorted(late.qid.unique()), "dates": sorted(set(t[t >= "2026-10-28"].dt.date.astype(str)))}
diff = subprocess.run(["git", "show", "d7e7bfe", "--", "experiments/2026-10-18-very_very_long-aayush/output/errors.json"], cwd=ROOT, capture_output=True, text=True).stdout
ids = sorted(set(re.findall(r'^-\s*"id": "([^"]+)"', diff, re.M)))
out["filled_in"]["errors_removed_by_d7e7bfe"] = len(ids)
out["filled_in"]["error_ids_sample"] = ids[:12]
q_f = sorted({"/".join(i.split("/")[:3]).replace("_en_US", "").replace("_hi_IN", "") for i in ids})
out["filled_in"]["questions_from_errors"] = q_f
rows = F[F.qid.isin(q_f)]
out["filled_in"]["records_in_questions"] = len(rows)
out["filled_in"]["time_range"] = [str(pd.to_datetime(rows.time).min()), str(pd.to_datetime(rows.time).max())]
out["filled_in"]["n_records_on_oct29"] = int((pd.to_datetime(rows.time) >= "2026-10-28").sum())
out["filled_in"]["acc_answered"] = round(float(rows.acc.mean()), 4)
out["dates"] = {str(k): int(v) for k, v in t.dt.date.value_counts().sort_index().items()}
dump(out, "integrity.json")
print(json.dumps(out, indent=1, ensure_ascii=False)[:6000])
