from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from typing_extensions import Annotated

from configpile import Config, Param, Positional, types
from configpile.arg import Derived


@dataclass(frozen=True)
class WithPositional(Config):
    """
    This is a description
    """

    a: Annotated[int, Param.store(types.int_)]  #: Super doc message

    strings: Annotated[
        Sequence[str],
        Param.append1(
            types.word,
            positional=Positional.ONE_OR_MORE,
            long_flag_name=None,
            short_flag_name=None,
        ),
    ]


def test_positional() -> None:
    res = WithPositional.from_command_line_(args=["--a", "2", "beautiful", "life"], env={})
    assert res.a == 2
    assert res.strings == ["beautiful", "life"]


def test_argparse() -> None:
    res = WithPositional.processor_().argument_parser
