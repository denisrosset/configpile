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

from .errors import Err, Result
from .processor import Processor, SpecialAction

C = TypeVar("C", bound="Config")


@dataclass(frozen=True)
class IniSection:
    """
    Describes a section of an INI file to include in the current configuration
    """

    name: str  #: Section name
    strict: bool  #: Whether all the keys must correspond to parsed arguments


class _ValidatorToken:
    pass


Validator = Annotated[Optional[Err], _ValidatorToken]


@dataclass(frozen=True)
class Config(ABC):
    """
    Base class for dataclasses holding configuration data
    """

    # #: Display usage information and exits
    # help: ClassVar[HelpCmd] = HelpCmd(short_flag_name="-h", long_flag_name="--help")

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
    def validators_(cls: Type[C]) -> Sequence[Callable[[C], Optional[Err]]]:
        """
        Returns all validators present in the given subclass of this class

        Validators are methods that take no arguments (except self) and return an optional error.
        They are annotated with the _ValidatorToken type, which has the alias Validator.

        Returns:
            A sequence of all validators
        """
        res: List[Callable[[C], Optional[Err]]] = []
        for name, meth in inspect.getmembers(cls, inspect.isroutine):
            m = getattr(cls, name)
            th = get_type_hints(m, include_extras=True)
            rt = th.get("return")
            if rt is not None and get_origin(rt) is Annotated and _ValidatorToken in get_args(rt):
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
    def processor_(cls: Type[C]) -> Processor[C]:
        """
        Returns a processor for this configuration
        """
        return Processor.make(cls)

    @classmethod
    def parse_command_line_(
        cls: Type[C],
        cwd: Path = Path.cwd(),
        args: Sequence[str] = sys.argv[1:],
        env: Mapping[str, str] = os.environ,
    ) -> Result[Union[C, SpecialAction]]:
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
        processor = cls.processor_()
        return processor.process(cwd, args, env)

    @classmethod
    def from_command_line_(
        cls: Type[C],
        cwd: Path = Path.cwd(),
        args: Sequence[str] = sys.argv[1:],
        env: Mapping[str, str] = os.environ,
    ) -> C:
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
        res = cls.parse_command_line_(cwd, args, env)

        if isinstance(res, cls):
            return res

        if isinstance(res, Err):
            res.pretty_print()
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
    def get_argument_parser_(cls: Type[C]) -> argparse.ArgumentParser:
        """
        Returns an :class:`argparse.ArgumentParser` for documentation purposes
        """
        return cls.processor_().argument_parser
