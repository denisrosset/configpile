"""
This module describes the state of a configuration under processing
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Generic, Iterable, List, Optional, TypeVar

from .arg import Param
from .collector import Collector
from .enums import SpecialAction
from .parsers import Parser
from .userr import Err, Res

_Value = TypeVar("_Value")


@dataclass(frozen=True)
class ComputedValue(Generic[_Value]):
    """Describes a computed value for a parameter"""

    #: Stored computed value
    value: _Value


@dataclass
class ParameterState(Generic[_Value]):
    """
    Describes a parameter in a configuration
    """

    #: Parameter name
    name: str

    #: Value parser
    parser: Parser[_Value]

    #: Value collector
    collector: Collector[_Value]

    #: The computed value if it has been requested in the past
    cached_value: Optional[ComputedValue[_Value]]

    #: List of parsed values
    parsed_values: List[_Value]

    #: List of encountered errors
    #:
    #: Those errors always have a ``("parameter", self.name)`` pair as the first context element
    errors: List[Err]

    def value(self) -> Res[_Value]:
        """
        Returns this parameter value or an error
        """
        err = Err.collect(*self.errors)
        if err is not None:
            return err
        if self.cached_value is not None:
            return self.cached_value.value
        res = self.collector.collect(self.parsed_values)
        if isinstance(res, Err):
            return res.in_context(parameter=self.name)
        self.cached_value = ComputedValue(res)
        return res

    @staticmethod
    def make(
        name: str,
        parser: Parser[_Value],
        collector: Collector[_Value],
        default_value: Optional[str],
    ) -> ParameterState[_Value]:
        """
        Creates and returns a new parameter state

        Args:
            parser: Parameter parser
            collector: Parameter collector
            default_value: Default value, if any

        Raises:
            ValueError: if the given default_value cannot be parsed
        """
        if default_value is not None:
            res = parser.parse(default_value)
            if isinstance(res, Err):
                raise ValueError(f"Invalid default value {default_value} for parameter {name}")
            parsed_values = [res]
        else:
            parsed_values = []
        return ParameterState(
            name=name,
            parser=parser,
            collector=collector,
            cached_value=None,
            parsed_values=parsed_values,
            errors=[],
        )

    def parse_and_append(self, value: str, **context: Any) -> None:
        """
        Parses and add the resulting value (or error) to this state

        Args:
            value (str): Value to parse
            contexts: Contexts (given as key/value pairs) to append to the context list

                      The first context value is always ``("parameter", self.name)``
        """
        if self.cached_value is not None:
            self.errors.append(
                Err.make(
                    "Cannot modify a parameter after its value has been computed",
                    parameter=self.name,
                    **context,
                )
            )
            return
        res = self.parser.parse(value)
        if isinstance(res, Err):
            self.errors.append(res.in_context(parameter=self.name, **context))
            return
        self.parsed_values.append(res)


@dataclass
class State:
    """
    Describes the (mutable) state of a configuration being parsed
    """

    #: Describes the state of each parameter in a configuration
    parameters: Dict[str, ParameterState[Any]]

    #: Errors
    errors: List[Err]

    #: Contains a list of configuration files to process
    config_files_to_process: List[Path]

    #: Contains a special action if flag was encountered
    special_action: Optional[SpecialAction]

    @staticmethod
    def make(params: Iterable[Param[Any]]) -> State:
        """
        Creates the initial state, populated with the default values when present

        Args:
            params: Sequence of parameters

        Raises:
            ValueError: If a default value cannot be parsed correctly

        Returns:
            The initial mutable state
        """
        parameters: Dict[str, ParameterState[Any]] = {}

        for p in params:
            assert p.name is not None, "Arguments have names after initialization"
            parameters[p.name] = ParameterState.make(
                p.name, p.parser, p.collector, p.default_value
            )
        return State(parameters, [], config_files_to_process=[], special_action=None)
