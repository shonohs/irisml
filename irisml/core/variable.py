from .cache_manager import CachedOutputs, HashGenerator


def replace_variables(value):
    """Replace a string '$env' and '$outputs' in the given object with Variable instances."""
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
    """Base class for Variables.

    In a task description, a string with '$' prefix is considered a variable.
    Currently we have two variable types: $env and $output. $env is Environment Variables that can be set to Context. $output is output objests from previous tasks.

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
        """Returns the actual value this variable represents."""
        raise NotImplementedError

    def get_hash(self, context):
        """Get hash value for the value that is stored in this Variable."""
        return HashGenerator.calculate_hash(self.resolve(context))


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

    def __str__(self):
        return f"EnvVar({self._name})"


class OutputVariable(Variable):
    """A variable with $output prefix. Outputs from a task."""
    def __init__(self, name):
        super().__init__(name)
        parts = name.split('.')
        if len(parts) != 3 or parts[0] != '$output' or not name.islower():
            raise ValueError(f"Invalid output variable name: {name}")

        self._name = parts[1]
        self._path = parts[2]

    def resolve(self, context):
        outputs = context.get_outputs(self._name)
        if not hasattr(outputs, self._path):
            raise ValueError(f"Output {self._name} doesn't have path {self._path}")
        return getattr(outputs, self._path)

    def get_hash(self, context):
        outputs = context.get_outputs(self._name)
        if isinstance(outputs, CachedOutputs):
            return outputs.get_hash(self._path)

        if not hasattr(outputs, self._path):
            raise ValueError(f"Output {self._name} doesn't have path {self._path}")
        value = getattr(outputs, self._path)
        return HashGenerator.calculate_hash(value, context)

    def __str__(self):
        return f"OutputVar({self._name}.{self._path})"
