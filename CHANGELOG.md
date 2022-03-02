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
