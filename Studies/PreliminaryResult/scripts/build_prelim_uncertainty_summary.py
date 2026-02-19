#!/usr/bin/env python3
"""Compatibility wrapper for the canonical summary builder in Unfolding/scripts."""

from __future__ import annotations

import os
import runpy
import sys


def main() -> None:
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
    target = os.path.join(repo_root, "Unfolding", "scripts", "build_prelim_uncertainty_summary.py")
    if not os.path.exists(target):
        raise FileNotFoundError(f"Missing canonical summary script: {target}")
    runpy.run_path(target, run_name="__main__")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
