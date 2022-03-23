from dataclasses import dataclass

from typing_extensions import Annotated

from configpile import *


class FloatPT(Parser[float]):
    """
    Parameter type that parses floats
    """

    def parse(self, arg: str) -> Res[float]:
        try:
            return float(arg)
        except ValueError as e:
            return Err.make(str(e))


floatPT = FloatPT()


@dataclass(frozen=True)
class Calc(Config):
    """
    Command-line tool that sums two floating point numbers
    """

    #: First argument
    x: Annotated[float, Param.store(floatPT)]

    #: Second argument
    y: Annotated[float, Param.store(floatPT)]


c = Calc.from_command_line_()
print(f"{c.x} + {c.y} = {c.x+c.y}")
