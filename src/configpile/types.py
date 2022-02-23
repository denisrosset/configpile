from __future__ import annotations

import pathlib
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import (
    Any,
    Callable,
    Generic,
    Iterable,
    List,
    Mapping,
    NoReturn,
    Optional,
    Sequence,
    Type,
    TypeVar,
    cast,
)

import parsy

from .errors import ParseErr, Result, collect_seq

T = TypeVar("T", covariant=True)  #: Item type

W = TypeVar("W", covariant=True)  #: Wrapped item type


class ArgType(ABC, Generic[T]):
    """Describes an argument type"""

    @abstractmethod
    def parse(self, arg: str) -> Result[T]:
        """
        Parses a string argument into a result type

        This method reports parsing errors using a result type instead of raising
        exceptions.

        Args:
            arg: Argument to parse

        Returns:
            A result containing either the parsed value or a description of an error
        """

    def argparse_argument_kwargs(self) -> Mapping[str, Any]:
        return {}

    def empty_means_none(self, strip: bool = True) -> ArgType[Optional[T]]:
        """
        Returns a new argument type where the empty string means None

        Args:
            strip: Whether to strip whitespace

        Returns:
            A new argument type
        """
        return _EmptyMeansNone(self, strip)

    def separated_by(
        self, sep: str, strip: bool = True, remove_empty: bool = True
    ) -> ArgType[Sequence[T]]:
        """
        Returns a new argument type that parses values separated by a string

        Args:
            sep: Separator
            strip: Whether to strip whitespace from separated values
            remove_empty: Whether to remove empty strings before parsing them

        Returns:
            A new argument type
        """
        return _SeparatedBy(self, sep, strip, remove_empty)

    @staticmethod
    def from_parser(type_: Type[T], parser: parsy.Parser) -> ArgType[T]:
        """
        Creates an argument type from a parsy parser

        Args:
            type_: PEP 484 type, used to type the return argument
            parser: Parser returning a value of type ``t``

        Returns:
            An argument type wrapping the parsy parser
        """
        return _Parsy(parser)

    @staticmethod
    def from_function(f: Callable[[str], T]) -> ArgType[T]:
        return _Function(f)

    @staticmethod
    def invalid() -> ArgType[NoReturn]:
        def invalid_fun(s: str) -> NoReturn:
            raise RuntimeError("Invalid argument type")

        return ArgType.from_function(invalid_fun)

    @staticmethod
    def choices_str(values: Sequence[str], strip: bool = True) -> ArgType[str]:
        return ArgType.choices({v: v for v in values})

    @staticmethod
    def choices(mapping: Mapping[str, T]) -> ArgType[T]:
        return _Choices(mapping)


@dataclass(frozen=True)
class _Choices(ArgType[T]):
    mapping: Mapping[str, T]

    def parse(self, arg: str) -> Result[T]:
        if arg in self.mapping:
            return self.mapping[arg]
        else:
            msg = f"Value {arg} not in choices {','.join(self.mapping.keys())}"
            return ParseErr(msg, arg, None)

    def argparse_argument_kwargs(self) -> Mapping[str, Any]:
        return {"choices": self.mapping.keys(), "type": str}


@dataclass  # not frozen because mypy bug, please be responsible
class _Function(ArgType[T]):
    """
    Wraps a function that may raise exceptions
    """

    # the optional is to make mypy happy
    fun: Callable[[str], T]  #: Callable function that may raise

    def parse(self, arg: str) -> Result[T]:
        try:
            f = self.fun
            assert f is not None
            return f(arg)
        except Exception as err:
            return ParseErr(str(err), arg, None)


@dataclass(frozen=True)
class _Parsy(ArgType[T]):
    parser: parsy.Parser

    def parse(self, arg: str) -> Result[T]:
        res = (self.parser << parsy.eof)(arg, 0)  # Inspired by Parser.parse
        if res.status:
            return cast(T, res.value)
        else:
            return ParseErr(res.expected, arg, res.furthest)


@dataclass(frozen=True)
class _EmptyMeansNone(ArgType[Optional[W]]):
    wrapped: ArgType[W]  #: Wrapped ArgType called if arg is not empty
    strip: bool  #:  Whether to strip whitespace before testing for empty

    def parse(self, arg: str) -> Result[Optional[W]]:
        if self.strip:
            arg = arg.strip()
        if not arg:
            return None
        else:
            return self.wrapped.parse(arg)


@dataclass(frozen=True)
class _SeparatedBy(ArgType[Sequence[W]]):
    item: ArgType[W]  #: ArgType of individual items
    sep: str  #: Item separator
    strip: bool  #: Whether to strip whitespace around separated strings
    remove_empty: bool  #: Whether to prune empty strings

    def parse(self, arg: str) -> Result[Sequence[W]]:
        items: Iterable[str] = arg.split(self.sep)
        if self.strip:
            items = map(lambda s: s.strip(), items)
        if self.remove_empty:
            items = filter(None, items)
        res: Sequence[Result[W]] = [self.item.parse(s) for s in items]
        return collect_seq(res)


path = ArgType.from_function(lambda s: pathlib.Path(s))
integer = ArgType.from_function(lambda s: int(s))
word = ArgType.from_function(lambda s: s.strip())
