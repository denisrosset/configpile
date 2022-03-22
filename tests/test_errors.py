import pytest

from configpile.userr import Err, wrap


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
        res = test(2)

    assert isinstance(test(1), Err)
    assert not isinstance(test(0), Err)


def test_err_check() -> None:
    assert Err.check(False, "This failed") is not None
    assert Err.check(True, "This cannot fail") is None
