from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from typing_extensions import Annotated

from configpile import *
from configpile.processor import SpecialAction


@dataclass(frozen=True)
class TestConfig(Config):
    ini_strict_sections_ = ["section"]
    a: Annotated[int, Param.store(parsers.int_parser, default_value="2")]
    b: Annotated[int, Param.store(parsers.int_parser, short_flag_name="-b")]


def test_config_files() -> None:
    dir = Path.cwd() / "tests"  # configpile root directory
    res = TestConfig.parse_ini_file_(dir / "example_config.ini")
    assert isinstance(res, TestConfig)
    assert res.a == 4
    assert res.b == 5
