"""Experiments module for the four experimental axes."""

from trd.experiments.base import BaseExperiment
from trd.experiments.variations import VariationsExperiment
from trd.experiments.difficulties import DifficultiesExperiment
from trd.experiments.insertions import InsertionsExperiment
from trd.experiments.memorization import MemorizationExperiment

__all__ = [
    "BaseExperiment",
    "VariationsExperiment",
    "DifficultiesExperiment",
    "InsertionsExperiment",
    "MemorizationExperiment",
]
