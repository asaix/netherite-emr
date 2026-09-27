"""Temporal Reasoning Dataset (TRD) - Multilingual benchmark for evaluating LLMs.

A programmatically generated, multilingual benchmark designed to evaluate
temporal reasoning capabilities in Large Language Models across 10 languages.

Supports 4 experimental axes:
- Variations: Medium difficulty baseline (9,000 samples)
- Difficulties: 5 difficulty levels (45,000 samples)
- Insertions: Contextual distractors (18,000 samples)
- Memorization: Temporal shifts 2025-2095 (32,000 samples)

Example usage:
    from trd import generate_variations, generate_all
    
    # Generate variations experiment
    generate_variations(output_dir="./dataset")
    
    # Generate complete dataset (104K samples)
    generate_all(output_dir="./dataset")
"""

__version__ = "1.0.0"

from trd.config import (
    DIFFICULTY_LEVELS,
    MEDIUM_TIMEFRAME,
    SUPPORTED_LANGUAGES,
    TimeframeConfig,
)
from trd.experiments import (
    DifficultiesExperiment,
    InsertionsExperiment,
    MemorizationExperiment,
    VariationsExperiment,
)
from trd.generators import GENERATOR_MAP, get_generator


def generate_variations(
    samples_per_task: int = 100,
    output_dir: str = "./output",
    seed: int = 9,
    languages: list = None,
    format: str = "csv",
) -> int:
    """Generate the Variations experiment dataset.
    
    Args:
        samples_per_task: Number of samples per task per language
        output_dir: Output directory
        seed: Random seed for reproducibility
        languages: List of language codes (default: all)
        format: Output format ("csv" or "json")
        
    Returns:
        Total number of samples generated
    """
    exp = VariationsExperiment(
        samples_per_task=samples_per_task,
        languages=languages,
        output_dir=output_dir,
        seed=seed,
        format=format,
    )
    return exp.generate()


def generate_difficulties(
    samples_per_task: int = 100,
    output_dir: str = "./output",
    seed: int = 9,
    languages: list = None,
    format: str = "csv",
) -> int:
    """Generate the Difficulties experiment dataset.
    
    Args:
        samples_per_task: Number of samples per task per language per difficulty
        output_dir: Output directory
        seed: Random seed for reproducibility
        languages: List of language codes (default: all)
        format: Output format ("csv" or "json")
        
    Returns:
        Total number of samples generated
    """
    exp = DifficultiesExperiment(
        samples_per_task=samples_per_task,
        languages=languages,
        output_dir=output_dir,
        seed=seed,
        format=format,
    )
    return exp.generate()


def generate_insertions(
    samples_per_task: int = 100,
    output_dir: str = "./output",
    seed: int = 9,
    languages: list = None,
    format: str = "csv",
) -> int:
    """Generate the Insertions experiment dataset.
    
    Args:
        samples_per_task: Number of samples per task per language per variation
        output_dir: Output directory
        seed: Random seed for reproducibility
        languages: List of language codes (default: all)
        format: Output format ("csv" or "json")
        
    Returns:
        Total number of samples generated
    """
    exp = InsertionsExperiment(
        samples_per_task=samples_per_task,
        languages=languages,
        output_dir=output_dir,
        seed=seed,
        format=format,
    )
    return exp.generate()


def generate_memorization(
    samples_per_task: int = 100,
    output_dir: str = "./output",
    seed: int = 9,
    languages: list = None,
    format: str = "csv",
    years: list = None,
) -> int:
    """Generate the Memorization experiment dataset.
    
    Args:
        samples_per_task: Number of samples per task per language per year
        output_dir: Output directory
        seed: Random seed for reproducibility
        languages: List of language codes (default: all)
        format: Output format ("csv" or "json")
        years: List of years (default: 2025-2095 step 10)
        
    Returns:
        Total number of samples generated
    """
    exp = MemorizationExperiment(
        samples_per_task=samples_per_task,
        languages=languages,
        output_dir=output_dir,
        seed=seed,
        format=format,
        years=years,
    )
    return exp.generate()


def generate_all(
    samples_per_task: int = 100,
    output_dir: str = "./output",
    seed: int = 9,
    languages: list = None,
    format: str = "csv",
) -> int:
    """Generate all experiments (104K samples with default settings).
    
    Args:
        samples_per_task: Number of samples per task
        output_dir: Output directory
        seed: Random seed for reproducibility
        languages: List of language codes (default: all)
        format: Output format ("csv" or "json")
        
    Returns:
        Total number of samples generated
    """
    total = 0
    total += generate_variations(samples_per_task, output_dir, seed, languages, format)
    total += generate_difficulties(samples_per_task, output_dir, seed, languages, format)
    total += generate_insertions(samples_per_task, output_dir, seed, languages, format)
    total += generate_memorization(samples_per_task, output_dir, seed, languages, format)
    return total


__all__ = [
    "__version__",
    # Configuration
    "TimeframeConfig",
    "MEDIUM_TIMEFRAME",
    "DIFFICULTY_LEVELS",
    "SUPPORTED_LANGUAGES",
    # Experiments
    "VariationsExperiment",
    "DifficultiesExperiment",
    "InsertionsExperiment",
    "MemorizationExperiment",
    # Generators
    "GENERATOR_MAP",
    "get_generator",
    # High-level API
    "generate_variations",
    "generate_difficulties",
    "generate_insertions",
    "generate_memorization",
    "generate_all",
]
