"""Génère les figures et le résumé des ajustements exponentiels à partir des CSV."""

import json

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from _common import FIGURES_DIR, METRICS_DIR  # noqa: E402

from src.bp.stats import fit_exponential_decay  # noqa: E402
from src.bp.sweep import load_rows  # noqa: E402

COLORS = {"global": "#c0392b", "local": "#1f77b4"}
INIT_STYLES = {"uniform": "-", "small": "--", "identity_block": ":"}


def _series(rows, **filters):
    selected = [r for r in rows if all(r[k] == v for k, v in filters.items())]
    return sorted(selected, key=lambda r: (r["n_qubits"], r["n_layers"]))


def _band(ax, xs, rows, color, label, linestyle="-"):
    ys = [r["grad_variance"] for r in rows]
    ax.plot(xs, ys, linestyle, marker="o", ms=4, color=color, label=label)
    ax.fill_between(xs, [r["var_ci_low"] for r in rows], [r["var_ci_high"] for r in rows],
                    color=color, alpha=0.15)


def figure_qubits(rows, fits):
    depths = sorted({r["n_layers"] for r in rows})
    fig, axes = plt.subplots(1, len(depths), figsize=(4.6 * len(depths), 4), sharey=True)
    axes = [axes] if len(depths) == 1 else list(axes)
    for ax, depth in zip(axes, depths):
        for cost in ("global", "local"):
            sub = _series(rows, n_layers=depth, cost=cost, init="uniform")
            xs = [r["n_qubits"] for r in sub]
            fit = fit_exponential_decay(xs, [r["grad_variance"] for r in sub])
            fits[f"qubits|L={depth}|{cost}|uniform"] = fit
            label = f"{cost} (x{fit['factor_per_qubit']:.2f}/qubit, R²={fit['r2']:.2f})"
            _band(ax, xs, sub, COLORS[cost], label)
        ax.set_yscale("log")
        ax.set_title(f"L = {depth} couches")
        ax.set_xlabel("nombre de qubits n")
        ax.grid(alpha=0.3, which="both")
        ax.legend(fontsize=8)
    axes[0].set_ylabel("Var[∂C/∂θ]  (échelle log)")
    fig.suptitle("Variance du gradient vs nombre de qubits (initialisation uniforme)")
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "variance_vs_qubits.png", dpi=160)
    plt.close(fig)


def figure_depth(rows):
    qubit_counts = sorted({r["n_qubits"] for r in rows})
    fig, axes = plt.subplots(1, len(qubit_counts), figsize=(4.6 * len(qubit_counts), 4),
                             sharey=True)
    axes = [axes] if len(qubit_counts) == 1 else list(axes)
    for ax, n in zip(axes, qubit_counts):
        for cost in ("global", "local"):
            sub = _series(rows, n_qubits=n, cost=cost, init="uniform")
            _band(ax, [r["n_layers"] for r in sub], sub, COLORS[cost], cost)
        ax.set_yscale("log")
        ax.set_title(f"n = {n} qubits")
        ax.set_xlabel("profondeur L (couches)")
        ax.grid(alpha=0.3, which="both")
        ax.legend(fontsize=8)
    axes[0].set_ylabel("Var[∂C/∂θ]  (échelle log)")
    fig.suptitle("Variance du gradient vs profondeur (initialisation uniforme)")
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "variance_vs_depth.png", dpi=160)
    plt.close(fig)


def figure_initialization(rows, fits):
    inits = [i for i in ("uniform", "small", "identity_block") if any(r["init"] == i for r in rows)]
    depth = rows[0]["n_layers"]
    fig, axes = plt.subplots(1, 2, figsize=(10, 4), sharey=True)
    for ax, cost in zip(axes, ("global", "local")):
        for init in inits:
            sub = _series(rows, cost=cost, init=init)
            xs = [r["n_qubits"] for r in sub]
            fit = fit_exponential_decay(xs, [r["grad_variance"] for r in sub])
            fits[f"init|L={depth}|{cost}|{init}"] = fit
            ax.plot(xs, [r["grad_variance"] for r in sub], INIT_STYLES[init], marker="o", ms=4,
                    label=f"{init} (x{fit['factor_per_qubit']:.2f}/qubit)")
            ax.fill_between(xs, [r["var_ci_low"] for r in sub], [r["var_ci_high"] for r in sub],
                            alpha=0.12)
        ax.set_yscale("log")
        ax.set_title(f"coût {cost}")
        ax.set_xlabel("nombre de qubits n")
        ax.grid(alpha=0.3, which="both")
        ax.legend(fontsize=8)
    axes[0].set_ylabel("Var[∂C/∂θ]  (échelle log)")
    fig.suptitle(f"Effet de l'initialisation (L = {depth})")
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "initialization_comparison.png", dpi=160)
    plt.close(fig)


def main():
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    fits: dict = {}
    produced = []
    for name, handler in (
        ("variance_vs_qubits.csv", lambda r: figure_qubits(r, fits)),
        ("variance_vs_depth.csv", figure_depth),
        ("initialization_comparison.csv", lambda r: figure_initialization(r, fits)),
    ):
        path = METRICS_DIR / name
        if path.exists():
            handler(load_rows(path))
            produced.append(name)
        else:
            print(f"[absent] {name} : lancez l'expérience correspondante")
    (METRICS_DIR / "decay_fits.json").write_text(json.dumps(fits, indent=2), encoding="utf-8")
    print("Figures générées pour :", ", ".join(produced) or "aucun fichier")


if __name__ == "__main__":
    main()
