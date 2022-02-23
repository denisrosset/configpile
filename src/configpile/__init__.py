from __future__ import annotations

__version__ = "0.0.1"

# @dataclass(frozen=True)
# class Param(Generic[T, R]):
#     """
#     Base class for configuration parameters
#     """

#     #: Function that parses a string into a value
#     #:
#     #: Can raise :class:`argparse.ArgumentError`
#
# e: Callable[[str], T]
#     help: str  #: Description
#     short_form: Optional[str]  #: Short form, should be a hyphen followed by a letter
#     in_file: bool  #: Whether this parameter can be set in config files
#     in_env: bool  #: Whether this parameter can be set using env. variables

#     def __post_init__(self):
#         assert self.__class__ != Param, "Cannot instantiate Param"
#         assert (self.short_from is None) or (
#             re.fullmatch(short_form_regex, self.short_form)
#         ), "Short parameter form should be hyphen and single letter"

#     def argparse_flags(self, dest: str) -> Sequence[str]:
#         """
#         Returns the flags to pass to :meth:`argparse.ArgumentParser.add_argument`

#         Args:
#             dest: Destination Python identifier
#         """
#         long_option = ParamName(dest).long_option_name()
#         flags = [long_option]
#         if self.short_form is not None:
#             flags.append(self.short_form)
#         return flags

#     def get(self, parsed: Mapping[str, Any], dest: str) -> R:
#         raise NotImplementedError


# class Configuration:
#     """
#     Description of the parameters that configure the execution of a script
#     """

#     @classmethod
#     def params_(cls, t: Type[ParamT]) -> Sequence[Tuple[str, ParamT]]:
#         return [
#             (k, v)
#             for (k, v) in cls.__dict__.items()
#             if not k.endswith("_") and ((t is None) or isinstance(v, t))
#         ]

#     @classmethod
#     def value_params_(cls) -> Mapping[str, ValueParam]:
#         return {k: v for (k, v) in cls.params_(ValueParam)}

#     @classmethod
#     def pos_params_(cls) -> Sequence[Tuple[str, PosParam]]:
#         return [(k, v) for (k, v) in cls.params_(PosParam)]

#     @classmethod
#     def config_params_(cls) -> Mapping[str, ConfigParam]:
#         return {k: v for (k, v) in cls.params_(ConfigParam)}

#     @classmethod
#     def get_parser_(cls) -> ArgumentParser:
#         p = ArgumentParser(
#             prog=cls.prog_,
#             description=cls.description_,
#             epilog=cls.epilog_,
#             allow_abbrev=cls.allow_abbrev_,
#         )
#         # add positional parameters
#         # for (k, v) in cls.pos_params_():
#         #     name = ParamName(k)
#         #     flags = [ParamName(k).long_option_name()]
#         #     if v.short_form is not None:
#         #         flags.append(v.short_form)
#         #         if nargs is None:
#         #             p.add_argument(*flags, help=v.help)
#         #         else:
#         #             p.add_argument(*flags, nargs=nargs, help=v.help)
#         for (k, v) in cls.value_params_().items():
#             kw_args: Dict[str, str] = {}
#             if v.choices is not None:
#                 kw_args["choices"] = v.choices
#                 p.add_argument(
#                     *v.argparse_flags(),
#                     dest=k,
#                     help=v.help,
#                     default=v.default,
#                     **kw_args,
#                 )
#         return p


# T = TypeVar("T")  #: Parsed type
# R = TypeVar("R")  #: Returned type

# short_form_regex = r"-[A-Za-z]"


# @dataclass(frozen=True)
# class Param(Generic[T, R]):
#     """
#     Base class for configuration parameters
#     """

#     #: Function that parses a string into a value
#     #:
#     #: Can raise :class:`argparse.ArgumentError`
#
# e: Callable[[str], T]
#     help: str  #: Description
#     short_form: Optional[str]  #: Short form, should be a hyphen followed by a letter
#     in_file: bool  #: Whether this parameter can be set in config files
#     in_env: bool  #: Whether this parameter can be set using env. variables

#     def __post_init__(self):
#         assert self.__class__ != Param, "Cannot instantiate Param"
#         assert (self.short_from is None) or (
#             re.fullmatch(short_form_regex, self.short_form)
#         ), "Short parameter form should be hyphen and single letter"

#     def argparse_flags(self, dest: str) -> Sequence[str]:
#         """
#         Returns the flags to pass to :meth:`argparse.ArgumentParser.add_argument`

#         Args:
#             dest: Destination Python identifier
#         """
#         long_option = ParamName(dest).long_option_name()
#         flags = [long_option]
#         if self.short_form is not None:
#             flags.append(self.short_form)
#         return flags

#     def get(self, parsed: Mapping[str, Any], dest: str) -> R:
#         raise NotImplementedError


# @dataclass(frozen=True)
# class ValueParam(Param[T, T]):
#     """
#     Parameter describing an option
#     """

#     default: str  #: Default value
#     choices: Optional[Sequence[str]]  #: If not None, list of valid values

#     def get(self, parsed: Mapping[str, Any], dest: str) -> T:
#         return self.type(parsed[dest])


# def value_param(
#     typ e: Callable[[str], T],
#     default: str,
#     help: str,
#     *,
#     short_form: Optional[str] = None,
#     in_file: bool = True,
#     in_env: bool = False,
#     choices: Optional[Sequence[str]],
# ) -> ValueParam[T]:
#     """
#     Constructs a value parameter

#     Args:
#         ty pe: Function that parses a str into a value
#         help: Description of the parameter
#         default: Parameter default value
#         choices: Set of strings from which the parameter value must be taken
#         short_form: Short flag form (hyphen+letter)
#         in_file: Whether the parameter can be set in a configuration file
#         in_env: Whether the parameter can be set in an environment variable

#     Returns:
#         The constructed parameter
#     """
#     return ValueParam(
#         type,
#         help,
#         short_form=short_form,
#         in_file=in_file,
#         in_env=in_env,
#         default=default,
#         choices=choices,
#     )


# @dataclass(frozen=True)
# class ConfigParam(Param[Sequence[Path], Sequence[Path]]):
#     """Parameter that appends configuration files"""

#     def __post_init__(self):
#         assert not self.in_file
#         super().__post_init__()

#     def get(self, parsed: Mapping[str, Any], dest: str) -> Sequence[Path]:
#         options: Sequence[str] = parsed[dest]
#         t: Callable[[str], Sequence[Path]] = self.type  # type: ignore
#         return [v for opt in options for v in t(opt)]


# def _config_param_type(s: str) -> Sequence[Path]:
#     return [Path(x.strip()) for x in s.split(",") if x.strip()]


# def config_param(
#     help: str = """
# Configuration file(s), separated by commas, multiple uses of this argument possible
# """,
#     *,
#     short_form: Optional[str] = None,
#     in_env: bool = True,
# ) -> ConfigParam:
#     """
#     Constructs a configuration file parameter

#     Args:
#         help: Description of the parameter
#         short_form: Short flag form (hyphen+letter)
#         in_env: Whether the parameter can be set in an environment variable

#     Returns:
#         The constructed parameter
#     """
#     return ConfigParam(
#         _config_param_type, help, short_form=short_form, in_file=False, in_env=in_env  # type: ignore
#     )


# @dataclass(frozen=True)
# class PosParam(Param[T, R]):
#     """
#     Describes positional parameters
#     """

#     def __post_init__(self):
#         super().__post_init__()
#         assert self.__class__ != Param, "Cannot instantiate PosParam"

#     def argparse_flags(self, dest: str) -> Sequence[str]:
#         return [dest]  # special case: those parameters do not have flags


# @dataclass(frozen=True)
# class PosParam1(PosParam[T, T]):
#     """
#     Describes a positional parameter that contains a single value
#     """

#     def get(self, parsed: Mapping[str, Any], dest: str) -> T:
#         return self.type(parsed[dest])


# def pos_param_1(type: Callable[[str], T], help: str) -> PosParam1[T]:
#     """
#     Constructs a positional parameter that takes a single value

#     Args:
#         ty pe: Function that parses a str into a value
#         help: Description of the parameter

#     Returns:
#         The constructed parameter
#     """
#     return PosParam1(type, help, short_form=None, in_file=False, in_env=False)


# @dataclass(frozen=True)
# class PosParamN(PosParam[T, Sequence[T]]):
#     """
#     Describes a positional parameter that contains multiple values
#     """

#     pass

#     def get(self, parsed: Mapping[str, Any], dest: str) -> Sequence[T]:
#         res: List[T] = []
#         values: Sequence[str] = parsed[dest]
#         t: Callable[[str], T] = self.type
#         for v in values:
#             res.append(t(v))
#         return res


# def pos_param_n(type: Callable[[str], T], help: str) -> PosParamN[T]:
#     """
#     Constructs a position parameter that takes multiple values

#     Args:
#         type1: Function that parses a str to a single value
#         help: Description of the parameter

#     Returns:
#         The constructed parameter
#     """
#     return PosParamN(type, help, short_form=None, in_file=False, in_env=False)


# ParamT = TypeVar("ParamT", bound=Param)


# class Test(Configuration):

#     env_prefix_ = "TEST"

#     dace_file = value_param(Path, "", "Relative path to the DACE CSV file")
#     instrument = value_param(str, "", "Instrument name if DACE file is not provided")
#     input_folder = value_param(
#         Path, "", "Relative path to the folder containing input data files"
#     )
#     sort_by_filename = value_param(
#         bool, "False",
#     )
#     info_file = value_param(Path, "", )

#     # a = ValueParam[str].make(
#     #    str, "", "Test parameter", in_file=True, in_env=False
#     # )


# # @dataclass(frozen=True)
# # class ConfigFileParameter(Parameter[Sequence[Path]]):
# #     """
# #     Parameter that includes configuration files
# #     """

# #     @staticmethod
# #     def make(
# #         dest: str, help: str = "Configuration file(s), can be separated by commas", in_env: bool=True,
# #     ):
# #         pass


# # @dataclass(frozen=True)
# # class PositionalParam1(Parameter[T], Generic[T]):
# #     pass


# # @dataclass(frozen=True)
# # class PositionalParamN(Parameter[Sequence[T]], Generic[T]):
# #     pass


# # @dataclass(frozen=True)
# # class OptionParameter(Parameter):
# #     pass


# # @staticmethod
# # def from_action(
# #     action: Action,
# #     env_var_name: Optional[str] = None,
# #     config_file_action: bool = False,
# # ) -> Parameter:
# #     """
# #     Creates an enriched action from a :class:`argparse.Action`
# #
# #     Args:
# #         action: Action to extract the information from
# #         env_var_name: Environment variable name
# #         config_file_action: Whether this is a "configuration file" action
# #     Returns:
# #         The corresponding enriched action
# #     """
# #     Parameter(action=action)

# # def __init__(self, action: Action, env_var_name: Optional[str] = None) -> None:
# #     self.action: Action = action
# #     self.dest: str = action.dest
# #     self.config_var_name: Optional[str] = self.extract_config_var_name(action)
# #     self.env_var_name: Optional[str] = env_var_name
# #
# # def __repr__(self):
# #     return f"ActionExtraData(dest={self.dest}, env_var_name={self.env_var_name}, action={self.action})"
# #

# #
# #


# # @dataclass
# # class ConfigSection(object):
# #     """
# #     Description of a configuration section to read in a configuration file
# #
# #     Attributes:
# #         name: Name of the section header
# #         strict: Whether the parsing is strict, i.e. all keys in the configuration file must correspond to
# #                 parameters (strict=True), or whether to ignore extra keys (strict=False)
# #     """
# #     name: str
# #     strict: bool = False
# #
# #
# # class ParametersParser(ArgumentParser):
# #     """
# #     Drop-in replacement for `argparse.ArgumentParser` that supports for environment variables and configuration files
# #
# #     Inspired by `<https://github.com/bw2/ConfigArgParse>`_ but allows for the provision of multiple configuration files
# #     that override each other parameters.
# #
# #     Note that relative configuration file paths are resolved according to the current directory when calling the
# #     `.parse_args` method.
# #
# #     The constructed parser is single-use.
# #
# #     Attributes:
# #         used: Whether the parser has been used already
# #         enriched_actions: List of `.EnrichedAction` instances, excluding the configuration action
# #         invalid_configfile_actions: Actions that cannot be used as config. file keys, including the conf. action itself
# #         config_common_section: Name of the common parameter section in configuration files
# #         config_sections: Sections to read in the configuration file
# #         config_parser: First parser called to extract configuration file paths
# #         config_action: Enriched action that appends configuration file paths (with the action in the config_parser)
# #     """
# #
# #     def __init__(self, *args, config_common_section: str = 'common',
# #                  config_sections: Sequence[str] = [], **kwargs):
# #         """
# #         Constructs a ParametersParser
# #
# #         Args:
# #             config_sections: Sections of the configuration file to use
# #             strict_config_sections: Sections of the config. file for which all keys should correspond to parameters
# #         """
# #         self.used = False
# #         self.enriched_actions: List[EnrichedAction] = []
# #         self.invalid_configfile_actions: List[Action] = []
# #         self.config_common_section: str = config_common_section
# #         self.config_sections: Sequence[ConfigSection] = [ConfigSection(name, name in strict_config_sections)
# #                                                          for name in (relaxed_config_sections + strict_config_sections)]
# #         self.config_parser: ArgumentParser = ArgumentParser()
# #         self.config_action: Optional[EnrichedAction] = None
# #         super().__init__(*args, **kwargs)
# #
# #     def add_config_argument(self, *args, env_var_name: Optional[str] = None, **kwargs) -> Action:
# #         """
# #         Adds a parameter that describes a configuration file input
# #
# #         This method has the same calling convention as `argparse.ArgumentParser.add_argument`.
# #
# #         This method can only be called once, must have 'action' set to 'append', must have 'type' set to 'pathlib.Path'
# #
# #         Args:
# #             env_var_name: Name of the environment variable containing the default configuration file
# #
# #         Returns:
# #             The construction configuration file action
# #         """
# #         assert self.config_action is None, 'The method add_config_argument must be called at parser construction'
# #
# #         # Add the configuration action to the configuration parser
# #         config_action = self.config_parser.add_argument(*args, **kwargs)  # it is the only option of the config. parser
# #         self.config_action = EnrichedAction(config_action, env_var_name)
# #
# #         # Add the configuration action to this parser, so that the option shows in the documentation/help
# #         action: Action = super().add_argument(*args, **kwargs)
# #         assert isinstance(action, argparse._AppendAction), \
# #             "For the configuration file option, the action must be 'append'"
# #         assert action.type == Path, "For configuration file option, the type of must pathlib.Path"
# #         self.invalid_configfile_actions.append(action)
# #
# #         return action
# #
# #     def add_argument(self, *args, env_var_name: Optional[str] = None, **kwargs) -> Action:
# #         """
# #         Adds a parameter to the argument parser
# #
# #         Args:
# #         env_var_name: Name of the environment variable containing the default configuration file
# #
# #         Returns:
# #             The constructed action
# #         """
# #         action: Action = super().add_argument(*args, **kwargs)
# #         if EnrichedAction.is_store_like_action(action):
# #             enriched_action = EnrichedAction(action, env_var_name)
# #             self.enriched_actions.append(enriched_action)
# #         else:
# #             self.invalid_configfile_actions.append(action)
# #         return action
# #
# #     @staticmethod
# #     def get_env_variable(action: EnrichedAction, env: Mapping[str, str]) -> Optional[str]:
# #         """
# #         Returns the value of the given action/parameter if it is present in the environment
# #
# #         Args:
# #             action: Enriched action to find the value of
# #             env: Environment variables
# #
# #         Returns:
# #             The parameter value if present, None is not present
# #         """
# #         env_var_name = action.env_var_name
# #         if env_var_name is not None:
# #             if env_var_name in env:
# #                 return env[env_var_name]
# #         return None
# #
# #     @staticmethod
# #     def explode_config_filenames(filenames: str) -> Sequence[Path]:
# #         return list([Path(name.strip()) for name in filenames.split(',') if name.strip()])
# #
# #     def get_config_files(self, args: Sequence[str], env: Mapping[str, str]) -> List[Path]:
# #         """
# #         Parses the environment and the command-line arguments to retrieve the list of configuration files to use
# #
# #         Args:
# #             args: Command-line arguments
# #             env: Environment variables
# #
# #         Returns:
# #             Path to configuration files
# #         """
# #         config_action = self.config_action
# #         assert config_action is not None, 'A ParametersParser must define exactly one config argument'
# #
# #         config_files: List[Path] = []
# #
# #         config_env = self.get_env_variable(config_action, env)
# #
# #         if config_env is not None:
# #             new_files: List[Path] = list(self.explode_config_filenames(config_env))
# #             if new_files:
# #                 logging.info('Using configuration files from the environment: ' + ','.join(map(str, new_files)))
# #             config_files.extend(new_files)
# #
# #         config_args, discard = self.config_parser.parse_known_args(args)
# #         config_cmdline_args = getattr(config_args, config_action.dest)
# #         if config_cmdline_args:
# #             new_files = []
# #             for filenames in config_cmdline_args:
# #                 new_files.extend(self.explode_config_filenames(filenames))
# #             if new_files:
# #                 logging.info('Using configuration files from the command-line: ' + ','.join(map(str, new_files)))
# #             config_files.extend(new_files)
# #
# #         return config_files
# #
# #     def populate_from_env_variables(self, env: Mapping[str, str]):
# #         """
# #         Populate parameter values from environment variables
# #
# #         Args:
# #             env: Environment variables
# #         """
# #         env_var_names: Dict[str, Action] = dict([(ea.env_var_name, ea.action) for ea in self.enriched_actions
# #                                                  if ea.env_var_name is not None])
# #         for name, value in env.items():
# #             if name in env_var_names:
# #                 action = env_var_names[name]
# #                 logging.info(f'Set {action.dest} to {value} from environment variable {name}')
# #                 action.default = value
# #
# #     def populate_from_config_section(self, section: SectionProxy, *, strict: bool):
# #         """
# #         Populate parameter values from section of configuration file
# #
# #         Args:
# #             section: Parsed configuration section
# #             strict: Whether to parse in strict mode
# #         """
# #         invalid_keys: Set[str] = \
# #             set([name for name in [EnrichedAction.extract_config_var_name(a) for a in self.invalid_configfile_actions]
# #                  if name is not None])
# #         config_option_names: Dict[str, Action] = dict([(ea.config_var_name, ea.action) for ea in self.enriched_actions
# #                                                        if ea.config_var_name is not None])
# #         for key, value in section.items():
# #             assert key not in invalid_keys, \
# #                 f"Key {key} is an option but not a valid configuration file key"
# #             if key in config_option_names:
# #                 logging.info(f'Set {key} to {value} from configuration file')
# #                 action = config_option_names[key]
# #                 action.default = value
# #             else:
# #                 assert not strict, f"Key {key} is unknown and the section {section.name} is parsed in strict mode"
# #
# #     def parse_all(self, args: Optional[Sequence[str]] = None, env: Optional[Mapping[str, str]] = None,
# #                   namespace: Optional[Namespace] = None) -> Namespace:
# #         """
# #         Parses environment variables, configuration files and command-line arguments
# #
# #         Args:
# #             args: Command line arguments
# #             env: Environment variables
# #             namespace: Optional namespace to populate
# #
# #         Returns:
# #             The populated namespace
# #         """
# #         assert not self.used, 'A ParametersParser can only be used once'
# #         self.used = True
# #         if args is None:
# #             args = sys.argv[1:]  # args default to the system args
# #         if env is None:
# #             env = os.environ
# #         config_files = self.get_config_files(args, env)
# #         self.populate_from_env_variables(env)
# #         for config_filename in config_files:
# #             cp = ConfigParser()
# #             with open(config_filename, 'r') as file:
# #                 cp.read_file(file, str(config_filename))
# #             try:
# #                 if self.config_common_section in cp.sections():
# #                     self.populate_from_config_section(cp[self.config_common_section], strict=False)
# #                 for section in self.config_sections:
# #                     strict = section.strict
# #                     section_name = section.name
# #                     if section_name in cp.sections():
# #                         self.populate_from_config_section(cp[section_name], strict=strict)
# #             except Exception as exc:
# #                 raise Exception(f"Configuration file {config_filename} could not be properly parsed") from exc
# #         return super().parse_args(args, namespace=namespace)
# #
# #
