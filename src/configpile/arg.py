"""
Argument definition

This module enables the definitions of various kinds of configuration arguments.

- Parameters (:class:`.Param`) correspond to values that will be present in the configuration. 
  Each invocation of a parameter has a user-provided string attached, which is parsed by a 
  :class:`~configpile.types.ParamType`. Those invocations can come from environment variables
  (:attr:`.Param.env_var_name`), configuration files (:attr:`.Param.config_key_name`),
  command-line flags (:attr:`.Arg.short_flag_name`, :attr:`.Arg.long_flag_name`), or finally
  as positional command-line parameters (:attr:`.Param.positional`).

- Configuration file inclusion using special parameters :meth:`.Param.config`

- Expanders (:class:`.Expander`) can only be present as command-line flags; their action is
  to insert a key/value pair in the command-line. This enables, for example, flags that set
  a boolean parameter to `True` or `False`. 

.. rubric:: Types

This module uses the following types. 

.. py:data:: ArgName

    Name used for an argument invocation; can be::abbreviation:
    
    - :attr:`.AutoName.FORBIDDEN`, in which case the argument cannot be invoked in that context

    - :attr:`.AutoName.DERIVED`, in which case the name is derived from the field name in the
      :class:`~configpile.config.Config` subclass.

    - a user provided string

.. py:data:: _Config

    Configuration dataclass type being constructed

.. py:data:: _Arg

    Precise argument type, used mostly internally.

    See `<https://en.wikipedia.org/wiki/Bounded_quantification>`_

.. py:data:: _Value

    Type of the parameter value

.. py:data:: _Item

    Item in a sequence
"""

from __future__ import annotations

import dataclasses
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
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

from typing_extensions import TypeGuard

from .collector import Collector
from .types import ParamType, path
from .userr import Err

# documented in the module docstring

_Value = TypeVar("_Value", covariant=True)

_Item = TypeVar("_Item", covariant=True)

if TYPE_CHECKING:
    from .config import Config
    from .processor import ProcessorFactory


class AutoName(Enum):
    """
    Describes automatic handling of an argument name
    """

    #: The argument should not be present in the corresponding source
    FORBIDDEN = 0

    #: Derives the argument name from the original Python identifier (default)
    DERIVED = 1

    @staticmethod
    def derive_long_flag_name(name: str) -> str:
        """
        Returns a long flag name

        Changes the snake_case to kebab-case and adds a ``--`` prefix

        Args:
            name: Python identifier used to derive the flag

        Returns:
            A long flag name
        """
        if name.endswith("_command"):
            name = name[:-8]
        return "--" + name.replace("_", "-")

    @staticmethod
    def derive_env_var_name(name: str, prefix: Optional[str]) -> str:
        """
        Returns a environment variable name derived from a Python identifier

        Keeps snake_case but transforms into upper case, and optionally adds a prefix,
        separated by an underscore.

        Args:
            name: Python identifier used to derive the flag
            prefix: Optional prefix

        Returns:
            An environment variable name
        """
        if prefix is not None:
            return prefix + "_" + name.upper()
        else:
            return name.upper()

    @staticmethod
    def derive_config_key_name(name: str) -> str:
        """
        Derives a INI key name

        It matches the Python identifier, with snake_case replaced by kebab-case.

        Args:
            name: Python identifier used to derive the key name

        Returns:
            INI file key name
        """
        return name.replace("_", "-")


# those types are documented in the module docstring

ArgName = Union[str, AutoName]

_Arg = TypeVar("_Arg", bound="Arg")
_Config = TypeVar("_Config", bound="Config")

# TODO: solve this bug


@dataclass(frozen=True)  # type: ignore[misc]
class Arg(ABC):
    """
    Base class for all kinds of arguments
    """

    #: Help for the argument
    help: Optional[str]

    #: Short option name, used in command line parsing, prefixed by a single hyphen
    short_flag_name: Optional[str]

    #: Long option name used in command line argument parsing
    #:
    #: It is in general lowercase, prefixed with ``--`` and words are separated by hyphens.,
    #:
    #: If set to
    long_flag_name: ArgName

    def all_flags(self) -> Sequence[str]:
        """
        Returns a sequence of all forms of command line flags
        """
        res: List[str] = []
        if self.short_flag_name is not None:
            res.append(self.short_flag_name)
        assert self.long_flag_name != AutoName.DERIVED
        if isinstance(self.long_flag_name, str):
            res.append(self.long_flag_name)
        return res

    def update_dict_(self, name: str, help: str, env_prefix: Optional[str]) -> Mapping[str, Any]:
        """
        Returns updated values for this argument, used during :class:`.App` construction

        Args:
            name: Argument field name
            help: Argument docstring which describes the argument role
            env_prefix: Uppercase prefix for all environment variables

        Returns:

        """
        res = {"help": help}
        if self.long_flag_name == AutoName.DERIVED:
            res["long_flag_name"] = AutoName.derive_long_flag_name(name)
        return res

    def updated(self: _Arg, name: str, help: str, env_prefix: Optional[str]) -> _Arg:
        """
        Returns a copy of this argument with some data updated from its declaration context

        Args:
            self:
            name: Identifier name
            help: Help string (derived from autodoc syntax)
            env_prefix: Environment prefix

        Returns:
            Updated argument
        """
        return dataclasses.replace(self, **self.update_dict_(name, help, env_prefix))

    @abstractmethod
    def update_processor(self, pf: ProcessorFactory[_Config]) -> None:
        """
        Updates a config processor with the processing required by this argument

        Args:
            pf: Processor factory
        """
        pass

    @abstractmethod
    def argparse_argument_kwargs(self) -> Mapping[str, Any]:
        """
        Returns the keyword arguments for use with argparse.ArgumentParser.add_argument

        Returns:
            Keyword arguments mapping
        """
        pass


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
        from .processor import CLInserter

        for flag in self.all_flags():
            pf.cl_flag_handlers[flag] = CLInserter([self.new_flag, self.new_value])
        pf.ap_commands.add_argument(*self.all_flags(), **self.argparse_argument_kwargs())

    @staticmethod
    def make(
        new_flag: str,
        new_value: str,
        *,
        help: Optional[str] = None,
        short_flag_name: Optional[str] = None,
        long_flag_name: ArgName = AutoName.DERIVED,
    ) -> Expander:
        """
        Constructs an expander that inserts a flag/value pair in the command line

        At least one of ``short_flag_name`` or ``long_flag_name`` must be defined.

        Args:
            new_flag: Inserted flag, including the hyphen prefix
            new_value: String value to insert following the flag

        Keyword Args:
            help: Help description (autodoc/docstring is used otherwise)
            short_flag_name: Short flag name of this command flag
            long_flag_name: Long flag name of this command flag
        """
        res = Expander(
            help=help,
            new_flag=new_flag,
            new_value=new_value,
            short_flag_name=short_flag_name,
            long_flag_name=long_flag_name,
        )
        return res

    def argparse_argument_kwargs(self) -> Mapping[str, Any]:
        return {"help": self.help}


class Positional(Enum):
    """
    Describes the positional behavior of a parameter
    """

    FORBIDDEN = 0  #: The argument is not positional
    ONCE = 1  #: The argument parses a single positional value
    ZERO_OR_MORE = 2  #: The argument parses the remaining positional value
    ONE_OR_MORE = 3  #: The argument parses at least one remaining positional value

    def should_be_last(self) -> bool:
        """
        Returns whether a positional parameter should be the last one
        """
        return self in {Positional.ZERO_OR_MORE, Positional.ONE_OR_MORE}

    def is_positional(self) -> bool:
        """
        Returns whether a parameter is positional
        """
        return self != Positional.FORBIDDEN


@dataclass(frozen=True)
class Param(Arg, Generic[_Value]):
    """
    Describes an argument holding a value of a given type

    You'll want to construct parameters using the static methods available:

    - :meth:`~.Param.store` to create a parameter that keeps the last value provided

    - :meth:`~.Param.append` to create a parameter that collects all the provided value into
      a sequence. Note that the parsed value must already be a sequence; for that, use the
      method :meth:`~configpile.types.ParamType.as_sequence_of_one` on the
      :class:`~configpile.types.ParamType` instance.

    For the two constructions above, you can construct positional parameters by setting the
    :attr:`.Param.positional` field.

    - :meth:`~.Param.config` returns a parameter that parses configuration files.
    """

    #: Argument type, parser from string to value
    param_type: ParamType[_Value]  # type: ignore

    is_config: bool  #: Whether this represent a list of config files

    #: Argument collector
    collector: Collector[_Value]  # type: ignore

    default_value: Optional[str]  #: Default value inserted as instance

    #: Python field identifier for this parameter in :class:`~configpile.config.Config`
    name: Optional[str]  #: Python identifier representing the argument

    #: Whether this parameter can appear as a positional parameter and how
    #:
    #: A positional parameter is a paramater that appears without a preceding flag
    positional: Positional

    #: Configuration key name used in INI files
    #:
    #: It is lowercase, and words are separated by hyphens.
    config_key_name: ArgName

    #: Environment variable name
    #:
    #: The environment variable name has an optional prefix, followed by the
    #: Python identifier in uppercase, with underscore as separator.
    #:
    #: This prefix is provided by :attr:`.App.env_prefix_`
    #:
    #: If a non-empty prefix is given, the name is prefixed with it
    #: (and an underscore).
    env_var_name: ArgName

    validator: Optional[Callable[[_Value], Optional[Err]]]

    def update_dict_(self, name: str, help: str, env_prefix: Optional[str]) -> Mapping[str, Any]:
        r = {"name": name, **super().update_dict_(name, help, env_prefix)}
        if self.config_key_name == AutoName.DERIVED:
            r["config_key_name"] = AutoName.derive_config_key_name(name)
        if self.env_var_name == AutoName.DERIVED and env_prefix is not None:
            r["env_var_name"] = AutoName.derive_env_var_name(name, env_prefix)
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
        return self.default_value is None and self.collector.arg_required()

    def argparse_argument_kwargs(self) -> Mapping[str, Any]:
        res: Dict[str, Any] = {"help": self.help}
        if self.is_required():
            res = {**res, "required": True}
        return {
            **res,
            **self.collector.argparse_argument_kwargs(),
            **self.param_type.argparse_argument_kwargs(),
        }

    def update_processor(self, pf: ProcessorFactory[_Config]) -> None:
        from .processor import CLConfigParam, CLParam, KVConfigParam, KVParam

        assert self.name is not None
        pf.params_by_name[self.name] = self
        if self.positional != Positional.FORBIDDEN:
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
            pf.ap_required.add_argument(
                *self.all_flags(), dest=self.name, **self.argparse_argument_kwargs()
            )
        else:
            pf.ap_optional.add_argument(
                *self.all_flags(), dest=self.name, **self.argparse_argument_kwargs()
            )

    @staticmethod
    def store(
        param_type: ParamType[_Value],
        *,
        help: Optional[str] = None,
        default_value: Optional[str] = None,
        positional: Positional = Positional.FORBIDDEN,
        short_flag_name: Optional[str] = None,
        long_flag_name: ArgName = AutoName.DERIVED,
        config_key_name: ArgName = AutoName.DERIVED,
        env_var_name: ArgName = AutoName.FORBIDDEN,
        validator: Optional[Callable[[_Value], Optional[Err]]] = None,
    ) -> Param[_Value]:
        """
        Creates a parameter that stores the last provided value

        If a default value is provided, the argument can be omitted. However,
        if the default_value ``None`` is given (default), then
        the parameter cannot be omitted.

        Args:
            param_type: Parser that transforms a string into a value

        Keyword Args:
            help: Help description (autodoc/docstring is used otherwise)
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
            name=None,
            help=help,
            param_type=param_type,
            collector=Collector.keep_last(),
            default_value=default_value,
            positional=positional,
            short_flag_name=short_flag_name,
            long_flag_name=long_flag_name,
            config_key_name=config_key_name,
            env_var_name=env_var_name,
            is_config=False,
            validator=validator,
        )

    @staticmethod
    def config(
        *,
        help: Optional[str] = None,
        short_flag_name: Optional[str] = None,
        long_flag_name: ArgName = AutoName.DERIVED,
        env_var_name: ArgName = AutoName.FORBIDDEN,
        validator: Optional[Callable[[Sequence[Path]], Optional[Err]]] = None,
    ) -> Param[Sequence[Path]]:
        """
        Creates a parameter that parses configuration files and stores their names

        Keyword Args:
            help: Help description (autodoc/docstring is used otherwise)
            short_flag_name: Short option name (optional)
            long_flag_name: Long option name (auto. derived from fieldname by default)
            env_var_name: Environment variable name (forbidden by default)

        Returns:
            A configuration files parameter
        """
        return Param(
            name=None,
            help=help,
            param_type=path.separated_by(",", strip=True, remove_empty=True),
            collector=Collector.append(),  # type: ignore
            positional=Positional.FORBIDDEN,
            short_flag_name=short_flag_name,
            long_flag_name=long_flag_name,
            config_key_name=AutoName.FORBIDDEN,
            env_var_name=env_var_name,
            is_config=True,
            default_value=None,
            validator=validator,
        )

    @staticmethod
    def append(
        param_type: ParamType[Sequence[_Item]],
        *,
        help: Optional[str] = None,
        positional: Positional = Positional.FORBIDDEN,
        short_flag_name: Optional[str] = None,
        long_flag_name: ArgName = AutoName.DERIVED,
        config_key_name: ArgName = AutoName.DERIVED,
        env_var_name: ArgName = AutoName.FORBIDDEN,
        validator: Optional[Callable[[Sequence[_Item]], Optional[Err]]] = None,
    ) -> Param[Sequence[_Item]]:
        """
        Creates an argument that stores the last provided value

        Args:
            param_type: Parser that transforms a string into a value

        Keyword Args:
            help: Help description (autodoc/docstring is used otherwise)
            positional: Whether this argument is present in positional arguments
            short_flag_name: Short option name (optional)
            long_flag_name: Long option name (auto. derived from fieldname by default)
            config_key_name: Config key name (auto. derived from fieldname by default)
            env_var_name: Environment variable name (forbidden by default)

        Returns:
            The constructed Arg instance
        """
        return Param(
            name=None,
            help=help,
            param_type=param_type,
            collector=Collector.append(),  # type: ignore
            default_value=None,
            positional=positional,
            short_flag_name=short_flag_name,
            long_flag_name=long_flag_name,
            config_key_name=config_key_name,
            env_var_name=env_var_name,
            is_config=False,
            validator=validator,
        )
