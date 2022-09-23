# pylint: disable=missing-class-docstring,missing-function-docstring,missing-module-docstring

from abc import ABC, abstractmethod
from typing import Any, ClassVar, Generic, Literal, Optional, Sequence, TypeVar, Union

from typing_extensions import get_args, get_origin, get_type_hints

from configpile.auto import derive
from configpile.userr import Err, collect_seq

T = TypeVar("T")


class Case(ABC):
    """Describes a test case for the auto parser/collector derivation system"""

    #: Strings as arguments being parsed
    args: Sequence[str]

    #: Provide a type from which the autoderivation will be done in the subclass
    value: Any

    def test_auto_derivation(self):
        th = get_type_hints(self, include_extras=True)
        vth = th["value"]

        parser, collector = derive(th["value"])
        parsed_values = collect_seq([parser.parse(s) for s in self.args])
        assert not isinstance(parsed_values, Err)
        res = collector.collect(parsed_values)
        assert not isinstance(res, Err)
        assert res == self.value


class TestInt(Case):

    args = ["12", "23"]
    value: int = 23


class TestFloat(Case):

    args = ["12.0", "23"]
    value: float = 23.0


class TestSequenceInt(Case):
    args = ["1", "2", "3"]
    value: Sequence[int] = [1, 2, 3]


class TestOptionalIntNoneEmptyString(Case):
    args = [""]
    value: Optional[int] = None


class TestOptionalIntValue(Case):
    args = ["2"]
    value: Optional[int] = 2


class TestLiteral(Case):
    args = ["blue"]
    value: Literal["red", "green", "blue"] = "blue"


class TestUnionOfLiterals(Case):
    args = ["blue"]
    value: Union[Literal["red"], Literal["green"], Literal["blue"]] = "blue"


class TestOptionalLiterals(Case):
    args = ["blue"]
    value: Optional[Union[Literal["red"], Literal["green"], Literal["blue"]]] = "blue"
