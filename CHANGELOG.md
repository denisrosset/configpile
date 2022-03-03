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
