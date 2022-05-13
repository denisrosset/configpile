"""
Calculator tutorial, step 5
"""
from dataclasses import dataclass
from math import prod
from typing import Sequence

from typing_extensions import Annotated

from configpile import Config, Param, Positional, parsers


@dataclass(frozen=True)
class Calc(Config):
    """
    Command-line tool that sums an arbitrary number of floating point values
    """

    #: Values to sum
    values: Annotated[
        Sequence[float],
        Param.append_one(
            parsers.float_parser,
            positional=Positional.ZERO_OR_MORE,
            short_flag_name=None,
            long_flag_name=None,
        ),
    ]

    #: Operation to perform, either addition "+" or multiplication "*"
    operation: Annotated[
        str,
        Param.store(
            parsers.Parser.from_choices(["+", "*"]),
            default_value="+",
        ),
    ]

    #: Number of digits to display
    #:
    #: This number of digits can also be set with the environment variable
    #: ``DIGITS``
    digits: Annotated[
        int,
        Param.store(
            parsers.int_parser.validated(lambda i: i > 0, "Must be a positive integer"),
            default_value="3",
            env_var_name="DIGITS",
        ),
    ]


c = Calc.from_command_line_()
fmt_string = f"%.{c.digits}f"
if c.operation == "+":
    print(fmt_string % sum(c.values))
elif c.operation == "*":
    print(fmt_string % prod(c.values))
