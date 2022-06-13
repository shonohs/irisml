import dataclasses
import sys
import unittest
from typing import Dict, List, Optional
from irisml.core import Context, TaskBase, TaskDescription
from irisml.core.task import Task


class TestTask(unittest.TestCase):
    def test_load_config(self):
        @dataclasses.dataclass
        class ChildConfig:
            int_var: int

        @dataclasses.dataclass
        class Config:
            int_var: int
            str_var: str
            optional_int_var: Optional[int]
            int_list_var: List[int]
            str_dict_var: Dict[str, str]
            nested: ChildConfig
            int_default_var: int = 42

        result = Task._load_config(Config, {'int_var': 12, 'str_var': '12', 'optional_int_var': 24, 'int_list_var': [1, 2, 3], 'str_dict_var': {'k': 'v', 'k2': 'v2'}, 'nested': {'int_var': 123}})
        self.assertEqual(result.nested, ChildConfig(int_var=123))
        self.assertEqual(result.int_var, 12)
        self.assertEqual(result.str_var, '12')
        self.assertEqual(result.optional_int_var, 24)
        self.assertEqual(result.int_list_var, [1, 2, 3])
        self.assertEqual(result.str_dict_var, {'k': 'v', 'k2': 'v2'})
        self.assertEqual(result.int_default_var, 42)

    def test_validate(self):
        class CustomTask:
            class Task(TaskBase):
                @dataclasses.dataclass
                class Outputs:
                    int_value: int

        class EmptyClass:
            pass

        with unittest.mock.patch.dict(sys.modules):
            sys.modules['irisml.tasks.custom_task'] = CustomTask
            task = Task(TaskDescription.from_dict({'task': 'custom_task'}))
            with self.assertRaises(RuntimeError):
                task.load_module()

            CustomTask.Task.Outputs = EmptyClass
            task = Task(TaskDescription.from_dict({'task': 'custom_task'}))
            with self.assertRaises(RuntimeError):
                task.load_module()

    def test_inputs_env(self):
        """Environment variable in inputs should be casted to the expected type."""
        task_description = TaskDescription.from_dict({'task': 'custom_task', 'inputs': {'input0': '$env.ENV_INPUT'}})

        class CustomTask:
            class Task(TaskBase):
                @dataclasses.dataclass
                class Inputs:
                    input0: int

                def execute(self, inputs):
                    if not isinstance(inputs.input0, int):
                        raise RuntimeError(f"Input type is {type(inputs.input0)}")
                    return self.Outputs()

        context = Context({'ENV_INPUT': '12345'})
        with unittest.mock.patch.dict(sys.modules):
            sys.modules['irisml.tasks.custom_task'] = CustomTask
            task = Task(task_description)
            task.load_module()
            task.execute(context)
