import argparse
from dataclasses import dataclass
from math import prod
from pathlib import Path
from typing import Sequence

from typing_extensions import Annotated

from configpile import *


@dataclass(frozen=True)
class Calculator(Config):
    """
    Example command-line tool that sums or multiplies floating-point numbers
    """

    #: Values to sum or multiply
    values: Annotated[
        Sequence[float],
        Param.append(
            types.float_.as_sequence_of_one(),
            positional=Positional.ONE_OR_MORE,
            long_flag_name=None,
        ),
    ]

    #: Operation to perform, either addition "+" or multiplication "*"
    operation: Annotated[
        str, Param.store(types.ParamType.choices_str(["+", "*"]), default_value="+")
    ]

    #: Number of digits to display
    #:
    #: This number of digits can also be set with the environment variable
    #: ``DIGITS``
    digits: Annotated[
        int,
        Param.store(
            types.int_.validated(lambda i: i > 0, "Must be a positive integer"),
            default_value="3",
            env_var_name="DIGITS",
        ),
    ]

    #: INI configuration files to parse
    config: Annotated[Sequence[Path], Param.config()]

    def validate_round_digits(self) -> Validator:
        """
        Example validator method
        """
        if self.digits > 15:
            return Err.make("A number of digits greater than 16 is nonsensical")
        else:
            return None


def parser() -> argparse.ArgumentParser:
    return Calculator.get_argument_parser_()


# calc = Calculator([2, 3, 4], "*", 6, [])

if __name__ == "__main__":
    calc = Calculator.from_command_line_()
    res: float = 0.0
    if calc.operation == "+":
        res = sum(calc.values)
    elif calc.operation == "*":
        res = prod(calc.values)
    print(f"%.{calc.digits}f" % res)
