import re
from typing import Any, Generic, Sequence, TypeVar, Union

T = TypeVar("T", bound=dict[Any, Any])


def deep_merge(dict1: T, dict2: T) -> T:
    """
    Recursively merge two dictionaries, including nested dictionaries.
    Values from dict2 will override those from dict1 in case of conflicts.
    """
    result = dict1.copy()  # Start with dict1's keys and values
    for key, value in dict2.items():
        # If the value is a dictionary, perform a deep merge
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)  # type: ignore
        else:
            # Otherwise, use the value from dict2
            result[key] = value
    return result  # type: ignore


class InvalidKeyPathError(ValueError):
    def __init__(self, msg: str, extras: dict[str, Any]):
        super().__init__(msg)
        self.extras = extras


_T = TypeVar("_T", bound=dict[str, Any] | list[Any] | None)


def _set_keypath_inner(
    d: _T,
    keys: list[Union[int, str]],
    value: Any,
) -> _T:
    if not keys:
        return value

    root = d
    key = keys[0]

    # Setting by index
    if isinstance(key, int):
        if root is None:
            root = []
        elif isinstance(root, dict):
            # key probably got converted by mistake
            root[f"{key}"] = _set_keypath_inner(root.get(f"{key}", None), keys[1:], value)
            return root
        elif not isinstance(root, list):  # type: ignore
            raise InvalidKeyPathError(f"Cannot set keypath {key} on non-list object", extras={"root": root})

        if key < 0:
            key = max(0, len(root) + key + 1)

        if len(root) <= key:
            root.extend([None for _ in range(key - len(root) + 1)])
        root[key] = _set_keypath_inner(root[key], keys[1:], value)
        return root

    # Setting by key
    if root is None:
        root = {}
    elif not isinstance(root, dict):
        raise InvalidKeyPathError(f"Cannot set keypath '{key}' on non-dict object", extras={"root": root})
    root[key] = _set_keypath_inner(root.get(key, None), keys[1:], value)

    return root


KeyPath = list[str | int]


def split_keys(key_path: str) -> KeyPath:
    def _convert_key(key: str) -> Union[str, int]:
        try:
            return int(key)
        except ValueError:
            return key

    return [_convert_key(k) for k in key_path.split(".")]


def set_at_keypath(
    d: _T,
    key_path: KeyPath,
    value: Any,
) -> _T:
    return _set_keypath_inner(d, key_path, value)


def set_at_keypath_str(
    d: _T,
    key_path: str,
    value: Any,
) -> _T:
    keys = split_keys(key_path)
    return _set_keypath_inner(d, keys, value)


def get_at_keypath_str(d: Any, key_path: str) -> Any:
    return get_at_keypath(d, split_keys(key_path))


def get_at_keypath(d: Any, key_path: KeyPath) -> Any:
    for key in key_path:
        if isinstance(d, dict):
            d = d[key]  # pyright: ignore [reportUnknownMemberType]
        elif isinstance(d, list):
            if not isinstance(key, int):
                raise KeyError(f"Cannot get keypath '{key}' on list object")
            try:
                d = d[key]  # pyright: ignore [reportUnknownMemberType]
            except IndexError:
                raise KeyError(f"Index {key} out of range")
        elif isinstance(key, str):
            try:
                d = getattr(d, key)  # pyright: ignore [reportUnknownArgumentType]
            except AttributeError:
                raise KeyError(f"Cannot get keypath '{key}' on object {type(d)})")  # pyright: ignore [reportUnknownArgumentType]
        else:
            raise KeyError(f"Cannot get keypath '{key}' on non-dict or list object")
    return d


def blacklist_keys(d: Any, replace_with: str, *keys: re.Pattern[str]) -> Any:
    """Recursively remove keys from a dictionary that match any of the provided patterns."""

    def _maybe_replace_value(k: Any, v: Any) -> Any:
        if isinstance(k, str) and any(p.match(k) for p in keys):
            return replace_with
        return _blacklist_keys_inner(v)

    def _blacklist_keys_inner(d: Any) -> Any:
        if isinstance(d, dict):
            return {k: _maybe_replace_value(k, v) for k, v in d.items()}  # pyright: ignore [reportUnknownVariableType]
        if isinstance(d, list):
            return [_blacklist_keys_inner(v) for v in d]  # pyright: ignore [reportUnknownVariableType]
        return d

    return _blacklist_keys_inner(d)


_K1 = TypeVar("_K1")
_K2 = TypeVar("_K2")


class TwoWayDict(Generic[_K1, _K2]):
    def __init__(self, *values: tuple[_K1, _K2]):
        self._forward = {v1: v2 for v1, v2 in values}
        self._backward = {v2: v1 for v1, v2 in values}

    def __getitem__(self, key: _K1) -> _K2:
        return self._forward[key]

    def backward(self, key: _K2) -> _K1:
        return self._backward[key]

    def __setitem__(self, key: _K1, value: _K2):
        self._forward[key] = value
        self._backward[value] = key

    def __contains__(self, key: _K1) -> bool:
        return key in self._forward or key in self._backward

    def in_forward_keys(self, key: _K1) -> bool:
        return key in self._forward


def _delete_at_keypath_in_list(root: list[Any], keys: Sequence[int | str]) -> list[Any]:
    key = keys[0]
    final_key = len(keys) == 1
    if key == "*":
        for i in range(len(root)):
            root[i] = delete_at_keypath(root[i], keys[1:])
        return root
    if not isinstance(key, int):
        try:
            key = int(key)
        except ValueError:
            raise InvalidKeyPathError(f"Cannot delete keypath '{key}' on non-list object", extras={"root": root})
    if final_key:
        try:
            root.pop(key)
        except IndexError:
            pass
        return root
    root[key] = delete_at_keypath(root[key], keys[1:])
    return root


def _delete_at_keypath_in_dict(root: dict[str, Any], keys: Sequence[int | str]) -> dict[str, Any]:
    key = keys[0]
    final_key = len(keys) == 1

    key = str(key)
    if final_key:
        root.pop(key, None)
        return root
    try:
        root[key] = delete_at_keypath(root[key], keys[1:])
    except KeyError:
        pass
    return root


def delete_at_keypath(d: _T, keys: Sequence[int | str]) -> _T:
    if not keys:
        return d
    if not d:
        return d

    if isinstance(d, list):
        return _delete_at_keypath_in_list(d, keys)
    if isinstance(d, dict):  # pyright: ignore [reportUnnecessaryIsInstance]
        return _delete_at_keypath_in_dict(d, keys)

    return d


def exclude_keys(d: dict[str, Any], keys: set[str]) -> dict[str, Any]:
    """Returns a copy of the dictionary without the keys in the set."""
    return {k: v for k, v in d.items() if k not in keys}
