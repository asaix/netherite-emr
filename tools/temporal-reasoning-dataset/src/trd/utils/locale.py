"""Locale utilities for multilingual day names."""

import locale
from datetime import datetime
from typing import Dict

# Day names in all supported languages (0=Monday, 6=Sunday)
# This avoids relying on system locale which may not be installed
DAY_NAMES: Dict[str, Dict[int, str]] = {
    "en_US": {
        0: "Monday",
        1: "Tuesday",
        2: "Wednesday",
        3: "Thursday",
        4: "Friday",
        5: "Saturday",
        6: "Sunday",
    },
    "es_ES": {
        0: "lunes",
        1: "martes",
        2: "miércoles",
        3: "jueves",
        4: "viernes",
        5: "sábado",
        6: "domingo",
    },
    "de_DE": {
        0: "Montag",
        1: "Dienstag",
        2: "Mittwoch",
        3: "Donnerstag",
        4: "Freitag",
        5: "Samstag",
        6: "Sonntag",
    },
    "fr_FR": {
        0: "lundi",
        1: "mardi",
        2: "mercredi",
        3: "jeudi",
        4: "vendredi",
        5: "samedi",
        6: "dimanche",
    },
    "it_IT": {
        0: "lunedì",
        1: "martedì",
        2: "mercoledì",
        3: "giovedì",
        4: "venerdì",
        5: "sabato",
        6: "domenica",
    },
    "pt_BR": {
        0: "segunda-feira",
        1: "terça-feira",
        2: "quarta-feira",
        3: "quinta-feira",
        4: "sexta-feira",
        5: "sábado",
        6: "domingo",
    },
    "nl_NL": {
        0: "maandag",
        1: "dinsdag",
        2: "woensdag",
        3: "donderdag",
        4: "vrijdag",
        5: "zaterdag",
        6: "zondag",
    },
    "ja_JP": {
        0: "月曜日",
        1: "火曜日",
        2: "水曜日",
        3: "木曜日",
        4: "金曜日",
        5: "土曜日",
        6: "日曜日",
    },
    "ar_SA": {
        0: "الاثنين",
        1: "الثلاثاء",
        2: "الأربعاء",
        3: "الخميس",
        4: "الجمعة",
        5: "السبت",
        6: "الأحد",
    },
    "hi_IN": {
        0: "सोमवार",
        1: "मंगलवार",
        2: "बुधवार",
        3: "गुरुवार",
        4: "शुक्रवार",
        5: "शनिवार",
        6: "रविवार",
    },
}


def get_day_name(date: datetime, language_code: str) -> str:
    """Get the day name for a date in the specified language.
    
    Uses built-in day name lookup instead of system locale to ensure
    consistent behavior across different systems.
    
    Args:
        date: The datetime object
        language_code: Language code (e.g., "en_US")
        
    Returns:
        Day name in the target language
        
    Raises:
        ValueError: If language_code is not supported
    """
    if language_code not in DAY_NAMES:
        valid = ", ".join(DAY_NAMES.keys())
        raise ValueError(f"Unsupported language: {language_code}. Valid: {valid}")
    
    # weekday() returns 0 for Monday, 6 for Sunday
    weekday = date.weekday()
    return DAY_NAMES[language_code][weekday]


def set_locale_safely(language_code: str) -> bool:
    """Attempt to set the system locale for the given language.
    
    This is a best-effort function that tries common locale variants.
    It's mainly used as a fallback if DAY_NAMES doesn't have the language.
    
    Args:
        language_code: Language code (e.g., "en_US")
        
    Returns:
        True if locale was set successfully, False otherwise
    """
    # Common locale suffixes to try
    suffixes = [".UTF-8", ".utf8", ""]
    
    for suffix in suffixes:
        try:
            locale.setlocale(locale.LC_TIME, f"{language_code}{suffix}")
            return True
        except locale.Error:
            continue
    
    return False


def reset_locale() -> None:
    """Reset locale to system default."""
    try:
        locale.setlocale(locale.LC_TIME, "")
    except locale.Error:
        pass
