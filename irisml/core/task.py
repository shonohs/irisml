import dataclasses
import importlib
from .task_base import TaskBase
from .variable import replace_variables


class Task:
    """Represents a task description. It doesn't require actual task modules until load_module() is called."""
    def __init__(self, task_name, inputs: dict, config_dict, name=None):
        self._task_name = task_name
        self._inputs = inputs
        self._config_dict = config_dict
        self._name = name or self._task_name
        self._task = None

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        self._name = value

    @property
    def task_name(self):
        return self._task_name

    def execute(self, context, dry_run=False):
        if not self._task:
            raise RuntimeError("load_module() must be called before executing the task.")

        inputs = context.resolve(self._inputs)

        if not dry_run:
            outputs = self._task(inputs)
        else:
            outputs = self._task.Outputs()  # TODO

        if not isinstance(outputs, self._task.Outputs):
            raise RuntimeError(f"Task {self._task_name} returned invalid outputs: {outputs}")

        context.add_outputs(self.name, outputs)

    def load_module(self):
        """Load a task module dynamically. If the module was not found, throws a RuntimeError"""
        try:
            task_module = importlib.import_module('irisml.tasks.' + self.task_name)
        except ModuleNotFoundError as e:
            raise RuntimeError(f"Task not found: irisml.tasks.{self.task_name}") from e

        task_class = getattr(task_module, 'Task')
        if not issubclass(task_class, TaskBase):
            raise RuntimeError(f"Failed to load {self.task_name}. Please make sure the Task class inherits the TaskBase class.")

        config = self._load_config(task_class.Config, self._config_dict)
        self._task = task_class(config)

    def _load_config(self, config_class: dataclasses.dataclass, config_dict):
        """Initialize a config class loaded from the actual task module."""
        # TODO
        pass

    @classmethod
    def from_dict(cls, data: dict):
        task_name = data['task']
        name = data.get('name')
        inputs = data.get('inputs', {})
        config = data.get('config', {})

        inputs = replace_variables(inputs)
        config = replace_variables(config)
        return cls(task_name, inputs, config, name=name)

    def __str__(self):
        return f"Task {self.task_name} (name: {self.name})"
