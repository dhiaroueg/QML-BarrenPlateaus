"""Lance les trois expériences puis génère les figures.

    python run_all.py --quick      # vérification rapide du flux
    python run_all.py              # protocole complet
    python run_all.py --workers 4  # parallélisme sur 4 processus
"""

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SCRIPTS = ("01_variance_vs_qubits.py", "02_variance_vs_depth.py", "03_initialization.py")


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--quick", action="store_true")
    parser.add_argument("--samples", type=int, default=None)
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--seed", type=int, default=None)
    args = parser.parse_args()

    options = []
    if args.quick:
        options.append("--quick")
    if args.samples is not None:
        options += ["--samples", str(args.samples)]
    if args.seed is not None:
        options += ["--seed", str(args.seed)]
    options += ["--workers", str(args.workers)]

    for script in SCRIPTS:
        subprocess.run([sys.executable, str(ROOT / "experiments" / script), *options], check=True)
    subprocess.run([sys.executable, str(ROOT / "experiments" / "04_make_figures.py")], check=True)


if __name__ == "__main__":
    main()
