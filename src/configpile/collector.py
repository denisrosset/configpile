from __future__ import annotations

import abc
from dataclasses import dataclass
from enum import Enum
from operator import truediv
from typing import TYPE_CHECKING, Any, Generic, List, Mapping, NoReturn, Sequence, TypeVar

from .errors import GenErr, Result, map_result
from .types import ArgType

T = TypeVar("T")  #: Item type

W = TypeVar("W")  #: Wrapped item type

if TYPE_CHECKING:
    from .sources import Source


@dataclass(frozen=True)
class Instance(Generic[T]):
    value: T
    string: str
    source: Source

    @staticmethod
    def parse(s: str, arg_type: ArgType[T], source: Source) -> Result[Instance[T]]:
        def res_to_instance(v: T) -> Instance[T]:
            return Instance(v, s, source)

        return map_result(res_to_instance, arg_type.parse(s))


class Collector(abc.ABC, Generic[T]):
    """
    Collects argument instances and computes the final value
    """

    @abc.abstractmethod
    def arg_required(self) -> bool:
        """
        Returns whether one instance of the argument needs to be present
        """
        pass

    @abc.abstractmethod
    def collect(self, seq: Sequence[Instance[T]]) -> Result[T]:
        pass

    @abc.abstractmethod
    def argparse_argument_kwargs(self) -> Mapping[str, Any]:
        pass

    @staticmethod
    def keep_last() -> Collector[T]:
        return _KeepLast()

    @staticmethod
    def append() -> Collector[Sequence[W]]:
        return _Append()

    @staticmethod
    def invalid() -> Collector[NoReturn]:
        return _Invalid()


class _KeepLast(Collector[T]):
    def arg_required(self) -> bool:
        return True

    def collect(self, seq: Sequence[Instance[T]]) -> Result[T]:
        if not seq:  # no instances provided
            return GenErr("Argument is required")
        else:  # instances are provided
            return seq[-1].value

    def argparse_argument_kwargs(self) -> Mapping[str, Any]:
        return {"action": "store"}


class _Append(Collector[Sequence[W]]):
    def arg_required(self) -> bool:
        return False

    def collect(self, seq: Sequence[Instance[Sequence[W]]]) -> Result[Sequence[W]]:
        res: List[W] = []
        for i in seq:
            res.extend(i.value)
        return res

    def argparse_argument_kwargs(self) -> Mapping[str, Any]:
        return {"action": "append"}


class _Invalid(Collector[Any]):
    def arg_required(self) -> bool:
        raise NotImplementedError

    def collect(self, seq: Sequence[Instance[T]]) -> Result[T]:
        return GenErr("Invalid collector")

    def argparse_argument_kwargs(self) -> Mapping[str, Any]:
        raise NotImplementedError(
            "This should have be replaced by a valid collector during construction"
        )
