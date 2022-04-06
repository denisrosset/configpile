from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from typing_extensions import Annotated

from configpile import Config, Param, parsers


@dataclass(frozen=True)
class Description(Config):
    """
    Configuration for the test suite
    """

    ini_strict_sections_ = ["section"]
    a: Annotated[int, Param.store(parsers.int_parser, default_value="2")]
    b: Annotated[int, Param.store(parsers.int_parser, short_flag_name="-b")]


def test_config_files() -> None:
    directory = Path.cwd() / "tests"  # configpile root directory
    res = Description.parse_ini_file_(directory / "example_config.ini")
    assert isinstance(res, Description)
    assert res.a == 4
    assert res.b == 5
