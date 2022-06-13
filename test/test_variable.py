import unittest
from unittest.mock import MagicMock
from irisml.core.context import Context
from irisml.core.variable import EnvironmentVariable, OutputVariable, replace_variables


class TestEnvironmentVariable(unittest.TestCase):
    def test_invalid_names(self):
        invalid_names = ['RANDOM_NAME', '$invalid_variable_type.RANDOM_NAME', '$env.NESTED.NAME', '$env.lower_case']
        for name in invalid_names:
            with self.assertRaises(ValueError):
                EnvironmentVariable(name)

    def test_resolve(self):
        context = Context({'CORRECT_VAR': '42'})
        v = EnvironmentVariable('$env.CORRECT_VAR')
        self.assertEqual(v.resolve(context), '42')
        v = EnvironmentVariable('$env.VAR_NOT_FOUND')
        with self.assertRaises(ValueError):
            v.resolve(context)


class TestOutputVariable(unittest.TestCase):
    def test_invalid_names(self):
        invalid_names = ['random_name', '$invalid_variable_type.random_name', '$output.task_name_only', '$output.task_name.UPPER_CASE']
        for name in invalid_names:
            with self.assertRaises(ValueError):
                OutputVariable(name)

    def test_resolve(self):
        context = Context()
        context.add_outputs('task_name', MagicMock(int_output=42, str_output='42'))
        v = OutputVariable('$output.task_name.int_output')
        self.assertEqual(v.resolve(context), 42)
        v = OutputVariable('$output.task_name.str_output')
        self.assertEqual(v.resolve(context), '42')

        with self.assertRaises(ValueError):
            EnvironmentVariable('$output.task_name.no_output').resolve(context)
        with self.assertRaises(ValueError):
            EnvironmentVariable('$output.no_task_name.str_output').resolve(context)


class TestReplaceVariables(unittest.TestCase):
    def test_replace_str(self):
        self.assertIsInstance(replace_variables('$env.ENV_VAR'), EnvironmentVariable)
        self.assertIsInstance(replace_variables('$output.task_name.var'), OutputVariable)

    def test_containers(self):
        self.assertEqual(replace_variables(['$env.ENV_VAR', 42]), [EnvironmentVariable('$env.ENV_VAR'), 42])
        self.assertEqual(replace_variables({'name': '$env.ENV_VAR', 'name2': 42}), {'name': EnvironmentVariable('$env.ENV_VAR'), 'name2': 42})

    def test_invalid_name(self):
        with self.assertRaises(ValueError):
            replace_variables('$new_var')
