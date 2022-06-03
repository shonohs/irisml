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
    def __init__(self, name):
        super().__init__(name)
        parts = name.split('.')
        if len(parts) != 2 or parts[0] != '$env' or not parts[1].isupper():
            raise ValueError(f"Invalid environment variable name: {name}")

        self._name = parts[1]

    def resolve(self, context):
        if self._name not in context.envs:
            raise ValueError(f"Environment variable {self._name} is not found.")
        return self._expected_type(context.envs[self._name])


class OutputVariable(Variable):
    def __init__(self, name):
        super().__init__(name)
        parts = name.split('.')
        if len(parts) <= 2 or parts[0] != '$output' or not name.islower():
            raise ValueError(f"Invalid output variable name: {name}")

        self._name = parts[1]
        self._path = parts[2:]

    def resolve(self, context):
        if self._name not in context.outputs:
            raise ValueError(f"Task output {self._name} is not found.")

        value = context.outputs[self._name]
        for p in self._path:
            if not hasattr(value, p):
                return ValueError(f"Variable not found: {self._path}")

            value = getattr(value, p)

        return value
