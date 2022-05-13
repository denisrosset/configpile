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

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional, Type, TypeVar

from ..userr import Err, Res
from .parser import ForceCase, Parser

#: Parses a path
path_parser: Parser[Path] = Parser.from_function_that_raises(Path)

#: Parses an integer
int_parser: Parser[int] = Parser.from_function_that_raises(int)

#: Parses a string, preserves whitespace
str_parser: Parser[str] = Parser.from_function(lambda s: s)

#: Parses a string, stripping whitespace left and right
stripped_str_parser: Parser[str] = Parser.from_function(lambda s: s.strip())

#: Parses a float
float_parser: Parser[float] = Parser.from_function_that_raises(float)

bool_parser: Parser[bool] = Parser.from_mapping(
    {"true": True, "false": False},
    force_case=ForceCase.LOWER,
    aliases={"t": True, "f": False, "1": True, "0": False},
)

#: Scalar type
_HasParser = TypeVar("_HasParser")


class HasParser(ABC):
    """Describes a class that can return a configpile parser"""

    @classmethod
    @abstractmethod
    def configpile_parser(cls: Type[_HasParser]) -> Parser[_HasParser]:
        """Returns a parser for instances of this class"""


@dataclass(frozen=True)
class LoggingLevel(HasParser):
    """Describes a logging level"""

    int_value: int

    @staticmethod
    def _parse(arg: str) -> Res[LoggingLevel]:
        try:
            return LoggingLevel(int(arg))
        except ValueError:
            pass
        res = logging.getLevelName(arg)
        if isinstance(res, int):
            return LoggingLevel(res)
        return Err.make(f"Cannot parse logging level {arg}")

    @classmethod
    def configpile_parser(cls) -> Parser[LoggingLevel]:
        return Parser.from_function(LoggingLevel._parse)

    def set(self, logger: Optional[logging.Logger] = None) -> None:
        """Sets the logging level in the provided logger

        Args:
            logger: Logger to update, or root logger (if :py:`None`)
        """
        if logger is None:
            logger = logging.getLogger()
        logger.setLevel(self.int_value)


#: Scalar types for which a parser can be automatically derived
scalar_type_parsers: Dict[type, Parser[Any]] = {
    Path: path_parser,
    int: int_parser,
    float: float_parser,
    str: str_parser,
    bool: bool_parser,
    LoggingLevel: LoggingLevel.configpile_parser(),
}
