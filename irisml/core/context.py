import logging
from .variable import Variable

logger = logging.getLogger(__name__)


class Context:
    def __init__(self, environment_variables: dict):
        self._envs = environment_variables
        self._outputs = {}

    def add_outputs(self, name, outputs_dict):
        if name in self._outputs:
            logger.warning(f"Duplicated task name: {name}. The outputs are overwritten.")
        self._outputs[name] = outputs_dict

    def resolve_variable(self, value):
        if isinstance(value, Variable):
            return value.resolve(self)

        return value
