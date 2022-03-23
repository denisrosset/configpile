from dataclasses import dataclass

from typing_extensions import Annotated

from configpile import *


@dataclass(frozen=True)
class Calc(Config):
    """
    Command-line tool that sums two floating point numbers
    """

    #: First argument
    x: Annotated[
        float,
        Param.store(
            types.float_,
            positional=Positional.ONCE,
            short_flag_name=None,
            long_flag_name=None,
        ),
    ]

    #: Second argument
    y: Annotated[
        float,
        Param.store(
            types.float_,
            positional=Positional.ONCE,
            short_flag_name=None,
            long_flag_name=None,
        ),
    ]


c = Calc.from_command_line_()
print(f"{c.x} + {c.y} = {c.x+c.y}")
