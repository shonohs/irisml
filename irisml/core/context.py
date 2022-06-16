import copy
import dataclasses
import logging
import typing
from .cache_manager import CachedOutputs
from .variable import Variable

logger = logging.getLogger(__name__)


class Context:
    """Manage variables for a single experiment."""
    def __init__(self, environment_variables: typing.Dict[str, str] = None, cache_manager=None):
        self._envs = copy.deepcopy(environment_variables or {})
        self._cache_manager = cache_manager
        self._outputs = {}

    def add_outputs(self, name: str, outputs: typing.Union[dataclasses.dataclass, CachedOutputs]):
        """Add Task outputs to the context so that subsequent Tasks can consume them.

        Args:
            name (str): the name of the task.
            outputs (Outputs or CachedOutputs instance): the outputs of the task.
        """
        if name in self._outputs:
            logger.warning(f"Duplicated task name: {name}. The outputs are overwritten.")
        self._outputs[name] = outputs

    def get_outputs(self, output_name: str):
        """Get the outputs of previous tasks.
        Args:
            name (str): the name of the task
        Returns:
            Outputs dataclass. If the task had been skipped, returns CachedOutputs.
        """
        if output_name not in self._outputs:
            raise ValueError(f"Output {output_name} is not found.")
        return self._outputs[output_name]

    def add_environment_variable(self, name: str, value: str):
        self._envs[name] = value

    def get_environment_variable(self, name: str):
        if name not in self._envs:
            raise ValueError(f"Environment variable {name} is not found.")
        return self._envs[name]

    def resolve(self, value):
        """Recursively replace Variables with actual value.

        Supported containers are:
            - Dict
            - List
            - dataclasses.dataclass
        """
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

    def get_cached_outputs(self, task_name, task_version, task_hash: str, outputs_class: dataclasses.dataclass) -> typing.Optional[CachedOutputs]:
        """Try to get cached outputs for the given task

        Args:
            task_name (str): Task name
            task_version (str): Task version
            config (Task.Config): Task Config dataclass instance. It can contain Variables.
            inputs (Task.Inputs): Task Inputs dataclass instance. It can contain Variables.

        Returns:
            CachedOutput instance if there is a cache. If not, returns None.
        """
        if not self._cache_manager:
            return None

        logger.debug(f"Trying to get cache for Task {task_name} version {task_version}. Hash: {task_hash}")
        return self._cache_manager.get_cache(task_name, task_version, task_hash, outputs_class)

    def add_cache_outputs(self, task_name, task_version, task_hash: str, outputs):
        """Save the task outputs to the cache storage."""
        if self._cache_manager:
            logger.debug(f"Uploading cache for Task {task_name} version {task_version}. Hash: {task_hash}")
            self._cache_manager.upload_cache(task_name, task_version, task_hash, outputs)

    def clone(self):
        return copy.deepcopy(self)
