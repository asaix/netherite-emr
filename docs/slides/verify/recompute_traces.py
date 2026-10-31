import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
FR = ROOT / "experiments/2026-10-31_final-report"
p = pd.read_csv(FR / "audit/lr/pairs.csv.gz")
print(list(p.columns), len(p))
t = pd.read_pickle(FR / "audit/part_c_encot/cache/tidy.pkl")
sub = t[t.qn < 50]
res = {}
for name, x in [("English CoT", sub[(sub.source == "standard") & (sub.lang == "en_US") & (sub.cond == "cot")]), ("en-CoT", sub[sub.source == "en-cot"]), ("Hindi CoT", sub[(sub.source == "standard") & (sub.lang == "hi_IN") & (sub.cond == "cot")])]:
    res[name] = {"all": round(100 * x.verif.mean(), 1), "scored": round(100 * x[x.scored].verif.mean(), 1), "stop": round(100 * x[x.finish == "stop"].verif.mean(), 1)}
s = t[(t.source == "standard") & (t.cond == "cot") & (t.ins == "similar_insertion")]
res["mentions"] = {f"{l} {c}": round(100 * s[s.lang == l][c].mean(), 1) for l in ["en_US", "hi_IN"] for c in ["m_similar_own", "m_similar_hi", "m_similar_en", "m_similar_both"]}
d = t[(t.source == "standard") & (t.cond == "cot") & (t.task == "day_of_week") & t.scored & (~t.correct.astype(bool))]
res["dow_late_full"] = {l: {"late": int((d[d.lang == l].wk_off == 1).sum()), "wrong_formatted": int(d[(d.lang == l)].wk_off.notna().sum())} for l in ["en_US", "hi_IN"]}
d2 = sub[(sub.source == "standard") & (sub.cond == "cot") & (sub.task == "day_of_week") & sub.scored & (~sub.correct.astype(bool))]
res["dow_late_subset"] = {l: {"late": int((d2[d2.lang == l].wk_off == 1).sum()), "wrong_formatted": int(d2[(d2.lang == l)].wk_off.notna().sum())} for l in ["en_US", "hi_IN"]}
print(json.dumps(res, indent=1))
(OUT / "recomputed_traces.json").write_text(json.dumps(res, indent=2, ensure_ascii=False))
