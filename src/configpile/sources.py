from __future__ import annotations

import abc
import configparser
from abc import abstractmethod
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Dict, Generic, Iterable, List, Literal, Mapping, Sequence, Tuple, TypeVar

from configpile.collector import Instance

from .arg import Arg, Positional
from .errors import ArgErr, Err, GenErr, ManyErr, Result, collect_seq

T = TypeVar("T")  #: Item type


class Source(abc.ABC):
    """
    Describes a source of argument name/value pairs
    """

    @abstractmethod
    def get_strings(self, arg: Arg[T]) -> Result[Sequence[str]]:
        pass

    def __getitem__(self, arg: Arg[T]) -> Result[Sequence[Instance[T]]]:
        res = self.get_strings(arg)
        if isinstance(res, Err):
            return res
        else:
            return collect_seq([Instance.parse(s, arg.arg_type, source=self) for s in res])

    @staticmethod
    def collect_instances(sources: Sequence[Source], arg: Arg[T]) -> Result[Sequence[Instance[T]]]:
        """
        Parses all instances of an argument in a sequence of sources

        Args:
            sources: Sequence of sources to get the strings from
            arg: Argument to parse

        Returns:
            A sequence of instances or an error
        """
        ok: List[Instance[T]] = []
        errs: List[Err] = []
        for source in sources:
            res = source[arg]
            if isinstance(res, ManyErr):
                errs.extend(res.errs)
            elif isinstance(res, Err):
                errs.append(res)
            else:
                ok.extend(res)
        if errs:
            return ManyErr(errs)
        else:
            return ok

    @staticmethod
    def collect(sources: Sequence[Source], arg: Arg[T]) -> Result[T]:
        """
        Parses and collect the value of an argument from a sequence of sources

        Args:
            sources: Sequence of sources to get the strings from
            arg: Argument to parse and collect

        Returns:
            The collected value or an error
        """
        instances = Source.collect_instances(sources, arg)
        if isinstance(instances, Err):
            return instances
        return arg.collector.collect(instances)


@dataclass(frozen=True)
class EnvironmentVariables(Source):
    env: Mapping[str, str]

    def get_strings(self, arg: Arg[T]) -> Result[Sequence[str]]:
        if isinstance(arg.env_var_name, str) and arg.env_var_name in self.env:
            return [self.env[arg.env_var_name]]
        else:
            return []


@dataclass(frozen=True)
class IniSection:
    name: str  #: Section name
    strict: bool  #: Whether all the keys must correspond to parsed arguments


@dataclass(frozen=True)
class IniSectionSource(Source):
    filename: Path
    section_name: str
    elements: Mapping[str, str]

    def get_strings(self, arg: Arg[T]) -> Result[Sequence[str]]:
        if isinstance(arg.config_key_name, str) and arg.config_key_name in self.elements:
            return [self.elements[arg.config_key_name]]
        else:
            return []

    @staticmethod
    def from_file(
        ini_file: Path, sections: Sequence[IniSection], valid_keys: Iterable[str]
    ) -> Result[Sequence[IniSectionSource]]:
        config = configparser.ConfigParser()
        try:
            with open(ini_file, "r") as f:
                config.read_file(f)
        except FileNotFoundError as e:
            return GenErr(f"File {ini_file} not found")
        res: List[IniSectionSource] = []
        for s in sections:  # loop through sections, later section values override earlier ones
            elements: Dict[str, str] = {}
            if s.name in config.sections():
                data: configparser.SectionProxy = config[s.name]
                if s.strict:
                    # we're strict, so we list all keys present in the section and match them
                    for k in data.keys():
                        if k not in valid_keys:
                            return GenErr(f"Invalid key {k} in section {s.name} of {ini_file}")
                        elements[k] = data[k]  # insert value
                else:
                    # we're not strict, so we only extract the valid keys
                    for k in valid_keys:
                        if k in data:
                            elements[k] = data[k]
            if elements:
                res.append(IniSectionSource(ini_file, s.name, elements))
        return res


@dataclass(frozen=True)
class CommandLine(Source):
    pairs: Sequence[Tuple[str, str]]  #: Key/value argument pairs
    positional: Sequence[str]  #: Remaining positional values

    def get_strings(self, arg: Arg[T]) -> Result[Sequence[str]]:
        from_pairs: List[str] = [value for (key, value) in self.pairs if key in arg.all_flags()]
        from_pos: List[str] = []
        if arg.positional != Positional.FORBIDDEN:
            if arg.positional == Positional.ONCE and len(self.positional) != 1:
                return GenErr("One positional argument must be provided")
            if arg.positional == Positional.ONE_OR_MORE and len(self.positional) == 0:
                return GenErr("At least one positional argument must be provided")
            from_pos = list(self.positional)
        return [*from_pos, *from_pairs]

    @staticmethod
    def make(
        args: Sequence[str],
        expanding_flags: Mapping[str, Tuple[str, str]],
        flags_followed_by_value: Iterable[str],
    ) -> Result[CommandLine]:
        """
        Returns processed command line arguments

        Args:
            args: Raw command line arguments
            expanding_flags: Flags that expand to a key/value pair
            flags_followed_by_value: Flags that are followed by a value

        Returns:
            The processed command line
        """
        pairs: List[Tuple[str, str]] = []
        rest: List[str] = []
        i = 0
        while i < len(args):
            k = args[i]
            if k in expanding_flags:
                kv = expanding_flags[k]
                pairs.append(kv)
            elif k in flags_followed_by_value:
                i += 1
                if i >= len(args):
                    return GenErr("Unexpected end of command line")
                else:
                    v = args[i]
                    pairs.append((k, v))
            else:
                rest.append(k)
            i += 1
        return CommandLine(pairs=pairs, positional=rest)
