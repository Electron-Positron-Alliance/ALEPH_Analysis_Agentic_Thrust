#!/usr/bin/env python3
"""Plot final-result total correlation matrix from CSV exports."""

from __future__ import annotations

import argparse
import csv
import os
import sys
from typing import List

import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "plotting")))
import alephstyle as als


def _summary(name: str) -> str:
    """Default to <run_dir>/summary/<name> from inputs.json rather than a fixed run."""
    try:
        import paths
        return os.path.join(paths.get("run_dir"), "summary", name)
    except Exception:
        return os.path.join("Studies", "PreliminaryResult", "summary", name)


def parse_args():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--corr-csv", default=_summary("corr_total.csv"),
                   help="Path to corr_total.csv (default: run_dir/summary from inputs.json)")
    p.add_argument("--binning-csv", default=_summary("binning.csv"),
                   help="Path to binning.csv (default: run_dir/summary from inputs.json)")
    p.add_argument("--output-pdf", default=_summary("matrix_total_correlation_final.pdf"),
                   help="Output PDF path (default: run_dir/summary from inputs.json)")
    return p.parse_args()


def load_corr_csv(path: str) -> List[List[float]]:
    rows: List[List[float]] = []
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        for row in reader:
            if not row:
                continue
            rows.append([float(x) for x in row])
    if not rows:
        raise ValueError(f"Correlation CSV is empty: {path}")
    n = len(rows[0])
    if any(len(r) != n for r in rows):
        raise ValueError(f"Non-rectangular correlation CSV: {path}")
    if len(rows) != n:
        raise ValueError(f"Correlation CSV must be square, got {len(rows)}x{n}: {path}")
    return rows


def load_edges(path: str) -> List[float]:
    lows: List[float] = []
    highs: List[float] = []
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None or "low" not in reader.fieldnames or "high" not in reader.fieldnames:
            raise ValueError(f"Binning CSV missing required columns 'low' and 'high': {path}")
        for row in reader:
            lows.append(float(row["low"]))
            highs.append(float(row["high"]))
    if not lows:
        raise ValueError(f"Binning CSV is empty: {path}")
    return [lows[0]] + highs


def draw_and_save(corr: List[List[float]], edges: List[float], out_pdf: str):
    n = len(corr)
    if len(edges) != n + 1:
        raise ValueError(f"Edge count mismatch: expected {n + 1}, got {len(edges)}")

    # scale=1.25: a colourbar plus a y label leaves the axes narrower than
    # the header needs at the default canvas width, and the two collide.
    fig, ax = als.figure(aspect=0.85, scale=1.25)
    # Correlation is signed, so a diverging map centred on zero; the previous
    # kBird palette put zero mid-ramp and made sign hard to read.
    mesh = ax.pcolormesh(edges, edges, np.asarray(corr, dtype=float).T,
                         cmap=als.CMAP_DIV, vmin=-1.0, vmax=1.0)
    # Without this the vector renderer leaves white seams between the quads.
    mesh.set_edgecolor("face")
    ax.set_xlim(*als.THRUST_RANGE)
    ax.set_ylim(*als.THRUST_RANGE)
    ax.set_xlabel(als.X["thrust"])
    ax.set_ylabel(als.X["thrust"])
    cb = fig.colorbar(mesh, ax=ax, fraction=0.046, pad=0.03)
    cb.set_label(als.Y["correlation"])
    als.header(ax)
    als.save(fig, out_pdf)


def main():
    args = parse_args()
    als.use()
    corr = load_corr_csv(args.corr_csv)
    edges = load_edges(args.binning_csv)
    draw_and_save(corr, edges, args.output_pdf)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
