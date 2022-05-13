"""
Argument definition

This module enables the definitions of various kinds of configuration arguments.

- Parameters (:class:`.Param`) correspond to values that will be present in the configuration.
  Each invocation of a parameter has a user-provided string attached, which is parsed by a
  :class:`~configpile.parsers.Parser`. Those invocations can come from environment variables
  (:attr:`.Param.env_var_name`), configuration files (:attr:`.Param.config_key_name`),
  command-line flags (:attr:`.Arg.short_flag_name`, :attr:`.Arg.long_flag_name`), or finally
  as positional command-line parameters (:attr:`.Param.positional`).

- Configuration file inclusion using special parameters :meth:`.Param.config`

- Expanders (:class:`.Expander`) can only be present as command-line flags; their action is
  to insert a key/value pair in the command-line. This enables, for example, flags that set
  a boolean parameter to `True` or `False`.

.. rubric:: Types

This module uses the following types.

.. py:data:: _Config

    Configuration dataclass type being constructed

.. py:data:: _Arg

    Precise argument type, used mostly internally.

    See `<https://en.wikipedia.org/wiki/Bounded_quantification>`_

.. py:data:: _Value_co

    Type of the parameter value

.. py:data:: _Item_co

    Item in a sequence
"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import (
    TYPE_CHECKING,
    Any,
    Dict,
    Generic,
    List,
    Mapping,
    Optional,
    Sequence,
    Tuple,
    TypeVar,
    Union,
)

from .collector import Collector
from .misc import Auto
from .parsers import Parser, path_parser
from .processing.cli_handlers import CLConfigParam, CLInserter, CLParam
from .processing.kv_handlers import KVConfigParam, KVParam

# documented in the module docstring

_Value_co = TypeVar("_Value_co", covariant=True)

_Item_co = TypeVar("_Item_co", covariant=True)

if TYPE_CHECKING:
    from .config import Config
    from .processing.processor import ProcessorFactory


_Arg = TypeVar("_Arg", bound="Arg")
_Config = TypeVar("_Config", bound="Config")


@dataclass(frozen=True)
class Positional:
    """Describes how many values a positional parameters collects"""

    #: Minimal number of values, >= 0
    min: int

    #: Maximal number of values, :py:`None` means unlimited
    max: Optional[int]

    def __post_init__(self) -> None:
        assert self.min >= 0
        assert self.max is None or self.max >= self.min

    def fixed_number(self) -> Optional[int]:
        """Returns, when relevant, the fixed number of values that this parameter collects"""
        if self.max is None or self.min != self.max:
            return None
        else:
            return self.min


class Derived(Enum):
    """Describes automatic handling of an argument name"""

    #: Derives the name/key using snake_case
    SNAKE_CASE = 1

    #: Derives the name/key using SNAKE_CASE (and sets uppercase, default for env. variables)
    SNAKE_CASE_UPPER_CASE = 2

    #: Derives the argument name using kebab-case (default for INI file keys and cmd line flags)
    KEBAB_CASE = 3

    def derive(self, name: str) -> str:
        """
        Returns a derived name from a field name

        Args:
            name: Field name in Python identifier format
        """
        assert str.isidentifier(name)
        if self == Derived.SNAKE_CASE:
            return name
        elif self == Derived.SNAKE_CASE_UPPER_CASE:
            return name.upper()
        elif self == Derived.KEBAB_CASE:
            return name.replace("_", "-")
        else:
            raise NotImplementedError


@dataclass(frozen=True)
class Arg:
    """
    Base class for all kinds of arguments
    """

    #: Doc for the argument, if Auto, taken from a Sphinx autodoc comment
    doc: Union[str, Auto, None]

    #: Short option name, used in command line parsing, prefixed by a single hyphen
    short_flag_name: Optional[str]

    #: Long option name used in command line argument parsing
    #:
    #: It is in general lowercase, prefixed with ``--`` and words are separated by hyphens.,
    #:
    #: If set to
    long_flag_name: Union[str, Derived, None]

    def __post_init__(self) -> None:
        if self.__class__ == Arg:
            raise NotImplementedError("Cannot instantiate Arg directly")

    def all_flags(self) -> Sequence[str]:
        """
        Returns a sequence of all forms of command line flags
        """
        res: List[str] = []
        if self.short_flag_name is not None:
            res.append(self.short_flag_name)
        assert not isinstance(self.long_flag_name, Derived)
        if isinstance(self.long_flag_name, str):
            res.append(self.long_flag_name)
        return res

    def update_dict_(
        self,
        name: str,
        doc: Optional[str],
        env_prefix: Optional[str],
    ) -> Mapping[str, Any]:
        """
        Returns updated values for this argument, used during :class:`.App` construction

        Args:
            name: Argument field name
            doc: Argument docstring which describes the argument role
            env_prefix: Uppercase prefix for all environment variables

        Returns:

        """
        res: Dict[str, Any] = {}
        if isinstance(self.doc, Auto):
            res = {"doc": doc}
        if isinstance(self.long_flag_name, Derived):
            res["long_flag_name"] = "--" + self.long_flag_name.derive(name)
        return res

    def updated(
        self: _Arg,
        name: str,
        doc: str,
        env_prefix: Optional[str],
    ) -> _Arg:
        """
        Returns a copy of this argument with some data updated from its declaration context

        Args:
            self:
            name: Identifier name
            doc: Documentation string (derived from autodoc syntax)
            env_prefix: Environment prefix

        Returns:
            Updated argument
        """
        return dataclasses.replace(self, **self.update_dict_(name, doc, env_prefix))

    def update_processor(self, pf: ProcessorFactory[_Config]) -> None:
        """
        Updates a config processor with the processing required by this argument

        Args:
            pf: Processor factory
        """
        raise NotImplementedError

    def argparse_argument_kwargs(self) -> Mapping[str, Any]:
        """
        Returns the keyword arguments for use with argparse.ArgumentParser.add_argument

        Returns:
            Keyword arguments mapping
        """
        raise NotImplementedError


@dataclass(frozen=True)
class Expander(Arg):
    """
    Command-line argument that expands into a flag/value pair
    """

    new_flag: str  #: Inserted flag in the command line

    new_value: str  #: Inserted value in the command line

    def inserts(self) -> Tuple[str, str]:
        """
        Returns the flag/value pair that is inserted when this command flag is present
        """
        return (self.new_flag, self.new_value)

    def update_processor(self, pf: ProcessorFactory[_Config]) -> None:
        for flag in self.all_flags():
            pf.cl_flag_handlers[flag] = CLInserter([self.new_flag, self.new_value])
        pf.ap_commands.add_argument(*self.all_flags(), **self.argparse_argument_kwargs())

    @staticmethod
    def make(
        new_flag: str,
        new_value: str,
        *,
        doc: Optional[str] = None,
        short_flag_name: Optional[str] = None,
        long_flag_name: Union[str, Derived, None] = Derived.KEBAB_CASE,
    ) -> Expander:
        """
        Constructs an expander that inserts a flag/value pair in the command line

        At least one of ``short_flag_name`` or ``long_flag_name`` must be defined.

        Args:
            new_flag: Inserted flag, including the hyphen prefix
            new_value: String value to insert following the flag

        Keyword Args:
            doc: Usage description (autodoc/docstring is used otherwise)
            short_flag_name: Short flag name of this command flag
            long_flag_name: Long flag name of this command flag
        """
        res = Expander(
            doc=doc,
            new_flag=new_flag,
            new_value=new_value,
            short_flag_name=short_flag_name,
            long_flag_name=long_flag_name,
        )
        return res

    def argparse_argument_kwargs(self) -> Mapping[str, Any]:
        return {"help": self.doc}


@dataclass(frozen=True)
class Param(Arg, Generic[_Value_co]):
    """
    Describes an argument holding a value of a given type

    You'll want to construct parameters using the static methods available:

    - :meth:`~.Param.store` to create a parameter that keeps the last value provided

    - :meth:`~.Param.append` to create a parameter that collects all the provided values into
      a sequence. Note that the parsed value must already be a sequence.

    - :meth:`~.Param.append1` to create a parameter that collects all the provided value into
      a sequence. The parsed value should not be a sequence.

    For the constructions above, you can construct positional parameters by setting the
    :attr:`.Param.positional` field.

    - :meth:`~.Param.config` returns a parameter that parses configuration files.
    """

    #: Python field identifier for this parameter in :class:`~configpile.config.Config`
    name: Union[str, Auto]  #: Python identifier representing the argument

    #: Argument type, parser from string to value
    parser: Union[Parser[_Value_co], Auto]

    #: Whether this represent a list of config files
    is_config: bool

    #: Argument collector
    collector: Union[Collector[_Value_co], Auto]

    #: Default value inserted as instance
    default_value: Optional[str]

    #: Whether this parameter can appear as a positional parameter and how
    #:
    #: A positional parameter is a parameter that appears without a preceding flag
    positional: Optional[Positional]

    #: Configuration key name used in INI files
    #:
    #: It is lowercase, and words are separated by hyphens.
    config_key_name: Union[str, Derived, None]

    #: Environment variable name
    #:
    #: The environment variable name has a prefix, followed by the
    #: Python identifier in uppercase, with underscore as separator.
    #:
    #: This prefix is provided by :attr:`.App.env_prefix_`
    env_var_name: Union[str, Derived, None]

    def update_dict_(
        self,
        name: str,
        doc: Optional[str],
        env_prefix: Optional[str],
    ) -> Mapping[str, Any]:
        r = {"name": name, **super().update_dict_(name, doc, env_prefix)}
        if isinstance(self.config_key_name, Derived):
            r["config_key_name"] = self.config_key_name.derive(name)
        if isinstance(self.env_var_name, Derived) and env_prefix is not None:
            r["env_var_name"] = env_prefix + self.env_var_name.derive(name)
        return r

    def all_config_key_names(self) -> Sequence[str]:
        """
        Returns a sequence of all forms of command line options

        Returns:
            Command line options
        """
        if isinstance(self.config_key_name, str):
            return [self.config_key_name]
        else:
            return []

    def all_env_var_names(self) -> Sequence[str]:
        """
        Returns a sequence of all forms of command line options

        Returns:
            Command line options
        """
        if isinstance(self.env_var_name, str):
            return [self.env_var_name]
        else:
            return []

    def is_required(self) -> bool:
        """
        Returns whether the argument is required
        """
        assert not isinstance(self.collector, Auto)
        return self.default_value is None and self.collector.arg_required()

    def argparse_argument_kwargs(self) -> Mapping[str, Any]:
        assert not isinstance(self.collector, Auto)
        assert not isinstance(self.parser, Auto)

        res: Dict[str, Any] = {"help": self.doc}
        choices = self.parser.choices()
        if choices is not None:
            res = {**res, "choices": choices, "type": str}
        return {
            **res,
            **self.collector.argparse_argument_kwargs(),
        }

    def update_processor(self, pf: ProcessorFactory[_Config]) -> None:
        assert not isinstance(self.name, Auto)
        pf.params_by_name[self.name] = self
        if self.positional is not None:
            pf.cl_positionals.append(self)
        for flag in self.all_flags():
            if self.is_config:
                pf.cl_flag_handlers[flag] = CLConfigParam(self)
            else:
                pf.cl_flag_handlers[flag] = CLParam(self)

        for key in self.all_config_key_names():
            pf.ini_handlers[key] = KVParam(self)
        for name in self.all_env_var_names():
            if self.is_config:
                pf.env_handlers[name] = KVConfigParam(self)
            else:
                pf.env_handlers[name] = KVParam(self)

        flags = self.all_flags()
        if self.is_required():
            pf.ap_required.add_argument(*flags, dest=self.name, **self.argparse_argument_kwargs())
        else:
            pf.ap_optional.add_argument(*flags, dest=self.name, **self.argparse_argument_kwargs())

    @staticmethod
    def store(
        parser: Parser[_Value_co],
        *,
        doc: Union[str, Auto] = Auto(),
        default_value: Optional[str] = None,
        positional: Optional[Positional] = None,
        short_flag_name: Optional[str] = None,
        long_flag_name: Union[str, Derived, None] = Derived.KEBAB_CASE,
        config_key_name: Union[str, Derived, None] = Derived.KEBAB_CASE,
        env_var_name: Union[str, Derived, None] = None,
    ) -> Param[_Value_co]:
        """Creates a parameter that stores the last provided value

        If a default value is provided, the argument can be omitted. However,
        if the default_value ``None`` is given (default), then
        the parameter cannot be omitted.

        Args:
            parser: Parser that transforms a string into a value

        Keyword Args:
            doc: Help description (autodoc/docstring is used otherwise)
            default_value: Default value
            positional: Whether this parameter is present in positional arguments
            short_flag_name: Short option name (optional)
            long_flag_name: Long option name (auto. derived from fieldname by default)
            config_key_name: Config key name (auto. derived from fieldname by default)
            env_var_name: Environment variable name (forbidden by default)

        Returns:
            The constructed Param instance
        """

        return Param(
            name=Auto(),
            doc=doc,
            parser=parser,
            collector=Collector.keep_last(),
            default_value=default_value,
            positional=positional,
            short_flag_name=short_flag_name,
            long_flag_name=long_flag_name,
            config_key_name=config_key_name,
            env_var_name=env_var_name,
            is_config=False,
        )

    @staticmethod
    def config(
        *,
        doc: Union[str, Auto] = Auto(),
        short_flag_name: Optional[str] = None,
        long_flag_name: Union[str, Derived, None] = Derived.KEBAB_CASE,
        env_var_name: Union[str, Derived, None] = None,
    ) -> Param[Sequence[Path]]:
        """
        Creates a parameter that parses configuration files and stores their names

        Keyword Args:
            doc: Help description (autodoc/docstring is used otherwise)
            short_flag_name: Short option name (optional)
            long_flag_name: Long option name (auto. derived from fieldname by default)
            env_var_name: Environment variable name (forbidden by default)

        Returns:
            A configuration files parameter
        """
        return Param(
            name=Auto(),
            doc=doc,
            parser=path_parser.separated_by(",", strip=True, remove_empty=True),
            collector=Collector.append(),  # type: ignore
            positional=None,
            short_flag_name=short_flag_name,
            long_flag_name=long_flag_name,
            config_key_name=None,
            env_var_name=env_var_name,
            is_config=True,
            default_value=None,
        )

    @staticmethod
    def append_one(
        parser: Parser[_Item_co],
        *,
        doc: Union[str, Auto] = Auto(),
        positional: Optional[Positional] = None,
        short_flag_name: Optional[str] = None,
        long_flag_name: Union[str, Derived, None] = Derived.KEBAB_CASE,
        config_key_name: Union[str, Derived, None] = Derived.KEBAB_CASE,
        env_var_name: Union[str, Derived, None] = None,
    ) -> Param[Sequence[_Item_co]]:
        """
        Returns a newly created argument that appends single parsed values

        While :meth:`~Param.append` creates a parameter that joins sequences of values, this method
        creates a parameter that appends single items to a sequence.

        Args:
            parser: Parser that transforms a string into a single value item

        Keyword Args:
            doc: Help description (autodoc/docstring is used otherwise)
            positional: Whether this argument is present in positional arguments
            short_flag_name: Short option name (optional)
            long_flag_name: Long option name (auto. derived from fieldname by default)
            config_key_name: Config key name (auto. derived from fieldname by default)
            env_var_name: Environment variable name (forbidden by default)
        """
        return Param(
            name=Auto(),
            doc=doc,
            parser=parser.as_sequence_of_one(),
            collector=Collector.append(),  # type: ignore
            default_value=None,
            positional=positional,
            short_flag_name=short_flag_name,
            long_flag_name=long_flag_name,
            config_key_name=config_key_name,
            env_var_name=env_var_name,
            is_config=False,
        )

    @staticmethod
    def append_many(
        parser: Parser[Sequence[_Item_co]],
        *,
        doc: Union[str, Auto] = Auto(),
        positional: Optional[Positional] = None,
        short_flag_name: Optional[str] = None,
        long_flag_name: Union[str, Derived, None] = Derived.KEBAB_CASE,
        config_key_name: Union[str, Derived, None] = Derived.KEBAB_CASE,
        env_var_name: Union[str, Derived, None] = None,
    ) -> Param[Sequence[_Item_co]]:
        """
        Returns a newly created argument that joins parsed sequences of values

        Args:
            parser: Parser that transforms a string into a sequence of values

        Keyword Args:
            doc: Help description (autodoc/docstring is used otherwise)
            positional: Whether this argument is present in positional arguments
            short_flag_name: Short option name (optional)
            long_flag_name: Long option name (auto. derived from fieldname by default)
            config_key_name: Config key name (auto. derived from fieldname by default)
            env_var_name: Environment variable name (forbidden by default)
        """
        return Param(
            name=Auto(),
            doc=doc,
            parser=parser,
            collector=Collector.append(),  # type: ignore
            default_value=None,
            positional=positional,
            short_flag_name=short_flag_name,
            long_flag_name=long_flag_name,
            config_key_name=config_key_name,
            env_var_name=env_var_name,
            is_config=False,
        )
