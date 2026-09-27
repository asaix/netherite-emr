"""Tests for trd.experiments module."""

import os
import tempfile
import pytest
from trd.experiments import (
    VariationsExperiment,
    DifficultiesExperiment,
    InsertionsExperiment,
    MemorizationExperiment,
)


class TestVariationsExperiment:
    """Tests for VariationsExperiment."""

    def test_init(self):
        """Test experiment initialization."""
        exp = VariationsExperiment(
            samples_per_task=10,
            languages=["en_US"],
            output_dir="./test_output",
            seed=42,
        )
        assert exp.samples_per_task == 10
        assert exp.languages == ["en_US"]
        assert exp.seed == 42

    def test_generate_small(self):
        """Test generating small dataset."""
        with tempfile.TemporaryDirectory() as tmpdir:
            exp = VariationsExperiment(
                samples_per_task=2,
                languages=["en_US"],
                output_dir=tmpdir,
                seed=42,
            )
            total = exp.generate()
            # 2 samples × 9 tasks × 1 language = 18
            assert total == 18

    def test_expected_total_default(self):
        """Test expected total with defaults."""
        exp = VariationsExperiment(
            samples_per_task=100,
            languages=None,  # All 10 languages
            output_dir="./test_output",
            seed=9,
        )
        # 100 samples × 9 tasks × 10 languages = 9,000
        expected = 100 * 9 * 10
        assert exp.get_total_expected_samples() == expected


class TestDifficultiesExperiment:
    """Tests for DifficultiesExperiment."""

    def test_init(self):
        """Test experiment initialization."""
        exp = DifficultiesExperiment(
            samples_per_task=10,
            languages=["en_US"],
            output_dir="./test_output",
            seed=42,
        )
        assert exp.samples_per_task == 10

    def test_generate_small(self):
        """Test generating small dataset."""
        with tempfile.TemporaryDirectory() as tmpdir:
            exp = DifficultiesExperiment(
                samples_per_task=2,
                languages=["en_US"],
                output_dir=tmpdir,
                seed=42,
            )
            total = exp.generate()
            # 2 samples × 9 tasks × 1 language × 5 difficulties = 90
            assert total == 90

    def test_expected_total_default(self):
        """Test expected total with defaults."""
        exp = DifficultiesExperiment(
            samples_per_task=100,
            languages=None,
            output_dir="./test_output",
            seed=9,
        )
        # 100 samples × 9 tasks × 10 languages × 5 difficulties = 45,000
        expected = 100 * 9 * 10 * 5
        assert exp.get_total_expected_samples() == expected


class TestInsertionsExperiment:
    """Tests for InsertionsExperiment."""

    def test_init(self):
        """Test experiment initialization."""
        exp = InsertionsExperiment(
            samples_per_task=10,
            languages=["en_US"],
            output_dir="./test_output",
            seed=42,
        )
        assert exp.samples_per_task == 10

    def test_generate_small(self):
        """Test generating small dataset."""
        with tempfile.TemporaryDirectory() as tmpdir:
            exp = InsertionsExperiment(
                samples_per_task=2,
                languages=["en_US"],
                output_dir=tmpdir,
                seed=42,
            )
            total = exp.generate()
            # 2 samples × 9 tasks × 1 language × 2 insertion types = 36
            assert total == 36

    def test_expected_total_default(self):
        """Test expected total with defaults."""
        exp = InsertionsExperiment(
            samples_per_task=100,
            languages=None,
            output_dir="./test_output",
            seed=9,
        )
        # 100 samples × 9 tasks × 10 languages × 2 insertion types = 18,000
        expected = 100 * 9 * 10 * 2
        assert exp.get_total_expected_samples() == expected


class TestMemorizationExperiment:
    """Tests for MemorizationExperiment."""

    def test_init(self):
        """Test experiment initialization."""
        exp = MemorizationExperiment(
            samples_per_task=10,
            languages=["en_US"],
            output_dir="./test_output",
            seed=42,
        )
        assert exp.samples_per_task == 10

    def test_init_custom_years(self):
        """Test initialization with custom years."""
        exp = MemorizationExperiment(
            samples_per_task=10,
            languages=["en_US"],
            output_dir="./test_output",
            seed=42,
            years=[2025, 2050, 2075],
        )
        assert exp.years == [2025, 2050, 2075]

    def test_default_years(self):
        """Test default years (2025-2095 step 10)."""
        exp = MemorizationExperiment(
            samples_per_task=10,
            languages=["en_US"],
            output_dir="./test_output",
            seed=42,
        )
        expected_years = [2025, 2035, 2045, 2055, 2065, 2075, 2085, 2095]
        assert exp.years == expected_years

    def test_generate_small(self):
        """Test generating small dataset."""
        with tempfile.TemporaryDirectory() as tmpdir:
            exp = MemorizationExperiment(
                samples_per_task=2,
                languages=["en_US"],
                output_dir=tmpdir,
                seed=42,
                years=[2025, 2035],  # Only 2 years for faster test
            )
            total = exp.generate()
            # Memorization uses 4 task types × 2 samples × 1 lang × 2 years = 16
            assert total > 0

    def test_expected_total_default(self):
        """Test expected total with defaults."""
        exp = MemorizationExperiment(
            samples_per_task=100,
            languages=None,
            output_dir="./test_output",
            seed=9,
        )
        # 100 samples × 4 tasks × 10 languages × 8 years = 32,000
        expected = 100 * 4 * 10 * 8
        assert exp.get_total_expected_samples() == expected


class TestExperimentReproducibility:
    """Tests for experiment reproducibility."""

    def test_variations_reproducibility(self):
        """Test variations experiment is reproducible."""
        with tempfile.TemporaryDirectory() as tmpdir1:
            with tempfile.TemporaryDirectory() as tmpdir2:
                exp1 = VariationsExperiment(
                    samples_per_task=2,
                    languages=["en_US"],
                    output_dir=tmpdir1,
                    seed=42,
                )
                exp2 = VariationsExperiment(
                    samples_per_task=2,
                    languages=["en_US"],
                    output_dir=tmpdir2,
                    seed=42,
                )
                total1 = exp1.generate()
                total2 = exp2.generate()
                assert total1 == total2
