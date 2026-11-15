"""Tests de correction : règle de décalage vs rétropropagation, bloc identité, etc."""

import sys
from pathlib import Path

import numpy as np
import pennylane as qml
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.bp.circuits import (apply_circuit, build_probs_qnode, costs_from_probs,  # noqa: E402
                             first_parameter_gradient)
from src.bp.config import PREP_ANGLE  # noqa: E402
from src.bp.stats import fit_exponential_decay  # noqa: E402
from src.bp.sweep import run_configuration, sample_circuit  # noqa: E402


def _zero_masks(n):
    """Matrice (2**n, n) : 1 si le qubit j vaut 0 dans l'état de base i."""
    return np.array([[1.0 if ((i >> (n - 1 - j)) & 1) == 0 else 0.0 for j in range(n)]
                     for i in range(2**n)])


def autograd_gradients(n, angles, gate_ids, mirror=None):
    """Gradient de référence par rétropropagation (indépendant du parameter-shift)."""
    device = qml.device("default.qubit", wires=n)
    masks = _zero_masks(n)

    @qml.qnode(device, interface="autograd", diff_method="backprop")
    def probs(theta):
        apply_circuit(n, theta, gate_ids, mirror)
        return qml.probs(wires=list(range(n)))

    def cost_global(theta):
        return 1.0 - probs(theta)[0]

    def cost_local(theta):
        return 1.0 - qml.math.mean(probs(theta) @ masks)

    theta = qml.numpy.array(angles, requires_grad=True)
    return np.array([qml.grad(cost_global)(theta)[0, 0], qml.grad(cost_local)(theta)[0, 0]])


@pytest.mark.parametrize("seed", [0, 1, 2])
def test_parameter_shift_matches_backprop_uniform(seed):
    n, layers = 3, 4
    rng = np.random.default_rng(seed)
    angles, gate_ids, mirror = sample_circuit(rng, n, layers, "uniform")
    shift = first_parameter_gradient(build_probs_qnode(n), n, angles, gate_ids, mirror)
    reference = autograd_gradients(n, angles, gate_ids, mirror)
    np.testing.assert_allclose(shift, reference, atol=1e-8)


def test_parameter_shift_matches_backprop_identity_block():
    n, layers = 3, 6
    rng = np.random.default_rng(7)
    angles, gate_ids, mirror = sample_circuit(rng, n, layers, "identity_block")
    shift = first_parameter_gradient(build_probs_qnode(n), n, angles, gate_ids, mirror)
    reference = autograd_gradients(n, angles, gate_ids, mirror)
    np.testing.assert_allclose(shift, reference, atol=1e-8)


def test_identity_block_is_exactly_identity():
    """Le circuit complet (moitié + son inverse) laisse l'état préparé inchangé."""
    n = 4
    rng = np.random.default_rng(3)
    angles, gate_ids, mirror = sample_circuit(rng, n, 8, "identity_block")
    circuit = build_probs_qnode(n)
    full = circuit(angles, gate_ids, mirror)
    prep_only = circuit(np.zeros((0, n)), np.zeros((0, n), dtype=int), None)
    np.testing.assert_allclose(full, prep_only, atol=1e-10)


def test_costs_of_product_state():
    n = 4
    circuit = build_probs_qnode(n)
    probs = circuit(np.zeros((0, n)), np.zeros((0, n), dtype=int), None)
    p0 = np.cos(PREP_ANGLE / 2) ** 2
    expected_global = 1.0 - p0**n
    expected_local = 1.0 - p0
    np.testing.assert_allclose(costs_from_probs(probs, n), [expected_global, expected_local],
                               atol=1e-10)


def test_probabilities_are_normalised():
    n = 5
    rng = np.random.default_rng(11)
    angles, gate_ids, _ = sample_circuit(rng, n, 6, "uniform")
    probs = build_probs_qnode(n)(angles, gate_ids, None)
    assert probs.shape == (2**n,)
    assert np.isclose(probs.sum(), 1.0)


def test_run_configuration_is_reproducible():
    task = {"n_qubits": 3, "n_layers": 2, "init": "uniform", "n_samples": 8,
            "bootstrap": 20, "seed": 5, "sigma": 0.1}
    first, second = run_configuration(task), run_configuration(task)
    for a, b in zip(first, second):
        assert a["grad_variance"] == b["grad_variance"]
        assert a["var_ci_low"] == b["var_ci_low"]


def test_identity_block_rejects_odd_depth():
    with pytest.raises(ValueError):
        sample_circuit(np.random.default_rng(0), 3, 5, "identity_block")


def test_exponential_fit_recovers_known_rate():
    n = np.arange(2, 10)
    variance = 0.5 * (0.5**n)
    fit = fit_exponential_decay(n, variance)
    assert np.isclose(fit["factor_per_qubit"], 0.5, atol=1e-9)
    assert fit["r2"] > 0.999999
