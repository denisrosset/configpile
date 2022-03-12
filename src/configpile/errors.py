from __future__ import annotations

import shutil
import textwrap
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Callable, List, Optional, Sequence, Tuple, TypeVar, Union, overload


class Err(ABC):
    """
    Describes an error or list of errors that occurred during argument parsing
    """

    @abstractmethod
    def markdown(self) -> Sequence[str]:
        """
        Returns a Markdown-formatted summary of this error (or list of errors)
        """
        pass

    @abstractmethod
    def errors(self) -> Sequence[Err]:
        """
        Returns a sequence of all contained errors

        If this is not a collection of errors :class:`.ManyErr`, returns a sequence with
        a single item, this instance itself.

        Returns:
            A sequence of errors
        """
        pass

    def pretty_print(self) -> None:
        """
        Pretty prints an error on the console
        """
        try:
            from rich.console import Console
            from rich.markdown import Markdown

            console = Console()
            md = Markdown("\n".join(self.markdown()))
            console.print(md)
        except:
            sz = shutil.get_terminal_size()
            t = self.markdown()
            print(textwrap.fill("\n".join(t), width=sz.columns))

    @staticmethod
    def collect(*errs: Err) -> Err:
        """
        Collect a non-empty sequence of errors into a single error

        Raises:
            ValueError: If no error is provided

        Returns:
            A consolidated error
        """
        assert errs, "At least one parameter must be provided"
        res = Err.collect_optional(*errs)
        if res is None:
            raise ValueError("Result cannot be None if at least one error is provided")
        return res

    @staticmethod
    def collect_optional(*errs: Err) -> Optional[Err]:
        """
        Collect a possibly empty sequence of errors into an optional single error

        Returns:
            An error or None
        """

        lst: List[Err] = []
        for e in errs:
            lst.extend(e.errors())
        if not lst:
            return None
        elif len(lst) == 1:
            return lst[0]
        else:
            return ManyErr(lst)

    @staticmethod
    def make(msg: str) -> Err:
        """
        Creates a single error

        Args:
            msg: Error message

        Returns:
            An error
        """
        return Err1(msg)


@dataclass(frozen=True)
class ManyErr(Err):

    errs: Sequence[Err]

    def __post_init__(self) -> None:
        assert len(self.errs) > 0, "A ManyErr should contain at least one error"
        assert all([not isinstance(e, ManyErr) for e in self.errs])

    def markdown(self) -> Sequence[str]:
        lines: List[str] = []
        for i, e in enumerate(self.errs):
            start = f"{i+1}. "
            res: Sequence[str] = e.markdown()
            if res:
                line1 = start + res[0]

                def space_prefix(s: str) -> str:
                    return (" " * len(start)) + s

                rest: List[str] = [space_prefix(l) for l in res[1:]]
                lines.append(line1)
                lines.extend(rest)
        return lines

    def errors(self) -> Sequence[Err]:
        return self.errs


@dataclass(frozen=True)
class Err1(Err):
    """
    Describes a single error
    """

    msg: str  #: Error message

    def errors(self) -> Sequence[Err]:
        return [self]

    def markdown(self) -> Sequence[str]:
        return [self.msg]


#: Ok value in our custom result type
T = TypeVar("T", covariant=True)

U = TypeVar("U")
V = TypeVar("V")
W = TypeVar("W")


Result = Union[T, Err]


def collect_seq(seq: Sequence[Result[T]]) -> Result[Sequence[T]]:
    ok: List[T] = []
    errs: List[Err] = []
    for res in seq:
        if isinstance(res, Err):
            errs.extend(res.errors())
        else:
            ok.append(res)
    if errs:
        return ManyErr(errs)
    else:
        return ok


@overload
def collect(t: Result[T], u: Result[U]) -> Result[Tuple[T, U]]:
    pass


@overload
def collect(t: Result[T], u: Result[U], v: Result[V]) -> Result[Tuple[T, U, V]]:
    pass


@overload
def collect(
    t: Result[T],
    u: Result[U],
    v: Result[V],
    w: Result[W],
) -> Result[Tuple[T, U, V, W]]:
    pass


def collect(*args):  # type: ignore[no-untyped-def]
    ok: List[Any] = []
    errs: List[Err] = []
    for arg in args:
        if isinstance(arg, Err):
            errs.extend(arg.errors())
        else:
            ok.append(arg)
    if errs:
        return ManyErr(errs)
    else:
        return tuple(ok)


def map_result(f: Callable[[T], U], r: Result[T]) -> Result[U]:
    if isinstance(r, Err):
        return r
    else:
        return f(r)
