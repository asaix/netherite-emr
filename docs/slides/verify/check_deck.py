import json
import re
import subprocess
import sys
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
FR = ROOT / "experiments/2026-10-31_final-report"
sys.path.insert(0, str(ROOT))
from ed import edit_distance as distance

en = ["GOAL DATE", "GIVEN 2025-09-11", "ADD 2025-09-12 1", "ADD 2025-09-13", "ANSWER 2025-09-13", "SPITANSWER 2025-09-13"]
hi = ["GIVEN 2025-09-11", "ADD 2025-09-13 2", "ANSWER 2025-09-13", "SPITANSWER 2025-09-13"]
wrong = hi[:2] + ["ANSWER 2025-09-14", "SPITANSWER 2025-09-14"]
print("example", distance(en, hi), distance(en, wrong))
corpus = ""
for p in [FR / "report/main.tex", FR / "report/appendix.tex", FR / "report/tables/accuracy.tex", FR / "report/tables/baseline.tex", FR / "CONSOLIDATED_ANALYSIS.md", FR / "audit/lr/analysis.md", FR / "audit/baseline/analysis.md", FR / "audit/hinglish/analysis.md", FR / "audit/part_a_clp/analysis.md", FR / "audit/part_b_interventions/analysis.md", FR / "audit/part_c_encot/analysis.md", *FR.glob("audit/part_c_encot/tables/c5_error_profile.csv"), *HERE.glob("recomputed*.json"), *(HERE.parent / "data").glob("*.csv")]:
    corpus += p.read_text(encoding="utf-8") + "\n"
known = {x.rstrip(".,").replace(",", "") for x in re.findall(r"\d[\d,]*\.?\d*", corpus)}
text = subprocess.run(["pdftotext", "-layout", str(HERE.parent / "ANLP Final Slides.pdf"), "-"], capture_output=True, text=True).stdout
pages = text.split("\f")
out = {}
for i, page in enumerate(pages, 1):
    miss = sorted({n for n in (x.rstrip(".,").replace(",", "") for x in re.findall(r"\d[\d,]*\.?\d*", page)) if n not in known})
    if miss:
        out[i] = miss
print(json.dumps(out, ensure_ascii=False))
