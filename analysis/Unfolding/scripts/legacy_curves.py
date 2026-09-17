#!/usr/bin/env python3
"""
Legacy OmniFold and IBU thrust curves from the unfold-ee-logtau results.

Extracted from build_prelim_uncertainty_summary.py so the figure producer can
reuse the derivation without importing that module, which pulls in PyROOT. The
PyROOT environment ships its own older mplhep that shadows the one the plotting
layer needs, so the plotting layer must stay ROOT-free.
"""

from __future__ import annotations

import numpy as np


def _calc_hist_with_weight_unc(vals: np.ndarray, bins: np.ndarray, weights: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    vals = np.asarray(vals, dtype=np.float64)
    bins = np.asarray(bins, dtype=np.float64)
    weights = np.asarray(weights, dtype=np.float64).reshape(-1)
    if vals.shape[0] != weights.shape[0]:
        raise ValueError(
            f"histogram values/weights length mismatch: {vals.shape[0]} vs {weights.shape[0]}"
        )
    hist, _ = np.histogram(vals, bins=bins, weights=weights)
    digits = np.digitize(vals, bins)
    errs = np.asarray(
        [np.linalg.norm(weights[digits == i]) for i in range(1, len(bins))],
        dtype=np.float64,
    )
    return hist.astype(np.float64), errs



def load_legacy_ibu_thrust_arrays(legacy_ibu_npz_path: str, n_bins_expected: int) -> dict:
    with np.load(legacy_ibu_npz_path, allow_pickle=True) as f:
        nominal_tau = np.asarray(f["nominal"], dtype=np.float64)
        total_unc_tau = np.asarray(f["total_uncert"], dtype=np.float64)
    if nominal_tau.shape[0] != n_bins_expected or total_unc_tau.shape[0] != n_bins_expected:
        raise ValueError(
            "legacy IBU arrays do not match ALEPH bin count "
            f"({nominal_tau.shape[0]}, {total_unc_tau.shape[0]}) vs {n_bins_expected}"
        )
    return {
        "values_thrust": nominal_tau[::-1].copy(),
        "errors_thrust": total_unc_tau[::-1].copy(),
    }


def _mc_bin_quality(
    *,
    data_counts: np.ndarray,
    data_err: np.ndarray,
    mc_counts: np.ndarray,
    mc_err: np.ndarray,
    rel_mc_unc_max: float = 0.20,
    pull_abs_max: float = 3.0,
) -> np.ndarray:
    data_counts = np.asarray(data_counts, dtype=np.float64)
    data_err = np.asarray(data_err, dtype=np.float64)
    mc_counts = np.asarray(mc_counts, dtype=np.float64)
    mc_err = np.asarray(mc_err, dtype=np.float64)

    sigma = np.sqrt(data_err**2 + mc_err**2)
    rel_mc_unc = np.divide(mc_err, mc_counts, out=np.zeros_like(mc_err), where=mc_counts > 0.0)
    pull = np.divide(
        mc_counts - data_counts,
        sigma,
        out=np.zeros_like(mc_err),
        where=sigma > 0.0,
    )
    good_rel_unc = rel_mc_unc <= rel_mc_unc_max
    good_pull = np.abs(pull) <= pull_abs_max
    return good_rel_unc & good_pull


def build_legacy_omnifold_thrust_arrays(legacy_of_h5_path: str, thrust_edges: np.ndarray) -> dict:
    import h5py

    with h5py.File(legacy_of_h5_path, "r") as f:
        data = {key: f[key][()] for key in f.keys()}

    tau_edges = 1.0 - np.asarray(thrust_edges, dtype=np.float64)[::-1]
    tau_gen = np.exp(np.asarray(data["archived_pythia61_gen"], dtype=np.float64))
    ensemble_weights = np.squeeze(np.asarray(data["ensemble_weights"], dtype=np.float64), axis=0)
    systematic_weights = np.asarray(data["systematic_weights"], dtype=np.float64)
    theory_weights = np.asarray(data["theory_weights"], dtype=np.float64)
    bootstrap_data_weights = np.squeeze(
        np.asarray(data["bootstrap_weights_data"], dtype=np.float64),
        axis=0,
    )
    bootstrap_mc_weights = np.squeeze(
        np.asarray(data["bootstrap_weights_mc"], dtype=np.float64),
        axis=0,
    )
    systematic_names = [
        x.decode("utf-8") if isinstance(x, (bytes, bytearray)) else str(x)
        for x in data["systematic_weights_order"]
    ]

    nominal_counts, nominal_stat = _calc_hist_with_weight_unc(
        tau_gen,
        tau_edges,
        ensemble_weights[0].reshape(-1),
    )

    ensemble_samples = []
    for i in range(1, ensemble_weights.shape[0]):
        counts_i, _ = _calc_hist_with_weight_unc(
            tau_gen,
            tau_edges,
            ensemble_weights[i].reshape(-1),
        )
        ensemble_samples.append(counts_i)
    total_ensemble_err = (
        np.std(np.asarray(ensemble_samples, dtype=np.float64), axis=0)
        if ensemble_samples
        else np.zeros_like(nominal_counts)
    )

    systematic_errs = []
    nes = {}
    for i, weights in enumerate(systematic_weights):
        name = systematic_names[i] if i < len(systematic_names) else f"systematic_{i}"
        counts_i, _ = _calc_hist_with_weight_unc(tau_gen, tau_edges, weights.reshape(-1))
        shift_i = nominal_counts - counts_i
        if name == "no_neutrals":
            continue
        if name in ("nes_up", "nes_down"):
            nes[name] = np.abs(shift_i)
            continue
        systematic_errs.append(shift_i)
    if "nes_up" in nes and "nes_down" in nes:
        systematic_errs.append(np.maximum(nes["nes_up"], nes["nes_down"]))
    elif "nes_up" in nes:
        systematic_errs.append(nes["nes_up"])
    elif "nes_down" in nes:
        systematic_errs.append(nes["nes_down"])
    total_exp_systematic_err = (
        np.sqrt(np.sum(np.square(np.stack(systematic_errs, axis=1)), axis=1))
        if systematic_errs
        else np.zeros_like(nominal_counts)
    )

    theory_errs = []
    theory_masks = []
    for i in range(theory_weights.shape[0]):
        counts_i, errs_i = _calc_hist_with_weight_unc(
            tau_gen,
            tau_edges,
            theory_weights[i].reshape(-1),
        )
        shift_i = nominal_counts - counts_i
        mask_i = _mc_bin_quality(
            data_counts=nominal_counts,
            data_err=nominal_stat,
            mc_counts=counts_i,
            mc_err=errs_i,
            rel_mc_unc_max=20.0,
            pull_abs_max=1.995,
        )
        theory_errs.append(shift_i)
        theory_masks.append(mask_i)
    if theory_errs:
        theory_err_arr = np.stack(theory_errs, axis=1)
        theory_mask_arr = np.stack(theory_masks, axis=1)
        abs_theory = np.abs(theory_err_arr)
        masked = np.where(theory_mask_arr, abs_theory, np.nan)
        has_valid = np.any(theory_mask_arr, axis=1)
        total_theory_err = np.zeros(abs_theory.shape[0], dtype=np.float64)
        if np.any(has_valid):
            total_theory_err[has_valid] = np.nanmax(masked[has_valid], axis=1)
        if np.any(~has_valid):
            total_theory_err[~has_valid] = np.nanmin(abs_theory[~has_valid], axis=1)
    else:
        total_theory_err = np.zeros_like(nominal_counts)

    boot_data_samples = []
    for i in range(bootstrap_data_weights.shape[0]):
        counts_i, _ = _calc_hist_with_weight_unc(
            tau_gen,
            tau_edges,
            bootstrap_data_weights[i].reshape(-1),
        )
        boot_data_samples.append(counts_i)
    bootstrap_data_err = (
        np.std(np.asarray(boot_data_samples, dtype=np.float64), axis=0)
        if boot_data_samples
        else np.zeros_like(nominal_counts)
    )

    boot_mc_samples = []
    for i in range(bootstrap_mc_weights.shape[0]):
        counts_i, _ = _calc_hist_with_weight_unc(
            tau_gen,
            tau_edges,
            bootstrap_mc_weights[i].reshape(-1),
        )
        boot_mc_samples.append(counts_i)
    bootstrap_mc_err = (
        np.std(np.asarray(boot_mc_samples, dtype=np.float64), axis=0)
        if boot_mc_samples
        else np.zeros_like(nominal_counts)
    )

    total_err_tau = np.sqrt(
        nominal_stat**2
        + total_ensemble_err**2
        + bootstrap_data_err**2
        + bootstrap_mc_err**2
        + total_exp_systematic_err**2
        + total_theory_err**2
    )
    bin_widths_tau = tau_edges[1:] - tau_edges[:-1]
    norm = np.sum(ensemble_weights[0]) * bin_widths_tau
    nominal_tau = np.divide(
        nominal_counts,
        norm,
        out=np.zeros_like(nominal_counts),
        where=norm > 0.0,
    )
    total_err_tau = np.divide(
        total_err_tau,
        norm,
        out=np.zeros_like(total_err_tau),
        where=norm > 0.0,
    )
    return {
        "values_thrust": nominal_tau[::-1].copy(),
        "errors_thrust": total_err_tau[::-1].copy(),
    }


