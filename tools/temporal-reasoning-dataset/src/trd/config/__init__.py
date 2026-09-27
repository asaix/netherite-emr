"""Configuration module for Temporal Reasoning Dataset."""

from trd.config.timeframes import (
    TimeframeConfig,
    SHORT_TIMEFRAME,
    MEDIUM_TIMEFRAME,
    LONG_TIMEFRAME,
    VERY_LONG_TIMEFRAME,
    VERY_VERY_LONG_TIMEFRAME,
    DIFFICULTY_LEVELS,
    DIFFICULTY_CONFIGS,
)
from trd.config.languages import (
    Language,
    SUPPORTED_LANGUAGES,
    EN,
    ES,
    DE,
    FR,
    HI,
    IT,
    JA,
    PT,
    AR,
    NL,
)
from trd.config.defaults import (
    RANDOM_SEED,
    NUMBER_OF_SAMPLES_DEFAULT,
    MEMORIZATION_YEARS,
    MEMORIZATION_TASKS,
    ALL_TASKS,
    REASONING_TASKS,
    MEMORIZATION_TASK_NAMES,
)

__all__ = [
    # Timeframes
    "TimeframeConfig",
    "SHORT_TIMEFRAME",
    "MEDIUM_TIMEFRAME",
    "LONG_TIMEFRAME",
    "VERY_LONG_TIMEFRAME",
    "VERY_VERY_LONG_TIMEFRAME",
    "DIFFICULTY_LEVELS",
    "DIFFICULTY_CONFIGS",
    # Languages
    "Language",
    "SUPPORTED_LANGUAGES",
    "EN",
    "ES",
    "DE",
    "FR",
    "HI",
    "IT",
    "JA",
    "PT",
    "AR",
    "NL",
    # Defaults
    "RANDOM_SEED",
    "NUMBER_OF_SAMPLES_DEFAULT",
    "MEMORIZATION_YEARS",
    "MEMORIZATION_TASKS",
    "ALL_TASKS",
    "REASONING_TASKS",
    "MEMORIZATION_TASK_NAMES",
]
