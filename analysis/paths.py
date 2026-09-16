"""
Resolve input paths from inputs.json instead of hardcoding them per script.

Before this existed the same inputs were spelled three different ways -- absolute
machine paths in PlotConfig.py, cwd-relative paths in unfold_config.json (which
resolved to a directory that does not exist in this repo layout), and absolute
defaults in run_thrust_prelim_workflow.py pointing at a pythia8316 example
directory that is gone. inputs.json is now the only place that knows.

Resolution order for a key, first hit wins:
  1. the key's upper-case environment variable  (TEMP_DIR, ISR0_FILE, ...)
  2. the value in inputs.json
Paths get ~ and $ENVVAR expanded, and may reference another key as ${key}.

Point ALEPH_INPUTS at a different JSON file to relocate everything at once.

Usage:
    from paths import get, temp, require
    get("temp_dir")                  # resolved directory
    temp("..._thrust_nominal_t.root")  # file inside temp_dir
    require("raw_data_file")         # same as get(), but errors if missing on disk
"""

from __future__ import annotations

import json
import os
import re

_HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_INPUTS = os.path.join(_HERE, "inputs.json")
_PLACEHOLDER = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}")

_cache: dict | None = None


def _expand(value: str) -> str:
    return os.path.expanduser(os.path.expandvars(value))


def load(inputs_file: str | None = None) -> dict:
    """Load and fully resolve inputs.json (cached)."""
    global _cache
    if _cache is not None and inputs_file is None:
        return _cache
    path = inputs_file or os.environ.get("ALEPH_INPUTS", DEFAULT_INPUTS)
    if not os.path.exists(path):
        raise FileNotFoundError(f"inputs config not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)

    resolved: dict[str, str] = {}

    def _resolve(key: str, seen: tuple[str, ...] = ()) -> str:
        if key in resolved:
            return resolved[key]
        if key in seen:
            raise ValueError(f"circular reference in inputs.json at '{key}'")
        env = os.environ.get(key.upper())
        value = env if env else raw.get(key)
        if value is None:
            raise KeyError(f"unknown input key '{key}' (not in {path}, no ${key.upper()})")
        if not isinstance(value, str):
            raise TypeError(f"input key '{key}' is not a string")
        # Only substitute from the file when the value did not come from the
        # environment -- an explicit override is taken literally.
        if not env:
            value = _PLACEHOLDER.sub(lambda m: _resolve(m.group(1), seen + (key,)), value)
        out = _expand(value)
        resolved[key] = out
        return out

    for k in raw:
        if not k.startswith("_"):
            _resolve(k)
    if inputs_file is None:
        _cache = resolved
    return resolved


def get(key: str) -> str:
    resolved = load()
    if key not in resolved:
        raise KeyError(
            f"unknown input key '{key}'. Known keys: {', '.join(sorted(resolved))}. "
            f"Add it to {os.environ.get('ALEPH_INPUTS', DEFAULT_INPUTS)} "
            f"or export {key.upper()}=<path>."
        )
    return resolved[key]


def require(key: str) -> str:
    """get(), but fail with a useful message when the file/dir is absent."""
    value = get(key)
    if not os.path.exists(value):
        raise FileNotFoundError(
            f"input '{key}' resolves to {value}, which does not exist. "
            f"Fix it in {os.environ.get('ALEPH_INPUTS', DEFAULT_INPUTS)} "
            f"or export {key.upper()}=<path>."
        )
    return value


def temp(filename: str) -> str:
    """Path to a processed ntuple inside temp_dir."""
    return os.path.join(get("temp_dir"), filename)


def substitute(value):
    """Expand ${key} references in an arbitrary config value (str/list/dict)."""
    if isinstance(value, str):
        return _expand(_PLACEHOLDER.sub(lambda m: get(m.group(1)), value))
    if isinstance(value, list):
        return [substitute(v) for v in value]
    if isinstance(value, dict):
        return {k: substitute(v) for k, v in value.items()}
    return value
