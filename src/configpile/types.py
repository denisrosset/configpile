"""
Argument value parsing

This module is mostly self-contained, and provides ways to construct :class:`.ParamType` instances
which parse string arguments into values.

During the configuration building, the parsed values are collected by a 
:class:`configpile.collector.Collector` instance.

.. rubric:: Types

This module uses the following types.

.. py:data:: _Value

    Value being parsed by a :class:`.ParamType`

.. py:data:: _Parameter

    Type received by a mapping function

.. py:data:: _ReturnType

    Type returned by a mapping function

.. py:data:: _Item

    Item in a sequence
"""

from __future__ import annotations

import pathlib
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Generic,
    Iterable,
    List,
    Literal,
    Mapping,
    NoReturn,
    Optional,
    Protocol,
    Sequence,
    Type,
    TypeVar,
    Union,
    cast,
)

if TYPE_CHECKING:
    import parsy

from . import userr
from .userr import Err, Res, collect_seq
from .util import assert_never

# those types are documented in the module docstring

_I = TypeVar("_I")  # type used only internally

_Value = TypeVar("_Value")

_Item = TypeVar("_Item")

_Parameter = TypeVar("_Parameter")

_ReturnType = TypeVar("_ReturnType")


class ForceCase(Enum):
    """
    Describes whether a string is normalized to lower or upper case before processing
    """

    NO_CHANGE = 0  #: Keep case
    UPPER = 1  #: Change to uppercase
    LOWER = 2  #: Change to lowercase


class ParamType(ABC, Generic[_Value]):
    """Describes a parameter type, which parses a string into a parameter value"""

    @abstractmethod
    def parse(self, arg: str) -> Res[_Value]:
        """
        Parses a string into a result

        This method reports parsing errors using a result type instead of raising
        exceptions.

        Example:
            >>> user_input = "invalid"
            >>> float_.parse(user_input)
            Err1("Error 'could not convert string to float: 'invalid'' in 'invalid'")
            >>> user_input = 2.0
            >>> float_.parse(user_input)
            2.0

        Args:
            arg: String value to parse

        Returns:
            A result containing either the parsed value or a description of an error
        """

    def argparse_argument_kwargs(self) -> Mapping[str, Any]:
        """
        Returns, if any, the keyword arguments that should be provided to :mod:`argparse`

        The arguments will be added to :meth:`argparse.ArgumentParser.add_argument`
        """
        return {}

    def map(self, f: Callable[[_Value], _Item]) -> ParamType[_Item]:
        """
        Maps successful results of the parser through the given function

        Args:
            f: Function to map the result through

        Returns:
            Updated parameter type
        """
        return _Mapped(self, f)

    def as_sequence_of_one(self) -> ParamType[Sequence[_Value]]:
        """
        Returns a parameter type, that returns a sequence of a single value on success

        Returns:
            Updated parameter type
        """
        f: Callable[[_I], Sequence[_I]] = lambda t: [t]
        return self.map(f)

    def empty_means_none(self, strip: bool = True) -> ParamType[Optional[_Value]]:
        """
        Returns a new parameter type where the empty string means None

        Args:
            strip: Whether to strip whitespace

        Returns:
            A new parameter type
        """
        return _EmptyMeansNone(self, strip)

    def separated_by(
        self, sep: str, strip: bool = True, remove_empty: bool = True
    ) -> ParamType[Sequence[_Value]]:
        """
        Returns a new parameter type that parses values separated by a string

        Args:
            sep: Separator
            strip: Whether to strip whitespace from separated values
            remove_empty: Whether to remove empty strings before parsing them

        Returns:
            A new parameter type
        """
        return _SeparatedBy(self, sep, strip, remove_empty)

    def validated(
        self, predicate: Callable[[_Value], bool], msg: Union[str, Callable[[str, _Value], str]]
    ) -> _Validated[_Value]:
        """
        Returns a parameter type that verifies a predicate after successful parse

        Args:
            predicate: Predicate to check
            msg: Either a string, or a function that constructs a string from the parsed string
                 and the result

        Returns:
            A new parameter type
        """
        if isinstance(msg, str):
            c: str = msg
            return _Validated(self, predicate, lambda a, t: c)
        else:
            return _Validated(
                self,
                predicate,
                msg,
            )

    @staticmethod
    def from_parser(type_: Type[_Value], parser: parsy.Parser) -> ParamType[_Value]:
        """
        Creates a parameter type from a parsy parser

        Args:
            type_: PEP 484 type, used to type the return argument
            parser: Parser returning a value of type ``t``

        Returns:
            Parameter type
        """
        return _Parsy(parser)

    @staticmethod
    def from_function_that_raises(f: Callable[[str], _Value]) -> ParamType[_Value]:
        """
        Creates a parameter type from a function that raises exceptions on parse errors

        Args:
            f: Function that parses the string

        Returns:
            Parameter type
        """
        return _FunctionThatRaises(f)

    @staticmethod
    def from_result_function(f: Callable[[str], Res[_Value]]) -> ParamType[_Value]:
        """
        Creates a parameter type from a function that returns a value or an error

        Args:
            f: Function that parses the string

        Returns:
            Parameter type
        """

        return _ResultFunction(f)

    @staticmethod
    def invalid() -> ParamType[_Value]:
        """
        Creates a parameter type that always return errors
        """

        def invalid_fun(s: str) -> NoReturn:
            raise RuntimeError("Invalid parameter type")

        return ParamType.from_function_that_raises(invalid_fun)

    @staticmethod
    def choices_str(
        values: Iterable[str],
        strip: bool = True,
        force_case: ForceCase = ForceCase.NO_CHANGE,
    ) -> ParamType[str]:
        """
        Creates a parameter type whose values are chosen from a set of strings

        Args:
            values: Set of values
            strip: Whether to strip whitespace before looking for choices

        Returns:
            Parameter type
        """

        return ParamType.choices({v: v for v in values}, strip, force_case)

    @staticmethod
    def choices(
        mapping: Mapping[str, _Value],
        strip: bool = True,
        force_case: ForceCase = ForceCase.NO_CHANGE,
        aliases: Mapping[str, _Value] = {},
    ) -> ParamType[_Value]:
        """
        Creates a parameter type whose strings correspond to keys in a dictionary

        Args:
            mapping: Dictionary mapping strings to values
            strip: Whether to strip whitespace before looking for keys
            force_case: Whether to normalize the case of the user string
            aliases: Additional mappings not shown in help

        Returns:
            Parameter type
        """
        return _Choices(mapping, strip, force_case, aliases)


@dataclass(frozen=True)
class _Choices(ParamType[_Value]):
    """
    Describes a multiple choice parameter type
    """

    mapping: Mapping[str, _Value]
    strip: bool
    force_case: ForceCase
    aliases: Mapping[str, _Value]

    def parse(self, arg: str) -> Res[_Value]:
        if self.strip:
            arg = arg.strip()
        if self.force_case is ForceCase.LOWER:
            arg = arg.lower()
        elif self.force_case is ForceCase.UPPER:
            arg = arg.upper()
        elif self.force_case is ForceCase.NO_CHANGE:
            pass
        else:
            assert_never(self.force_case)
        all_mappings = {**self.mapping, **self.aliases}
        if arg in all_mappings:
            return all_mappings[arg]
        else:
            msg = f"Value {arg} not in choices {','.join(self.mapping.keys())}"
            return Err.make(msg)

    def argparse_argument_kwargs(self) -> Mapping[str, Any]:
        return {"choices": self.mapping.keys(), "type": str}


@dataclass  # not frozen because mypy bug, please be responsible
class _FunctionThatRaises(ParamType[_Value]):
    """
    Wraps a function that may raise exceptions
    """

    # the optional is to make mypy happy
    fun: Callable[[str], _Value]  #: Callable function that may raise

    def parse(self, arg: str) -> Res[_Value]:
        try:
            f = self.fun
            assert f is not None
            return f(arg)
        except Exception as err:
            return Err.make(f"Error '{err}' in '{arg}'")


@dataclass  # not frozen because mypy bug, please be responsible
class _ResultFunction(ParamType[_Value]):
    """
    Wraps a function that returns a result
    """

    fun: Callable[[str], Res[_Value]]

    def parse(self, arg: str) -> Res[_Value]:
        return self.fun(arg)


@dataclass(frozen=True)
class _Parsy(ParamType[_Value]):
    """
    Wraps a parser from the parsy library
    """

    parser: parsy.Parser

    def parse(self, arg: str) -> Res[_Value]:
        res = (self.parser << parsy.eof)(arg, 0)  # Inspired by Parser.parse
        if res.status:
            return cast(_Value, res.value)
        else:
            if res.furthest is not None:
                return Err.make(
                    f"Parse error '{res.expected}' in '{arg}' at position '{res.furthest}'"
                )
            else:
                return Err.make(f"Parse error '{res.expected}' in '{arg}'")


@dataclass(frozen=True)
class _EmptyMeansNone(ParamType[Optional[_Item]]):
    """
    Wraps an existing parameter type so that "empty means none"
    """

    wrapped: ParamType[_Item]  #: Wrapped ParamType called if value is not empty
    strip: bool  #:  Whether to strip whitespace before testing for empty

    def parse(self, value: str) -> Res[Optional[_Item]]:
        if self.strip:
            value = value.strip()
        if not value:
            return None
        else:
            return self.wrapped.parse(value)


@dataclass(frozen=True)
class _Mapped(ParamType[_ReturnType], Generic[_Parameter, _ReturnType]):
    """
    Wraps an existing parser and applies a function to its successful result
    """

    wrapped: ParamType[_Parameter]  #: Wrapped parser
    f: Optional[Callable[[_Parameter], _ReturnType]]  #: Mapping function, made optional as a hack

    def parse(self, arg: str) -> Res[_ReturnType]:
        assert self.f is not None
        res: Res[_Parameter] = self.wrapped.parse(arg)
        if isinstance(res, Err):
            return res
        return self.f(res)


@dataclass(frozen=True)
class _SeparatedBy(ParamType[Sequence[_Item]]):
    """
    Parses values separated by a given separator
    """

    item: ParamType[_Item]  #: ParamType of individual items
    sep: str  #: Item separator
    strip: bool  #: Whether to strip whitespace around separated strings
    remove_empty: bool  #: Whether to prune empty strings

    def parse(self, arg: str) -> Res[Sequence[_Item]]:
        items: Iterable[str] = arg.split(self.sep)
        if self.strip:
            items = map(lambda s: s.strip(), items)
        if self.remove_empty:
            items = filter(None, items)
        res: Sequence[Res[_Item]] = [self.item.parse(s) for s in items]

        return collect_seq(res)


@dataclass  # TODO: (frozen=True) when mypy sorts out dataclasses with Callable fields
class _Validated(ParamType[_Value]):
    """
    Parses a value and validates it
    """

    wrapped: ParamType[_Value]
    predicate: Callable[[_Value], bool]
    msg: Callable[[str, _Value], str]

    def parse(self, arg: str) -> Res[_Value]:
        res = self.wrapped.parse(arg)
        if isinstance(res, Err):
            return res
        p = self.predicate
        if p(res):
            return res
        return Err.make(self.msg(arg, res))


#: Parses a path
path: ParamType[pathlib.Path] = ParamType.from_function_that_raises(lambda s: pathlib.Path(s))

#: Parses an integer
int_: ParamType[int] = ParamType.from_function_that_raises(lambda s: int(s))

#: Parses a word, stripping whitespace on the left and right
word: ParamType[str] = ParamType.from_function_that_raises(lambda s: s.strip())

#: Float parameter type
float_: ParamType[float] = ParamType.from_function_that_raises(lambda s: float(s))
bool_: ParamType[bool] = ParamType.choices(
    {"true": True, "false": False},
    force_case=ForceCase.LOWER,
    aliases={"t": True, "f": False, "1": True, "0": False},
)
