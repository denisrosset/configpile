"""
Argument value parsing

This module is mostly self-contained, and provides ways to construct :class:`.Parser` instances
which parse string arguments into values.

During the configuration building, the parsed values are collected by a
:class:`configpile.collector.Collector` instance.

.. rubric:: Types

This module uses the following types.

.. py:data:: _Value

    Value being parsed by a :class:`.Parser`

.. py:data:: _Parameter

    Type received by a mapping function

.. py:data:: _ReturnType

    Type returned by a mapping function

.. py:data:: _Item

    Item in a sequence
"""

from .auto import derive_parser_and_collector
from .parser import (
    ErrorMessageProvider,
    ForceCase,
    Parser,
    Predicate,
    _Item,
    _Parameter,
    _Returned,
    _Value,
)
from .std import (
    HasParser,
    LoggingLevel,
    _HasParser,
    bool_parser,
    float_parser,
    int_parser,
    path_parser,
    scalar_type_parsers,
    str_parser,
    stripped_str_parser,
)

__all__ = [
    "derive_parser_and_collector",
    "Parser",
    "Predicate",
    "ForceCase",
    "ErrorMessageProvider",
    "path_parser",
    "int_parser",
    "str_parser",
    "stripped_str_parser",
    "float_parser",
    "bool_parser",
    "HasParser",
    "_HasParser",
    "LoggingLevel",
    "scalar_type_parsers",
]
