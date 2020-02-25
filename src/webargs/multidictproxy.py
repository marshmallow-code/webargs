from collections.abc import Mapping

from webargs.compat import MARSHMALLOW_VERSION_INFO
from webargs.core import missing, is_multiple


class MultiDictProxy(Mapping):
    """
    A proxy object which wraps multidict types along with a matching schema
    Whenever a value is looked up, it is checked against the schema to see if
    there is a matching field where `is_multiple` is True. If there is, then
    the data should be loaded as a list or tuple.

    In all other cases, __getitem__ proxies directly to the input multidict.
    """

    def __init__(self, multidict, schema):
        self.data = multidict
        self.multiple_keys = self._collect_multiple_keys(schema)

    @staticmethod
    def _collect_multiple_keys(schema):
        result = set()
        for name, field in schema.fields.items():
            if not is_multiple(field):
                continue
            if MARSHMALLOW_VERSION_INFO[0] < 3:
                result.add(field.load_from if field.load_from is not None else name)
            else:
                result.add(field.data_key if field.data_key is not None else name)
        return result

    def __getitem__(self, key):
        val = self.data.get(key, missing)
        if val is missing or key not in self.multiple_keys:
            return val
        if hasattr(self.data, "getlist"):
            return self.data.getlist(key)
        if hasattr(self.data, "getall"):
            return self.data.getall(key)
        if isinstance(val, (list, tuple)):
            return val
        if val is None:
            return None
        return [val]

    def __delitem__(self, key):
        del self.data[key]

    def __setitem__(self, key, value):
        self.data[key] = value

    def __getattr__(self, name):
        return getattr(self.data, name)

    def __iter__(self):
        return iter(self.data)

    def __contains__(self, x):
        return x in self.data

    def __len__(self):
        return len(self.data)

    def __eq__(self, other):
        return self.data == other

    def __ne__(self, other):
        return self.data != other
