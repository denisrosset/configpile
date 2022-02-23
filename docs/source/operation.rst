Operation principle
===================

ArgType
-------

Parses a string into a value of type T (or an error)


ArgInstance
-----------

Instance of argument use: can be an environment variable, a line in a config section,
an invocation on the command line

Contains the value parsed by ArgType

Remembers where it occurred

Takes care of:

- Interpreting passed string values

Reducer
-------

Takes a sequence of ArgInstances and returns a result of type R (or an error)

Takes care of:

- what if no ArgInstances are there? default value or error?
- what to do with multiple invocations? override, append or error?
