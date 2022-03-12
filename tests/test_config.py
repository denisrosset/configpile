from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import ClassVar, Optional, Sequence

import pytest
from typing_extensions import Annotated

from configpile import types
from configpile.arg import Param
from configpile.config import Config
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

    a: Annotated[int, Param.store(types.int_)]  #: Super doc message


def test_construct() -> None:
    res = MyApp.parse_command_line_(args=[], env={})


def test_cmd() -> None:
    res = MyApp.parse_command_line_(args=["-h"], env={})
    assert res == SpecialAction.HELP


@dataclass(frozen=True)
class A(Config):
    config: Annotated[Sequence[Path], Param.config()]
    a: Annotated[int, Param.store(types.int_, default_value="2")]


@dataclass(frozen=True)
class B(A):
    ini_strict_sections_ = ["section"]
    b: Annotated[int, Param.store(types.int_, short_flag_name="-b")]


def test_default_values() -> None:
    res = B.parse_command_line_(args=["-b", "3"], env={})
    assert isinstance(res, B)
    assert res.a == 2


def test_config_files() -> None:
    dir = Path.cwd() / "tests"  # configpile root directory
    res = B.parse_command_line_(cwd=dir, args=["--config", "test.ini"], env={})
    assert isinstance(res, B)
    assert res.a == 4
    assert res.b == 5
