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
from typing import TYPE_CHECKING, Generic, Optional, Sequence, Tuple, TypeVar

from ..misc import Auto, SpecialAction
from ..userr import Err, in_context

if TYPE_CHECKING:
    from ..arg import Param
    from .state import State

_Value = TypeVar("_Value")


class CLHandler(ABC):
    """
    A handler for command-line arguments
    """

    @abstractmethod
    def handle(self, args: Sequence[str], state: State) -> Tuple[Sequence[str], Optional[Err]]:
        """
        Processes arguments, possibly updating the state or returning errors

        Args:
            args: Command-line arguments not processed yet
            state: (Mutable) state to possibly update

        Returns:
            The updated command-line and an optional error
        """


@dataclass(frozen=True)
class CLSpecialAction(CLHandler):
    """
    A handler that sets the special action
    """

    special_action: SpecialAction  #: Special action to set

    def handle(self, args: Sequence[str], state: State) -> Tuple[Sequence[str], Optional[Err]]:
        if state.special_action is not None:
            before = state.special_action.name
            now = self.special_action.name
            err = Err.make(f"We had already action {before}, conflicts with action {now}")
            return (args, err)
        state.special_action = self.special_action
        return (args, None)


@dataclass(frozen=True)
class CLInserter(CLHandler):
    """Expands into a sequence of args inserted into the command line to be parsed"""

    #: Arguments inserted in the command-line
    inserted_args: Sequence[str]

    def handle(self, args: Sequence[str], state: State) -> Tuple[Sequence[str], Optional[Err]]:
        return ([*self.inserted_args, *args], None)


@dataclass(frozen=True)
class CLParam(CLHandler, Generic[_Value]):
    """
    Parameter handler

    Takes a single string argument from the command line, parses it and pushes into the
    corresponding sequence of instances
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

    def handle(self, args: Sequence[str], state: State) -> Tuple[Sequence[str], Optional[Err]]:
        if args:
            assert not isinstance(self.param.parser, Auto)
            res = self.param.parser.parse(args[0])
            if isinstance(res, Err):
                return (args[1:], res.in_context(param=self.param.name))
            else:
                assert self.param.name is not None, "Names are assigned after initialization"
                err = in_context(self.action(res, state), param=self.param.name)
                assert not isinstance(self.param.name, Auto)
                state.instances[self.param.name].append(res)
                return (args[1:], err)
        else:
            return (
                args,
                Err.make("Expected value, but no argument present", param=self.param.name),
            )


@dataclass(frozen=True)
class CLConfigParam(CLParam[Sequence[Path]]):
    """A configuration file parameter handler

    If paths are successfully parsed, it appends configuration files to be parsed to the current
    state.
    """

    def action(self, value: Sequence[Path], state: State) -> Optional[Err]:
        state.config_files_to_process.extend(value)
        return None


@dataclass(frozen=True)
class CLRestIsPositional(CLHandler):
    """Moves all command-line arguments to the positionals"""

    def handle(self, args: Sequence[str], state: State) -> Tuple[Sequence[str], Optional[Err]]:
        state.positionals.extend(args)
        return ([], None)
