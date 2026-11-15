"""Aides partagées par les scripts d'expérience."""

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

METRICS_DIR = ROOT / "results" / "metrics"
FIGURES_DIR = ROOT / "results" / "figures"


def parse_args(description: str) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("--quick", action="store_true",
                        help="grilles réduites pour vérifier le flux (pas de conclusion)")
    parser.add_argument("--samples", type=int, default=None,
                        help="nombre d'initialisations aléatoires par configuration")
    parser.add_argument("--workers", type=int, default=1,
                        help="processus parallèles (1 = séquentiel)")
    parser.add_argument("--seed", type=int, default=None)
    return parser.parse_args()
