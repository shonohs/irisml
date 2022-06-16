import dataclasses
from irisml.core.context import Context


class TaskBase:
    """Base class for Task definition.

    Attributes:
        VERSION (str): Task must overwrite this atttribute. The format is "(major).(minor).(patch)".
        CACHE_ENABLED (bool): Set False is Task canno be cached.
    """
    VERSION = '0.0.0'
    CACHE_ENABLED = True

    @dataclasses.dataclass(frozen=True)
    class Config:
        """Configuration for the task. Must be overwritten if the task requires a config"""
        pass

    @dataclasses.dataclass(frozen=True)
    class Inputs:
        """Inputs type. Must be overwritten if the task requires inputs. Nested dataclass is not allowed."""
        pass

    @dataclasses.dataclass(frozen=True)
    class Outputs:
        """Outputs type. Must be overwritten if the task has outputs. Nested dataclass is not allowed."""
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

    def dry_run(self, inputs: Inputs) -> Outputs:
        """This method will be called in dry-run mode. Task can overwrite this method."""
        return self.Outputs()
