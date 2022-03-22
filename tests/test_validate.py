from __future__ import annotations

from ast import With
from dataclasses import dataclass
from typing import Optional, Sequence

from typing_extensions import Annotated

from configpile import Config, Err, Param, Positional, Validator, config, types


@dataclass(frozen=True)
class WithParamValidation(Config):
    """
    This is a description
    """

    a: Annotated[
        int,
        Param.store(
            types.int_, validator=lambda v: Err.make("Must be non-negative") if v < 0 else None
        ),
    ]  #: Super doc message


@dataclass(frozen=True)
class WithClassValidation(Config):
    """
    This is a description
    """

    a: Annotated[int, Param.store(types.int_)]  #: Super doc message

    def validate_a(self) -> Validator:
        if self.a < 0:
            return Err.make("Argument a cannot be negative")
        return None


def test_class_validation() -> None:
    assert len(WithClassValidation.validators_()) == 1
    res = WithClassValidation.parse_command_line_(args=["--a", "2"], env={})
    assert not isinstance(res, Err)
    res1 = WithClassValidation.parse_command_line_(args=["--a", "-2"], env={})
    assert isinstance(res1, Err)


def test_param_validation() -> None:
    res = WithParamValidation.parse_command_line_(args=["--a", "2"], env={})
    assert not isinstance(res, Err)
    res1 = WithParamValidation.parse_command_line_(args=["--a", "-2"], env={})
    assert isinstance(res1, Err)
