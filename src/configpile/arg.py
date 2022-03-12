from __future__ import annotations

import dataclasses
from abc import ABC, abstractmethod
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

from typing_extensions import TypeGuard

from .collector import Collector
from .errors import Err, Result
from .types import ParamType, path

T = TypeVar("T", covariant=True)  #: Item type

W = TypeVar("W", covariant=True)  #: Wrapped item type

if TYPE_CHECKING:
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


ArgName = Union[str, AutoName]

A = TypeVar("A", bound="Arg")


# TODO: solve this bug


@dataclass(frozen=True)  # type: ignore
class Arg(ABC):
    """
    Base class for all kinds of arguments
    """

    help: Optional[str]  #: Help for the argument

    #: Short option name, used in command line parsing, prefixed by a single hyphen
    short_flag_name: Optional[str]

    #: Long option name used in command line argument parsing
    #:
    #: It is lowercase, prefixed with ``--`` and words are separated by hyphens
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

    def updated(self: A, name: str, help: str, env_prefix: Optional[str]) -> A:
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
    def update_processor(self, pf: ProcessorFactory) -> None:
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

    def update_processor(self, pf: ProcessorFactory) -> None:
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
        short_flag_name: Optional[str],
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
        assert res.all_flags(), "Provide at least one of short_flag_name or long_flag_name"
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
class Param(Arg, Generic[T]):
    """
    Describes an argument holding a value of a given type

    .. note::
        Instances of :class:`.Param` have two "states":

        * Initially, instances of :class:`.Param` are assigned to class attributes of
        subclasses of :class:`.app.App`. In that state, :attr:`.Param.name` is not set,
        and the other ``XXX_name`` attributes contain either a custom name provided by the user, or
        instructions about the derivation of the corresponding name.

        * When an instance of :class:`.App` is constructed, the :attr:`.name` attribute and the
          ``XXX_name`` attributes of the instance are updated.
    """

    #: Argument type, parser from string to value
    param_type: ParamType[T]  # type: ignore

    is_config: bool  #: Whether this represent a list of config files

    #: Argument collector
    collector: Collector[T]  # type: ignore

    default_value: Optional[str]  #: Default value inserted as instance

    name: Optional[str]  #: Python identifier representing the argument

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

    def update_processor(self, pf: ProcessorFactory) -> None:
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
        if self.is_required():
            pf.ap_required.add_argument(*self.all_flags(), **self.argparse_argument_kwargs())
        else:
            pf.ap_optional.add_argument(*self.all_flags(), **self.argparse_argument_kwargs())

    @staticmethod
    def store(
        param_type: ParamType[T],
        *,
        help: Optional[str] = None,
        default_value: Optional[str] = None,
        positional: Positional = Positional.FORBIDDEN,
        short_flag_name: Optional[str] = None,
        long_flag_name: ArgName = AutoName.DERIVED,
        config_key_name: ArgName = AutoName.DERIVED,
        env_var_name: ArgName = AutoName.FORBIDDEN,
    ) -> Param[T]:
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
        )

    @staticmethod
    def config(
        *,
        help: Optional[str] = None,
        short_flag_name: Optional[str] = None,
        long_flag_name: ArgName = AutoName.DERIVED,
        env_var_name: ArgName = AutoName.FORBIDDEN,
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
        )

    @staticmethod
    def append(
        param_type: ParamType[Sequence[W]],
        *,
        positional: Positional = Positional.FORBIDDEN,
        short_flag_name: Optional[str] = None,
        long_flag_name: ArgName = AutoName.DERIVED,
        config_key_name: ArgName = AutoName.DERIVED,
        env_var_name: ArgName = AutoName.FORBIDDEN,
    ) -> Param[Sequence[W]]:
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
            param_type=param_type,
            collector=Collector.append(),  # type: ignore
            default_value=None,
            positional=positional,
            short_flag_name=short_flag_name,
            long_flag_name=long_flag_name,
            config_key_name=config_key_name,
            env_var_name=env_var_name,
            is_config=False,
        )
