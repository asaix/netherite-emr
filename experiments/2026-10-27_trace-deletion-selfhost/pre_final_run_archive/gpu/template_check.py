import json
import sys
from pathlib import Path

from huggingface_hub import hf_hub_download
from transformers import AutoTokenizer

REPO = "sarvamai/sarvam-105b-fp8"
FILES = ["tokenizer.json", "tokenizer_config.json", "special_tokens_map.json", "chat_template.jinja", "config.json", "configuration_sarvam_moe.py"]
EXP = Path(__file__).resolve().parent.parent
BOS_ID, END_OF_TURN_ID, ASSISTANT = 6, 26, "<|start_of_turn|><|assistant|>"

local = Path(hf_hub_download(REPO, FILES[0])).parent
for f in FILES[1:]:
    hf_hub_download(REPO, f)
try:
    tok = AutoTokenizer.from_pretrained(local)
except Exception:
    tok = AutoTokenizer.from_pretrained(local, trust_remote_code=True)
reqs = json.load(open(EXP / "outputs" / "requests_cap1000.json", encoding="utf-8"))
by = {r["id"]: r for r in reqs}
hi_a = next(r for r in reqs if r["meta"]["language"] == "hi_IN" and r["meta"]["version"] == "A")
sid = hi_a["meta"]["source_id"]
en_a = next(r for r in reqs if r["meta"]["language"] == "en_US" and r["meta"]["version"] == "A")
cases = [
    ("open-ended continuation", [{"role": "user", "content": "Write two sentences about the capital of France."}, {"role": "assistant", "content": "The capital of France is"}], True),
    ("Hindi A", by[sid + "/A"]["messages"], True),
    ("Hindi B", by[sid + "/B"]["messages"], True),
    ("Hindi C", by[sid + "/C"]["messages"], True),
    ("English A", en_a["messages"], True),
    ("fresh with <think></think> (informational)", [hi_a["messages"][0], {"role": "assistant", "content": "<think></think>"}], False),
]
ok_all = True
print(f"transformers tokenizer: {type(tok).__name__}; special ids: [@BOS@]={tok.convert_tokens_to_ids('[@BOS@]')}, <|end_of_turn|>={tok.convert_tokens_to_ids('<|end_of_turn|>')}")
for name, messages, blocking in cases:
    text = tok.apply_chat_template(messages, tokenize=False, add_generation_prompt=False, continue_final_message=True,
                                   enable_thinking=False, reasoning_effort=None)
    final = messages[-1]["content"].strip()
    tail = text.split(ASSISTANT)[-1]
    ids = tok(text, add_special_tokens=False)["input_ids"]
    after = ids[len(ids) - len(tok(tail, add_special_tokens=False)["input_ids"]):]
    checks = {
        "user turn ends with <|nothink|>": "<|nothink|><|end_of_turn|>" in text,
        "prompt ends exactly with the assistant prefix": text.endswith(final),
        "assistant part is '\\n<think></think>\\n' + prefix": tail == "\n<think></think>\n" + final,
        "no <|end_of_turn|> after the assistant opener": "<|end_of_turn|>" not in tail and END_OF_TURN_ID not in after,
        "exactly one [@BOS@], at the start": ids[0] == BOS_ID and ids.count(BOS_ID) == 1,
    }
    passed = all(checks.values())
    ok_all &= passed or not blocking
    print(f"\n=== {name}: {'PASS' if passed else ('FAIL' if blocking else 'INFO')} ({len(ids)} prompt tokens)")
    for k, v in checks.items():
        print(f"  [{'ok' if v else 'NO'}] {k}")
    print(f"  assistant part as rendered: {tail[:160]!r}{' ...' if len(tail) > 160 else ''}")
    print(f"  last 12 tokens: {tok.convert_ids_to_tokens(ids[-12:])}")
print("\nTEMPLATE CHECK:", "PASS" if ok_all else "FAIL")
sys.exit(0 if ok_all else 1)
