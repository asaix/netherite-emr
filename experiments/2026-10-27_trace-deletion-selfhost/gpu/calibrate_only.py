"""Run the 90-question calibration against the server that is already running (no start, no smoke test).

Decoding comes from the environment, read by bringup.py at import:
TEMPERATURE, TOP_P, CAL_MAX_TOKENS, CAL_TAG (file suffix), CAL_CONCURRENCY.
Information only: the exit code is 0 whatever the accuracy, 5 if the server does not answer.
"""
import json
import os
import sys
import urllib.request

os.environ.setdefault("CAL_MODE", "info")  # label only: this script never stops or rejects anything
import bringup  # noqa: E402

try:
    urllib.request.urlopen(f"{bringup.URL}/v1/models", timeout=10).read()
except OSError as e:
    print(f"CALIBRATE ONLY: server not answering on {bringup.URL}: {e!r}", flush=True)
    sys.exit(5)
name = sys.argv[1] if len(sys.argv) > 1 else "redhat_v031_triton_mla"
ok, summary = bringup.calibrate(name)
print(f"CALIBRATE ONLY DONE: {json.dumps({k: summary[k] for k in ('decoding', 'finished', 'n', 'self_accuracy', 'api_accuracy')})}", flush=True)
