#!/usr/bin/env python3
"""Example of using individual generators directly."""

from trd.generators import get_generator, GENERATOR_MAP
from trd.config import MEDIUM_TIMEFRAME, DIFFICULTY_LEVELS, TimeframeConfig

# List all available generators
print("Available generators:")
for task_type in GENERATOR_MAP:
    print(f"  - {task_type}")

# Use a specific generator
print("\n--- Date Addition Examples ---")
date_add_gen = get_generator("date_addition")
samples = date_add_gen.generate(
    language="en_US",
    timeframe=MEDIUM_TIMEFRAME,
    num_samples=3,
    seed=42,
)
for sample in samples:
    print(f"Q: {sample['question']}")
    print(f"A: {sample['answer']}\n")

# Generate with different difficulty levels
print("\n--- Day of Week Examples (different difficulties) ---")
dow_gen = get_generator("day_of_week")

for difficulty, config in DIFFICULTY_LEVELS.items():
    print(f"\n{difficulty.upper()}:")
    samples = dow_gen.generate(
        language="de_DE",
        timeframe=config,
        num_samples=2,
        seed=42,
    )
    for sample in samples:
        print(f"  Q: {sample['question']}")
        print(f"  A: {sample['answer']}")

# Create custom timeframe configuration
print("\n--- Custom Timeframe ---")
custom_config = TimeframeConfig(
    days_range=(1, 30),
    weeks_range=(1, 4),
    months_range=(1, 6),
    years_range=(1, 2),
    hours_range=(1, 12),
    minutes_range=(1, 30),
    year_range=(2030, 2035),  # Custom year range
)

samples = date_add_gen.generate(
    language="ja_JP",
    timeframe=custom_config,
    num_samples=3,
    seed=42,
)
for sample in samples:
    print(f"Q: {sample['question']}")
    print(f"A: {sample['answer']}\n")

# Generate time-based samples
print("\n--- Time Duration Examples ---")
time_dur_gen = get_generator("time_duration")
samples = time_dur_gen.generate(
    language="fr_FR",
    timeframe=MEDIUM_TIMEFRAME,
    num_samples=3,
    seed=42,
)
for sample in samples:
    print(f"Q: {sample['question']}")
    print(f"A: {sample['answer']}\n")
