from collections import OrderedDict
from dataclasses import dataclass
from typing import Callable, Dict, Generic, List, NoReturn, Optional
from typing import OrderedDict as OrderedDictT
from typing import Sequence, Tuple, Type, TypeVar, ValuesView, overload

K = TypeVar("K")
T = TypeVar("T")
U = TypeVar("U")
V = TypeVar("V")
W = TypeVar("W")
E = TypeVar("E")  #: Error type


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
    pairs: Sequence[Tuple[K, W]] = [(k, v) for (k, v) in od.items() if isinstance(v, w)]
    return OrderedDict(pairs)


def filter_ordered_dict(
    f: Callable[[K, V], bool],
    od: OrderedDictT[K, V],
) -> OrderedDictT[K, V]:
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
