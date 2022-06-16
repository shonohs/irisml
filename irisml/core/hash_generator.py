import copyreg
import dataclasses
import hashlib
import io
import json
import pickle
import torch


def _reduce_tensor(tensor):
    """__reduce__ for torch.Tensor.

    Since pickle.dumps(tensor) is not deterministic, we convert torch.Tensor to numpy array.
    """
    return torch.Tensor, (tensor.cpu().numpy(),)


class HashPickler(pickle.Pickler):
    """Pickler to calculate hash.

    Note that it's not guaranteed that the loads(dumps(obj)) will create the same object.
    """
    dispatch_table = copyreg.dispatch_table.copy()
    dispatch_table[torch.Tensor] = _reduce_tensor


class HashGenerator:
    """Calculate hash for the given object.

    Note that we cannot simply hashlib.sha1(pickle.dumps(obj)) since some of the contents might be cached on remote. For nested objects, we calculate hash for each child element recursively.
    """
    @classmethod
    def calculate_hash(cls, value, context=None):
        from .variable import Variable

        def get_hash(value):
            if isinstance(value, dict):
                value = json.dumps({k: get_hash(v) for k, v in sorted(value.items())}).encode('utf-8')
            elif isinstance(value, list):
                value = json.dumps([get_hash(v) for v in value]).encode('utf-8')
            elif dataclasses.is_dataclass(value):
                value = json.dumps({k: get_hash(v) for k, v in sorted(dataclasses.asdict(value).items())}).encode('utf-8')
            elif isinstance(value, Variable):
                return value.get_hash(context)
            elif hasattr(value, '__getstate__'):
                return get_hash(value.__getstate__())
            else:
                f = io.BytesIO()
                p = HashPickler(f)
                p.dump(value)
                value = f.getbuffer()

            return hashlib.sha1(value).hexdigest()

        return get_hash(value)
