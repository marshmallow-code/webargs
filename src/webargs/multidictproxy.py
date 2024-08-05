from __future__ import annotations

import typing
from collections.abc import MutableMapping

import marshmallow as ma


class MultiDictProxy(MutableMapping):
    """
    A proxy object which wraps multidict types along with a matching schema
    Whenever a value is looked up, it is checked against the schema to see if
    there is a matching field where `is_multiple` is True. If there is, then
    the data should be loaded as a list or tuple.

    In all other cases, __getitem__ proxies directly to the input multidict.
    """

    def __init__(
        self,
        multidict: MutableMapping,
        schema: ma.Schema,
        known_multi_fields: tuple[type, ...] = (
            ma.fields.List,
            ma.fields.Tuple,
        ),
    ):
        self.data = multidict
        self.known_multi_fields = known_multi_fields
        self.multiple_keys = self._collect_multiple_keys(schema)

    def _is_multiple(self, field: ma.fields.Field) -> bool:
        """Return whether or not `field` handles repeated/multi-value arguments."""
        # fields which set `is_multiple = True/False` will have the value selected,
        # otherwise, we check for explicit criteria
        is_multiple_attr = getattr(field, "is_multiple", None)
        if is_multiple_attr is not None:
            return is_multiple_attr
        return isinstance(field, self.known_multi_fields)

    def _collect_multiple_keys(self, schema: ma.Schema) -> set[str]:
        result = set()
        for name, field in schema.fields.items():
            if not self._is_multiple(field):
                continue
            result.add(field.data_key if field.data_key is not None else name)
        return result

    def __getitem__(self, key: str) -> typing.Any:
        val = self.data.get(key, ma.missing)
        if val is ma.missing or key not in self.multiple_keys:
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

    def __str__(self) -> str:  # str(proxy) proxies to str(proxy.data)
        return str(self.data)

    def __repr__(self) -> str:
        return (
            f"MultiDictProxy(data={self.data!r}, multiple_keys={self.multiple_keys!r})"
        )

    def __delitem__(self, key: str) -> None:
        del self.data[key]

    def __setitem__(self, key: str, value: typing.Any) -> None:
        self.data[key] = value

    def __getattr__(self, name: str) -> typing.Any:
        return getattr(self.data, name)

    def __iter__(self) -> typing.Iterator[str]:
        for x in iter(self.data):
            # special case for header dicts which produce an iterator of tuples
            # instead of an iterator of strings
            if isinstance(x, tuple):
                yield x[0]
            else:
                yield x

    def __contains__(self, x: object) -> bool:
        return x in self.data

    def __len__(self) -> int:
        return len(self.data)

    def __eq__(self, other: object) -> bool:
        return self.data == other

    def __ne__(self, other: object) -> bool:
        return self.data != other
