"""Generators module for creating temporal reasoning samples."""

from trd.generators.base import BaseGenerator, Sample
from trd.generators.date_arithmetic import DateAdditionGenerator, DateSubtractionGenerator
from trd.generators.time_arithmetic import TimeAdditionGenerator, TimeSubtractionGenerator
from trd.generators.duration import DateDurationGenerator, TimeDurationGenerator
from trd.generators.recurrence import RecurrenceGenerator
from trd.generators.interval import IntervalGenerator
from trd.generators.day_of_week import DayOfWeekGenerator

# Mapping from task name to generator class
GENERATOR_MAP = {
    "date_addition": DateAdditionGenerator,
    "date_subtraction": DateSubtractionGenerator,
    "time_addition": TimeAdditionGenerator,
    "time_subtraction": TimeSubtractionGenerator,
    "date_duration": DateDurationGenerator,
    "time_duration": TimeDurationGenerator,
    "date_recurrence": RecurrenceGenerator,
    "interval_date": IntervalGenerator,
    "day_of_week": DayOfWeekGenerator,
}


def get_generator(task_name: str) -> type:
    """Get the generator class for a task name.
    
    Args:
        task_name: Name of the task (e.g., "date_addition")
        
    Returns:
        Generator class
        
    Raises:
        ValueError: If task_name is not valid
    """
    if task_name not in GENERATOR_MAP:
        valid = ", ".join(GENERATOR_MAP.keys())
        raise ValueError(f"Unknown task: {task_name}. Valid tasks: {valid}")
    return GENERATOR_MAP[task_name]


__all__ = [
    "BaseGenerator",
    "Sample",
    "DateAdditionGenerator",
    "DateSubtractionGenerator",
    "TimeAdditionGenerator",
    "TimeSubtractionGenerator",
    "DateDurationGenerator",
    "TimeDurationGenerator",
    "RecurrenceGenerator",
    "IntervalGenerator",
    "DayOfWeekGenerator",
    "GENERATOR_MAP",
    "get_generator",
]
