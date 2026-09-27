"""Timeframe configurations for different difficulty levels.

Based on Table 5 from the paper:
- short: Simple near-term operations
- medium: Moderate complexity (baseline)
- long: Extended temporal range
- very_long: Multi-year operations
- very_very_long: Complex long-horizon reasoning
"""

from dataclasses import dataclass
from datetime import date
from typing import Dict, Tuple


@dataclass(frozen=True)
class TimeframeConfig:
    """Configuration for a specific difficulty level.
    
    Attributes:
        name: Difficulty level name
        start_date: Start of date range (year, month, day)
        end_date: End of date range (year, month, day)
        days_min: Minimum days to add/subtract
        days_max: Maximum days to add/subtract
        hours_min: Minimum hours to add/subtract
        hours_max: Maximum hours to add/subtract
        recurrence_every_min: Minimum recurrence interval (days)
        recurrence_every_max: Maximum recurrence interval (days)
        recurrence_question_min: Minimum occurrence to query
        recurrence_question_max: Maximum occurrence to query
        duration_date_min: Minimum date duration (days)
        duration_date_max: Maximum date duration (days)
        duration_time_min: Minimum time duration (minutes)
        duration_time_max: Maximum time duration (minutes)
    """
    name: str
    start_date: Tuple[int, int, int]
    end_date: Tuple[int, int, int]
    days_min: int
    days_max: int
    hours_min: int
    hours_max: int
    recurrence_every_min: int
    recurrence_every_max: int
    recurrence_question_min: int
    recurrence_question_max: int
    duration_date_min: int
    duration_date_max: int
    duration_time_min: int
    duration_time_max: int
    
    @classmethod
    def short(cls) -> "TimeframeConfig":
        """Create short timeframe configuration."""
        return SHORT_TIMEFRAME
    
    @classmethod
    def medium(cls) -> "TimeframeConfig":
        """Create medium timeframe configuration (baseline)."""
        return MEDIUM_TIMEFRAME
    
    @classmethod
    def long(cls) -> "TimeframeConfig":
        """Create long timeframe configuration."""
        return LONG_TIMEFRAME
    
    @classmethod
    def very_long(cls) -> "TimeframeConfig":
        """Create very long timeframe configuration."""
        return VERY_LONG_TIMEFRAME
    
    @classmethod
    def very_very_long(cls) -> "TimeframeConfig":
        """Create very very long timeframe configuration."""
        return VERY_VERY_LONG_TIMEFRAME
    
    @classmethod
    def from_name(cls, name: str) -> "TimeframeConfig":
        """Get timeframe configuration by name.
        
        Args:
            name: Difficulty level name (short, medium, long, very_long, very_very_long)
            
        Returns:
            TimeframeConfig for the specified difficulty level
            
        Raises:
            ValueError: If name is not a valid difficulty level
        """
        configs = {
            "short": SHORT_TIMEFRAME,
            "medium": MEDIUM_TIMEFRAME,
            "long": LONG_TIMEFRAME,
            "very_long": VERY_LONG_TIMEFRAME,
            "very_very_long": VERY_VERY_LONG_TIMEFRAME,
        }
        if name not in configs:
            valid = ", ".join(configs.keys())
            raise ValueError(f"Invalid difficulty level: {name}. Valid options: {valid}")
        return configs[name]
    
    def to_dict(self) -> Dict:
        """Convert configuration to dictionary for use in generators."""
        return {
            "START_DATE": self.start_date,
            "END_DATE": self.end_date,
            "DAYS_TO_ADD_MIN": self.days_min,
            "DAYS_TO_ADD_MAX": self.days_max,
            "HOURS_TO_ADD_MIN": self.hours_min,
            "HOURS_TO_ADD_MAX": self.hours_max,
            "RECURRENCE_EVERY_MIN": self.recurrence_every_min,
            "RECURRENCE_EVERY_MAX": self.recurrence_every_max,
            "RECURRENCE_AFTER_MIN": self.recurrence_question_min,
            "RECURRENCE_AFTER_MAX": self.recurrence_question_max,
            "MAX_DURATION_DATE_MIN": self.duration_date_min,
            "MAX_DURATION_DATE_MAX": self.duration_date_max,
            "MAX_DURATION_TIME_MIN": self.duration_time_min,
            "MAX_DURATION_TIME_MAX": self.duration_time_max,
        }
    
    def with_year_range(self, start_year: int, end_year: int) -> "TimeframeConfig":
        """Create a new config with modified year range (for memorization experiment).
        
        Args:
            start_year: New start year
            end_year: New end year
            
        Returns:
            New TimeframeConfig with updated year range
        """
        return TimeframeConfig(
            name=f"{self.name}_{start_year}",
            start_date=(start_year, 1, 1),
            end_date=(end_year, 12, 31),
            days_min=self.days_min,
            days_max=self.days_max,
            hours_min=self.hours_min,
            hours_max=self.hours_max,
            recurrence_every_min=self.recurrence_every_min,
            recurrence_every_max=self.recurrence_every_max,
            recurrence_question_min=self.recurrence_question_min,
            recurrence_question_max=self.recurrence_question_max,
            duration_date_min=self.duration_date_min,
            duration_date_max=self.duration_date_max,
            duration_time_min=self.duration_time_min,
            duration_time_max=self.duration_time_max,
        )


# Configuration values from Table 5 of the paper
# Short: 2025, 1-4 days/hours, 1-4 every, 1-2 question, 1-4 date duration, 1-60 time duration
SHORT_TIMEFRAME = TimeframeConfig(
    name="short",
    start_date=(2025, 1, 1),
    end_date=(2025, 12, 31),
    days_min=1,
    days_max=4,
    hours_min=1,
    hours_max=4,
    recurrence_every_min=1,
    recurrence_every_max=4,
    recurrence_question_min=1,
    recurrence_question_max=2,
    duration_date_min=1,
    duration_date_max=4,
    duration_time_min=1,
    duration_time_max=60,
)

# Medium: 2025-2028, 4-8 days/hours, 4-8 every, 2-4 question, 4-8 date duration, 60-120 time duration
MEDIUM_TIMEFRAME = TimeframeConfig(
    name="medium",
    start_date=(2025, 1, 1),
    end_date=(2028, 12, 31),
    days_min=4,
    days_max=8,
    hours_min=4,
    hours_max=8,
    recurrence_every_min=4,
    recurrence_every_max=8,
    recurrence_question_min=2,
    recurrence_question_max=4,
    duration_date_min=4,
    duration_date_max=8,
    duration_time_min=60,
    duration_time_max=120,
)

# Long: 2025-2030, 8-16 days/hours, 8-16 every, 4-8 question, 8-16 date duration, 120-240 time duration
LONG_TIMEFRAME = TimeframeConfig(
    name="long",
    start_date=(2025, 1, 1),
    end_date=(2030, 12, 31),
    days_min=8,
    days_max=16,
    hours_min=8,
    hours_max=16,
    recurrence_every_min=8,
    recurrence_every_max=16,
    recurrence_question_min=4,
    recurrence_question_max=8,
    duration_date_min=8,
    duration_date_max=16,
    duration_time_min=120,
    duration_time_max=240,
)

# Very Long: 2025-2033, 16-32 days/hours, 16-32 every, 8-16 question, 16-32 date duration, 240-480 time duration
VERY_LONG_TIMEFRAME = TimeframeConfig(
    name="very_long",
    start_date=(2025, 1, 1),
    end_date=(2033, 12, 31),
    days_min=16,
    days_max=32,
    hours_min=16,
    hours_max=32,
    recurrence_every_min=16,
    recurrence_every_max=32,
    recurrence_question_min=8,
    recurrence_question_max=16,
    duration_date_min=16,
    duration_date_max=32,
    duration_time_min=240,
    duration_time_max=480,
)

# Very Very Long: 2025-2036, 32-64 days/hours, 32-64 every, 16-32 question, 32-64 date duration, 480-960 time duration
VERY_VERY_LONG_TIMEFRAME = TimeframeConfig(
    name="very_very_long",
    start_date=(2025, 1, 1),
    end_date=(2036, 12, 31),
    days_min=32,
    days_max=64,
    hours_min=32,
    hours_max=64,
    recurrence_every_min=32,
    recurrence_every_max=64,
    recurrence_question_min=16,
    recurrence_question_max=32,
    duration_date_min=32,
    duration_date_max=64,
    duration_time_min=480,
    duration_time_max=960,
)

# List of all difficulty levels
DIFFICULTY_LEVELS = ["short", "medium", "long", "very_long", "very_very_long"]

# Mapping from difficulty name to configuration
DIFFICULTY_CONFIGS = {
    "short": SHORT_TIMEFRAME,
    "medium": MEDIUM_TIMEFRAME,
    "long": LONG_TIMEFRAME,
    "very_long": VERY_LONG_TIMEFRAME,
    "very_very_long": VERY_VERY_LONG_TIMEFRAME,
}
