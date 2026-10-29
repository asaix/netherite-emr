import json
from pathlib import Path

from build_requests import M, ROOT, RUNS, save
from run import HERE, Keys, call, load_config

FLAGS = {"continue_final_message": True, "add_generation_prompt": False}
SHORT = {"model": "sarvam-105b", "reasoning_effort": None, "temperature": 0.0, "top_p": 1.0, "max_tokens": 300}
RESTART = "very_long/interval_date_en_US/10/similar_insertion/cot"
DRIFTED = "short/time_addition_hi_IN/103/similar_insertion/cot"
REPEAT = [
    "short/time_addition_hi_IN/103/similar_insertion/cot",
    "long/day_of_week_hi_IN/37/similar_insertion/cot",
    "medium/interval_date_en_US/60/similar_insertion/cot",
    "short/interval_date_en_US/76/similar_insertion/cot",
]

cfg = load_config(HERE / "config" / "run.cfg")
keys = Keys(cfg["keys"])
pilot = {r["id"]: r for r in json.load(open(HERE / "outputs" / "requests_pilot.json", encoding="utf-8"))}
originals = {r["id"]: r for run in RUNS for r in json.load(open(ROOT / "experiments" / run / "results.json", encoding="utf-8")) if r["id"] in REPEAT}
out = []


def go(name, payload, note=""):
    data, _ = call(cfg, keys, payload)
    content = data["choices"][0]["message"].get("content") or ""
    out.append({"test": name, "note": note, "content": content, "finish_reason": data["choices"][0].get("finish_reason")})
    print(f"=== {name} {note}\n{content[:300]!r}\n", flush=True)
    return content


paris = [{"role": "user", "content": "Write one sentence about the capital of France."}, {"role": "assistant", "content": "The capital of France is Par"}]
go("1 split-word prefill, plain", {**SHORT, "messages": paris}, "true continuation starts with 'is'; a new turn restarts the sentence")
go("2 split-word prefill, flags", {**SHORT, "messages": paris, **FLAGS})
restart = pilot[RESTART + "/A"]
go("3 English A prefix, plain", {**SHORT, "messages": restart["messages"]}, "restart if it begins 'I need to find'")
go("4 English A prefix, flags", {**SHORT, "messages": restart["messages"], **FLAGS})
go("5 Hindi A prefix, flags", {**SHORT, "messages": pilot[DRIFTED + "/A"]["messages"], **FLAGS}, "compare with the pilot A continuation")
for sid in REPEAT:
    o = originals[sid]
    payload = {k: v for k, v in o["request"].items()}
    for i in (1, 2):
        c = go(f"6 repeat original request {i}", payload, sid)
        out[-1].update({"source_id": sid, "answer": M.extract_answer(c), "original_answer": M.extract_answer(o["content"]), "identical_to_original": c == o["content"]})
        print(f"   answer {out[-1]['answer']} | original {out[-1]['original_answer']} | identical text {out[-1]['identical_to_original']}\n", flush=True)

(HERE / "outputs" / "diag").mkdir(exist_ok=True)
save(HERE / "outputs" / "diag" / "continuation_diag.json", out)
print("saved outputs/diag/continuation_diag.json")
