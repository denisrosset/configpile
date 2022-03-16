## v7.5.0 (2022-03-16)

### Feat

- add parameter validation

## v7.4.0 (2022-03-16)

### Feat

- **config**: add support for validator methods

## v7.3.0 (2022-03-16)

### Feat

- **errors**: add errors.{wrap_exceptions, is_value, is_err)

## v7.2.0 (2022-03-16)

### Feat

- reexport configpile.Result

## v7.1.3 (2022-03-16)

### Fix

- **arg**: fix support for Expander flag commands

## v7.1.2 (2022-03-16)

### Fix

- **errors**: separate context lines in error printing

## v7.1.1 (2022-03-16)

### Fix

- **processor**: add context in collector errors too

## v7.1.0 (2022-03-16)

### Feat

- **errors**: add context in error reporting

## v7.0.2 (2022-03-16)

### Fix

- **config**: let argparse handle positional arguments for help display

## v7.0.1 (2022-03-15)

### Fix

- **processor**: fix typo

## v7.0.0 (2022-03-15)

### Feat

- **errors**: renamed collect_optional->collect, added collect_optional that collects a seq of Optional[Err]
- **config**: add post-construction config validation with error reporting

### BREAKING CHANGE

- Renamed collect_optional->collect, collect->collect_non_empty

## v6.1.0 (2022-03-15)

### Feat

- **types**: add ParamType.map/as_sequence_of_one
- add reexport of common identifiers
- **types**: added float parameter type

### Fix

- **processor**: make config file paths relative
- **arg**: correct bug in ParamType.append

## v6.0.0 (2022-03-12)

### Refactor

- major refactoring of the processing back-end

### BREAKING CHANGE

- There are breaking changes but they are too numerous to describe.

## v5.0.1 (2022-03-09)

### Fix

- **config**: enumerate commands in usage information

## v5.0.0 (2022-03-04)

### Refactor

- **config**: INI configuration file parameter is now named "config"
- **config**: removed dead code

### BREAKING CHANGE

- Config.ini_files is renamed to Config.config

## v4.2.1 (2022-03-04)

### Fix

- do not ignore default parameter values anymore

## v4.2.0 (2022-03-04)

### Feat

- **config**: implement help command flag

## v4.1.3 (2022-03-03)

### Fix

- **util**: fix bug in attribute documentation lookup

## v4.1.2 (2022-03-03)

### Fix

- **config**: fix retrieval of argument documentation in parent classes

## v4.1.1 (2022-03-03)

### Fix

- **config**: Fixed the formatter used in usage/help formatting, so that it preserves newlines

## v4.1.0 (2022-03-03)

### Feat

- **config**: better formatting of usage/help when running from CLI

### Fix

- **make-Pylance-type-checker-happy**: Added exceptions and corrected types to avoid Pylance errors. Allows unused "type: ignore" in mypy config to make both tools happy

## v4.0.0 (2022-03-02)

### Refactor

- use static methods for dataclass construction

### BREAKING CHANGE

- Renamed collector.{keep_last, invalid, append} -> collector.Collector.{keep_last, invalid, append}; arg.{append, store} -> arg.Param.{append, store}

## v3.0.0 (2022-03-02)

### Feat

- **types**: added bool_ type

### Refactor

- **types**: changed names of default types to standard Python names, followed by underscore

### BREAKING CHANGE

- types.integer is now types.int_

## v2.1.0 (2022-03-02)

### Feat

- **types**: add aliases for ParamType.choices

## v2.0.0 (2022-03-02)

### Refactor

- introduce new syntax based on typing.Annotated

## v1.0.0 (2022-02-24)

### Refactor

- harmonized terminology for arguments/parameters
- **types**: more descriptive ArgType creation from functions, documentation

### BREAKING CHANGE

- The following classes have been renamed: BaseArg -> Arg, Cmd -> Expander, Arg -> Param, ArgType -> ParamType
- ArgType.from_function is renamed to ArgType.from_function_that_raises

### Feat

- **types**: add case normalization in ArgType.choices[_str]
- **sources**: add support for generic command line flags

## v0.1.0 (2022-02-24)
