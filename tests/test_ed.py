import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ed import CONFIG, edit_distance

half = CONFIG["partial_date_cost"]

assert edit_distance([], []) == 0
assert edit_distance(["GIVEN 2025-05-26"], []) == 1
assert edit_distance(["SUB 26 4", "ANSWER 2025-05-22"], ["SUB 2025-05-26 4", "ANSWER 2025-05-22"]) == half
assert edit_distance(list("kitten"), list("sitting")) == 3
assert edit_distance(["STEP", "STEP", "STEP", "ANSWER"], ["SUB", "ANSWER"]) == 3

assert edit_distance(["SUB 2025-06-05 3"], ["SUB 06-05 3"]) == half
assert edit_distance(["MONTHLEN 2025-02"], ["MONTHLEN 02"]) == half
assert edit_distance(["ANCHOR 2025-06-05 Thursday"], ["ANCHOR 5 Thursday"]) == half
assert edit_distance(["SUB 2025-06-05 2025-06-02"], ["SUB 06-05 2"]) == half
assert edit_distance(["ANSWER 2025-06-02..2025-06-08"], ["ANSWER 06-02..06-08"]) == half
assert edit_distance(["SUB 2025-06-04 1"], ["SUB 06-05 3"]) == 1
assert edit_distance(["SUB 2025-06-05 3"], ["SUB 2025-06-05 4"]) == 1
assert edit_distance(["SUB 2025-06-05 3"], ["ADD 06-05 3"]) == 1
assert edit_distance(["MONTHLEN 2025-02"], ["MONTHLEN 03"]) == 1
assert edit_distance(["SUB 2025-06-05 3"], ["SUB 06-05"]) == 1
assert edit_distance(["ADD 21:34 6"], ["ADD 34 6"]) == 1
assert edit_distance(["SUB 2025-06-05 3", "SUB 06-02 3"], ["SUB 06-05 3", "SUB 2025-06-02 3"]) == 2 * half
print("17 edit distance checks passed")
