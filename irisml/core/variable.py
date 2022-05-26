def variable_from_str(value):
    if value[0] == '$':
        # TODO
        pass
    return value


class Variable:
    def __init__(self, variable_type, name):
        assert variable_type in ['env', 'output']
        self._type = variable_type

    def resolve(self, context):
        raise NotImplementedError


class EnvironmentVariable(Variable):
    def __init__(self, name):
        self._name = name

    def resolve(self, context):
        return context.env[self._name]


class OutputVariable(Variable):
    def __init__(self, name):
        self._name = name

    def resolve(self, context):
        return context.outputs[self._name]
