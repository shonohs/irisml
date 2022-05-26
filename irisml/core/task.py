import dataclasses
import importlib
from .task_base import TaskBase
from .variable import Variable


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

    @property
    def task_name(self):
        return self._task_name

    def execute(self, context):
        if not self._task:
            raise RuntimeError("load_module() must be called before executing the task.")

        inputs = {k: v.resolve(context) if isinstance(v, Variable) else v for k, v in self._inputs.items()}
        outputs_dict = self._task(inputs)
        context.add_outputs(self.name, outputs_dict)

    def load_module(self):
        """Load a task module dynamically. If the module was not found, throws a RuntimeError"""
        task_module = importlib.import_module(self.task_name, 'irisml.tasks')
        if not task_module:
            raise RuntimeError(f"Task not found: {self.task_name}")

        task_class = getattr(task_module, 'Task')
        if not isinstance(task_class, TaskBase):
            raise RuntimeError(f"Failed to load {self.task_name}. It's not a valid Task class.")

        config = self.load_config(task_class.Config, self._config_dict)
        self._task = task_class(config)

    def load_config(config_class: dataclasses.dataclass, config_dict):
        """Initialize a config class loaded from the actual task module."""
        pass

    @classmethod
    def from_dict(cls, data: dict):
        task_name = data['name']
        inputs = data.get('inputs', {})
        config = data.get('config', {})

        return cls(task_name, inputs, config)
