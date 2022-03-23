from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

from typing_extensions import Annotated

from configpile import Config, Param, types
from configpile.arg import Expander


@dataclass(frozen=True)
class A(Config):
    a: Annotated[int, Param.store(types.int_, default_value="2")]
    set_a_to_zero: ClassVar[Expander] = Expander.make("--a", "0")


def test_expander() -> None:
    res = A.from_command_line_(args=["--set-a-to-zero"], env={})
    assert isinstance(res, A)
    assert res.a == 0
