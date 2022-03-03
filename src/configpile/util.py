from __future__ import annotations

import textwrap
from collections import OrderedDict
from dataclasses import dataclass
from typing import Any, Callable, Dict, Generic, List, Mapping, NoReturn, Optional
from typing import OrderedDict as OrderedDictT
from typing import Sequence, Tuple, Type, TypeVar, ValuesView, overload

from class_doc import extract_docs_from_cls_obj

K = TypeVar("K")
T = TypeVar("T")
U = TypeVar("U")
V = TypeVar("V")
W = TypeVar("W")
E = TypeVar("E")  #: Error type


@dataclass(frozen=True)
class ClassDoc(Generic[T]):
    """
    Stores information about Sphinx autodoc-style documentation for a class

    See `<https://pypi.org/project/class-doc/>`_
    """

    docs: Sequence[Mapping[str, Sequence[str]]]  #: Documentation for the class and parents

    def raw(self, attribute_name: str) -> Optional[Sequence[str]]:
        for d in self.docs:
            if attribute_name in d:
                return d[attribute_name]
        return None

    def __getitem__(self, attribute_name: str) -> Optional[Sequence[str]]:
        """
        Returns the documentation for a given attribute

        This returns the documentation present in the first class in the Method Resolution Order.

        Args:
            attribute_name: Name of the attribute to query

        Returns:
            Documentation lines or None if not found
        """
        res = self.raw(attribute_name)
        if res is None:
            return None
        return textwrap.dedent("\n".join(res)).split("\n")

    @staticmethod
    def make(t: Type[T]) -> ClassDoc[T]:
        """
        Retrieves the documentation for the attributes of a class

        Args:
            t: Class type to investigate

        Returns:
            A ClassDoc instance
        """
        docs: List[Mapping[str, Sequence[str]]] = []
        for c in t.mro():
            try:
                docs.append(extract_docs_from_cls_obj(c))
            except TypeError:
                pass

        return ClassDoc(docs)


def dict_from_multiple_keys(pairs: Sequence[Tuple[Sequence[K], V]]) -> Dict[K, V]:
    """
    Constructs a dict from a list of items where a value can have multiple keys

    Args:
        pairs: List of dict elements

    Returns:
        A dictionary
    """
    return {k: v for (kk, v) in pairs for k in kk}


def filter_ordered_dict_by_value_type(w: Type[W], od: OrderedDictT[K, V]) -> OrderedDictT[K, W]:
    """
    Filters values of an ordered dictionary that correspond to a given type

    Returns:
        A new dictionary
    """
    pairs: Sequence[Tuple[K, W]] = [(k, v) for (k, v) in od.items() if isinstance(v, w)]
    return OrderedDict(pairs)


def filter_ordered_dict(
    f: Callable[[K, V], bool],
    od: OrderedDictT[K, V],
) -> OrderedDictT[K, V]:
    """
    Filters items of an ordered dictionary based on a predicate

    Args:
        f: Predicate taking a key/value pair as arguments
        od: Ordered dictionary to filter

    Returns:
        A new dictionary
    """
    return OrderedDict([(k, v) for (k, v) in od.items() if f(k, v)])


def filter_sequence_by_value_type(
    w: Type[W], seq: Sequence[V], predicate: Optional[Callable[[W], bool]]
) -> Sequence[W]:
    """
    Filter values using their type and an optional predicate

    Args:
        w: Type to keep
        seq: Sequence to filter
        predicate: Optional predicate, default: keep all values of given type

    Returns:
        The filtered sequence
    """
    if predicate is None:
        predicate = lambda w: True
    return [v for v in seq if isinstance(v, w) if predicate(v)]


def assert_never(value: NoReturn) -> NoReturn:
    """
    Function used for exhaustiveness checks

    See `<https://github.com/python/cpython/pull/30842>`_
    """
    assert False, f"Unhandled value: {value} ({type(value).__name__})"


def filter_types(
    t: Type[T], seq: Sequence[Any], min_el: int = 0, max_el: Optional[int] = None
) -> Sequence[T]:
    """
    Searches for elements of a given type in a sequence


    Args:
        t: Type to search for
        seq: Sequence to search in
        min_el: Minimum number of elements to recover
        max_el: Maximum number of elements to recover (optional)

    Raises:
        ValueError: if the number of recovered elements is not between ``min_el`` and ``max_el``

    Returns:
        A sequence of elements of the given type
    """
    filtered = [s for s in seq if isinstance(s, t)]
    n = len(filtered)
    if n < min_el:
        raise ValueError(f"Minimum {min_el} elements of type {t} need to be present, {n} found")
    if max_el and n > max_el:
        raise ValueError(f"Minimum {max_el} elements of type {t} need to be present, {n} found")
    return filtered


def filter_types_single(t: Type[T], seq: Sequence[Any]) -> Optional[T]:
    """
    Searches for zero or one elements of a given type in a sequence

    Args:
        t: Type to search for
        seq: Sequence to search in

    Raises:
        ValueError: if the number of recovered elements is not between ``min_el`` and ``max_el``

    Returns:
        A single element or None
    """
    res = filter_types(t, seq, min_el=0, max_el=1)
    if res:
        return res[0]
    else:
        return None
