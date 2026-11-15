"""Circuit à couches aléatoires et coûts global / local.

Architecture (McClean et al., 2018) :
    1. couche fixe RY(pi/4) sur chaque qubit ;
    2. L couches, chacune = une rotation RX, RY ou RZ tirée au hasard par qubit
       (paramètre entraînable) puis des CZ en « brickwork » (paires (0,1),(2,3)...
       aux couches paires, (1,2),(3,4)... aux couches impaires).

Coûts (Cerezo et al., 2021), calculés sur la MÊME exécution à partir des
probabilités de la base de calcul :
    C_global = 1 - P(|0...0>)
    C_local  = 1 - (1/n) * somme_j P(qubit j = 0)

Les deux sont linéaires en probabilités : la règle de décalage de paramètre
(parameter-shift, décalage pi/2) donne donc leur gradient exact (shots=None).
"""

import numpy as np
import pennylane as qml

from .config import PREP_ANGLE

GATES = (qml.RX, qml.RY, qml.RZ)
GATE_NAMES = ("RX", "RY", "RZ")


def cz_pairs(n_qubits: int, layer: int) -> list[tuple[int, int]]:
    """Paires de CZ de la couche `layer` (brickwork)."""
    return [(i, i + 1) for i in range(layer % 2, n_qubits - 1, 2)]


def _rotation_layer(angles, gate_ids) -> None:
    for wire, (angle, gate_id) in enumerate(zip(angles, gate_ids)):
        GATES[int(gate_id)](angle, wires=wire)


def _cz_layer(n_qubits: int, layer: int) -> None:
    for left, right in cz_pairs(n_qubits, layer):
        qml.CZ(wires=[left, right])


def apply_circuit(n_qubits, angles, gate_ids, mirror_angles=None, prep_angle=PREP_ANGLE):
    """Applique le circuit sur le périphérique courant.

    Si `mirror_angles` est fourni, la seconde moitié du circuit est l'inverse
    exact de la première (bloc identité, Grant et al., 2019) : les angles de la
    seconde moitié valent -mirror_angles et ne sont PAS décalés lors du calcul
    du gradient.
    """
    for wire in range(n_qubits):
        qml.RY(prep_angle, wires=wire)
    n_layers = len(angles)
    for layer in range(n_layers):
        _rotation_layer(angles[layer], gate_ids[layer])
        _cz_layer(n_qubits, layer)
    if mirror_angles is not None:
        for layer in reversed(range(n_layers)):
            _cz_layer(n_qubits, layer)  # CZ est son propre inverse
            _rotation_layer(-np.asarray(mirror_angles[layer]), gate_ids[layer])


def build_probs_qnode(n_qubits: int, prep_angle: float = PREP_ANGLE):
    """QNode renvoyant les 2**n probabilités de la base de calcul."""
    if n_qubits < 2:
        raise ValueError("Le circuit demande au moins deux qubits")
    device = qml.device("default.qubit", wires=n_qubits)

    @qml.qnode(device)
    def circuit(angles, gate_ids, mirror_angles=None):
        apply_circuit(n_qubits, angles, gate_ids, mirror_angles, prep_angle)
        return qml.probs(wires=list(range(n_qubits)))

    return circuit


def costs_from_probs(probs: np.ndarray, n_qubits: int) -> np.ndarray:
    """Renvoie [C_global, C_local] à partir des probabilités (wire 0 = poids fort)."""
    probs = np.asarray(probs, dtype=float)
    c_global = 1.0 - probs[0]
    tensor = probs.reshape((2,) * n_qubits)
    p_zero = [tensor.take(0, axis=wire).sum() for wire in range(n_qubits)]
    c_local = 1.0 - float(np.mean(p_zero))
    return np.array([c_global, c_local])


def estimate_costs(circuit, n_qubits, angles, gate_ids, mirror_angles=None) -> np.ndarray:
    return costs_from_probs(circuit(angles, gate_ids, mirror_angles), n_qubits)


def first_parameter_gradient(circuit, n_qubits, angles, gate_ids, mirror_angles=None,
                             index=(0, 0)) -> np.ndarray:
    """Gradient exact [dC_global, dC_local] par rapport à angles[index].

    Règle de décalage : dC/dtheta = [C(theta + pi/2) - C(theta - pi/2)] / 2,
    valable pour une rotation Pauli et un coût linéaire en probabilités.
    La seconde moitié du bloc identité (si présente) reste figée.
    """
    plus = np.array(angles, dtype=float, copy=True)
    minus = np.array(angles, dtype=float, copy=True)
    plus[index] += np.pi / 2
    minus[index] -= np.pi / 2
    frozen = None if mirror_angles is None else np.array(mirror_angles, dtype=float, copy=True)
    cost_plus = estimate_costs(circuit, n_qubits, plus, gate_ids, frozen)
    cost_minus = estimate_costs(circuit, n_qubits, minus, gate_ids, frozen)
    return (cost_plus - cost_minus) / 2.0
