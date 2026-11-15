"""Expérience 03 : effet de l'initialisation sur la variance du gradient.

Compare initialisation uniforme, petits angles (sigma configurable) et bloc
identité (Grant et al., 2019), à profondeur fixée, pour les deux coûts.
"""

from _common import METRICS_DIR, parse_args

from src.bp import config
from src.bp.sweep import run_sweep, save_rows


def main():
    args = parse_args(__doc__)
    qubits = config.QUICK_QUBITS if args.quick else config.QUBITS
    depth = 6 if args.quick else config.INIT_STUDY_DEPTH
    samples = args.samples or (config.QUICK_SAMPLES if args.quick else config.N_SAMPLES)
    boot = config.QUICK_BOOTSTRAP if args.quick else config.BOOTSTRAP
    print(f"Exp. 03 | qubits={qubits} profondeur={depth} échantillons={samples}"
          f"{' [QUICK]' if args.quick else ''}")
    rows = run_sweep(qubits, (depth,), config.INITS, samples, boot,
                     seed=args.seed if args.seed is not None else config.SEED,
                     sigma=config.SMALL_SIGMA, workers=args.workers)
    output = METRICS_DIR / "initialization_comparison.csv"
    save_rows(rows, output)
    print(f"-> {output}")


if __name__ == "__main__":
    main()
