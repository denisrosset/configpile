"""
This module defines the handlers that are used during processing.

.. rubric:: Types

This module uses the following types.

.. py:data:: _Value

    Value being parsed by a :class:`~configpile.parsers.Parser`
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Generic, Optional, Sequence, TypeVar

from ..misc import Auto
from ..userr import Err, in_context

if TYPE_CHECKING:
    from ..arg import Param
    from .state import State

_Value = TypeVar("_Value")


class KVHandler(ABC):
    """
    Handler for key/value pairs found for example in environment variables or INI files

    Note that the key is not stored/processed in this class.
    """

    @abstractmethod
    def handle(self, value: str, state: State) -> Optional[Err]:
        """
        Processes

        Args:
            value: Value to parse and process
            state: State to update

        Returns:
            An error if an error occurred
        """


@dataclass(frozen=True)
class KVParam(KVHandler, Generic[_Value]):
    """
    Handler for the value following a key corresponding to a parameter
    """

    #: Parameter to handle
    param: Param[_Value]

    def action(self, value: _Value, state: State) -> Optional[Err]:
        """
        A method called on the successful parse of a value

        Can be overridden. By default does nothing.

        Args:
            value: Parsed value
            state: State to possibly update

        Returns:
            An optional error
        """
        return None

    def handle(self, value: str, state: State) -> Optional[Err]:
        assert not isinstance(self.param.parser, Auto)
        res = self.param.parser.parse(value)
        if isinstance(res, Err):
            return res
        else:
            assert not isinstance(self.param.name, Auto)
            err = self.action(res, state)
            state.instances[self.param.name] = [*state.instances[self.param.name], res]
            return in_context(err, param=self.param.name)


@dataclass(frozen=True)
class KVConfigParam(KVParam[Sequence[Path]]):
    """
    Handler for the configuration file value following a key corresponding to a parameter
    """

    def action(self, value: Sequence[Path], state: State) -> Optional[Err]:
        state.config_files_to_process.extend(value)
        return None
