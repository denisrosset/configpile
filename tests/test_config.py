# pylint: disable=missing-class-docstring,missing-function-docstring,missing-module-docstring
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from typing_extensions import Annotated

from configpile import Config, Param, parsers
from configpile.processor import SpecialAction


@dataclass(frozen=True)
class MyApp(Config):
    """
    This is a description
    """

    #: Configuration file paths
    #:
    #: The paths are absolute or relative to the current working directory, and
    #: point to existing INI files containing configuration settings
    config: Annotated[Sequence[Path], Param.config()]

    a: Annotated[int, Param.store(parsers.int_parser)]  #: Super doc message


def test_construct() -> None:
    MyApp.parse_command_line_(args=[], env={})


def test_cmd() -> None:
    res = MyApp.parse_command_line_(args=["-h"], env={})
    assert res == SpecialAction.HELP


@dataclass(frozen=True)
class ConfigA(Config):
    config: Annotated[Sequence[Path], Param.config()]
    a: Annotated[int, Param.store(parsers.int_parser, default_value="2")]


@dataclass(frozen=True)
class ConfigB(ConfigA):
    ini_strict_sections_ = ["section"]
    b: Annotated[int, Param.store(parsers.int_parser, short_flag_name="-b")]


def test_default_values() -> None:
    res = ConfigB.parse_command_line_(args=["-b", "3"], env={})
    assert isinstance(res, ConfigB)
    assert res.a == 2


def test_config_files() -> None:
    directory = Path.cwd() / "tests"  # configpile root directory
    res = ConfigB.parse_command_line_(
        cwd=directory, args=["--config", "example_config.ini"], env={}
    )
    assert isinstance(res, ConfigB)
    assert res.a == 4
    assert res.b == 5
