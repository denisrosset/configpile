"""
This module defines data classes and enums that are used elsewhere.

We group them here to break circular imports.
"""

from enum import Enum


class SpecialAction(Enum):
    """Describes special actions that do not correspond to normal execution"""

    HELP = "help"  #: Display a help message
    VERSION = "version"  #: Print the version number


class Auto:
    """Describes a value that is derived automatically from context"""
