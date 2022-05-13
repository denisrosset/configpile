"""This module implements automated derivation of parser instances from type hints"""
import collections.abc
from typing import Any, Optional, Tuple, Union

from typing_extensions import Annotated, get_args, get_origin

from ..collector import Collector
from .parser import Parser
from .std import scalar_type_parsers


def derive_parser_and_collector(type_hint: Any) -> Tuple[Parser[Any], Collector[Any]]:
    """Returns a parser and collector guessed from a type annotation

    It supports the scalar types defined in the :mod:`configpile.parsers` module,
    and the following collections:

    - :py:`typing.Annotated` we throw away the extra information
    - :py:`typing.Sequence` the argument can be provided repeatedly
    - :py:`typing.Optional` an empty string is mapped to the :py:`None` value
    """
    if get_origin(type_hint) is Annotated:
        type_hint = get_args(type_hint)[0]
    if type_hint in scalar_type_parsers:
        return (scalar_type_parsers[type_hint], Collector.keep_last())
    origin = get_origin(type_hint)
    if origin is collections.abc.Sequence:
        item_type = get_args(type_hint)[0]
        if item_type in scalar_type_parsers:
            return (scalar_type_parsers[item_type].as_sequence_of_one(), Collector.append())
    if origin is Optional:
        item_type = get_args(type_hint)[0]
        if item_type in scalar_type_parsers:
            return (scalar_type_parsers[item_type].empty_means_none(), Collector.keep_last())
    raise ValueError(f"Cannot derive parser for type {type_hint}")
    @staticmethod
    def auto_flag(
        *,
        doc: Union[str, Auto] = Auto(),
        default_value: Optional[str] = None,
        short_flag_name: Optional[str] = None,
        long_flag_name: Union[str, Derived, None] = Derived.KEBAB_CASE,
        config_key_name: Union[str, Derived, None] = Derived.KEBAB_CASE,
        env_var_name: Union[str, Derived, None] = None,
    ) -> Param[_Value_co]:
        """_summary_

        Args:
            doc: _description_. Defaults to Auto().
            default_value: _description_. Defaults to None.
            short_flag_name: _description_. Defaults to None.
            long_flag_name: _description_. Defaults to Derived.KEBAB_CASE.
            config_key_name: _description_. Defaults to Derived.KEBAB_CASE.
            env_var_name: _description_. Defaults to None.

        Returns:
            _description_
        """
        return Param(
            parser=Auto(),
            collector=Auto(),
            name=Auto(),
            doc=doc,
            default_value=default_value,
            positional=None,
            short_flag_name=short_flag_name,
            long_flag_name=long_flag_name,
            config_key_name=config_key_name,
            env_var_name=env_var_name,
            is_config=False,
        )

def positional(
    *, minimum: int = 1, maximum: Optional[int] = 1, doc: Union[str, Auto] = Auto()
) -> Param[_Value_co]:
    """_summary_

    Args:
        minimum: _description_. Defaults to 1.
        maximum: _description_. Defaults to 1.
        doc: _description_. Defaults to Auto().

    Returns:
        _description_
    """
    return Param(
        parser=Auto(),
        collector=Auto(),
        name=Auto(),
        doc=doc,
        default_value=None,
        positional=Positional(minimum, maximum),
        short_flag_name=None,
        long_flag_name=None,
        config_key_name=None,
        env_var_name=None,
        is_config=False,
    )

