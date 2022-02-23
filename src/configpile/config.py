from __future__ import annotations

import abc
import argparse
import os
import sys
import textwrap
import typing
from cmath import exp
from collections import OrderedDict, _OrderedDictItemsView
from configparser import ConfigParser
from dataclasses import dataclass
from distutils.cmd import Command
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
from typing import Sequence, Tuple, Type, TypeVar, Union, cast

import class_doc

from . import sources, types
from .arg import Arg, BaseArg, Cmd, Positional
from .collector import Instance
from .errors import ArgErr, Err, ManyErr, Result, collect, map_result
from .sources import CommandLine, EnvironmentVariables, IniSectionSource, Source
from .util import dict_from_multiple_keys, filter_ordered_dict_by_value_type

if TYPE_CHECKING:
    from .app import App

A = TypeVar("A", bound="App")
T = TypeVar("T", covariant=True)


@dataclass(frozen=True)
class Config:
    values: Mapping[str, Any]

    def __getitem__(self, arg: Arg[T]) -> T:
        assert arg.name is not None
        return cast(T, self.values[arg.name])

    @staticmethod
    def make(
        app: App,
        cwd: Path,
        args: Sequence[str],
        env: Mapping[str, str],
    ) -> Result[Config]:
        return Processor(app, cwd, args, env).process()


@dataclass(frozen=True)
class Processor:
    app: App  #: App describing the configuration arguments
    cwd: Path  #: Path from which relative paths for conf. files are resolved
    args: Sequence[str]  #: Command line arguments as a sequence of strings
    env: Mapping[str, str]  #: Environment variables

    def command_line(self) -> Result[CommandLine]:
        """
        Constructs a command line source

        Returns:
            A source or an error
        """
        exp_flags = {flag: cmd.inserts() for (flag, cmd) in self.app.args_.cl_commands.items()}
        val_flags = frozenset(self.app.args_.cl_flag_value.keys())
        return CommandLine.make(self.args, exp_flags, val_flags)

    def environment_variables(self) -> Result[EnvironmentVariables]:
        """
        Constructs a source from environment variables

        Returns:
            A source or an error
        """
        return EnvironmentVariables(self.env)

    def process(self) -> Result[Config]:
        """
        Process the

        Returns:

        """
        app = self.app
        config_sources: Result[Tuple[CommandLine, EnvironmentVariables]] = collect(
            self.command_line(), self.environment_variables()
        )
        if isinstance(config_sources, Err):
            return config_sources
        cl, env = config_sources
        ini_from_env: Result[Sequence[Instance[Sequence[Path]]]] = env[app.ini_files]
        if isinstance(ini_from_env, Err):
            return ini_from_env
        ini_from_cl: Result[Sequence[Instance[Sequence[Path]]]] = cl[app.ini_files]
        if isinstance(ini_from_cl, Err):
            return ini_from_cl
        sources: List[Source] = [env]
        ini_instances: Sequence[Path] = [
            ins for instances in [*ini_from_env, *ini_from_cl] for ins in instances.value
        ]
        for fn in ini_instances:
            sections_res = IniSectionSource.from_file(
                self.cwd / fn, app.ini_sections_(), app.args_.cf_keys
            )
            if isinstance(sections_res, Err):
                return sections_res
            sources.extend(sections_res)
        sources.append(cl)
        values: List[Tuple[str, Any]] = []
        errs: List[Err] = []
        for name, arg in app.args_.fields.items():
            res = Source.collect(sources, arg)
            if isinstance(res, Err):
                errs.append(ArgErr(arg, res))
            else:
                values.append((name, res))
        if errs:
            return ManyErr(errs)
        else:
            return Config(dict(values))
