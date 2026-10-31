import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
STEPS = ["build_frame.py", "integrity.py", "rq.py", "secondary.py", "ron.py", "raw_checks.py", "raw_mentions.py", "dataset_checks.py", "hand_sample.py", "hand_mentions.py", "figdata.py", "make_analysis.py", "make_claims.py"]
for s in STEPS:
    print("==", s, flush=True)
    subprocess.run([sys.executable, "-B", s], cwd=HERE, check=True, stdout=subprocess.DEVNULL if s.startswith("hand") else None)
