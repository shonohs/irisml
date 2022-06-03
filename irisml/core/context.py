import dataclasses
import logging
import typing
from .variable import Variable

logger = logging.getLogger(__name__)


class Context:
    def __init__(self, environment_variables: typing.Dict[str, str]):
        self._envs = environment_variables
        self._outputs = {}

    @property
    def envs(self):
        return self._envs

    @property
    def outputs(self):
        return self._outputs

    def add_outputs(self, name, outputs):
        if name in self._outputs:
            logger.warning(f"Duplicated task name: {name}. The outputs are overwritten.")
        self._outputs[name] = outputs

    def resolve(self, value):

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
