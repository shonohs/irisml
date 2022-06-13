import copy
import dataclasses
import logging
import typing
from .variable import Variable

logger = logging.getLogger(__name__)


class Context:
    """Manage variables for a single experiment."""
    def __init__(self, environment_variables: typing.Dict[str, str] = None):
        self._envs = copy.deepcopy(environment_variables or {})
        self._outputs = {}

    def add_outputs(self, name: str, outputs: typing.Dict):
        if name in self._outputs:
            logger.warning(f"Duplicated task name: {name}. The outputs are overwritten.")
        self._outputs[name] = outputs

    def get_outputs(self, name: str):
        output_name, *paths = name.split('.')
        if output_name not in self._outputs:
            raise ValueError(f"Output {output_name} is not found.")
        value = self._outputs[output_name]
        for p in paths:
            if not hasattr(value, p):
                raise ValueError(f"Output {output_name} doesn't have path {paths}")
            value = getattr(value, p)
        return value

    def add_environment_variable(self, name: str, value: str):
        self._envs[name] = value

    def get_environment_variable(self, name: str):
        if name not in self._envs:
            raise ValueError(f"Environment variable {name} is not found.")
        return self._envs[name]

    def resolve(self, value):
        """Recursively resolve variables in the given value."""
        if isinstance(value, dict):
            return {k: self.resolve(v) for k, v in value.items()}
        elif dataclasses.is_dataclass(value):
            return type(value)(**{k: self.resolve(v) for k, v in dataclasses.asdict(value).items()})
        elif isinstance(value, list):
            return [self.resolve(v) for v in value]
        elif isinstance(value, Variable):
            return value.resolve(self)
        else:
            return value

    def clone(self):
        return copy.deepcopy(self)
