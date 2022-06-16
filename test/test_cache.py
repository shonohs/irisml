import collections
import dataclasses
import pickle
import typing
import unittest
import torch
from irisml.core.cache_manager import CachedOutputs, StorageManager
from irisml.core.hash_generator import HashGenerator
from irisml.core.variable import Variable


class Dummy:
    def __init__(self, t):
        self._t = t


class DummyModule(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.conv = torch.nn.Conv2d(3, 42, 3)

    def forward(self, x):
        return self.conv(x)


class TestHashGenerator(unittest.TestCase):
    def test_objects_without_variable(self):
        self.assertIsNotNone(HashGenerator.calculate_hash('abcde'))
        self.assertIsNotNone(HashGenerator.calculate_hash(123456))
        self.assertIsNotNone(HashGenerator.calculate_hash(123.456))
        self.assertIsNotNone(HashGenerator.calculate_hash(None))
        self.assertIsNotNone(HashGenerator.calculate_hash(True))
        self.assertIsNotNone(HashGenerator.calculate_hash(False))
        self.assertIsNotNone(HashGenerator.calculate_hash([1, 2, 3]))
        self.assertIsNotNone(HashGenerator.calculate_hash([]))
        self.assertIsNotNone(HashGenerator.calculate_hash([[1, 2], [3, 4], []]))
        self.assertIsNotNone(HashGenerator.calculate_hash({'a': 3, 'b': 4}))
        self.assertIsNotNone(HashGenerator.calculate_hash({'a': {'aa': 3}}))

        @dataclasses.dataclass
        class Dummy:
            int_value: int
            float_value: float
            str_value: str
            list_int_value: typing.List[int]

        dummy = Dummy(int_value=3, float_value=3.4, str_value='345', list_int_value=[1, 2, 3])
        self.assertIsNotNone(HashGenerator.calculate_hash(dummy))

    def test_collections(self):
        a = collections.OrderedDict([('0', 12345), ('1', 67890)])
        b = pickle.loads(pickle.dumps(a))
        self._assert_same_hash(a, b)

    def test_stable(self):
        self.assertEqual(HashGenerator.calculate_hash(1), HashGenerator.calculate_hash(1))
        self.assertEqual(HashGenerator.calculate_hash(True), HashGenerator.calculate_hash(True))
        self.assertEqual(HashGenerator.calculate_hash('12345'), HashGenerator.calculate_hash('12345'))
        self.assertEqual(HashGenerator.calculate_hash({'a': 3, 'b': 5}), HashGenerator.calculate_hash({'b': 5, 'a': 3}))

    def test_variables(self):
        variable = Variable('dummy')
        variable.get_hash = lambda x: HashGenerator.calculate_hash(12345)

        self.assertEqual(HashGenerator.calculate_hash(variable), HashGenerator.calculate_hash(12345))
        self.assertEqual(HashGenerator.calculate_hash([variable, 67890]), HashGenerator.calculate_hash([12345, 67890]))

    def test_torch(self):
        a = torch.tensor([1, 2, 3], dtype=float)
        b = torch.tensor([1, 2, 3], dtype=float)
        self.assertEqual(HashGenerator.calculate_hash(a), HashGenerator.calculate_hash(b))
        self.assertEqual(HashGenerator.calculate_hash(pickle.loads(pickle.dumps(a))), HashGenerator.calculate_hash(a))

        a = torch.zeros(10, dtype=float)
        b = torch.zeros(10, dtype=float)
        self.assertEqual(HashGenerator.calculate_hash(a), HashGenerator.calculate_hash(b))

        self.assertNotEqual(HashGenerator.calculate_hash(torch.tensor([2, 3])), HashGenerator.calculate_hash(torch.tensor([1, 2])))

    def test_nn_module(self):
        torch.manual_seed(0)
        a = DummyModule()
        torch.manual_seed(0)
        b = DummyModule()
        self.assertEqual(HashGenerator.calculate_hash(a), HashGenerator.calculate_hash(a))
        self.assertEqual(HashGenerator.calculate_hash(a), HashGenerator.calculate_hash(b))

    def test_nn_sequence(self):
        torch.manual_seed(0)
        a = torch.nn.Sequential(torch.nn.Conv2d(3, 3, 3), torch.nn.Conv2d(3, 3, 3))
        torch.manual_seed(0)
        b = torch.nn.Sequential(torch.nn.Conv2d(3, 3, 3), torch.nn.Conv2d(3, 3, 3))

        self.assertEqual(HashGenerator.calculate_hash(a), HashGenerator.calculate_hash(b))
        self.assertEqual(HashGenerator.calculate_hash(a), HashGenerator.calculate_hash(pickle.loads(pickle.dumps(a))))

    def test_torch_in_class(self):
        dummy_instance = Dummy(torch.tensor([1, 2, 3]))
        dummy_instance2 = Dummy(torch.tensor([1, 2, 3]))

        self.assertEqual(HashGenerator.calculate_hash(dummy_instance), HashGenerator.calculate_hash(dummy_instance2))

    def _assert_same_hash(self, a, b):
        self.assertEqual(HashGenerator.calculate_hash(a), HashGenerator.calculate_hash(b))


class FakeStorageManager(StorageManager):
    def __init__(self, data=None):
        self._data = data or {}

    def get_hash(self, paths):
        data = self._data.get('/'.join(paths))
        return data and data[1]

    def get_contents(self, paths):
        data = self._data.get('/'.join(paths))
        return data and data[0]

    def put_contents(self, paths, contents, hash_value):
        self._data['/'.join(paths)] = (contents, hash_value)


class TestCachedOutputs(unittest.TestCase):
    def test_get_hash(self):
        @dataclasses.dataclass
        class Outputs:
            elem0: int
            elem1: str

        c = CachedOutputs(None, ['base'], Outputs, {'elem0': 'elem0_hash', 'elem1': 'elem1_hash'})
        self.assertEqual(c.get_hash('elem0'), 'elem0_hash')
        self.assertEqual(c.get_hash('elem1'), 'elem1_hash')
        with self.assertRaises(KeyError):
            c.get_hash('unknown')

    def test_get_contents(self):
        @dataclasses.dataclass
        class Outputs:
            elem0: int
            elem1: str

        storage = FakeStorageManager({'base/elem0': (pickle.dumps(12345), 'elem0_hash'), 'base/elem1': (pickle.dumps('12345'), 'elem1_hash')})
        c = CachedOutputs(storage, ['base'], Outputs, {'elem0': 'elem0_hash', 'elem1': 'elem1_hash'})

        self.assertEqual(c.elem0, 12345)
        self.assertEqual(c.elem1, '12345')
