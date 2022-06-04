import dataclasses
from irisml.core.context import Context


class TaskBase:
    VERSION = '0.0.0'  # Version number of the task. Each task must overwrite this variable.

    @dataclasses.dataclass(frozen=True)
    class Config:
        """Configuration for the task. Must be overwritten if the task requires a config"""
        pass

    @dataclasses.dataclass(frozen=True)
    class Inputs:
        """Inputs type. Must be overwritten if the task requires inputs."""
        pass

    @dataclasses.dataclass(frozen=True)
    class Outputs:
        """Outputs type. Must be overwritten if the task has outputs."""
        pass

    def __init__(self, config: Config, context: Context):
        self._config = config
        self._context = context

    @property
    def config(self):
        return self._config

    @property
    def context(self):
        return self._context

    def __call__(self, inputs: Inputs) -> Outputs:
        return self.execute(inputs)

    def execute(self, inputs: Inputs) -> Outputs:
        """This method must be overwritten by the task."""
        raise NotImplementedError
