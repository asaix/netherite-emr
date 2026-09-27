"""Tests for trd.generators module."""

import random
import pytest
from trd.generators import get_generator, GENERATOR_MAP, Sample
from trd.config import MEDIUM_TIMEFRAME
from trd.config.languages import LANGUAGE_CODES


class TestGeneratorMap:
    """Tests for generator registration."""

    def test_all_generators_registered(self):
        """Test all 9 task types have generators."""
        expected_types = [
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
        assert len(GENERATOR_MAP) == 9
        for task_type in expected_types:
            assert task_type in GENERATOR_MAP

    def test_get_generator_valid(self):
        """Test getting valid generators."""
        gen_class = get_generator("date_addition")
        assert gen_class is not None
        # Instantiate and check it works
        gen = gen_class(MEDIUM_TIMEFRAME, "en_US")
        assert gen.task_name == "date_addition"

    def test_get_generator_invalid(self):
        """Test getting invalid generator raises error."""
        with pytest.raises(ValueError):
            get_generator("invalid_task")


class TestDateAdditionGenerator:
    """Tests for DateAdditionGenerator."""

    def test_generate_samples(self):
        """Test generating date addition samples."""
        gen_class = get_generator("date_addition")
        gen = gen_class(MEDIUM_TIMEFRAME, "en_US")
        random.seed(42)
        samples = gen.generate_samples(5)
        
        assert len(samples) == 5
        for sample in samples:
            assert isinstance(sample, Sample)
            assert len(sample.question) > 0
            assert len(sample.answer) > 0
            assert sample.task == "date_addition"
            assert sample.language == "en_US"

    def test_reproducibility(self):
        """Test same seed produces same samples."""
        gen_class = get_generator("date_addition")
        
        random.seed(42)
        gen1 = gen_class(MEDIUM_TIMEFRAME, "en_US")
        samples1 = gen1.generate_samples(3)
        
        random.seed(42)
        gen2 = gen_class(MEDIUM_TIMEFRAME, "en_US")
        samples2 = gen2.generate_samples(3)
        
        for s1, s2 in zip(samples1, samples2):
            assert s1.question == s2.question
            assert s1.answer == s2.answer

    def test_different_seeds(self):
        """Test different seeds produce different samples."""
        gen_class = get_generator("date_addition")
        
        random.seed(42)
        gen1 = gen_class(MEDIUM_TIMEFRAME, "en_US")
        samples1 = gen1.generate_samples(3)
        
        random.seed(99)
        gen2 = gen_class(MEDIUM_TIMEFRAME, "en_US")
        samples2 = gen2.generate_samples(3)
        
        # At least one sample should be different
        different = any(
            s1.question != s2.question 
            for s1, s2 in zip(samples1, samples2)
        )
        assert different


class TestDateSubtractionGenerator:
    """Tests for DateSubtractionGenerator."""

    def test_generate_samples(self):
        """Test generating date subtraction samples."""
        gen_class = get_generator("date_subtraction")
        gen = gen_class(MEDIUM_TIMEFRAME, "en_US")
        random.seed(42)
        samples = gen.generate_samples(5)
        
        assert len(samples) == 5
        for sample in samples:
            assert sample.task == "date_subtraction"


class TestTimeAdditionGenerator:
    """Tests for TimeAdditionGenerator."""

    def test_generate_samples(self):
        """Test generating time addition samples."""
        gen_class = get_generator("time_addition")
        gen = gen_class(MEDIUM_TIMEFRAME, "en_US")
        random.seed(42)
        samples = gen.generate_samples(5)
        
        assert len(samples) == 5
        for sample in samples:
            assert sample.task == "time_addition"


class TestTimeSubtractionGenerator:
    """Tests for TimeSubtractionGenerator."""

    def test_generate_samples(self):
        """Test generating time subtraction samples."""
        gen_class = get_generator("time_subtraction")
        gen = gen_class(MEDIUM_TIMEFRAME, "en_US")
        random.seed(42)
        samples = gen.generate_samples(5)
        
        assert len(samples) == 5
        for sample in samples:
            assert sample.task == "time_subtraction"


class TestDateDurationGenerator:
    """Tests for DateDurationGenerator."""

    def test_generate_samples(self):
        """Test generating date duration samples."""
        gen_class = get_generator("date_duration")
        gen = gen_class(MEDIUM_TIMEFRAME, "en_US")
        random.seed(42)
        samples = gen.generate_samples(5)
        
        assert len(samples) == 5
        for sample in samples:
            assert sample.task == "date_duration"


class TestTimeDurationGenerator:
    """Tests for TimeDurationGenerator."""

    def test_generate_samples(self):
        """Test generating time duration samples."""
        gen_class = get_generator("time_duration")
        gen = gen_class(MEDIUM_TIMEFRAME, "en_US")
        random.seed(42)
        samples = gen.generate_samples(5)
        
        assert len(samples) == 5
        for sample in samples:
            assert sample.task == "time_duration"


class TestDateRecurrenceGenerator:
    """Tests for DateRecurrenceGenerator."""

    def test_generate_samples(self):
        """Test generating date recurrence samples."""
        gen_class = get_generator("date_recurrence")
        gen = gen_class(MEDIUM_TIMEFRAME, "en_US")
        random.seed(42)
        samples = gen.generate_samples(5)
        
        assert len(samples) == 5
        for sample in samples:
            assert sample.task == "date_recurrence"


class TestIntervalDateGenerator:
    """Tests for IntervalDateGenerator."""

    def test_generate_samples(self):
        """Test generating interval date samples."""
        gen_class = get_generator("interval_date")
        gen = gen_class(MEDIUM_TIMEFRAME, "en_US")
        random.seed(42)
        samples = gen.generate_samples(5)
        
        assert len(samples) == 5
        for sample in samples:
            assert sample.task == "interval_date"


class TestDayOfWeekGenerator:
    """Tests for DayOfWeekGenerator."""

    def test_generate_samples(self):
        """Test generating day of week samples."""
        gen_class = get_generator("day_of_week")
        gen = gen_class(MEDIUM_TIMEFRAME, "en_US")
        random.seed(42)
        samples = gen.generate_samples(5)
        
        assert len(samples) == 5
        for sample in samples:
            assert sample.task == "day_of_week"


class TestMultilingualGeneration:
    """Tests for multilingual generation."""

    @pytest.mark.parametrize("language", LANGUAGE_CODES)
    def test_generate_all_languages(self, language):
        """Test generation works for all supported languages."""
        gen_class = get_generator("date_addition")
        gen = gen_class(MEDIUM_TIMEFRAME, language)
        random.seed(42)
        samples = gen.generate_samples(2)
        
        assert len(samples) == 2
        for sample in samples:
            assert sample.language == language
            assert len(sample.question) > 0
            assert len(sample.answer) > 0
