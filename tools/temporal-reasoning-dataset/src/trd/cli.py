"""Command-line interface for the Temporal Reasoning Dataset generator."""

import argparse
import sys

from trd.config.defaults import NUMBER_OF_SAMPLES_DEFAULT, RANDOM_SEED
from trd.config.languages import LANGUAGE_CODES
from trd.experiments import (
    DifficultiesExperiment,
    InsertionsExperiment,
    MemorizationExperiment,
    VariationsExperiment,
)


def add_common_options(parser: argparse.ArgumentParser) -> None:
    """Add common options shared across generate subcommands."""
    parser.add_argument(
        "--samples", "-s",
        type=int,
        default=NUMBER_OF_SAMPLES_DEFAULT,
        help=f"Number of samples per task per language (default: {NUMBER_OF_SAMPLES_DEFAULT})",
    )
    parser.add_argument(
        "--output", "-o",
        default="./output",
        help="Output directory (default: ./output)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=RANDOM_SEED,
        help=f"Random seed for reproducibility (default: {RANDOM_SEED})",
    )
    parser.add_argument(
        "--format", "-f",
        choices=["csv", "json"],
        default="csv",
        help="Output format (default: csv)",
    )
    parser.add_argument(
        "--languages", "-l",
        default=None,
        help="Comma-separated language codes (default: all)",
    )


def cmd_generate_all(args: argparse.Namespace) -> None:
    """Generate complete dataset (all 4 experiments, ~104K samples)."""
    lang_list = args.languages.split(",") if args.languages else None
    total = 0

    print("🕐 Generating Temporal Reasoning Dataset...")
    print(f"   Output: {args.output}")
    print(f"   Samples per task: {args.samples}")
    print(f"   Seed: {args.seed}")
    print()

    # Variations
    print("📊 Generating Variations experiment...")
    exp = VariationsExperiment(
        samples_per_task=args.samples,
        languages=lang_list,
        output_dir=args.output,
        seed=args.seed,
        format=args.format,
    )
    count = exp.generate()
    total += count
    print(f"   ✓ Generated {count:,} samples")

    # Difficulties
    print("📊 Generating Difficulties experiment...")
    exp = DifficultiesExperiment(
        samples_per_task=args.samples,
        languages=lang_list,
        output_dir=args.output,
        seed=args.seed,
        format=args.format,
    )
    count = exp.generate()
    total += count
    print(f"   ✓ Generated {count:,} samples")

    # Insertions
    print("📊 Generating Insertions experiment...")
    exp = InsertionsExperiment(
        samples_per_task=args.samples,
        languages=lang_list,
        output_dir=args.output,
        seed=args.seed,
        format=args.format,
    )
    count = exp.generate()
    total += count
    print(f"   ✓ Generated {count:,} samples")

    # Memorization
    print("📊 Generating Memorization experiment...")
    exp = MemorizationExperiment(
        samples_per_task=args.samples,
        languages=lang_list,
        output_dir=args.output,
        seed=args.seed,
        format=args.format,
    )
    count = exp.generate()
    total += count
    print(f"   ✓ Generated {count:,} samples")

    print()
    print(f"✅ Complete! Total samples: {total:,}")


def cmd_generate_variations(args: argparse.Namespace) -> None:
    """Generate Variations experiment (9K samples with default settings)."""
    lang_list = args.languages.split(",") if args.languages else None

    print("📊 Generating Variations experiment...")
    exp = VariationsExperiment(
        samples_per_task=args.samples,
        languages=lang_list,
        output_dir=args.output,
        seed=args.seed,
        format=args.format,
    )
    count = exp.generate()
    print(f"✅ Generated {count:,} samples in {args.output}/variations/")


def cmd_generate_difficulties(args: argparse.Namespace) -> None:
    """Generate Difficulties experiment (45K samples with default settings)."""
    lang_list = args.languages.split(",") if args.languages else None

    print("📊 Generating Difficulties experiment...")
    exp = DifficultiesExperiment(
        samples_per_task=args.samples,
        languages=lang_list,
        output_dir=args.output,
        seed=args.seed,
        format=args.format,
    )
    count = exp.generate()
    print(f"✅ Generated {count:,} samples in {args.output}/difficulties/")


def cmd_generate_insertions(args: argparse.Namespace) -> None:
    """Generate Insertions experiment (18K samples with default settings)."""
    lang_list = args.languages.split(",") if args.languages else None

    print("📊 Generating Insertions experiment...")
    exp = InsertionsExperiment(
        samples_per_task=args.samples,
        languages=lang_list,
        output_dir=args.output,
        seed=args.seed,
        format=args.format,
    )
    count = exp.generate()
    print(f"✅ Generated {count:,} samples in {args.output}/insertions/")


def cmd_generate_memorization(args: argparse.Namespace) -> None:
    """Generate Memorization experiment (32K samples with default settings)."""
    lang_list = args.languages.split(",") if args.languages else None

    print("📊 Generating Memorization experiment...")
    exp = MemorizationExperiment(
        samples_per_task=args.samples,
        languages=lang_list,
        output_dir=args.output,
        seed=args.seed,
        format=args.format,
    )
    count = exp.generate()
    print(f"✅ Generated {count:,} samples in {args.output}/memorization/")


def cmd_info(args: argparse.Namespace) -> None:
    """Show information about supported languages and tasks."""
    from trd.config.defaults import ALL_TASKS, MEMORIZATION_TASKS
    from trd.config.languages import SUPPORTED_LANGUAGES
    from trd.config.timeframes import DIFFICULTY_LEVELS

    print("🌍 Supported Languages (10):")
    for lang in SUPPORTED_LANGUAGES:
        print(f"   • {lang.code}: {lang.name} ({lang.family}/{lang.branch})")

    print()
    print("📋 Tasks (9):")
    for task in ALL_TASKS:
        print(f"   • {task}")

    print()
    print("📈 Difficulty Levels (5):")
    for level in DIFFICULTY_LEVELS:
        print(f"   • {level}")

    print()
    print("🧠 Memorization Tasks (4):")
    for task in MEMORIZATION_TASKS:
        print(f"   • {task}")

    print()
    print("📊 Default Sample Counts:")
    print(f"   • Variations:    9 × 100 × 10 × 1 =  9,000")
    print(f"   • Difficulties:  9 × 100 × 10 × 5 = 45,000")
    print(f"   • Insertions:    9 × 100 × 10 × 2 = 18,000")
    print(f"   • Memorization:  4 × 100 × 10 × 8 = 32,000")
    print(f"   • Total:                          104,000")


def cli(argv: list[str] | None = None) -> None:
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        prog="trd",
        description=(
            "Temporal Reasoning Dataset (TRD) - Multilingual benchmark generator.\n\n"
            "Generate temporal reasoning datasets for evaluating LLMs across 10 languages\n"
            "with 4 experimental axes: variations, difficulties, insertions, and memorization.\n\n"
            "Total samples with default settings: 104,000"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 1.0.0",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # generate command group
    generate_parser = subparsers.add_parser(
        "generate",
        help="Generate datasets for different experiments",
    )
    generate_subparsers = generate_parser.add_subparsers(
        dest="experiment",
        help="Experiment type",
    )

    # generate all
    all_parser = generate_subparsers.add_parser(
        "all",
        help="Generate complete dataset (all 4 experiments, ~104K samples)",
        description=(
            "Generate complete dataset (all 4 experiments, ~104K samples).\n\n"
            "This generates all experimental axes:\n"
            "- Variations: 9,000 samples (medium difficulty baseline)\n"
            "- Difficulties: 45,000 samples (all 5 difficulty levels)\n"
            "- Insertions: 18,000 samples (similar/dissimilar distractors)\n"
            "- Memorization: 32,000 samples (temporal shifts 2025-2095)"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    add_common_options(all_parser)
    all_parser.set_defaults(func=cmd_generate_all)

    # generate variations
    variations_parser = generate_subparsers.add_parser(
        "variations",
        help="Generate Variations experiment (9K samples with default settings)",
        description=(
            "Generate Variations experiment (9K samples with default settings).\n\n"
            "Medium difficulty baseline across all 9 tasks and 10 languages.\n"
            "Formula: 9 tasks × 100 samples × 10 languages = 9,000 samples"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    add_common_options(variations_parser)
    variations_parser.set_defaults(func=cmd_generate_variations)

    # generate difficulties
    difficulties_parser = generate_subparsers.add_parser(
        "difficulties",
        help="Generate Difficulties experiment (45K samples with default settings)",
        description=(
            "Generate Difficulties experiment (45K samples with default settings).\n\n"
            "All 5 difficulty levels: short, medium, long, very_long, very_very_long.\n"
            "Formula: 9 tasks × 100 samples × 10 languages × 5 difficulties = 45,000 samples"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    add_common_options(difficulties_parser)
    difficulties_parser.set_defaults(func=cmd_generate_difficulties)

    # generate insertions
    insertions_parser = generate_subparsers.add_parser(
        "insertions",
        help="Generate Insertions experiment (18K samples with default settings)",
        description=(
            "Generate Insertions experiment (18K samples with default settings).\n\n"
            "Contextual distractors: similar (time-related) and dissimilar (unrelated).\n"
            "Formula: 9 tasks × 100 samples × 10 languages × 2 variations = 18,000 samples"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    add_common_options(insertions_parser)
    insertions_parser.set_defaults(func=cmd_generate_insertions)

    # generate memorization
    memorization_parser = generate_subparsers.add_parser(
        "memorization",
        help="Generate Memorization experiment (32K samples with default settings)",
        description=(
            "Generate Memorization experiment (32K samples with default settings).\n\n"
            "Temporal shifts testing dates from 2025 to 2095.\n"
            "Formula: 4 tasks × 100 samples × 10 languages × 8 years = 32,000 samples"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    add_common_options(memorization_parser)
    memorization_parser.set_defaults(func=cmd_generate_memorization)

    # info command
    info_parser = subparsers.add_parser(
        "info",
        help="Show information about supported languages and tasks",
    )
    info_parser.set_defaults(func=cmd_info)

    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_help()
        sys.exit(0)

    if args.command == "generate" and args.experiment is None:
        generate_parser.print_help()
        sys.exit(0)

    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()
        sys.exit(0)


def main():
    """Entry point for the CLI."""
    cli()


if __name__ == "__main__":
    main()
