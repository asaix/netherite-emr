"""Language configurations for multilingual dataset generation.

Supports 10 languages across multiple language families as described in Table 1 of the paper:
- Indo-European (Germanic): English, German, Dutch
- Indo-European (Romance): Spanish, French, Italian, Portuguese  
- Indo-European (Indo-Aryan): Hindi
- Afro-Asiatic: Arabic
- Japonic: Japanese
"""

from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class Language:
    """Language configuration.
    
    Attributes:
        code: ISO-639-1 language code with locale (e.g., "en_US")
        name: Full language name
        family: Language family
        branch: Language branch within family
        script: Writing script used
        locale_code: System locale code for day names
    """
    code: str
    name: str
    family: str
    branch: str
    script: str
    locale_code: str
    
    def __str__(self) -> str:
        return self.code


# Language constants
EN = Language(
    code="en_US",
    name="English",
    family="Indo-European",
    branch="Germanic",
    script="Latin",
    locale_code="en_US.UTF-8",
)

ES = Language(
    code="es_ES",
    name="Spanish",
    family="Indo-European",
    branch="Romance",
    script="Latin",
    locale_code="es_ES.UTF-8",
)

DE = Language(
    code="de_DE",
    name="German",
    family="Indo-European",
    branch="Germanic",
    script="Latin",
    locale_code="de_DE.UTF-8",
)

FR = Language(
    code="fr_FR",
    name="French",
    family="Indo-European",
    branch="Romance",
    script="Latin",
    locale_code="fr_FR.UTF-8",
)

IT = Language(
    code="it_IT",
    name="Italian",
    family="Indo-European",
    branch="Romance",
    script="Latin",
    locale_code="it_IT.UTF-8",
)

PT = Language(
    code="pt_BR",
    name="Portuguese",
    family="Indo-European",
    branch="Romance",
    script="Latin",
    locale_code="pt_BR.UTF-8",
)

NL = Language(
    code="nl_NL",
    name="Dutch",
    family="Indo-European",
    branch="Germanic",
    script="Latin",
    locale_code="nl_NL.UTF-8",
)

HI = Language(
    code="hi_IN",
    name="Hindi",
    family="Indo-European",
    branch="Indo-Aryan",
    script="Devanagari",
    locale_code="hi_IN.UTF-8",
)

AR = Language(
    code="ar_SA",
    name="Arabic",
    family="Afro-Asiatic",
    branch="Semitic",
    script="Arabic",
    locale_code="ar_SA.UTF-8",
)

JA = Language(
    code="ja_JP",
    name="Japanese",
    family="Japonic",
    branch="Japanese",
    script="Japanese",
    locale_code="ja_JP.UTF-8",
)

# List of all supported languages
SUPPORTED_LANGUAGES: List[Language] = [EN, ES, DE, FR, IT, PT, NL, HI, AR, JA]

# Language codes for convenience
LANGUAGE_CODES: List[str] = [lang.code for lang in SUPPORTED_LANGUAGES]

# Mapping from code to Language object
LANGUAGE_MAP = {lang.code: lang for lang in SUPPORTED_LANGUAGES}


def get_language(code: str) -> Language:
    """Get Language object by code.
    
    Args:
        code: Language code (e.g., "en_US")
        
    Returns:
        Language object
        
    Raises:
        ValueError: If code is not a supported language
    """
    if code not in LANGUAGE_MAP:
        valid = ", ".join(LANGUAGE_CODES)
        raise ValueError(f"Unsupported language code: {code}. Valid options: {valid}")
    return LANGUAGE_MAP[code]


def get_languages_by_family(family: str) -> List[Language]:
    """Get all languages in a family.
    
    Args:
        family: Language family name (e.g., "Indo-European")
        
    Returns:
        List of Language objects in that family
    """
    return [lang for lang in SUPPORTED_LANGUAGES if lang.family == family]


def get_languages_by_script(script: str) -> List[Language]:
    """Get all languages using a specific script.
    
    Args:
        script: Script name (e.g., "Latin")
        
    Returns:
        List of Language objects using that script
    """
    return [lang for lang in SUPPORTED_LANGUAGES if lang.script == script]
