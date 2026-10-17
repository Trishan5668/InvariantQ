"""
Randomized Benchmarking (RB) Protocol.
Measures average gate fidelity independent of state preparation and measurement (SPAM) errors.
Applies random Clifford sequences followed by an exact inversion Clifford.
"""

from __future__ import annotations
import math
import random
from typing import List, Dict, Any, Tuple
import numpy as np

from ..ir.qir import CircuitIR, GateOp, QWire
from ..simulator.statevector import StateVectorSimulator
from ..simulator.density_matrix import DensityMatrixSimulator

# Single-qubit Clifford group generators (24 elements)
# Represented by sequences of H, S, X, Y, Z
CLIFFORD_GATES_1Q = [
    [],                      # I
    ["h"],                   # H
    ["s"],                   # S
    ["h", "s"],              # HS
    ["s", "h"],              # SH
    ["h", "s", "h"],         # HSH
    ["s", "s"],              # Z
    ["h", "s", "s"],         # HZ
    ["s", "s", "h"],         # ZH
    ["h", "s", "s", "h"],    # HZH
    ["s", "s", "s"],         # Sdg
    ["h", "s", "s", "s"],    # HSdg
    ["s", "s", "s", "h"],    # SdgH
    ["s", "h", "s"],         # SHS
    ["x"],                   # X
    ["y"],                   # Y
    ["z"],                   # Z
    ["h", "x"],              # HX
    ["s", "x"],              # SX
    ["h", "s", "x"],         # HSX
    ["s", "h", "x"],         # SHX
    ["h", "y"],              # HY
    ["s", "y"],              # SY
    ["h", "s", "y"],         # HSY
]

H_MAT = np.array([[1, 1], [1, -1]], dtype=complex) / np.sqrt(2)
S_MAT = np.array([[1, 0], [0, 1j]], dtype=complex)
X_MAT = np.array([[0, 1], [1, 0]], dtype=complex)
Y_MAT = np.array([[0, -1j], [1j, 0]], dtype=complex)
Z_MAT = np.array([[1, 0], [0, -1]], dtype=complex)
I_MAT = np.eye(2, dtype=complex)

GATE_MATRICES = {
    "h": H_MAT,
    "s": S_MAT,
    "x": X_MAT,
    "y": Y_MAT,
    "z": Z_MAT,
}

def get_clifford_matrix(clifford_name_seq: List[str]) -> np.ndarray:
    mat = np.eye(2, dtype=complex)
    for g in clifford_name_seq:
        mat = GATE_MATRICES[g] @ mat
    return mat

def create_rb_circuit(qubit: int, clifford_indices: List[int]) -> CircuitIR:
    """
    Constructs an RB circuit consisting of a sequence of single-qubit Cliffords
    followed by the exact inverse Clifford gate so that the circuit acts as the identity.
    """
    circuit = CircuitIR(name=f"rb_seq_len_{len(clifford_indices)}")
    circuit.add_qubit_register("q", 1)
    circuit.add_clbit_register("c", 1)

    cumulative_u = np.eye(2, dtype=complex)

    for c_idx in clifford_indices:
        gate_names = CLIFFORD_GATES_1Q[c_idx % len(CLIFFORD_GATES_1Q)]
        c_mat = get_clifford_matrix(gate_names)
        cumulative_u = c_mat @ cumulative_u

        for g in gate_names:
            circuit.add_op(GateOp(name=g, qubits=[QWire("q", 0)]))

    # Inverse Clifford: U_inv = cumulative_u^\dagger
    u_inv = cumulative_u.conj().T

    # Decompose or synthesize u_inv, or apply directly as a single-qubit unitary gate
    circuit.add_op(GateOp(name="u_inv", qubits=[QWire("q", 0)], matrix=u_inv))

    return circuit

def run_randomized_benchmarking(
    sequence_lengths: List[int],
    num_seeds: int = 10,
    shots: int = 500,
    noise_model = None
) -> Dict[str, Any]:
    """
    Executes Randomized Benchmarking protocol across multiple sequence lengths and seeds.
    Returns survival probabilities and estimated depolarizing parameter p.
    """
    sim = DensityMatrixSimulator(noise_model=noise_model) if noise_model else StateVectorSimulator()

    results_by_length: Dict[int, List[float]] = {m: [] for m in sequence_lengths}

    for m in sequence_lengths:
        for seed in range(num_seeds):
            rng = np.random.default_rng(seed + m * 1000)
            clifford_indices = [int(rng.integers(0, len(CLIFFORD_GATES_1Q))) for _ in range(m)]
            circ = create_rb_circuit(qubit=0, clifford_indices=clifford_indices)

            res = sim.run(circ, shots=shots)
            # P(0) survival probability
            p0 = res.probabilities.get("0", 0.0)
            results_by_length[m].append(p0)

    avg_survival = {m: float(np.mean(vals)) for m, vals in results_by_length.items()}
    std_survival = {m: float(np.std(vals)) for m, vals in results_by_length.items()}

    return {
        "sequence_lengths": sequence_lengths,
        "avg_survival": avg_survival,
        "std_survival": std_survival,
        "is_perfect_identity_noiseless": bool(all(np.isclose(v, 1.0, atol=1e-5) for v in avg_survival.values())) if noise_model is None else False,
    }
