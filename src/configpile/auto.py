from __future__ import annotations

import collections.abc
import operator
import typing
from abc import ABC, abstractmethod
from dataclasses import dataclass
from functools import reduce
from typing import (
    Any,
    Callable,
    ClassVar,
    Dict,
    Literal,
    Optional,
    Sequence,
    Tuple,
    Type,
    TypeVar,
    Union,
)

from typing_extensions import Protocol, get_args, get_origin, get_type_hints, runtime_checkable

from .arg import Param

from . import parsers
from .collector import Collector
from .enums import Derived, ForceCase, Positional
from .parsers import Parser

T = TypeVar("T")
U = TypeVar("U")


@dataclass
class Env:
    """Describes how a parameter can be populated from environment variables"""

    env_var_name: Union[str, Derived, None]

    @staticmethod
    def default() -> Env:
        return Env(None)


@dataclass(frozen=True)
class INI:
    """Describes how a parameter can be populated from configuration (INI) files"""

    #: Name of the key
    key_name: Union[str, Derived, None]

    @staticmethod
    def default() -> INI:
        return INI(Derived.KEBAB_CASE)

@dataclass(frozen=True)
class Default:
    """Describes the default value of a parameter"""
    value: str

@dataclass(frozen=True)
class Flags:
    """Describes how a parameter can be populated from command-line flags"""

    #: Short command-line flag, should be a single letter or None
    short_flag_name: Optional[str]

    #: Long command-line flag
    #:
    #: Either a string without the preceding two hyphens, a derivation instruction or None
    long_flag_name: Union[str, Derived, None]

    def __init__(self, *, short: Optional[str], long: Union[str, Derived, None]):
        """Constructs a FLag instance

        Args:
            short: Short flag name (single letter), with or without preceding hyphen
            long: Long flag name (string), with or without the two preceding hyphens
        """
        if isinstance(short, str):
            if short[0] == "-":
                short = short[1:]
        if isinstance(long, str):
            if len(long) >= 2 and long[0:1] == "--":
                long = long[2:]
        setattr(self, "short_flag_name", short)
        setattr(self, "long_flag_name", long)


def derive_param(field_name: str, t: Type[T], args: Sequence[Any])

def derive_param_from_parts(
    field_name: str,
    t: Type[T],
    parser: Optional[Parser[T]],
    collector: Optional[Collector[T]],
    default_value: Optional[Default],
    command_line_positional: Optional[Positional],
    command_line_flags: Optional[Flags],
    config_key: Optional[INI],
    env_var_name: Optional[Env],
) -> Param[T]:
    pass


@runtime_checkable
class Parseable(Protocol):
    """Scalar-like type that can be parsed in a configuration"""

    @classmethod
    def _configpile_parser(cls: Type[T]) -> Parser[T]:
        """Returns a configpile parser for this class"""
        ...


_scalar_parsers: Dict[Any, Parser] = {
    int: parsers.int_parser,
    str: parsers.str_parser,
    float: parsers.float_parser,
}
"""List of default scalar parsers"""


def derive_scalar(t: Type[T]) -> Parser[T]:
    """
    Returns a parser for a scalar type

    Args:
        t: Type for which to derive a parser

    Raises:
        Exception: If a parser cannot be derived
    """
    if isinstance(t, Parseable):
        return t.configpile_parser()
    if t in _scalar_parsers:
        return _scalar_parsers[t]
    raise Exception(f"Does not know how to derive a parser for type {t}")


def is_string_literal(element: Any) -> bool:
    """Returns whether the given type is a literal with string values"""
    return get_origin(element) is Literal and all([isinstance(a, str) for a in get_args(element)])


def derive_union(elements: Sequence[Any]) -> Tuple[Parser[T], Collector[T]]:
    """Returns a parser for a union type

    Args:
        elements: Arguments of the union type

    Raises:
        Exception: If the derivation fails
    """
    is_none = [el is type(None) for el in elements]
    if any(is_none):
        rest = [elements[i] for i, b in enumerate(is_none) if not b]
        if all(map(is_string_literal, rest)):
            strings = reduce(operator.concat, map(get_args, rest))
            return (
                Parser.from_choices(
                    strings, strip=False, force_case=ForceCase.NO_CHANGE
                ).empty_means_none(),
                Collector.keep_last(),
            )
        if len(rest) == 1:
            scalar = rest[0]
            return (derive_scalar(scalar).empty_means_none(), Collector.keep_last())
        raise Exception(
            f"Can derive a parser for Optional[X] only when X is a scalar or a union of string literals, {elements} given"
        )
    else:
        if all(map(is_string_literal, elements)):
            strings = reduce(operator.concat, map(get_args, elements))
            return (
                Parser.from_choices(strings, strip=False, force_case=ForceCase.NO_CHANGE),
                Collector.keep_last(),
            )
        raise Exception(f"Cannot derive a parser for this kind of Union with elements {elements}")


def derive(t: Type[T]) -> Tuple[Parser[T], Collector[T]]:
    """Returns a tuple containing a parser and a collector for a type

    Args:
        t: Type for which to derive a parser and collector
    """
    o = get_origin(t)
    if o is not None:
        a = get_args(t)
        if o is collections.abc.Sequence:
            assert len(a) == 1
            scalar = a[0]
            return (derive_scalar(scalar).as_sequence_of_one(), Collector.append())
        if o is Union:
            return derive_union(a)
        if o is Literal:
            assert is_string_literal(t), "Can only derive parsers for literals containing strings"
            return (
                Parser.from_choices(a, strip=False, force_case=ForceCase.NO_CHANGE),
                Collector.keep_last(),
            )

    return (derive_scalar(t), Collector.keep_last())
