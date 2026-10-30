import json
import sys
from collections import defaultdict
from pathlib import Path

from huggingface_hub import hf_hub_download
from transformers import AutoTokenizer

REPO = "sarvamai/sarvam-105b-fp8"
FILES = ["tokenizer.json", "tokenizer_config.json", "special_tokens_map.json", "chat_template.jinja", "config.json", "configuration_sarvam_moe.py"]
EXP = Path(__file__).resolve().parent.parent
BOS_ID, END_OF_TURN_ID, ASSISTANT, EMPTY = 6, 26, "<|start_of_turn|><|assistant|>", "<think></think>"

local = Path(hf_hub_download(REPO, FILES[0])).parent
for f in FILES[1:]:
    hf_hub_download(REPO, f)
try:
    tok = AutoTokenizer.from_pretrained(local)
except Exception:
    tok = AutoTokenizer.from_pretrained(local, trust_remote_code=True)
traces = defaultdict(dict)
for r in json.load(open(EXP / "outputs" / "requests_resample.json", encoding="utf-8")):
    traces[r["meta"]["source_id"]][r["meta"]["arm"]] = r
pick = [next(t for t in traces.values() if t["P"]["meta"]["language"] == lang and t["P"]["meta"]["opening_mention"] == opening and (opening or t["P"]["meta"]["first_mention"] >= 2))
        for lang in ("hi_IN", "en_US") for opening in (True, False)]


def render(messages):
    text = tok.apply_chat_template(messages, tokenize=False, add_generation_prompt=False, continue_final_message=True, enable_thinking=False, reasoning_effort=None)
    return text, tok(text, add_special_tokens=False)["input_ids"]


ok_all = True
tails = {}
for t in pick:
    sid = t["P"]["meta"]["source_id"]
    print(f"\n##### {sid} (first mention at sentence {t['P']['meta']['first_mention']})")
    texts = {}
    for arm, r in t.items():
        text, ids = render(r["messages"])
        texts[arm] = text
        final = r["messages"][-1]["content"]
        tail = text.split(ASSISTANT)[-1]
        checks = {
            "user turn ends with <|nothink|>": "<|nothink|><|end_of_turn|>" in text,
            "exactly one [@BOS@], at the start": ids[0] == BOS_ID and ids.count(BOS_ID) == 1,
            "no <|end_of_turn|> after the assistant opener": "<|end_of_turn|>" not in tail,
        }
        if final == EMPTY:
            tails[tail] = tails.get(tail, 0) + 1
        else:
            checks["assistant part is '\\n<think></think>\\n' + prefix"] = tail == "\n<think></think>\n" + final.strip()
        passed = all(checks.values())
        ok_all &= passed
        print(f"=== {arm}{' (empty prefix)' if final == EMPTY else ''}: {'PASS' if passed else 'FAIL'} ({len(ids)} prompt tokens)")
        for k, v in checks.items():
            print(f"  [{'ok' if v else 'NO'}] {k}")
        print(f"  assistant part as rendered: {tail[:140]!r}{' ...' if len(tail) > 140 else ''}")
    same_tail = texts["Q"].split(ASSISTANT)[-1] == texts["P"].split(ASSISTANT)[-1]
    distractor_only = texts["P"].split(ASSISTANT)[0] != texts["Q"].split(ASSISTANT)[0]
    ok_all &= same_tail and distractor_only
    print(f"  [{'ok' if same_tail and distractor_only else 'NO'}] Q and P differ in the user question and not in the assistant part")
print("\nempty-prefix assistant part as rendered (informational):", {repr(k): v for k, v in tails.items()})
print("TEMPLATE CHECK:", "PASS" if ok_all else "FAIL")
sys.exit(0 if ok_all else 1)
