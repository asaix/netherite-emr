"""Plural forms for temporal units (days, hours, minutes) in all supported languages.

Some languages like Japanese and Hindi use the same word for singular and plural.
Arabic uses different plural forms based on the number, we provide the most common form.
"""

from typing import Dict

# Singular/plural form keys
ONE = "one"
MORE = "more"

# Days in all languages
DAYS: Dict[str, Dict[str, str]] = {
    ONE: {
        "en_US": "day",
        "es_ES": "día",
        "it_IT": "giorno",
        "fr_FR": "jour",
        "de_DE": "Tag",
        "pt_BR": "dia",
        "nl_NL": "dag",
        "ja_JP": "日",
        "ar_SA": "يوم",
        "hi_IN": "दिन",
    },
    MORE: {
        "en_US": "days",
        "es_ES": "días",
        "it_IT": "giorni",
        "fr_FR": "jours",
        "de_DE": "Tage",
        "pt_BR": "dias",
        "nl_NL": "dagen",
        "ja_JP": "日",  # Same as singular in Japanese
        "ar_SA": "أيام",
        "hi_IN": "दिन",  # Same as singular in Hindi
    },
}

# Hours in all languages
HOURS: Dict[str, Dict[str, str]] = {
    ONE: {
        "en_US": "hour",
        "es_ES": "hora",
        "it_IT": "ora",
        "fr_FR": "heure",
        "de_DE": "Stunde",
        "pt_BR": "hora",
        "nl_NL": "uur",
        "ja_JP": "時間",
        "ar_SA": "ساعة",
        "hi_IN": "घंटा",
    },
    MORE: {
        "en_US": "hours",
        "es_ES": "horas",
        "it_IT": "ore",
        "fr_FR": "heures",
        "de_DE": "Stunden",
        "pt_BR": "horas",
        "nl_NL": "uur",  # Same as singular in Dutch
        "ja_JP": "時間",  # Same as singular in Japanese
        "ar_SA": "ساعات",
        "hi_IN": "घंटे",
    },
}

# Minutes in all languages
MINUTES: Dict[str, Dict[str, str]] = {
    ONE: {
        "en_US": "minute",
        "es_ES": "minuto",
        "it_IT": "minuto",
        "fr_FR": "minute",
        "de_DE": "Minute",
        "pt_BR": "minuto",
        "nl_NL": "minuut",
        "ja_JP": "分",
        "ar_SA": "دقيقة",
        "hi_IN": "मिनट",
    },
    MORE: {
        "en_US": "minutes",
        "es_ES": "minutos",
        "it_IT": "minuti",
        "fr_FR": "minutes",
        "de_DE": "Minuten",
        "pt_BR": "minutos",
        "nl_NL": "minuten",
        "ja_JP": "分",  # Same as singular in Japanese
        "ar_SA": "دقائق",
        "hi_IN": "मिनट",  # Same as singular in Hindi
    },
}


def get_plural_form(unit: str, count: int, language_code: str) -> str:
    """Get the correct singular/plural form for a temporal unit.
    
    Args:
        unit: Unit type ("day", "hour", "minute")
        count: The number to determine singular/plural
        language_code: Language code (e.g., "en_US")
        
    Returns:
        The correct form of the unit in the specified language
        
    Raises:
        ValueError: If unit or language is not supported
    """
    unit_map = {
        "day": DAYS,
        "days": DAYS,
        "hour": HOURS,
        "hours": HOURS,
        "minute": MINUTES,
        "minutes": MINUTES,
    }
    
    if unit.lower() not in unit_map:
        valid_units = ["day", "hour", "minute"]
        raise ValueError(f"Unknown unit: {unit}. Valid units: {valid_units}")
    
    unit_dict = unit_map[unit.lower()]
    form = ONE if count == 1 else MORE
    
    if language_code not in unit_dict[form]:
        valid_langs = list(unit_dict[form].keys())
        raise ValueError(f"Unknown language: {language_code}. Valid: {valid_langs}")
    
    return unit_dict[form][language_code]


def get_day_form(count: int, language_code: str) -> str:
    """Get the correct singular/plural form for 'day'.
    
    Args:
        count: The number of days
        language_code: Language code (e.g., "en_US")
        
    Returns:
        The correct form of 'day' in the specified language
    """
    return get_plural_form("day", count, language_code)


def get_hour_form(count: int, language_code: str) -> str:
    """Get the correct singular/plural form for 'hour'.
    
    Args:
        count: The number of hours
        language_code: Language code (e.g., "en_US")
        
    Returns:
        The correct form of 'hour' in the specified language
    """
    return get_plural_form("hour", count, language_code)


def get_minute_form(count: int, language_code: str) -> str:
    """Get the correct singular/plural form for 'minute'.
    
    Args:
        count: The number of minutes
        language_code: Language code (e.g., "en_US")
        
    Returns:
        The correct form of 'minute' in the specified language
    """
    return get_plural_form("minute", count, language_code)
