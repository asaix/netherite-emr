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
    "344 दिन 2038 में 20 दिसंबर के बराबर होता है।": ["CONVERT 12-20"],
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
    "So January 1, 2025 is Monday + 2 = Wednesday?": ["ANCHOR 2025-01-01 Wednesday", "ADD Monday 2"],
    "So February 14, 2025 is 2 days after Wednesday.": ["ADD 2025-02-14 2"],
    "today is 2025-04-17 and Monday is the first day of the week": ["GIVEN 2025-04-17", "RULE MONDAY_FIRST"],
    "2025-11-03 से 14 दिन बाद 2025-11-17 आता है, जो रविवार है।": ["ANCHOR 2025-11-17 Sunday", "ADD 2025-11-03 14"],
    "January: 31 days, so February 1 is day 32": ["MONTHLEN 01", "CONVERT 02-01 DAY_OF_YEAR"],
    "From 2000 to 2024 is 25 years.": ["SUB 2000 2024"],
    "January: 30 days after Jan 1": ["ADD 01-01 30"],
    "Feb: 28": ["MONTHLEN 02"],
    "February has 30 days": ["MONTHLEN 02"],
    "Day 1: 2025-12-28": ["STEP 2025-12-28 +1"],
    "45 मिनट में 53 मिनट जोडने पर 98 मिनट होते हैं।": ["ADD 45 53"],
    "जनवरी 2030 = 31": ["MONTHLEN 2030-01"],
    "First, let me convert both times to minutes past midnight.": ["CONVERT"],
    "Leap years in this period: 2000, 2004, 2008, 2012": ["LEAP 2000", "STEP 2000 +1"],
    "इस प्रश्न को हल करने के लिए हमें एक-एक कदम करके तर्क करना होगा।": ["PLAN STEPWISE"],
    "इसलिए, अगले सप्ताह की शुरुआत 2025-01-20 से होगी और अंत 2025-01-26 को होगा।": [],
    "So next week starts on Monday, 2025-04-21 and ends on Sunday, 2025-04-27.": ["ANCHOR 2025-04-21 Monday"],
    "0: Wednesday": ["CONVERT 0 WEEKDAY"],
    "h = 0 => शनिवार": ["CONVERT 0 WEEKDAY"],
    "1: Jan 30": ["STEP 01-30 +1"],
    "Thursday (1)": ["STEP Thursday +1"],
    "मार्च के दिन: 23": ["ADD 23"],
    "Start with today's date: 2025-08-26": ["GIVEN 2025-08-26"],
    "2021: +1 = Thursday": ["ANCHOR 2021 Thursday"],
    "22 तारीख = सोमवार": ["ANCHOR"],
    "End of Feb: 60": ["CONVERT 60 DAY_OF_YEAR"],
    "January 3 through January 31 = 29 days": ["SUB 01-03 01-31"],
    "Day 40: November 29": ["STEP 11-29 +1"],
    "Day 355: (354 mod 7) = 4.": ["CONVERT 355 DAY_OF_YEAR", "DIV 354 7"],
    "29 जनवरी से 31 जनवरी तक के दिन:": ["SUB 01-29 01-31"],
    "Identify today's date.": ["PLAN"],
    "Today's date is 2028-12-09.": ["GIVEN 2028-12-09"],
    "Current week (assuming week starts Monday): Aug 11-17 (Mon-Sun)": ["RULE MONDAY_FIRST", "ANCHOR 08-11 Monday", "SUB 08-11 17", "SUB Monday Sunday"],
    "Next week is the full Monday-to-Sunday period that follows this one.": ["RULE NEXT_WEEK"],
    "फरवरी के दिन: 28 (2025 लीप वर्ष नहीं है)": ["MONTHLEN 02", "LEAP 2025"],
    "2028-09-01 (1 सितंबर) भी शनिवार है।": ["ANCHOR 2028-09-01 Saturday", "STEP 2028-09-01 +1"],
    "Let me recount from Monday Nov 17:": ["REVISE", "ANCHOR 11-17 Monday"],
    "Give only the final answer.": ["FORMAT"],
    "1 Sat": ["STEP Saturday +1"],
    "Thu 1": ["STEP Thursday +1"],
    "1800s: Friday": ["ANCHOR 1800 Friday"],
    "Nov 19 = +1": ["STEP 11-19 +1"],
    "May 7 (-1)": ["STEP 05-07 -1"],
    "+1: 2025-12-28": ["STEP 2025-12-28 +1"],
    "Feb 2 is 32.": ["CONVERT 02-02 DAY_OF_YEAR"],
    "Feb 2 is 32 days after Jan 1.": ["ADD 02-02 32"],
    "2012 leap: +2 -> Thursday.": ["LEAP 2012"],
    "February 1 to February 13 is 12 more days": ["SUB 02-01 02-13"],
    "N=4: 3. 3+3=6 -> Saturday.": ["ADD 3 3", "CONVERT 6 WEEKDAY"],
    "So the number of days that have passed between March 10 and March 24 is 14.": ["SUB 03-10 03-24"],
    "इसलिए, 2025-08-27 और 2025-08-28 के बीच 1 दिन बीत चुका है।": ["SUB 2025-08-27 2025-08-28"],
    "August 27 to October 1 is 36.": ["SUB 08-27 10-01"],
    "Then October 1 is 274.": ["CONVERT 10-01 DAY_OF_YEAR"],
    "40 hours = 1 day 16 hours": ["CONVERT 40 HOURS"],
    "But Zeller gave h=0 => Saturday for 2024-01-01.": ["PLAN ZELLER", "CONVERT 0 WEEKDAY", "ANCHOR 2024-01-01 Saturday"],
}

for text, expected in CASES.items():
    assert parse(text) == expected, (text, parse(text))

QUESTION = "अभी 19:50 बजे हैं, 5 मिनट पहले समय क्या था?"
assert parse("अब 19:47 में से 2 मिनट घटाने पर 19:45 हो जाएगा।", question=QUESTION) == ["SUB 19:47 2"]
assert parse("अभी 19:50 बजे हैं।", question=QUESTION) == ["GIVEN 19:50"]
Q2 = "आज 2026-02-27 है, और मेरे पास हर 6 दिनों पर एक पुनरावृत्ति है।"
assert parse("आज की तारीख (2026-02-27) को छोडकर, हमें अगली 3 घटनाओं की तारीखें निकालनी हैं।", question=Q2)[:1] == ["GIVEN 2026-02-27"]
assert parse("आज की तारीख है: 2026-02-27", question=Q2) == ["GIVEN 2026-02-27"]
assert "GIVEN" not in " ".join(parse("आज से 3 दिन बाद की तारीख 2026-03-02 होगी।", question=Q2))
assert "GIVEN" not in " ".join(parse("दो दिन पहले की तारीख ज्ञात करने के लिए, आज की तारीख से 6 दिन घटाना होगा।", question=Q2))
assert parse("आज की तारीख से शुरू करते हैं: 2026-02-27", question=Q2) == ["GIVEN 2026-02-27"]
assert parse("इसलिए 27 दिन बाद की अंतिम तारीख 2030-04-08 होगी।", question="आज 2030-03-12 है, 27 दिन बाद की तारीख क्या होगी?") == ["ADD 2030-04-08 27"]
assert parse("So the start date is 2025-05-12 and the end date is 2025-05-18.", question="Today is 2025-05-08. What are the start and end dates of next week?") == []

assert parse(None) is None
assert parse("आज 2025-05-26 है। इसलिए, 4 दिन पहले की तारीख 2025-05-22 थी।\n\nAnswer: 2025-05-22") == ["GIVEN 2025-05-26", "ANSWER 2025-05-22", "SPITANSWER 2025-05-22"]
assert parse("मेरे भाई ने मोटरसाइकिल खरीदी। भाई की मोटरसाइकिल का इस सवाल से कोई संबंध नहीं है।", "मेरे भाई ने मोटरसाइकिल खरीदी।") == ["IGNORE", "IGNORE"]
print(f"{len(CASES) + 3} parser checks passed")
