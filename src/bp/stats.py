"""Statistiques : variance avec intervalle bootstrap et ajustement exponentiel."""

import numpy as np


def variance_with_ci(values: np.ndarray, n_boot: int, rng: np.random.Generator):
    """Variance non biaisée et intervalle bootstrap percentile à 95 %."""
    values = np.asarray(values, dtype=float)
    variance = float(np.var(values, ddof=1))
    if n_boot <= 0:
        return variance, float("nan"), float("nan")
    indices = rng.integers(0, len(values), size=(n_boot, len(values)))
    boots = np.var(values[indices], axis=1, ddof=1)
    low, high = np.percentile(boots, [2.5, 97.5])
    return variance, float(low), float(high)


def fit_exponential_decay(n_qubits, variances) -> dict:
    """Ajuste log10(Var) = a + b * n et renvoie pente, facteur par qubit et R²."""
    n_qubits = np.asarray(n_qubits, dtype=float)
    variances = np.asarray(variances, dtype=float)
    mask = variances > 0
    if mask.sum() < 3:
        return {"slope_log10": float("nan"), "factor_per_qubit": float("nan"),
                "r2": float("nan"), "n_points": int(mask.sum())}
    x, y = n_qubits[mask], np.log10(variances[mask])
    slope, intercept = np.polyfit(x, y, 1)
    residual = y - (slope * x + intercept)
    total = np.sum((y - y.mean()) ** 2)
    r2 = 1.0 - np.sum(residual**2) / total if total > 0 else float("nan")
    return {"slope_log10": float(slope), "factor_per_qubit": float(10**slope),
            "r2": float(r2), "n_points": int(mask.sum())}
