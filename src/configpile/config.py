"""
Configuration definition

This module defines the :class:`.Config` base class, from which all configuration derive.

.. rubric:: Types

This module uses the following types.

.. py:data:: _Config

    Configuration dataclass type being constructed

"""

from __future__ import annotations

import argparse
import inspect
import os
import sys
from abc import ABC
from dataclasses import dataclass
from pathlib import Path
from typing import (
    Callable,
    ClassVar,
    List,
    Mapping,
    Optional,
    Sequence,
    Type,
    TypeVar,
    Union,
    get_args,
)

from typing_extensions import Annotated, get_origin, get_type_hints

from . import types
from .arg import Param
from .processor import Processor, SpecialAction
from .userr import Err, Res

_Config = TypeVar("_Config", bound="Config")


@dataclass(frozen=True)
class IniSection:
    """
    Describes a section of an INI file to include in the current configuration
    """

    name: str  #: Section name
    strict: bool  #: Whether all the keys must correspond to parsed arguments


@dataclass(frozen=True)
class Config(ABC):
    """
    Base class for dataclasses holding configuration data

    Example:
        .. code-block:: python

            @dataclass(frozen=True)
            class Adder(Config):
                x: Annotated[int, Param.store(types.int_)]
                y: Annotated[int, Param.store(types.int_, default_value="0")]

            res = Adder.from_command_line_(args=['x','2', 'y','3'], env={})
            res.x + res.y
    """

    #: Names of sections to parse in configuration files, with unknown keys ignored
    ini_relaxed_sections_: ClassVar[Sequence[str]] = ["Common", "COMMON", "common"]

    #: Names of additional sections to parse in configuration files, unknown keys error
    ini_strict_sections_: ClassVar[Sequence[str]] = []

    @classmethod
    def ini_sections_(cls) -> Sequence[IniSection]:
        """
        Returns a sequence of INI file sections to parse

        By default, this parses first the relaxed sections and then the strict ones.

        This method can be overridden.
        """
        relaxed = [IniSection(name, False) for name in cls.ini_relaxed_sections_]
        strict = [IniSection(name, True) for name in cls.ini_strict_sections_]
        return relaxed + strict

    prog_: ClassVar[Optional[str]] = None  #: Program name
    description_: ClassVar[Optional[str]] = None  #: Text to display before the argument help
    env_prefix_: ClassVar[Optional[str]] = None  #: Prefix for environment variables

    @classmethod
    def validators_(cls: Type[_Config]) -> Sequence[Callable[[_Config], Optional[Err]]]:
        """
        Returns all validators present in the given subclass of this class

        Validators are methods that take no arguments (except self) and return an optional error.
        Their name starts with ``validate_`` and ends with an underscore.

        Returns:
            A sequence of all validators
        """
        res: List[Callable[[_Config], Optional[Err]]] = []
        for name, meth in inspect.getmembers(cls, inspect.isroutine):
            if name.startswith("validate_") and name.endswith("_"):
                res.append(getattr(cls, name))
        return res

    @classmethod
    def version_(cls) -> Optional[str]:
        """
        Returns the version number of this script

        Designed to be overridden by a subclass

        Returns:
            Version
        """
        return None

    @classmethod
    def processor_(cls: Type[_Config]) -> Processor[_Config]:
        """
        Returns a processor for this configuration
        """
        return Processor.make(cls)

    @classmethod
    def parse_command_line_(
        cls: Type[_Config],
        cwd: Optional[Path] = None,
        args: Optional[Sequence[str]] = None,
        env: Optional[Mapping[str, str]] = None,
    ) -> Res[Union[_Config, SpecialAction]]:
        """
        Parses multiple information sources, returns a configuration, a command or an error

        Default values are taken from the current working directory, the script command line
        arguments, and the current environment variables.

        Args:
            cwd: Directory used as a base for the configuration file relative paths
            args: Command line arguments
            env: Environment variables

        Returns:
            A parsed configuration or an error
        """
        if cwd is None:
            cwd = Path.cwd()
        if args is None:
            args = sys.argv[1:]
        if env is None:
            env = os.environ
        processor = cls.processor_()
        return processor.process(cwd, args, env)

    @classmethod
    def from_command_line_(
        cls: Type[_Config],
        cwd: Optional[Path] = None,
        args: Optional[Sequence[str]] = None,
        env: Optional[Mapping[str, str]] = None,
    ) -> _Config:
        """
        Parses multiple information sources into a configuration and display help on error

        Default values are taken from the current working directory, the script command line
        arguments, and the current environment variables.

        Args:
            cwd: Directory used as a base for the configuration file relative paths
            args: Command line arguments
            env: Environment variables

        Returns:
            A parsed configuration
        """
        if cwd is None:
            cwd = Path.cwd()
        if args is None:
            args = sys.argv[1:]
        if env is None:
            env = os.environ
        res = cls.parse_command_line_(cwd, args, env)

        if isinstance(res, cls):
            return res

        if isinstance(res, Err):
            print("Encountered errors:")
            res.pretty_print()
            print(" ")
            cls.get_argument_parser_().print_help()
            sys.exit(1)

        assert isinstance(res, SpecialAction)
        if res == SpecialAction.HELP:
            cls.processor_().argument_parser.print_help()
            sys.exit(0)
        elif res == SpecialAction.VERSION:
            v = cls.version_()
            if v is None:
                v = "Unknown version number"
            print(v)
            sys.exit(0)
        else:
            raise NotImplementedError(f"Unknown special action {res}")

    @classmethod
    def get_argument_parser_(cls: Type[_Config]) -> argparse.ArgumentParser:
        """
        Returns an :class:`argparse.ArgumentParser` for documentation purposes
        """
        return cls.processor_().argument_parser
