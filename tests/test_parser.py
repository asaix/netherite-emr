import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from parser import parse

CASES = {
    "1 day before: 2025-05-25": ["STEP 2025-05-25 -1"],
    "26 में से 4 घटाने पर 22 आता है।": ["SUB 26 4"],
    "First, I'll subtract 29 days from May 2, 2027.": ["SUB 2027-05-02 29"],
    "Total: 31 + 28 + 31 = 90 days": ["ADD 31 28", "ADD 28 31"],
    "अब मिनटों को देखें: 26 मिनट + 9 मिनट = 35 मिनट।": ["ADD 26 9"],
    "456 ÷ 7 = 65 remainder 1": ["DIV 456 7"],
    "h = (31 + 10 - 40) mod 7": ["ADD 31 10", "SUB 10 40", "DIV () 7"],
    "7 × (3 + 2) = 35": ["MUL 7 ()", "ADD 3 2"],
    "h = (q + ⌊13(m+1)/5⌋ + K) mod 7": ["DIV () 5", "DIV () 7"],
    "2025-08-26 (Tuesday) + 3 days": ["ANCHOR 2025-08-26 Tuesday"],
    "Thursday - 2 = Tuesday.": ["SUB Thursday 2"],
    "सोमवार से 6 दिन बाद रविवार आता है।": ["ADD Monday 6"],
    "From 07:34 to 09:07:": ["SUB 07:34 09:07"],
    "1 मार्च = बुधवार।": ["ANCHOR 03-01 Wednesday"],
    "February 4 = Thursday": ["ANCHOR 02-04 Thursday"],
    "h = 2 means Monday": ["CONVERT 2 WEEKDAY"],
    "101 minutes = 1 hour and 41 minutes": ["CONVERT 101 HOURS"],
    "Feb 28 = 59": ["CONVERT 02-28 DAY_OF_YEAR"],
    "January has 31 days": ["MONTHLEN 01"],
    "2024 is a leap year (divisible by 4)": ["LEAP 2024"],
    "Without counting today, the 7th occurrence is 7 intervals.": ["RULE EXCLUDE_TODAY"],
    "तो, 10:62 का मतलब 11:02 हो जाता है।": ["ROLL HOUR"],
    "Wait, let me verify this with another approach.": ["REVISE", "CHECK", "PLAN"],
    "Answer: 2025-12-15 to 2025-12-21": ["ANSWER 2025-12-15..2025-12-21"],
    "Answer: सोमवार": ["ANSWER Monday"],
}

for text, expected in CASES.items():
    assert parse(text) == expected, (text, parse(text))

assert parse(None) is None
assert parse("आज 2025-05-26 है। इसलिए, 4 दिन पहले की तारीख 2025-05-22 थी।\n\nAnswer: 2025-05-22") == ["GIVEN 2025-05-26", "ANSWER 2025-05-22", "ANSWER 2025-05-22"]
assert parse("मेरे भाई ने मोटरसाइकिल खरीदी। भाई की मोटरसाइकिल का इस सवाल से कोई संबंध नहीं है।", "मेरे भाई ने मोटरसाइकिल खरीदी।") == ["IGNORE", "IGNORE"]
print(f"{len(CASES) + 3} parser checks passed")
