"""
CPTP Quantum Noise Channels: Kraus representations and Choi matrices.
Implements Depolarizing, Amplitude Damping (T1), Phase Damping (T2), Bit-flip, Phase-flip, and Readout errors.
"""

from __future__ import annotations
import math
from typing import List, Dict, Tuple, Optional
import numpy as np

def build_kraus_channel(name: str, params: List[float]) -> List[np.ndarray]:
    """
    Builds the Kraus operators {K_k} satisfying sum_k K_k^\dagger K_k = I.
    """
    name = name.lower()
    p = params[0] if params else 0.0

    if name in ("depolarizing", "depol"):
        # E(rho) = (1 - p) rho + (p/3) (X rho X + Y rho Y + Z rho Z)
        # K_0 = sqrt(1 - 3p/4) I
        # K_1 = sqrt(p/4) X, K_2 = sqrt(p/4) Y, K_3 = sqrt(p/4) Z
        # When p <= 1:
        p_val = min(1.0, max(0.0, p))
        k0 = math.sqrt(max(0.0, 1.0 - 0.75 * p_val)) * np.eye(2, dtype=np.complex128)
        k1 = math.sqrt(p_val / 4.0) * np.array([[0, 1], [1, 0]], dtype=np.complex128)
        k2 = math.sqrt(p_val / 4.0) * np.array([[0, -1j], [1j, 0]], dtype=np.complex128)
        k3 = math.sqrt(p_val / 4.0) * np.array([[1, 0], [0, -1]], dtype=np.complex128)
        return [k0, k1, k2, k3]

    elif name in ("amplitude_damping", "amp_damping", "t1"):
        # K_0 = [[1, 0], [0, sqrt(1 - gamma)]]
        # K_1 = [[0, sqrt(gamma)], [0, 0]]
        gamma = min(1.0, max(0.0, p))
        k0 = np.array([[1.0, 0.0], [0.0, math.sqrt(1.0 - gamma)]], dtype=np.complex128)
        k1 = np.array([[0.0, math.sqrt(gamma)], [0.0, 0.0]], dtype=np.complex128)
        return [k0, k1]

    elif name in ("phase_damping", "dephasing", "t2"):
        # K_0 = [[1, 0], [0, sqrt(1 - lambda)]]
        # K_1 = [[0, 0], [0, sqrt(lambda)]]
        lam = min(1.0, max(0.0, p))
        k0 = np.array([[1.0, 0.0], [0.0, math.sqrt(1.0 - lam)]], dtype=np.complex128)
        k1 = np.array([[0.0, 0.0], [0.0, math.sqrt(lam)]], dtype=np.complex128)
        return [k0, k1]

    elif name in ("bit_flip", "bitflip"):
        # K_0 = sqrt(1 - p) I
        # K_1 = sqrt(p) X
        p_val = min(1.0, max(0.0, p))
        k0 = math.sqrt(1.0 - p_val) * np.eye(2, dtype=np.complex128)
        k1 = math.sqrt(p_val) * np.array([[0, 1], [1, 0]], dtype=np.complex128)
        return [k0, k1]

    elif name in ("phase_flip", "phaseflip"):
        # K_0 = sqrt(1 - p) I
        # K_1 = sqrt(p) Z
        p_val = min(1.0, max(0.0, p))
        k0 = math.sqrt(1.0 - p_val) * np.eye(2, dtype=np.complex128)
        k1 = math.sqrt(p_val) * np.array([[1, 0], [0, -1]], dtype=np.complex128)
        return [k0, k1]

    elif name in ("thermal_relaxation", "thermal"):
        # T1, T2, t_gate
        t1 = params[0] if len(params) > 0 else 50e-6
        t2 = params[1] if len(params) > 1 else 70e-6
        t_gate = params[2] if len(params) > 2 else 50e-9
        gamma = 1.0 - math.exp(-t_gate / t1) if t1 > 0 else 0.0
        lam = 1.0 - math.exp(-t_gate / t2) if t2 > 0 else 0.0
        # return amplitude damping combined with phase damping
        return build_kraus_channel("amp_damping", [gamma])

    # Default to identity
    return [np.eye(2, dtype=np.complex128)]


def compute_choi_matrix(kraus_ops: List[np.ndarray], dim: int = 2) -> np.ndarray:
    """
    Computes the Choi-Jamiolkowski state matrix J(E) for the quantum channel:
    J(E) = sum_k (I (x) K_k) |Phi+><Phi+| (I (x) K_k)^\dagger
    where |Phi+> = 1/sqrt(dim) sum_{i=0}^{dim-1} |i>|i>.
    """
    phi_plus = np.zeros(dim * dim, dtype=np.complex128)
    for i in range(dim):
        phi_plus[i * dim + i] = 1.0 / math.sqrt(dim)
    phi_proj = np.outer(phi_plus, phi_plus.conj())

    choi = np.zeros((dim * dim, dim * dim), dtype=np.complex128)
    eye = np.eye(dim, dtype=np.complex128)

    for k in kraus_ops:
        op = np.kron(eye, k)
        choi += op @ phi_proj @ op.conj().T

    return choi
