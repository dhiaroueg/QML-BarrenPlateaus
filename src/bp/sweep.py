"""Moteur d'échantillonnage : variance du gradient sur des circuits aléatoires."""

import csv
import platform
from concurrent.futures import ProcessPoolExecutor
from importlib.metadata import version
from pathlib import Path
from time import perf_counter

import numpy as np

from .circuits import build_probs_qnode, first_parameter_gradient
from .config import BOOTSTRAP, COSTS, INITS, N_SAMPLES, SEED, SMALL_SIGMA
from .stats import variance_with_ci


def library_versions() -> dict:
    return {
        "python_version": platform.python_version(),
        "pennylane_version": version("PennyLane"),
        "numpy_version": version("numpy"),
    }


def sample_circuit(rng, n_qubits, n_layers, init, sigma=SMALL_SIGMA):
    """Tire (angles, gate_ids, mirror_angles) selon l'initialisation demandée."""
    if init not in INITS:
        raise ValueError(f"init doit appartenir à {INITS}")
    if init == "identity_block":
        if n_layers % 2 != 0:
            raise ValueError("identity_block demande une profondeur paire")
        trainable_layers = n_layers // 2
    else:
        trainable_layers = n_layers
    gate_ids = rng.integers(0, 3, size=(trainable_layers, n_qubits))
    if init == "small":
        angles = rng.normal(0.0, sigma, size=(trainable_layers, n_qubits))
    else:
        angles = rng.uniform(0.0, 2.0 * np.pi, size=(trainable_layers, n_qubits))
    mirror = angles.copy() if init == "identity_block" else None
    return angles, gate_ids, mirror


def run_configuration(task: dict) -> list[dict]:
    """Une configuration (n, L, init) -> une ligne par fonction de coût."""
    n_qubits, n_layers, init = task["n_qubits"], task["n_layers"], task["init"]
    n_samples, n_boot = task["n_samples"], task["bootstrap"]
    seed_seq = np.random.SeedSequence([task["seed"], n_qubits, n_layers, INITS.index(init)])
    rng = np.random.default_rng(seed_seq)
    circuit = build_probs_qnode(n_qubits)

    start = perf_counter()
    gradients = np.empty((n_samples, len(COSTS)))
    for sample in range(n_samples):
        angles, gate_ids, mirror = sample_circuit(rng, n_qubits, n_layers, init, task["sigma"])
        gradients[sample] = first_parameter_gradient(circuit, n_qubits, angles, gate_ids, mirror)
    seconds = perf_counter() - start

    boot_rng = np.random.default_rng(seed_seq.spawn(1)[0])
    rows = []
    for column, cost_name in enumerate(COSTS):
        values = gradients[:, column]
        variance, low, high = variance_with_ci(values, n_boot, boot_rng)
        rows.append({
            "n_qubits": n_qubits, "n_layers": n_layers, "init": init, "cost": cost_name,
            "n_samples": n_samples, "grad_variance": variance,
            "var_ci_low": low, "var_ci_high": high,
            "grad_mean": float(values.mean()), "grad_mean_abs": float(np.abs(values).mean()),
            "seconds_for_both_costs": seconds, "seed": task["seed"],
            **library_versions(),
        })
    return rows


def run_sweep(qubits, depths, inits, n_samples=N_SAMPLES, bootstrap=BOOTSTRAP,
              seed=SEED, sigma=SMALL_SIGMA, workers=1, verbose=True) -> list[dict]:
    """Balaie la grille (n, L, init). Les configurations invalides sont ignorées."""
    tasks = []
    for init in inits:
        for n_layers in depths:
            if init == "identity_block" and n_layers % 2 != 0:
                if verbose:
                    print(f"  [ignoré] identity_block avec L={n_layers} (impair)")
                continue
            for n_qubits in qubits:
                tasks.append({"n_qubits": n_qubits, "n_layers": n_layers, "init": init,
                              "n_samples": n_samples, "bootstrap": bootstrap,
                              "seed": seed, "sigma": sigma})
    rows: list[dict] = []
    if workers > 1:
        with ProcessPoolExecutor(max_workers=workers) as pool:
            results = pool.map(run_configuration, tasks)
            for task, result in zip(tasks, results):
                rows.extend(result)
                if verbose:
                    print(_progress(task, result))
    else:
        for task in tasks:
            result = run_configuration(task)
            rows.extend(result)
            if verbose:
                print(_progress(task, result))
    return rows


def _progress(task, result) -> str:
    g = next(r for r in result if r["cost"] == "global")["grad_variance"]
    l = next(r for r in result if r["cost"] == "local")["grad_variance"]
    return (f"  n={task['n_qubits']:>2} L={task['n_layers']:>2} {task['init']:<14} "
            f"Var global={g:.3e}  Var local={l:.3e}")


def save_rows(rows: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def load_rows(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    for row in rows:
        for key in ("n_qubits", "n_layers", "n_samples", "seed"):
            row[key] = int(row[key])
        for key in ("grad_variance", "var_ci_low", "var_ci_high", "grad_mean",
                    "grad_mean_abs", "seconds_for_both_costs"):
            row[key] = float(row[key])
    return rows
