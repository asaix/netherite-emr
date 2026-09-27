"""Default configuration values for the Temporal Reasoning Dataset."""

from typing import List

# Random seed for reproducibility (matches paper)
RANDOM_SEED = 9

# Default number of samples per task
NUMBER_OF_SAMPLES_DEFAULT = 100

# Memorization experiment years (2025 to 2095, step of 10)
MEMORIZATION_YEARS: List[int] = [2025, 2035, 2045, 2055, 2065, 2075, 2085, 2095]

# All task names (9 tasks total)
ALL_TASKS: List[str] = [
    "date_addition",
    "date_subtraction",
    "time_addition",
    "time_subtraction",
    "date_duration",
    "time_duration",
    "date_recurrence",
    "interval_date",
    "day_of_week",
]

# Reasoning tasks (require computation)
REASONING_TASKS: List[str] = [
    "date_addition",
    "date_subtraction",
    "time_addition",
    "time_subtraction",
    "date_duration",
    "time_duration",
    "date_recurrence",
]

# Memorization task names (depend on calendar knowledge)
MEMORIZATION_TASK_NAMES: List[str] = [
    "interval_date",
    "day_of_week",
]

# Tasks used in memorization experiment (4 tasks from paper)
# day_of_week and interval_date are pure memorization
# date_addition and date_recurrence are included to test temporal shifts
MEMORIZATION_TASKS: List[str] = [
    "day_of_week",
    "interval_date",
    "date_addition",
    "date_recurrence",
]

# Mapping from task name to template key
TASK_TO_TEMPLATE_KEY = {
    "date_addition": "addition_date",
    "date_subtraction": "subtraction_date",
    "time_addition": "addition_time",
    "time_subtraction": "subtraction_time",
    "date_duration": "duration_date",
    "time_duration": "duration_time",
    "date_recurrence": "recurrence_date",
    "interval_date": "interval_date",
    "day_of_week": "day_of_week",
}

# Output file extension
OUTPUT_EXTENSION = ".csv"

# Default output directory
DEFAULT_OUTPUT_DIR = "./output"
