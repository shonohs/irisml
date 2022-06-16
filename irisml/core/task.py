import dataclasses
import importlib
import logging
import random
import typing
import torch
from irisml.core import TaskDescription
from .hash_generator import HashGenerator
from .task_base import TaskBase
from .variable import replace_variables, Variable


logger = logging.getLogger(__name__)


class Task:
    """Represents a task. It doesn't require actual task modules until load_module() is called."""
    def __init__(self, description: TaskDescription):
        assert description.task.islower()

        self._task_name = description.task
        self._inputs_dict = replace_variables(description.inputs or {})
        self._config_dict = replace_variables(description.config or {})
        self._name = description.name or self._task_name
        self._task_class = None

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
        if dry_run:
            return self.dry_run(context)

        if not self._task_class:
            raise RuntimeError("load_module() must be called before executing the task.")

        config = self._load_config(self._task_class.Config, self._config_dict)
        inputs = self._load_inputs(self._task_class.Inputs, self._inputs_dict)

        task_hash = HashGenerator.calculate_hash([config, inputs], context)
        if self._task_class.CACHE_ENABLED:
            cached_outputs = context.get_cached_outputs(self._task_name, self._task_class.VERSION, task_hash, self._task_class.Outputs)
            if cached_outputs:
                logger.info(f"[{self._task_name}]: Found cached outputs. Skipping the task.")
                context.add_outputs(self.name, cached_outputs)
                return cached_outputs

        logger.info(f"[{self._task_name}]: Running the task.")
        resolved_config = context.resolve(config)
        resolved_inputs = context.resolve(inputs)

        if self._task_class.CACHE_ENABLED:
            if HashGenerator.calculate_hash(config, context) != HashGenerator.calculate_hash(resolved_config):
                logger.error("Resolved config has different hash.")
            if HashGenerator.calculate_hash(inputs, context) != HashGenerator.calculate_hash(resolved_inputs):
                logger.error("Resolved inputs has different hash.")

        self._reset_random_seed()
        logger.debug(f"Instantiating the task module. config={resolved_config}")
        task = self._task_class(resolved_config, context)
        outputs = task.execute(resolved_inputs)
        if outputs is None:
            logger.warning(f"{self} returned None output.")
            outputs = self._task_class.Outputs()

        if not isinstance(outputs, self._task_class.Outputs):
            raise RuntimeError(f"Task {self._task_name} returned invalid outputs: {outputs}")

        context.add_outputs(self.name, outputs)
        if self._task_class.CACHE_ENABLED:
            context.add_cache_outputs(self._task_name, self._task_class.VERSION, task_hash, outputs)
        return outputs

    def dry_run(self, context):
        """Dry run the task. Task can define its own dry_run() method."""
        if not self._task_class:
            raise RuntimeError("load_module() must be called before executing the task.")

        config = self._load_config(self._task_class.Config, self._config_dict)
        inputs = self._load_inputs(self._task_class.Inputs, self._inputs_dict)

        resolved_config = context.resolve(config)
        resolved_inputs = context.resolve(inputs)

        logger.debug(f"Instantiating the task module. config={resolved_config}")
        task = self._task_class(resolved_config, context)
        outputs = task.dry_run(resolved_inputs)

        if not isinstance(outputs, self._task_class.Outputs):
            raise RuntimeError(f"Task {self._task_name} returned invalid outputs: {outputs}")

        context.add_outputs(self.name, outputs)
        return outputs

    def load_module(self):
        """Load a task module dynamically. If the module was not found, throws a RuntimeError"""
        try:
            task_module = importlib.import_module('irisml.tasks.' + self.task_name)
        except ModuleNotFoundError as e:
            raise RuntimeError(f"Task not found: irisml.tasks.{self.task_name}") from e

        task_class = getattr(task_module, 'Task')
        if not issubclass(task_class, TaskBase):
            raise RuntimeError(f"Failed to load {self.task_name}. Please make sure the Task class inherits the TaskBase class.")
        self._task_class = task_class

        # Verify that the config is loadable.
        self._load_config(task_class.Config, self._config_dict)
        self.validate()

    def validate(self):
        """Check if the task satisfies the rules."""
        if not self._task_class:
            raise RuntimeError("load_module() must be called first.")

        if self._task_class.VERSION == '0.0.0':
            logger.warning(f"Task {self._task_name} is version 0.0.0. Please define VERSION attribute in the Task class..")

        if not dataclasses.is_dataclass(self._task_class.Config):
            raise RuntimeError(f"Config class must be a dataclass. Actual: {type(self._task_class.Config)}")
        if not dataclasses.is_dataclass(self._task_class.Inputs):
            raise RuntimeError(f"Inputs class must be a dataclass. Actual: {type(self._task_class.Inputs)}")
        if not dataclasses.is_dataclass(self._task_class.Outputs):
            raise RuntimeError(f"Outputs class must be a dataclass. Actual: {type(self._task_class.Outputs)}")

        for f in dataclasses.fields(self._task_class.Inputs):
            if dataclasses.is_dataclass(f.type):
                raise RuntimeError(f"Nested input dataclass is not allowed: {f.name}")

        for f in dataclasses.fields(self._task_class.Outputs):
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

                unused_keys = set(value.keys()) - set(c.keys())
                if unused_keys:
                    raise ValueError(f"There are redundant fields: {unused_keys}")
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
                if isinstance(value, Variable):
                    value.expected_type = type_class
                    return value
                return type_class(value)
            else:
                raise ValueError(f"Config data type is not supported: {type_class} value: {value}")

        return load(config_class, config_dict)

    @staticmethod
    def _load_inputs(inputs_class: dataclasses.dataclass, inputs_dict: dict):
        c = {}
        # Inputs doesn't have nested values.
        for field in dataclasses.fields(inputs_class):
            if field.name in inputs_dict:
                if isinstance(inputs_dict[field.name], Variable):
                    inputs_dict[field.name].expected_type = field.type
                c[field.name] = inputs_dict[field.name]
        return inputs_class(**c)

    def _reset_random_seed(self):
        """Reset the random seed.

        To make sure the tasks are deterministic, we reset the random seed every time a task starts.
        """
        torch.manual_seed(42)
        random.seed(42)

    def __str__(self):
        return f"Task {self.task_name} (name: {self.name})"
