"""
JSON serialization for numpy-bearing structures.

Analyzers return dicts full of numpy scalars and arrays, which `json` refuses to
encode. This module is the single place that knows how to coerce them - it
replaces the encoder that used to live in the (now removed) analyzer cache and
the parallel `convert_numpy_types` walker in export_data.

Two entry points, because the two situations are genuinely different:
  * `NumpyEncoder` - streaming straight to a file, no intermediate copy;
  * `to_builtin`   - when the structure must be inspected or reshaped first.
"""

import json
from typing import Any

import numpy as np


class NumpyEncoder(json.JSONEncoder):
    """JSON encoder that understands numpy scalars and arrays."""

    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.bool_):
            return bool(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, (set, frozenset)):
            return sorted(obj)
        return super().default(obj)


def to_builtin(obj: Any) -> Any:
    """
    Recursively convert numpy types to plain Python equivalents.

    Dict *keys* are converted too: numpy integer keys are common (cluster ids
    from a value_counts) and json would reject them.
    """
    if isinstance(obj, dict):
        return {to_builtin(k): to_builtin(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        converted = [to_builtin(i) for i in obj]
        return tuple(converted) if isinstance(obj, tuple) else converted
    if isinstance(obj, np.ndarray):
        return to_builtin(obj.tolist())
    if isinstance(obj, np.integer):
        return int(obj)
    if isinstance(obj, np.floating):
        return float(obj)
    if isinstance(obj, np.bool_):
        return bool(obj)
    if isinstance(obj, np.generic):
        return obj.item()
    return obj


def dump_json(value: Any, path, *, indent: int | None = None) -> int:
    """
    Write JSON to `path` and return the byte size.

    Defaults to no indentation: indentation cost 14 MB on the Camera payload and
    nothing reads these files by eye.
    """
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(value, f, ensure_ascii=False, indent=indent, cls=NumpyEncoder)
    return path.stat().st_size
