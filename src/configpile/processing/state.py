"""
Configuration state during processing
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from ..arg import Param
from ..misc import Auto, SpecialAction
from ..userr import Err


@dataclass
class State:
    """Describes the (mutable) state of a configuration being parsed"""

    #: Contains the sequence of values for each parameter
    instances: Dict[str, List[Any]]

    #: Contains a list of configuration files to process
    config_files_to_process: List[Path]

    #: Contains a special action if flag was encountered
    special_action: Optional[SpecialAction]

    #: Positional values
    positionals: List[str]

    def append(self, key: str, value: Any) -> None:
        """
        Appends a value to a parameter

        No type checking is performed, be careful.

        Args:
            key: Parameter name
            value: Value to append
        """
        assert key in self.instances, f"{key} is not a Param name"
        self.instances[key] = [*self.instances[key], value]

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
        instances: Dict[str, List[Any]] = {}

        for p in params:
            assert not isinstance(p.parser, Auto), "Parsers are not Auto after initialization"
            assert not isinstance(p.name, Auto), "Arguments have names after initialization"
            if p.default_value is not None:
                res = p.parser.parse(p.default_value)
                if isinstance(res, Err):
                    raise ValueError(f"Invalid default {p.default_value} for parameter {p.name}")
                instances[p.name] = [res]
            else:
                instances[p.name] = []

        return State(
            instances,
            config_files_to_process=[],
            special_action=None,
            positionals=[],
        )
