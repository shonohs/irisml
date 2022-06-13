import unittest
from irisml.core.context import Context
from irisml.core.variable import EnvironmentVariable, OutputVariable


class TestContext(unittest.TestCase):
    def test_clone(self):
        context = Context({'env': 'value'})
        new_context = context.clone()
        self.assertEqual(new_context.get_environment_variable('env'), 'value')

        new_context.add_environment_variable('env2', 'value2')
        new_context.add_outputs('out', None)

        with self.assertRaises(ValueError):
            context.get_environment_variable('env2')

        with self.assertRaises(ValueError):
            context.get_outputs('out')

    def test_resolve(self):
        context = Context()
        self.assertEqual(context.resolve(123), 123)
        self.assertEqual(context.resolve('123'), '123')
        self.assertEqual(context.resolve([1, 2, 3]), [1, 2, 3])
        self.assertEqual(context.resolve([1, '2', 3]), [1, '2', 3])

        with self.assertRaises(ValueError):
            context.resolve(EnvironmentVariable('$env.E'))

        context = Context({'E': 'v'})
        self.assertEqual(context.resolve(EnvironmentVariable('$env.E')), 'v')
        self.assertEqual(context.resolve([3, EnvironmentVariable('$env.E')]), [3, 'v'])

        class DummyOutput:
            value = 3

        context.add_outputs('test_out', DummyOutput())
        self.assertEqual(context.resolve([123, OutputVariable('$output.test_out.value')]), [123, 3])
