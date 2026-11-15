"""Expérience 01 : variance du gradient en fonction du nombre de qubits.

Initialisation uniforme, plusieurs profondeurs, coûts global ET local calculés
sur les mêmes circuits aléatoires.
"""

from _common import METRICS_DIR, parse_args

from src.bp import config
from src.bp.sweep import run_sweep, save_rows


def main():
    args = parse_args(__doc__)
    qubits = config.QUICK_QUBITS if args.quick else config.QUBITS
    depths = config.QUICK_DEPTHS if args.quick else config.DEPTHS_QUBIT_SWEEP
    samples = args.samples or (config.QUICK_SAMPLES if args.quick else config.N_SAMPLES)
    boot = config.QUICK_BOOTSTRAP if args.quick else config.BOOTSTRAP
    print(f"Exp. 01 | qubits={qubits} profondeurs={depths} échantillons={samples}"
          f"{' [QUICK]' if args.quick else ''}")
    rows = run_sweep(qubits, depths, ("uniform",), samples, boot,
                     seed=args.seed if args.seed is not None else config.SEED,
                     workers=args.workers)
    output = METRICS_DIR / "variance_vs_qubits.csv"
    save_rows(rows, output)
    print(f"-> {output}")


if __name__ == "__main__":
    main()
