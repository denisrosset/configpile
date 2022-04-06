# pylint: disable=missing-class-docstring,missing-function-docstring,missing-module-docstring
import pytest

from configpile import Err
from configpile.userr import wrap


def test_wrap_exceptions() -> None:
    @wrap(NotImplementedError)
    def test(i: int) -> int:
        if i == 1:
            raise NotImplementedError
        elif i == 2:
            raise ValueError
        else:
            return i

    with pytest.raises(ValueError):
        test(2)

    assert isinstance(test(1), Err)
    assert not isinstance(test(0), Err)


def test_err_check() -> None:
    assert Err.check(False, "This failed") is not None
    assert Err.check(True, "This cannot fail") is None
