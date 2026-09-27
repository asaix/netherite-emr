#!/usr/bin/env python3
"""Basic usage example for TRD package."""

from trd import generate_variations, generate_all, SUPPORTED_LANGUAGES

# Generate variations experiment (9K samples with defaults)
print("Generating variations experiment...")
total = generate_variations(
    samples_per_task=100,
    output_dir="./output/variations",
    seed=9,
)
print(f"Generated {total} samples for variations experiment")

# Generate complete dataset (104K samples)
print("\nGenerating complete dataset...")
total = generate_all(
    samples_per_task=100,
    output_dir="./output/complete",
    seed=9,
)
print(f"Generated {total} total samples")

# Generate for specific languages only
print("\nGenerating for English and German only...")
total = generate_variations(
    samples_per_task=50,
    languages=["en_US", "de_DE"],
    output_dir="./output/subset",
    seed=9,
    format="json",
)
print(f"Generated {total} samples for subset")

print("\nDone! Check the ./output directory for generated datasets.")
