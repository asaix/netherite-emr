import csv
import json
import re
from pathlib import Path

HERE = Path(__file__).parent
ROOT = HERE.parents[1]
SOURCES = [HERE / "audit" / n / "analysis.md" for n in ["baseline", "hinglish", "lr", "part_a_clp", "part_b_interventions", "part_c_encot"]]
SOURCES += [ROOT / "tests/ed_audit/outputs/final_report_audit/analysis.md", HERE / "CONSOLIDATED_ANALYSIS.md", ROOT / "docs/final/ANALYSIS.md", HERE / "audit/lr/corrected_regression_table.csv", HERE / "audit/error_trends/error-trends.txt"]
NUM = re.compile(r"(?<![\w.\-])\d[\d,]*(?:\.\d+)?(?![\w])")


def strip_tex(t):
    t = t[t.index("\\begin{abstract}"):]
    t = re.sub(r"(?m)(?<!\\)%.*$", "", t)
    t = re.sub(r"\\begin\{tikzpicture\}.*?\\end\{tikzpicture\}", " ", t, flags=re.S)
    t = re.sub(r"\\(?:cite[a-z]*|label|ref|includegraphics(?:\[[^\]]*\])?|input|bibliography|section\*?|subsection|addcontentsline)\{[^}]*\}", " ", t)
    t = re.sub(r"\[width=[^\]]*\]|\[t\]|\[!ht\]|\\setlength\{[^}]*\}\{[^}]*\}|\{\\textwidth\}", " ", t)
    return t.replace("$-$", "-").replace("\\%", "%")


def corpus():
    files = {}
    for p in SOURCES:
        files[str(p.relative_to(ROOT))] = set(x.replace(",", "") for x in NUM.findall(p.read_text()))
    h = json.loads((HERE / "headline.json").read_text())
    vals = set()

    def walk(o):
        if isinstance(o, dict):
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)
        elif isinstance(o, (int, float)):
            a = abs(float(o))
            vals.update({f"{a:.1f}", f"{a:.2f}", str(o)})
    walk(h)
    files["experiments/2026-10-31_final-report/headline.json"] = vals
    return files


files = corpus()
rows, missing = [], 0
for name in ["main.tex", "appendix.tex"]:
    raw = (HERE / "report" / name).read_text()
    text = strip_tex(raw) if name == "main.tex" else raw
    for para in re.split(r"\n\s*\n", text):
        for sent in re.split(r"(?<=[.;:])\s+", para):
            for m in NUM.finditer(sent):
                v = m.group(0).replace(",", "")
                if float(v) <= 9 and "." not in v:
                    continue
                if re.fullmatch(r"20\d\d", v):
                    continue
                src = [k for k, s in files.items() if v in s]
                rows.append({"file": name, "value": m.group(0), "sentence": re.sub(r"\s+", " ", sent)[:220], "sources": "; ".join(src[:3]), "status": "found" if src else "NOT_FOUND"})
                missing += not src
with open(HERE / "claims_ledger.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["file", "value", "sentence", "sources", "status"])
    w.writeheader()
    w.writerows(rows)
print(len(rows), "numbers,", missing, "not found")
for r in rows:
    if r["status"] != "found":
        print(r["value"], "|", r["sentence"][:150])
