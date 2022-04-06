# pylint: disable=missing-class-docstring,missing-function-docstring,missing-module-docstring
from __future__ import annotations

from configpile import Err, parsers


def test_integer() -> None:
    assert parsers.int_parser.parse("345") == 345
    assert isinstance(parsers.int_parser.parse("qwe"), Err)


def test_separated_by() -> None:
    assert parsers.int_parser.separated_by(",").parse("3,4,56") == [3, 4, 56]


def test_word() -> None:
    assert parsers.stripped_str_parser.parse(" test  ") == "test"
