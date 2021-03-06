# pylint: disable=missing-class-docstring,missing-function-docstring,missing-module-docstring
from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

from typing_extensions import Annotated

from configpile import Config, Expander, Param, parsers


@dataclass(frozen=True)
class A(Config):
    a: Annotated[int, Param.store(parsers.int_parser, default_value="2")]
    set_a_to_zero: ClassVar[Expander] = Expander.make("--a", "0")


def test_expander() -> None:
    res = A.from_command_line_(args=["--set-a-to-zero"], env={})
    assert isinstance(res, A)
    assert res.a == 0
