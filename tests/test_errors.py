import pytest

from configpile.errors import Err, is_err, is_value, wrap_exceptions


def test_wrap_exceptions() -> None:
    def fails() -> int:
        raise NotImplementedError

    def works() -> int:
        return 0

    with pytest.raises(NotImplementedError):
        res = wrap_exceptions(fails, ValueError)

    assert is_err(wrap_exceptions(fails))
    assert is_err(wrap_exceptions(fails, ValueError, NotImplementedError))
    assert is_err(wrap_exceptions(fails, NotImplementedError))
    assert is_value(wrap_exceptions(works))
