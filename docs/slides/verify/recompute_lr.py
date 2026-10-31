import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
p = pd.read_csv(ROOT / "experiments/2026-10-31_final-report/audit/lr/pairs.csv.gz")
p = p[p.en_correct.notna() & p.hi_correct.notna() & p.c_full.notna()].copy()
p["en_correct"] = p.en_correct.astype(bool)
p["hi_correct"] = p.hi_correct.astype(bool)
p["y"] = (p.en_correct.astype(bool) != p.hi_correct.astype(bool)).astype(int)
p["gap"] = (p.c_full_en - p.c_full_hi).abs() / p[["c_full_en", "c_full_hi"]].max(axis=1)
p["cl"] = p.difficulty + "/" + p.task + "/" + p.question_id.astype(str)
res = {"pairs": len(p), "off": int((p["mode"] == "off").sum()), "disagree_pct": round(100 * p.y.mean(), 2), "rds_disagree": round(p[p.y == 1].c_full.mean(), 3), "rds_agree": round(p[p.y == 0].c_full.mean(), 3)}
res["outcomes"] = {"both": int((p.en_correct & p.hi_correct).sum()), "en_only": int((p.en_correct & ~p.hi_correct).sum()), "hi_only": int((~p.en_correct & p.hi_correct).sum()), "neither": int((~p.en_correct & ~p.hi_correct).sum())}
base = "y ~ {} + C(task) + C(difficulty) + C(insertion) + C(mode)"
for name, col, extra in [("full", "c_full", ""), ("full + length gap", "c_full", " + gap"), ("no answer tokens", "c_noans", ""), ("op types, no answers", "c_opsnoans", "")]:
    x = p[p[col].notna()]
    groups = x.cl.astype("category").cat.codes
    m = smf.logit(base.format(col) + extra, x).fit(disp=0, cov_type="cluster", cov_kwds={"groups": groups})
    b, se = m.params[col], m.bse[col]
    res[name] = {"n": len(x), "or_per_0.1": round(float(np.exp(b / 10)), 3), "lo": round(float(np.exp((b - 1.96 * se) / 10)), 3), "hi": round(float(np.exp((b + 1.96 * se) / 10)), 3)}
(OUT / "recomputed_lr.json").write_text(json.dumps(res, indent=2))
print(json.dumps(res, indent=1))
