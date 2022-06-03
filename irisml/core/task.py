import dataclasses
import importlib
import typing
from .task_base import TaskBase
from .variable import replace_variables


class Task:
    """Represents a task description. It doesn't require actual task modules until load_module() is called."""
    def __init__(self, task_name, inputs: dict, config_dict, name=None):
        """
        Args:
            task_name: Module name of the task
            inputs (dict): Input description
            config_dict (dict): Config description
            name (str): Optional unique name for the task.
        """
        assert task_name.islower()

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

        resolved_inputs = context.resolve(self._inputs)
        inputs = self._task.Inputs(**resolved_inputs)

        if not dry_run:
            outputs = self._task(inputs)
        else:
            outputs = self._task.Outputs()

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
        self.validate()

    def validate(self):
        """Check if the task satisfies the rules."""
        if not self._task:
            raise RuntimeError("load_module() must be called first.")

        if not dataclasses.is_dataclass(self._task.Config):
            raise RuntimeError(f"Config class must be a dataclass. Actual: {type(self._task.Config)}")
        if not dataclasses.is_dataclass(self._task.Inputs):
            raise RuntimeError(f"Inputs class must be a dataclass. Actual: {type(self._task.Inputs)}")
        if not dataclasses.is_dataclass(self._task.Outputs):
            raise RuntimeError(f"Outputs class must be a dataclass. Actual: {type(self._task.Outputs)}")

        for f in dataclasses.fields(self._task.Inputs):
            if dataclasses.is_dataclass(f.type):
                raise RuntimeError(f"Nested input dataclass is not allowed: {f.name}")

        for f in dataclasses.fields(self._task.Outputs):
            if f.default == dataclasses.MISSING and f.default_factory == dataclasses.MISSING:
                raise RuntimeError(f"All output fields must have a default value or a default factory: {f.name}")
            if dataclasses.is_dataclass(f.type):
                raise RuntimeError(f"Nested output dataclass is not allowed: {f.name}")

    @staticmethod
    def _load_config(config_class: dataclasses.dataclass, config_dict):
        """Initialize a config class loaded from the actual task module."""
        assert dataclasses.is_dataclass(config_class)

        def load(type_class, value):
            origin = typing.get_origin(type_class)
            args = typing.get_args(type_class)
            if dataclasses.is_dataclass(type_class):
                assert isinstance(value, dict)
                c = {}
                for field in dataclasses.fields(type_class):
                    if field.name in value:
                        c[field.name] = load(field.type, value[field.name])
                return type_class(**c)
            elif origin is list:
                return [load(args[0], v) for v in value]
            elif origin is dict:
                return {load(args[0], k): load(args[1], v) for k, v in value.items()}
            elif origin is typing.Union:  # Optional[X] is Union[X, NoneType]
                if len(args) == 2 and type(None) in args:
                    expected_type = next(a for a in args if a is not type(None))  # noqa: E721
                    return load(expected_type, value)
                else:
                    raise ValueError(f"Union type is not allowed: {field.type} name: {field.name} value: {value[field.name]}")
            elif origin is None:
                return type_class(value)
            else:
                raise ValueError(f"Config data type is not supported: {type_class} value: {value}")

        return load(config_class, config_dict)

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
