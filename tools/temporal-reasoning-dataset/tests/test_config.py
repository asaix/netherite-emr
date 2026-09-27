"""Tests for trd.config module."""

import pytest
from trd.config import (
    TimeframeConfig,
    SHORT_TIMEFRAME,
    MEDIUM_TIMEFRAME,
    LONG_TIMEFRAME,
    VERY_LONG_TIMEFRAME,
    VERY_VERY_LONG_TIMEFRAME,
    DIFFICULTY_LEVELS,
    DIFFICULTY_CONFIGS,
    SUPPORTED_LANGUAGES,
)
from trd.config.languages import LANGUAGE_CODES


class TestTimeframeConfig:
    """Tests for TimeframeConfig dataclass."""

    def test_short_values(self):
        """Test short timeframe values from Table 5."""
        config = SHORT_TIMEFRAME
        assert config.name == "short"
        assert config.start_date == (2025, 1, 1)
        assert config.end_date == (2025, 12, 31)
        assert config.days_min == 1
        assert config.days_max == 4
        assert config.hours_min == 1
        assert config.hours_max == 4

    def test_medium_values(self):
        """Test medium timeframe values from Table 5."""
        config = MEDIUM_TIMEFRAME
        assert config.name == "medium"
        assert config.start_date == (2025, 1, 1)
        assert config.end_date == (2028, 12, 31)
        assert config.days_min == 4
        assert config.days_max == 8
        assert config.hours_min == 4
        assert config.hours_max == 8

    def test_with_year_range(self):
        """Test with_year_range factory method."""
        base = MEDIUM_TIMEFRAME
        modified = base.with_year_range(2050, 2060)
        
        # Original unchanged
        assert base.start_date == (2025, 1, 1)
        assert base.end_date == (2028, 12, 31)
        # New config has updated year range
        assert modified.start_date == (2050, 1, 1)
        assert modified.end_date == (2060, 12, 31)
        # Other values preserved
        assert modified.days_min == base.days_min
        assert modified.days_max == base.days_max

    def test_short_factory(self):
        """Test short timeframe factory."""
        config = TimeframeConfig.short()
        assert config.name == "short"
        assert config.days_min == 1
        assert config.days_max == 4

    def test_medium_factory(self):
        """Test medium timeframe factory."""
        config = TimeframeConfig.medium()
        assert config.name == "medium"
        assert config.days_min == 4
        assert config.days_max == 8

    def test_long_factory(self):
        """Test long timeframe factory."""
        config = TimeframeConfig.long()
        assert config.name == "long"
        assert config.days_min == 8
        assert config.days_max == 16

    def test_very_long_factory(self):
        """Test very_long timeframe factory."""
        config = TimeframeConfig.very_long()
        assert config.name == "very_long"
        assert config.days_min == 16
        assert config.days_max == 32

    def test_very_very_long_factory(self):
        """Test very_very_long timeframe factory."""
        config = TimeframeConfig.very_very_long()
        assert config.name == "very_very_long"
        assert config.days_min == 32
        assert config.days_max == 64

    def test_from_name(self):
        """Test from_name factory method."""
        assert TimeframeConfig.from_name("short") == SHORT_TIMEFRAME
        assert TimeframeConfig.from_name("medium") == MEDIUM_TIMEFRAME
        assert TimeframeConfig.from_name("long") == LONG_TIMEFRAME
        assert TimeframeConfig.from_name("very_long") == VERY_LONG_TIMEFRAME
        assert TimeframeConfig.from_name("very_very_long") == VERY_VERY_LONG_TIMEFRAME
        
    def test_from_name_invalid(self):
        """Test from_name with invalid name raises error."""
        with pytest.raises(ValueError):
            TimeframeConfig.from_name("invalid")

    def test_to_dict(self):
        """Test to_dict method returns correct keys."""
        config = MEDIUM_TIMEFRAME
        d = config.to_dict()
        assert "START_DATE" in d
        assert "END_DATE" in d
        assert "DAYS_TO_ADD_MIN" in d
        assert "DAYS_TO_ADD_MAX" in d


class TestDifficultyLevels:
    """Tests for DIFFICULTY_LEVELS configuration."""

    def test_all_levels_present(self):
        """Test all 5 difficulty levels are defined."""
        expected = ["short", "medium", "long", "very_long", "very_very_long"]
        assert DIFFICULTY_LEVELS == expected

    def test_levels_are_timeframe_configs(self):
        """Test each level is a TimeframeConfig."""
        for level in DIFFICULTY_LEVELS:
            config = DIFFICULTY_CONFIGS[level]
            assert isinstance(config, TimeframeConfig), f"{level} is not a TimeframeConfig"

    def test_difficulty_progression(self):
        """Test difficulty levels have increasing ranges."""
        configs = [DIFFICULTY_CONFIGS[level] for level in DIFFICULTY_LEVELS]
        for i in range(len(configs) - 1):
            current = configs[i]
            next_level = configs[i + 1]
            assert current.days_max <= next_level.days_max


class TestSupportedLanguages:
    """Tests for SUPPORTED_LANGUAGES."""

    def test_all_languages_present(self):
        """Test all 10 languages are supported."""
        assert len(SUPPORTED_LANGUAGES) == 10

    def test_expected_languages(self):
        """Test expected language codes."""
        expected = [
            "en_US", "es_ES", "de_DE", "fr_FR", "it_IT",
            "pt_BR", "nl_NL", "ja_JP", "ar_SA", "hi_IN"
        ]
        assert set(LANGUAGE_CODES) == set(expected)
