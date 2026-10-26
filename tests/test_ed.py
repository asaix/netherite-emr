import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ed import edit_distance

assert edit_distance([], []) == 0
assert edit_distance(["GIVEN 2025-05-26"], []) == 1
assert edit_distance(["SUB 26 4", "ANSWER 2025-05-22"], ["SUB 2025-05-26 4", "ANSWER 2025-05-22"]) == 1
assert edit_distance(list("kitten"), list("sitting")) == 3
assert edit_distance(["STEP", "STEP", "STEP", "ANSWER"], ["SUB", "ANSWER"]) == 3
print("5 edit distance checks passed")
