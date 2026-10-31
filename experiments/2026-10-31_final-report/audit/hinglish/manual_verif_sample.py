import json
import random
from pathlib import Path

from features import ANS, DIFFS, FN, LATIN, ROOT, VERIF_EXT, VERIF_ORIG

random.seed(11)
rows = []
for d in DIFFS:
    for r in json.load(open(ROOT / "responses/hinglish" / f"{d}.json", encoding="utf-8")):
        if r["meta"]["language"] != "en_US" or r["finish_reason"] != "stop":
            continue
        b = ANS.sub("", r["content"])
        w = [x.lower() for x in LATIN.findall(b)]
        if w and sum(x in FN["wide"] for x in w) / len(w) >= 0.05:
            rows.append({"id": r["id"], "orig": bool(VERIF_ORIG.search(b)), "ext": bool(VERIF_EXT.search(b)), "tail": b.strip()[-420:]})
pick = random.sample([r for r in rows if not r["ext"]], 30) + random.sample([r for r in rows if r["ext"] and not r["orig"]], 15)
Path(__file__).with_name("results").joinpath("manual_verif_sample.json").write_text(json.dumps(pick, indent=2, ensure_ascii=False), encoding="utf-8")
for p in pick:
    print(p["id"], p["orig"], p["ext"])
    print(p["tail"].replace("\n", " / "))
    print()
