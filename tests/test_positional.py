from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from typing_extensions import Annotated

from configpile import Config, Param, Positional, types


@dataclass(frozen=True)
class WithPositional(Config):
    """
    This is a description
    """

    a: Annotated[int, Param.store(types.int_)]  #: Super doc message

    strs: Annotated[
        Sequence[str],
        Param.append(types.word.as_sequence_of_one(), positional=Positional.ONE_OR_MORE),
    ]


def test_positional() -> None:
    res = WithPositional.parse_command_line_(args=["--a", "2", "beautiful", "life"], env={})
    assert res.a == 2
    assert res.strs == ["beautiful", "life"]
