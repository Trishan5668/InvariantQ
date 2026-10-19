"""Validated quantum-information protocol demonstrations.

These routines use the same statevector binding as the simulator backend, but
keep protocol-specific measurement/feed-forward orchestration explicit until
generic qIR conditional execution is complete.
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Sequence, Tuple

import numpy as np

from .core.binding import NativeStateVector

_H = np.array([[1, 1], [1, -1]], dtype=np.complex128) / np.sqrt(2)
_X = np.array([[0, 1], [1, 0]], dtype=np.complex128)
_Z = np.array([[1, 0], [0, -1]], dtype=np.complex128)
_I = np.eye(2, dtype=np.complex128)
_CX = np.array(
    [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 0, 1], [0, 0, 1, 0]],
    dtype=np.complex128,
)


def _validate_shots(shots: int) -> int:
    if isinstance(shots, bool) or not isinstance(shots, int) or shots <= 0:
        raise ValueError("shots must be a positive integer")
    return shots


def _normalise_state(alpha: complex, beta: complex) -> Tuple[complex, complex]:
    vector = np.asarray([alpha, beta], dtype=np.complex128)
    norm = float(np.linalg.norm(vector))
    if not np.isfinite(norm) or norm <= 0:
        raise ValueError("input state must have finite non-zero norm")
    vector /= norm
    return complex(vector[0]), complex(vector[1])


def _reduced_density_matrix(
    state: np.ndarray, num_qubits: int, subsystem: Sequence[int]
) -> np.ndarray:
    selected = list(subsystem)
    if not selected or len(set(selected)) != len(selected):
        raise ValueError("subsystem must contain unique qubit indices")
    if any(q < 0 or q >= num_qubits for q in selected):
        raise ValueError("subsystem qubit index is out of range")
    rest = [q for q in range(num_qubits) if q not in selected]
    tensor = np.asarray(state, dtype=np.complex128).reshape([2] * num_qubits, order="F")
    matrix = np.transpose(tensor, selected + rest).reshape(1 << len(selected), -1)
    return matrix @ matrix.conj().T


def entanglement_explorer(state: str = "bell") -> Dict[str, Any]:
    """Analyze verified pure Bell, GHZ, or product states."""
    state = state.lower()
    if state == "product":
        vector = np.array([1, 0, 0, 0], dtype=np.complex128)
        num_qubits = 2
    elif state == "bell":
        vector = np.array([1, 0, 0, 1], dtype=np.complex128) / np.sqrt(2)
        num_qubits = 2
    elif state == "ghz":
        vector = np.zeros(8, dtype=np.complex128)
        vector[[0, 7]] = 1 / np.sqrt(2)
        num_qubits = 3
    else:
        raise ValueError("state must be one of: product, bell, ghz")

    subsystem = [0]
    reduced = _reduced_density_matrix(vector, num_qubits, subsystem)
    eigenvalues = np.linalg.eigvalsh(reduced).real
    eigenvalues = np.clip(eigenvalues, 0.0, None)
    entropy = float(
        -sum(value * np.log2(value) for value in eigenvalues if value > 1e-15)
    )
    probabilities = {
        f"{index:0{num_qubits}b}": float(abs(amplitude) ** 2)
        for index, amplitude in enumerate(vector)
        if abs(amplitude) ** 2 > 1e-15
    }
    return {
        "protocol": "entanglement_explorer",
        "state": state,
        "num_qubits": num_qubits,
        "subsystem": subsystem,
        "state_probabilities": probabilities,
        "reduced_density_matrix": [
            [[float(value.real), float(value.imag)] for value in row]
            for row in reduced
        ],
        "reduced_eigenvalues": eigenvalues.tolist(),
        "von_neumann_entropy_bits": entropy,
        "interpretation": (
            "For this pure bipartite state, non-zero entropy certifies entanglement "
            "across the selected partition; zero entropy is a product state here."
        ),
    }


def superdense_coding(shots: int = 1, seed: int = 42) -> Dict[str, Any]:
    """Encode and decode all four classical messages using a Bell pair."""
    shots = _validate_shots(shots)
    rng = np.random.default_rng(seed)
    encoders = {
        "00": _I,
        "01": _X,
        "10": _Z,
        "11": _X @ _Z,
    }
    results: Dict[str, Any] = {}
    for message, encoder in encoders.items():
        decoded: List[str] = []
        for _ in range(shots):
            state = NativeStateVector(2)
            state.apply_1q(0, _H)
            state.apply_2q(0, 1, _CX)
            state.apply_1q(0, encoder)
            state.apply_2q(0, 1, _CX)
            state.apply_1q(0, _H)
            first = state.measure(0, float(rng.random()))
            second = state.measure(1, float(rng.random()))
            decoded.append(f"{first}{second}")
        counts = {value: decoded.count(value) for value in sorted(set(decoded))}
        results[message] = {
            "decoded_counts": counts,
            "success_probability": counts.get(message, 0) / shots,
            "correct": all(value == message for value in decoded),
        }
    return {
        "protocol": "superdense_coding",
        "shots_per_message": shots,
        "messages": results,
        "circuit_stages": [
            "Bell pair preparation",
            "Alice encodes two classical bits locally",
            "Bob applies CNOT and Hadamard decoding",
            "Bob measures both qubits",
        ],
    }


def quantum_teleportation(
    alpha: complex = 1 / np.sqrt(2),
    beta: complex = 1j / np.sqrt(2),
    shots: int = 128,
    seed: int = 42,
) -> Dict[str, Any]:
    """Teleport an arbitrary pure qubit with explicit measurement feed-forward."""
    shots = _validate_shots(shots)
    alpha, beta = _normalise_state(alpha, beta)
    preparation = np.array(
        [[alpha, -np.conj(beta)], [beta, np.conj(alpha)]], dtype=np.complex128
    )
    rng = np.random.default_rng(seed)
    fidelities: List[float] = []
    outcomes: Dict[str, int] = {}
    for _ in range(shots):
        state = NativeStateVector(3)
        state.apply_1q(0, preparation)
        state.apply_1q(1, _H)
        state.apply_2q(1, 2, _CX)
        state.apply_2q(0, 1, _CX)
        state.apply_1q(0, _H)
        first = state.measure(0, float(rng.random()))
        second = state.measure(1, float(rng.random()))
        if second:
            state.apply_1q(2, _X)
        if first:
            state.apply_1q(2, _Z)
        amplitudes = state.get_amplitudes()
        bob = np.array([amplitudes[0b000 | (first << 0) | (second << 1) | (0 << 2)],
                        amplitudes[0b000 | (first << 0) | (second << 1) | (1 << 2)]])
        bob_norm = np.linalg.norm(bob)
        if bob_norm <= 1e-12:
            raise RuntimeError("teleportation produced a zero-norm Bob state")
        bob /= bob_norm
        fidelity = float(abs(np.vdot(np.array([alpha, beta]), bob)) ** 2)
        fidelities.append(fidelity)
        key = f"{first}{second}"
        outcomes[key] = outcomes.get(key, 0) + 1
    return {
        "protocol": "quantum_teleportation",
        "input_state": {"alpha": [alpha.real, alpha.imag], "beta": [beta.real, beta.imag]},
        "measurement_outcomes": outcomes,
        "fidelities": fidelities,
        "average_fidelity": float(np.mean(fidelities)),
        "minimum_fidelity": float(np.min(fidelities)),
        "verified": bool(np.min(fidelities) > 1 - 1e-10),
        "feed_forward": "X correction controlled by Alice's second bit; Z correction controlled by first bit",
    }
