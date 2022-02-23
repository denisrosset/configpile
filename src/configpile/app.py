from __future__ import annotations

import argparse
import os
import shutil
import sys
import textwrap
from cmath import exp
from collections import OrderedDict
from configparser import ConfigParser
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    FrozenSet,
    Generic,
    Iterable,
    List,
    Mapping,
    Optional,
)
from typing import OrderedDict as OrderedDictT
from typing import Sequence, Tuple, Type, TypeVar

import class_doc

from . import sources, types
from .arg import Arg, BaseArg, Cmd
from .config import Config
from .errors import Err
from .util import dict_from_multiple_keys, filter_ordered_dict_by_value_type

A = TypeVar("A", bound="App")
T = TypeVar("T", covariant=True)


@dataclass(frozen=True)
class Args:

    #: All flags and arguments present in the app
    #:
    #: Those are indexed by the field name
    all: Mapping[str, BaseArg]

    #: All arguments present in the app, for which a value is recovered
    #:
    #: Those are indexed
    fields: Mapping[str, Arg]  # type: ignore[type-arg]

    #: All command line flags that expand into a (key, value) pair of strings
    #:
    #:
    cl_commands: Mapping[str, Cmd]
    #: All command line arguments that are followed by a value
    cl_flag_value: Mapping[str, Arg]  # type: ignore[type-arg]
    #: The positional arguments
    cl_positional: Optional[Arg]  # type: ignore[type-arg]

    #: Map of all config file keys
    cf_keys: Mapping[str, Arg]  # type: ignore[type-arg]

    #: Map of all supported env. variables
    env_vars: Mapping[str, Arg]  # type: ignore[type-arg]

    @staticmethod
    def populated_base_args(cls: Type[A]) -> OrderedDictT[str, BaseArg]:
        """
        Returns an ordered dictionary of configuration arguments

        In the returned dictionary, the :class:`.Arg` instances are updated with their
        field name and help string.

        Args:
            cls: App class type

        Returns:
            Argument dictionary
        """
        docs: Mapping[str, Sequence[str]] = class_doc.extract_docs_from_cls_obj(cls)

        def get_help(name: str) -> str:
            seq = docs.get(name, [])
            return textwrap.dedent("\n".join(seq))

        elements: List[Tuple[str, BaseArg]] = [
            (
                name,
                arg.updated(name=name, help=get_help(name), env_prefix=cls.env_prefix_),
            )
            for parent_including_itself in cls.__mro__
            for (name, arg) in parent_including_itself.__dict__.items()
            if isinstance(arg, BaseArg) and not name.endswith("_")
        ]
        return OrderedDict(elements)

    @staticmethod
    def from_app_class(cls: Type[A]) -> Args:
        """
        Returns a :class:`.Args` instance populated with updated arguments

        Args:
            cls: The :class:`.App` subclass to investigate

        Returns:
            An object holding the arguments/flags sorted by type
        """
        all: OrderedDictT[str, BaseArg] = Args.populated_base_args(cls)
        fields: OrderedDictT[str, Arg] = filter_ordered_dict_by_value_type(Arg, all)  # type: ignore[type-arg]

        cl_all: Mapping[str, BaseArg] = dict_from_multiple_keys(
            [(arg.all_flags(), arg) for arg in all.values()]
        )
        cl_commands: Mapping[str, Cmd] = {k: v for (k, v) in cl_all.items() if isinstance(v, Cmd)}
        cl_flag_args: Mapping[str, Arg] = {k: v for (k, v) in cl_all.items() if isinstance(v, Arg)}  # type: ignore[type-arg]
        cl_pos_args: Sequence[Arg] = [a for a in fields.values() if a.positional.is_positional()]  # type: ignore[type-arg]
        if len(cl_pos_args) == 0:
            cl_positional = None
        elif len(cl_pos_args) == 1:
            cl_positional = cl_pos_args[0]
        else:
            raise ValueError("At most one positional argument can be given")
        cf_keys: Mapping[str, Arg] = dict_from_multiple_keys(  # type: ignore[type-arg]
            [(arg.all_config_key_names(), arg) for arg in fields.values()]
        )
        env_vars: Mapping[str, Arg] = dict_from_multiple_keys(  # type: ignore[type-arg]
            [(arg.all_env_var_names(), arg) for arg in fields.values()]
        )
        assert not any(
            map(lambda a: a.positional.should_be_last(), cl_pos_args[:-1])
        ), "Only the last positional argument may take a variable number of values"
        return Args(
            all=all,
            fields=fields,
            cl_commands=cl_commands,
            cl_flag_value=cl_flag_args,
            cl_positional=cl_positional,
            cf_keys=cf_keys,
            env_vars=env_vars,
        )


class App:
    """
    A base class for the configuration of Python scripts
    """

    #: Configuration file paths
    #:
    #: The paths are absolute or relative to the current working directory, and
    #: point to existing INI files containing configuration settings
    ini_files: Arg[Sequence[Path]] = Arg.append(types.path.separated_by(","))

    #: Names of sections to parse in configuration files, with unknown keys ignored
    ini_relaxed_sections_: Sequence[str] = ["Common", "COMMON", "common"]

    #: Names of additional sections to parse in configuration files, unknown keys error
    ini_strict_sections_: Sequence[str] = []

    @classmethod
    def ini_sections_(cls) -> Sequence[sources.IniSection]:
        """
        Returns a sequence of INI file sections to parse

        By default, this parses first the relaxed sections and then the strict ones.

        This method can be overridden.
        """
        relaxed = [sources.IniSection(name, False) for name in cls.ini_relaxed_sections_]
        strict = [sources.IniSection(name, True) for name in cls.ini_strict_sections_]
        return relaxed + strict

    prog_: Optional[str] = None  #: Program name
    description_: Optional[str] = None  #: Text to display before the argument help
    env_prefix_: Optional[str] = None  #: Uppercase prefix of environment variables

    args_: Args  #: Arguments

    @classmethod
    def app_(cls: Type[A]) -> A:
        """
        Creates an instance with updated fields

        This class method should be called on subclasses of :class:`.App`.

        Returns:
            An instance of App
        """
        res = cls()
        assert (
            not cls.ini_files.positional.is_positional()
        ), "Configuration files cannot be given as positional arguments"
        if res.prog_ is None:
            res.prog_ = sys.argv[0]
        if res.description_ is None:
            res.description_ = cls.__doc__
        res.args_ = Args.from_app_class(cls)
        for name, arg in res.args_.all.items():
            res.__setattr__(name, arg)
        return res

    def parse_(
        self,
        cwd: Path = Path.cwd(),
        args: Sequence[str] = sys.argv[1:],
        env: Mapping[str, str] = os.environ,
    ) -> Config:
        res = Config.make(self, cwd, args, env)
        if isinstance(res, Err):
            try:
                from rich.console import Console
                from rich.markdown import Markdown

                console = Console()
                md = Markdown("\n".join(res.markdown()))
                console.print(md)
            except:
                sz = shutil.get_terminal_size()
                t = res.markdown()
                print(textwrap.fill("\n".join(t), width=sz.columns))
            self.argument_parser_().print_help()
            sys.exit(1)
        return res

    def argument_parser_(self) -> argparse.ArgumentParser:
        """
        Returns an :class:`argparse.ArgumentParser` for documentation purposes
        """
        p = argparse.ArgumentParser(prog=self.prog_, description=self.description_)
        for arg in self.args_.cl_flag_value.values():
            p.add_argument(
                *arg.all_flags(),
                **arg.argparse_argument_kwargs(),
            )
        return p
