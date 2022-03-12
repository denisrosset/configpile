from __future__ import annotations

import abc
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, Any, Generic, List, Mapping, NoReturn, Sequence, Tuple, TypeVar

from .errors import Err, Err1, Result
from .types import ParamType

T = TypeVar("T")  #: Item type

W = TypeVar("W")  #: Wrapped item type


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
    def collect(self, seq: Sequence[T]) -> Result[T]:
        """
        Collects a sequence of values into a result

        Args:
            seq: Sequence of parsed values

        Returns:
            Either the consolidated value or an error
        """
        pass

    @abc.abstractmethod
    def argparse_argument_kwargs(self) -> Mapping[str, Any]:
        """
        Returns the arguments using in documentation (piggy backing on argparse)
        """
        pass

    @staticmethod
    def keep_last() -> Collector[T]:
        """
        Returns a collector that keeps the last value
        """
        return _KeepLast()

    @staticmethod
    def append() -> Collector[Sequence[W]]:
        """
        Returns a collector that appends sequences
        """
        return _Append()

    @staticmethod
    def invalid() -> Collector[NoReturn]:
        """
        Returns an invalid collector that always returns an error
        """
        return _Invalid()


class _KeepLast(Collector[T]):
    def arg_required(self) -> bool:
        return True

    def collect(self, seq: Sequence[T]) -> Result[T]:
        if not seq:  # no instances provided
            return Err.make("Argument is required")
        else:  # instances are provided
            return seq[-1]

    def argparse_argument_kwargs(self) -> Mapping[str, Any]:
        return {"action": "store"}


class _Append(Collector[Sequence[W]]):
    def arg_required(self) -> bool:
        return False

    def collect(self, seq: Sequence[Sequence[W]]) -> Result[Sequence[W]]:
        res: List[W] = []
        for i in seq:
            res.extend(i)
        return res

    def argparse_argument_kwargs(self) -> Mapping[str, Any]:
        return {"action": "append"}


class _Invalid(Collector[Any]):
    def arg_required(self) -> bool:
        raise NotImplementedError

    def collect(self, seq: Sequence[T]) -> Result[T]:
        return Err.make("Invalid collector")

    def argparse_argument_kwargs(self) -> Mapping[str, Any]:
        raise NotImplementedError(
            "This should have be replaced by a valid collector during construction"
        )
