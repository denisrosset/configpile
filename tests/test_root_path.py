# pylint: disable=missing-class-docstring,missing-function-docstring,missing-module-docstring
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from typing_extensions import Annotated

from configpile import Config, Param, parsers


@dataclass(frozen=True)
class ConfigA(Config):
    root: Annotated[Path, Param.root_path(env_var_name="ROOT")]
    config: Annotated[Sequence[Path], Param.config()]
    a: Annotated[int, Param.store(parsers.int_parser, default_value="2")]


def test_config_files() -> None:
    directory = Path.cwd() / "tests"  # configpile root directory
    res = ConfigA.parse_command_line_(
        cwd=directory, args=["--config", "b/c.ini"], env={"ROOT": str(Path.cwd() / "tests" / "a")}
    )
    print(res)
    assert isinstance(res, ConfigA)
    assert res.a == 4
