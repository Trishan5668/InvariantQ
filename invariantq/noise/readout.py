"""
Readout Error Modeling and Inversion Calibration.
Simulates detector confusion matrices and classical readout error mitigation.
"""

from __future__ import annotations
from typing import Dict, List, Tuple
import numpy as np

class ReadoutError:
    def __init__(self, p01: float = 0.02, p10: float = 0.03):
        """
        p01: Probability that prepared |0> is measured as |1>
        p10: Probability that prepared |1> is measured as |0>
        """
        self.p01 = p01
        self.p10 = p10
        # Confusion matrix M[meas, true]
        self.matrix = np.array([
            [1.0 - p01, p10],
            [p01, 1.0 - p10]
        ], dtype=np.float64)

    def apply_to_bitstring(self, bitstr: str, rng: np.random.Generator) -> str:
        noisy_chars = []
        for ch in bitstr:
            true_bit = int(ch)
            p_flip = self.p01 if true_bit == 0 else self.p10
            if rng.random() < p_flip:
                noisy_chars.append("1" if true_bit == 0 else "0")
            else:
                noisy_chars.append(ch)
        return "".join(noisy_chars)

    def apply_to_counts(self, counts: Dict[str, int], seed: int = 42) -> Dict[str, int]:
        rng = np.random.default_rng(seed)
        noisy_counts: Dict[str, int] = {}
        for bitstr, cnt in counts.items():
            for _ in range(cnt):
                noisy_str = self.apply_to_bitstring(bitstr, rng)
                noisy_counts[noisy_str] = noisy_counts.get(noisy_str, 0) + 1
        return noisy_counts

    def mitigate_counts(self, noisy_counts: Dict[str, int], num_qubits: int) -> Dict[str, float]:
        """
        Applies inverse calibration matrix to mitigate readout error.
        """
        # For small qubit counts, invert full Kronecker confusion matrix
        total_shots = sum(noisy_counts.values())
        if total_shots == 0:
            return {}

        dim = 1 << num_qubits
        p_vec = np.zeros(dim, dtype=np.float64)
        for bitstr, cnt in noisy_counts.items():
            idx = int(bitstr, 2)
            if idx < dim:
                p_vec[idx] = cnt / total_shots

        # 1-qubit inverse
        inv_m = np.linalg.inv(self.matrix)
        full_inv = inv_m
        for _ in range(num_qubits - 1):
            full_inv = np.kron(full_inv, inv_m)

        mitigated = full_inv @ p_vec
        # Project onto probability simplex (clip negative, normalize)
        mitigated = np.maximum(0.0, mitigated)
        s = np.sum(mitigated)
        if s > 0:
            mitigated /= s

        result: Dict[str, float] = {}
        for i, val in enumerate(mitigated):
            if val > 1e-6:
                result[f"{i:0{num_qubits}b}"] = float(val)

        return result
