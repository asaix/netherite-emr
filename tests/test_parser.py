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
    "Answer: 2025-12-15 to 2025-12-21": ["SPITANSWER 2025-12-15..2025-12-21"],
    "Answer: सोमवार": ["SPITANSWER Monday"],
    "recurrence every 11 days, starting from today (2026-11-11)": ["GIVEN 2026-11-11"],
    "पहली तिथि 29 मार्च 2028 है और दूसरी तिथि 6 अप्रैल 2028 है।": ["GIVEN 2028-03-29"],
    "यहां 12 घंटे और 52 मिनट व्यतीत हुए।": ["SUB 12 52"],
    "34 घंटे को हम 24 घंटे और 10 घंटे में विभाजित करते हैं।": ["DIV 34 24"],
    "344 दिन 2038 में 20 दिसंबर के बराबर होता है।": ["CONVERT 344"],
    "2000 का विशेष दिन मंगलवार है।": ["ANCHOR 2000 Tuesday"],
    "2025 की शुरुआत बुधवार से हुई थी": ["ANCHOR 2025 Wednesday"],
    "छह बजे से सात बजे तक का अंतर": ["SUB 06:00 07:00"],
    "रात के दस बजकर दो मिनट से 3 घंटे पहले": ["SUB 22:02 3"],
    "दोपहर 2 बजे में 1 घंटा जोडें": ["ADD 14:00 1"],
    "+31 = 212": ["CUMADD 31"],
    "-2 = Friday.": ["CUMSUB 2"],
    "+1 day: 2025-05-27": ["STEP 2025-05-27 +1"],
    "Aug 31 -> 243": ["CONVERT 08-31 DAY_OF_YEAR"],
    "Jul 212": ["CONVERT 212 DAY_OF_YEAR"],
    "-2J = -40": [],
    "−126 + 1440 = 1314 minutes.": ["ADD 126 1440"],
    "+35 weeks = November 9.": ["CUMADD 35"],
    "+30 (2): Jul 1: Tue": ["CUMADD 30", "ANCHOR 07-01 Tuesday"],
    "2032 एक लीप वर्ष है क्योंकि यह 4 से पूरी तरह विभाजित होता है।": ["LEAP 2032"],
    "10 को 7 से विभाजित करने पर शेष 3 बचता है।": ["DIV 10 7"],
    "1900 लीप वर्ष नहीं है क्योंकि यह 100 से विभाजित है लेकिन 400 से नहीं।": ["LEAP 1900"],
    "अब हमें यह देखना है कि क्या यह अंतर 5 या 9 के बराबर है।": ["PLAN", "SUB 5 9"],
    "210 दिन 30 सप्ताह के बराबर होते हैं।": ["CONVERT 210"],
    "दूसरा, आज की विशेष दिनांक 2025-07-30 है।": [],
    "2031 में भी 365 दिन होते हैं, जिससे 2032 की शुरुआत शुक्रवार को होती है।": ["LEAP 2031", "ANCHOR 2032 Friday"],
    "For 2025: The anchor day for 2000 is Tuesday.": ["PLAN ANCHOR_COUNT", "ANCHOR 2000 Tuesday"],
    "So 1187 days later is 4 days after Monday, which is Friday.": ["ADD Monday 1187", "ANCHOR"],
    "11 बजे से 9 बजे तक 2 घंटे होते हैं।": ["SUB 11:00 09:00"],
}

for text, expected in CASES.items():
    assert parse(text) == expected, (text, parse(text))

assert parse(None) is None
assert parse("आज 2025-05-26 है। इसलिए, 4 दिन पहले की तारीख 2025-05-22 थी।\n\nAnswer: 2025-05-22") == ["GIVEN 2025-05-26", "ANSWER 2025-05-22", "SPITANSWER 2025-05-22"]
assert parse("मेरे भाई ने मोटरसाइकिल खरीदी। भाई की मोटरसाइकिल का इस सवाल से कोई संबंध नहीं है।", "मेरे भाई ने मोटरसाइकिल खरीदी।") == ["IGNORE", "IGNORE"]
print(f"{len(CASES) + 3} parser checks passed")
