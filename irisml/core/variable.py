def replace_variables(value):
    if isinstance(value, dict):
        return {k: replace_variables(v) for k, v in value.items()}
    elif isinstance(value, list):
        return [replace_variables(v) for v in value]
    elif isinstance(value, str) and value[0] == '$':
        if value.startswith('$env.'):
            return EnvironmentVariable(value)
        elif value.startswith('$output.'):
            return OutputVariable(value)
        else:
            raise ValueError(f"Unknown variable type: {value}")
    else:
        return value


class Variable:
    """In a task description, a string with '$' prefix is considered a variable.
       This class will be used to resolve such variables.
    """
    def __init__(self, name):
        self._var_str = name
        self._expected_type = str

    @property
    def expected_type(self):
        return self._expected_type

    @expected_type.setter
    def expected_type(self, value):
        self._expected_type = value

    def __eq__(self, other):
        return type(self) is type(other) and self._var_str == other._var_str

    def __hash__(self):
        return hash(self._var_str)

    def resolve(self, context):
        raise NotImplementedError


class EnvironmentVariable(Variable):
    """A variable with $env prefix"""
    def __init__(self, name):
        super().__init__(name)
        parts = name.split('.')
        if len(parts) != 2 or parts[0] != '$env' or not parts[1].isupper():
            raise ValueError(f"Invalid environment variable name: {name}")

        self._name = parts[1]

    def resolve(self, context):
        return self._expected_type(context.get_environment_variable(self._name))


class OutputVariable(Variable):
    """A variable with $output prefix. Outputs from a task."""
    def __init__(self, name):
        super().__init__(name)
        parts = name.split('.')
        if len(parts) <= 2 or parts[0] != '$output' or not name.islower():
            raise ValueError(f"Invalid output variable name: {name}")

        self._name = '.'.join(parts[1:])

    def resolve(self, context):
        return context.get_outputs(self._name)
