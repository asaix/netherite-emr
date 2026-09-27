"""Templates module for question generation in multiple languages."""

from trd.templates.questions import QUESTION_TEMPLATES, get_question_template
from trd.templates.plurals import DAYS, HOURS, MINUTES, get_plural_form
from trd.templates.insertions import (
    SIMILAR_INSERTIONS,
    DISSIMILAR_INSERTIONS,
    get_random_insertion,
    prepend_insertion,
)

__all__ = [
    "QUESTION_TEMPLATES",
    "get_question_template",
    "DAYS",
    "HOURS",
    "MINUTES",
    "get_plural_form",
    "SIMILAR_INSERTIONS",
    "DISSIMILAR_INSERTIONS",
    "get_random_insertion",
    "prepend_insertion",
]
