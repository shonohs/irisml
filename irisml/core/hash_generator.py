import copyreg
import dataclasses
import hashlib
import io
import pickle
import torch


def reduce_tensor(tensor):
    return torch.Tensor, (tensor.cpu().numpy(),)


class HashPickler(pickle.Pickler):
    dispatch_table = copyreg.dispatch_table.copy()
    dispatch_table[torch.Tensor] = reduce_tensor


class HashGenerator:
    """Calculate hash for the given object.

    Note that we cannot simply hashlib.sha1(pickle.dumps(obj)) since some of the contents might be cached on remote.
    For containers such as dict and list, we calculate hash for each elements and construct a new container with them and calculate hash recursively.
    """
    @classmethod
    def calculate_hash(cls, value, context=None):
        from .variable import Variable

        def get_hash(value):
            if isinstance(value, dict):
                value = pickle.dumps({k: get_hash(v) for k, v in sorted(value.items())})
            elif isinstance(value, list):
                value = pickle.dumps([get_hash(v) for v in value])
            elif dataclasses.is_dataclass(value):
                value = pickle.dumps({k: get_hash(v) for k, v in sorted(dataclasses.asdict(value).items())})
            elif isinstance(value, Variable):
                return value.get_hash(context)
            else:
                f = io.BytesIO()
                p = HashPickler(f)
                p.dump(value)
                value = f.getbuffer()

            return hashlib.sha1(value).hexdigest()

        return get_hash(value)
