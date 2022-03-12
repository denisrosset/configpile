from __future__ import annotations

import argparse
import configparser
import copy
import os
import sys
from abc import ABC, abstractmethod
from ast import arg
from configparser import ConfigParser
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import (
    TYPE_CHECKING,
    Any,
    ClassVar,
    Dict,
    Generic,
    Iterable,
    List,
    Mapping,
    Optional,
    Sequence,
    Tuple,
    Type,
    TypeVar,
    Union,
)

from typing_extensions import Annotated, get_args, get_origin, get_type_hints

from .arg import Arg, Expander, Param, Positional
from .errors import Err, Err1, Result
from .types import ParamType
from .util import ClassDoc, filter_types_single

if TYPE_CHECKING:
    from .config import Config

C = TypeVar("C", bound="Config")

T = TypeVar("T")  #: Item type


class CLHandler(ABC):
    """
    A handler for command-line arguments
    """

    @abstractmethod
    def handle(self, args: Sequence[str], state: State) -> Tuple[Sequence[str], Optional[Err]]:
        """
        Processes arguments, possibly updating the state or returning errors

        Args:
            args: Command-line arguments not processed yet
            state: (Mutable) state to possibly update

        Returns:
            The updated command-line and an optional error
        """
        pass


@dataclass(frozen=True)
class CLSpecialAction(CLHandler):
    """
    A handler that sets the special action
    """

    special_action: SpecialAction

    def handle(self, args: Sequence[str], state: State) -> Tuple[Sequence[str], Optional[Err]]:
        if state.special_action is not None:
            before = state.special_action.name
            now = self.special_action.name
            err = Err.make(f"We had already action {before}, conflicts with action {now}")
            return (args, err)
        state.special_action = self.special_action
        return (args, None)


@dataclass(frozen=True)
class CLInserter(CLHandler):
    """
    Handler that expands a flag into a sequence of args inserted into the command line to be parsed
    """

    inserted_args: Sequence[str]

    def handle(self, args: Sequence[str], state: State) -> Tuple[Sequence[str], Optional[Err]]:
        # TODO: run the command line parser on the inserted args
        return ([*self.inserted_args, *args], None)


@dataclass(frozen=True)
class CLParam(CLHandler, Generic[T]):
    """
    Parameter handler

    Takes a single string argument from the command line, parses it and pushes into the
    corresponding sequence of instances
    """

    param: Param[T]

    def action(self, value: T, state: State) -> Optional[Err]:
        """
        A method called on the successful parse of a value

        Can be overidden. By default does nothing.

        Args:
            value: Parsed value
            state: State to possibly update

        Returns:
            An optional error
        """
        return None

    def handle(self, args: Sequence[str], state: State) -> Tuple[Sequence[str], Optional[Err]]:
        if args:
            res = self.param.param_type.parse(args[0])
            if isinstance(res, Err):
                return (args[1:], res)
            else:
                assert self.param.name is not None, "Names are assigned after initialization"
                err = self.action(res, state)
                state.instances[self.param.name] = [*state.instances[self.param.name], res]
                return (args[1:], err)
        else:
            return (args, Err.make("Expected value, but no argument present"))


@dataclass(frozen=True)
class CLConfigParam(CLParam[Sequence[Path]]):
    """
    A configuration file parameter handler

    If paths are successfully parsed, it appends configuration files to be parsed to the current
    state.
    """

    def action(self, value: Sequence[Path], state: State) -> Optional[Err]:
        state.config_files_to_process.extend(value)
        return None


@dataclass
class CLPos(CLHandler):
    """
    Handles positional parameters

    Note that this handler has state, namely the positional parameters that are still expected.
    """

    pos: List[Param[Any]]  #: (Mutable) list of positional parameters

    @staticmethod
    def make(seq: Sequence[Param[Any]]) -> CLPos:
        """
        Constructs a positional parameter handler from a sequence of positional parameters

        Args:
            seq: Positional parameters

        Returns:
            Handler
        """
        assert all(
            [p.positional.is_positional() for p in seq]
        ), "All parameters should be positional"
        assert all(
            [not p.positional.should_be_last() for p in seq[:-1]]
        ), "Positional parameters with a variable number of arguments should be last"
        l = list(seq)  # makes a mutable copy
        return CLPos(l)

    def handle(self, args: Sequence[str], state: State) -> Tuple[Sequence[str], Optional[Err]]:
        if not args:
            return (args, None)  # should not happen ,but let's not crash
        if not self.pos:
            return (args[1:], Err.make(f"Unknown argument {args[0]}"))
        p = self.pos[0]
        assert p.name is not None
        res = p.param_type.parse(args[0])
        if isinstance(res, Err):
            return (args[1:], res)
        else:
            state.append(p.name, res)
            if p.positional == Positional.ONCE:
                self.pos = self.pos[1:]
            return (args[1:], None)


@dataclass(frozen=True)
class CLStdHandler(CLHandler):
    """
    The standard command line arguments handler

    It processes arguments one by one. If it recognizes a flag, the corresponding handler is
    called. Otherwise, control is passed to the fallback handler, which by default processes
    positional parameters.
    """

    flags: Mapping[str, CLHandler]
    fallback: CLHandler

    def handle(self, args: Sequence[str], state: State) -> Tuple[Sequence[str], Optional[Err]]:
        if not args:
            return (args, None)
        flag = args[0]
        handler = self.flags.get(flag)
        if handler is not None:
            next_args, err = handler.handle(args[1:], state)
            # TODO: add context
            return next_args, err
        else:
            return self.fallback.handle(args, state)


class KVHandler(ABC):
    """
    Handler for key/value pairs found for example in environment variables or INI files

    Note that the key is not stored/processed in this class.
    """

    @abstractmethod
    def handle(self, value: str, state: State) -> Optional[Err]:
        """
        Processes

        Args:
            value: Value to parse and process
            state: State to update

        Returns:
            An error if an error occurred
        """
        pass


@dataclass(frozen=True)
class KVParam(KVHandler, Generic[T]):
    param: Param[T]

    def action(self, value: T, state: State) -> Optional[Err]:
        """
        A method called on the successful parse of a value

        Can be overridden. By default does nothing.

        Args:
            value: Parsed value
            state: State to possibly update

        Returns:
            An optional error
        """
        return None

    def handle(self, value: str, state: State) -> Optional[Err]:
        res = self.param.param_type.parse(value)
        if isinstance(res, Err):
            return res
        else:
            assert self.param.name is not None
            err = self.action(res, state)
            state.instances[self.param.name] = [*state.instances[self.param.name], res]
            return err


@dataclass(frozen=True)
class KVConfigParam(KVParam[Sequence[Path]]):
    def action(self, value: Sequence[Path], state: State) -> Optional[Err]:
        state.config_files_to_process.extend(value)
        return None


class SpecialAction(Enum):
    """
    Describes special actions that do not correspond to normal execution
    """

    HELP = "help"  #: Display a help message
    VERSION = "version"  #: Print the version number


@dataclass
class State:
    """
    Describes the (mutable) state of a configuration being parsed
    """

    instances: Dict[str, List[Any]]  #: Contains the sequence of values for each parameter
    config_files_to_process: List[Path]  #: Contains a list of configuration files to process
    special_action: Optional[SpecialAction]  #: Contains a special action if flag was encountered

    def append(self, key: str, value: Any) -> None:
        """
        Appends a value to a parameter

        No type checking is performed, be careful.

        Args:
            key: Parameter name
            value: Value to append
        """
        assert key in self.instances, f"{key} is not a Param name"
        self.instances[key] = [*self.instances[key], value]

    @staticmethod
    def make(params: Iterable[Param[Any]]) -> State:
        """
        Creates the initial state, populated with the default values when present

        Args:
            params: Sequence of parameters

        Raises:
            ValueError: If a default value cannot be parsed correctly

        Returns:
            The initial mutable state
        """
        instances: Dict[str, List[Any]] = {}

        for p in params:
            assert p.name is not None, "Arguments have names after initialization"
            if p.default_value is not None:
                res = p.param_type.parse(p.default_value)
                if isinstance(res, Err):
                    raise ValueError(f"Invalid default {p.default_value} for parameter {p.name}")
                instances[p.name] = [res]
            else:
                instances[p.name] = []
        return State(instances, config_files_to_process=[], special_action=None)


@dataclass(frozen=True)
class IniProcessor:
    """
    INI configuration file processor
    """

    section_strict: Mapping[str, bool]  #: Sections and their strictness
    kv_handlers: Mapping[str, KVHandler]  #: Handler for key/value pairs

    def process(self, ini_path: Path, state: State) -> Optional[Err]:
        """
        Processes a configuration file

        Args:
            ini_path: Path to the INI file
            state: Mutable state to update

        Returns:
            An optional error
        """
        errors: List[Err] = []
        if not ini_path.exists():
            return Err1(f"Config file {ini_path} does not exist")
        if not ini_path.is_file():
            return Err1(f"Path {ini_path} is not a file")
        parser = ConfigParser()
        try:
            with open(ini_path, "r") as file:
                parser.read_file(file)
                for section_name in parser.sections():
                    if section_name in self.section_strict:
                        for key, value in parser[section_name].items():
                            err: Optional[Err] = None
                            if key in self.kv_handlers:
                                res = self.kv_handlers[key].handle(value, state)
                                if isinstance(res, Err):
                                    errors.append(res)
                            else:
                                if self.section_strict[section_name]:
                                    errors.append(Err.make(f"Unknown key {key}"))
        except configparser.Error as e:
            errors.append(Err.make(f"Parse error in {ini_path}"))
        except IOError as e:
            errors.append(Err.make(f"IO Error in {ini_path}"))
        if errors:
            return Err.collect_optional(*errors)
        else:
            return None


@dataclass
class ProcessorFactory:
    """
    Describes a processor in construction

    This factory is passed to the different arguments present in the configuration.
    """

    #: List of parameters indexed by their field name
    params_by_name: Dict[str, Param[Any]]

    #: Argument parser to update, used to display help and for the Sphinx documentation
    argument_parser: argparse.ArgumentParser

    #: Argument parser group for commands
    ap_commands: argparse._ArgumentGroup

    #: Argument parser group for required parameters
    ap_required: argparse._ArgumentGroup

    #: Argument parser group for optional parameters
    ap_optional: argparse._ArgumentGroup

    #: Handlers for environment variables
    env_handlers: Dict[str, KVHandler]  # = {}

    #: List of INI sections with their corresponding strictness
    ini_section_strict: Dict[str, bool]

    #: List of handlers for key/value pairs present in INI files
    ini_handlers: Dict[str, KVHandler]  # = {}

    #: List of command line flag handlers
    cl_flag_handlers: Dict[str, CLHandler]  # = {}\

    #: List of positional arguments
    cl_positionals: List[Param[Any]]  # = []

    @staticmethod
    def make(config_type: Type[C]) -> ProcessorFactory:
        """
        Constructs an empty processor factory

        Args:
            config_type: Configuration to process

        Returns:
            A processor factory
        """
        # fill program name from script invocation
        prog = config_type.prog_
        if prog is None:
            prog = sys.argv[0]

        # fill description from class docstring
        description: Optional[str] = config_type.description_
        if description is None:
            description = config_type.__doc__

        argument_parser = argparse.ArgumentParser(
            prog=prog,
            description=description,
            formatter_class=argparse.RawTextHelpFormatter,
            add_help=False,
        )
        argument_parser._action_groups.pop()
        return ProcessorFactory(
            params_by_name={},
            argument_parser=argument_parser,
            ap_commands=argument_parser.add_argument_group("commands"),
            ap_optional=argument_parser.add_argument_group("optional arguments"),
            ap_required=argument_parser.add_argument_group("required arguments"),
            env_handlers={},
            ini_section_strict={s.name: s.strict for s in config_type.ini_sections_()},
            ini_handlers={},
            cl_flag_handlers={},
            cl_positionals=[],
        )


@dataclass(frozen=True)
class Processor(Generic[C]):
    """
    Configuration processor
    """

    #: Configuration to parse
    config_type: Type[C]

    #: Completed argument parser, used only for documentation purposes (CLI and Sphinx)
    argument_parser: argparse.ArgumentParser

    #: Environment variable handlers
    env_handlers: Mapping[str, KVHandler]

    #: INI file processor
    ini_processor: IniProcessor

    #: Command line arguments handler
    cl_handler: CLHandler

    #: Dictionnary of parameters by field name
    params_by_name: Mapping[str, Param[Any]]

    @staticmethod
    def process_fields(config_type: Type[C]) -> Sequence[Arg]:
        """
        Returns a sequence of the arguments present in a configuration, with updated data

        Args:
            config_type: Configuration to process

        Returns:
            Sequence of arguments
        """
        args: List[Arg] = []
        docs: ClassDoc[C] = ClassDoc.make(config_type)
        th = get_type_hints(config_type, include_extras=True)
        for name, typ in th.items():
            arg: Optional[Arg] = None
            if get_origin(typ) is ClassVar:
                a = getattr(config_type, name)
                if isinstance(a, Arg):
                    assert isinstance(a, Expander), "Only commands (Cmd) can be class attributes"
                    arg = a
            if get_origin(typ) is Annotated:
                param = filter_types_single(Param, get_args(typ))
                if param is not None:
                    arg = param
            if arg is not None:
                help_lines = docs[name]
                if help_lines is None:
                    help = ""
                else:
                    help = "\n".join(help_lines)
                arg = arg.updated(name, help, config_type.env_prefix_)
                args.append(arg)
        return args

    @staticmethod
    def make(
        config_type: Type[C],
    ) -> Processor[C]:
        """
        Creates the processor corresponding to a configuration
        """

        pf = ProcessorFactory.make(config_type)
        for arg in Processor.process_fields(config_type):
            arg.update_processor(pf)
        pf.cl_flag_handlers["-h"] = CLSpecialAction(SpecialAction.HELP)
        pf.cl_flag_handlers["--help"] = CLSpecialAction(SpecialAction.HELP)

        return Processor(
            config_type=config_type,
            argument_parser=pf.argument_parser,
            env_handlers=pf.env_handlers,
            ini_processor=IniProcessor(pf.ini_section_strict, pf.ini_handlers),
            cl_handler=CLStdHandler(pf.cl_flag_handlers, CLPos(pf.cl_positionals)),
            params_by_name=pf.params_by_name,
        )

    def process_config(self, state: State) -> Optional[Err]:
        """
        Processes configuration files if such processing was requested by a handler

        Args:
            state: Mutable state to update

        Returns:
            An optional error
        """
        paths = state.config_files_to_process
        state.config_files_to_process = []
        errors: List[Err] = []
        for p in paths:
            err = self.ini_processor.process(p, state)
            if err is not None:
                errors.append(err)  # TODO: add context
        return Err.collect_optional(*errors)

    def process(
        self,
        cwd: Path,
        args: Sequence[str],
        env: Mapping[str, str],
    ) -> Result[Union[C, SpecialAction]]:
        """
        Processes command-line arguments, configuration files and environment variables

        Args:
            cwd: Working directory, used as a base for configuration file relative paths
            args: Command line arguments to parse
            env: Environment variables

        Returns:
            Either a parsed configuration, a special action to execute, or (a list of) errors
        """
        errors: List[Err] = []
        state = State.make(self.params_by_name.values())
        # process environment variables
        for key, value in env.items():
            handler = self.env_handlers.get(key)
            if handler is not None:
                err = handler.handle(value, state)
                if err is not None:
                    errors.append(err)  # TODO: add context
            err = self.process_config(state)
            if err is not None:
                errors.append(err)
        # process command line arguments
        rest_args: Sequence[str] = args
        while rest_args:
            rest_args, err = self.cl_handler.handle(rest_args, state)
            if err is not None:
                errors.append(err)
            err = self.process_config(state)
            if err is not None:
                errors.append(err)

        if state.special_action is not None:
            return state.special_action

        if errors:
            return Err.collect(*errors)
        collected: Dict[str, Any] = {}
        for name, param in self.params_by_name.items():
            instances = state.instances[name]
            res = param.collector.collect(instances)
            if isinstance(res, Err):
                errors.append(res)
            else:
                collected[name] = res
        if errors:
            return Err.collect(*errors)
        return self.config_type(**collected)
