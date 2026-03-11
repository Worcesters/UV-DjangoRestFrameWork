"""
Enumeration of supported languages.

This module contains an enumeration of languages that the program supports,
and provides a way to refer to them by their unique string identifier, which
is also used as the module name of the parser.

The enumeration is defined in the `Language` class.
"""
from enum import Enum

class Language(Enum):
    """
    Enumeration of languages supported by the program.

    Each language is represented by a unique string identifier,
    which is also used as the module name of the parser.
    """
    PHP = "php"
    PYTHON = "python"
    JAVA = "java"
