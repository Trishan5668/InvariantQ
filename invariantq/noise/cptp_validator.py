"""
Rigorous CPTP (Completely Positive Trace-Preserving) Verification Suite.
Validates Choi matrix positive semidefiniteness, trace preservation, and channel composition.
"""

from __future__ import annotations
from typing import List, Dict, Any, Tuple
import numpy as np
from .channels import compute_choi_matrix

class CPTPValidationError(Exception):
    pass

def validate_cptp(kraus_ops: List[np.ndarray], tol: float = 1e-10) -> Dict[str, Any]:
    r"""
    Rigorously verifies CPTP criteria for a set of Kraus operators:
    1. Completeness / Trace Preservation: sum_k K_k^\dagger K_k = I
    2. Complete Positivity: Choi matrix J(E) is Positive Semidefinite (eigenvalues >= -tol)
    3. Action on random density matrices preserves trace=1 and positivity.
    """
    dim = kraus_ops[0].shape[0]

    # Check 1: Trace Preservation
    sum_k_dag_k = np.zeros((dim, dim), dtype=np.complex128)
    for k in kraus_ops:
        sum_k_dag_k += k.conj().T @ k

    tp_diff = np.linalg.norm(sum_k_dag_k - np.eye(dim, dtype=np.complex128))
    is_trace_preserving = bool(tp_diff <= tol)

    # Check 2: Complete Positivity via Choi Matrix
    choi = compute_choi_matrix(kraus_ops, dim=dim)
    choi_eigs = np.linalg.eigvalsh(choi)
    min_choi_eig = float(np.min(choi_eigs))
    is_completely_positive = bool(min_choi_eig >= -tol)

    # Check 3: Action on random density matrices
    random_test_passed = True
    rng = np.random.default_rng(1337)
    for _ in range(10):
        # Generate random Ginibre matrix -> Wishart state
        g = rng.normal(size=(dim, dim)) + 1j * rng.normal(size=(dim, dim))
        rho_in = g @ g.conj().T
        rho_in /= np.trace(rho_in)

        # Apply channel
        rho_out = np.zeros((dim, dim), dtype=np.complex128)
        for k in kraus_ops:
            rho_out += k @ rho_in @ k.conj().T

        # Verify trace = 1
        if abs(np.trace(rho_out).real - 1.0) > tol:
            random_test_passed = False
            break

        # Verify eigenvalues >= -tol
        out_eigs = np.linalg.eigvalsh(rho_out)
        if np.min(out_eigs) < -tol:
            random_test_passed = False
            break

    is_cptp = bool(is_trace_preserving and is_completely_positive and random_test_passed)

    return {
        "is_cptp": is_cptp,
        "is_trace_preserving": is_trace_preserving,
        "is_completely_positive": is_completely_positive,
        "trace_preserving_residual": float(tp_diff),
        "choi_min_eigenvalue": min_choi_eig,
        "random_density_tests_passed": bool(random_test_passed)
    }


def verify_channel_composition(c1_ops: List[np.ndarray], c2_ops: List[np.ndarray], tol: float = 1e-10) -> Dict[str, Any]:
    """
    Verifies that the composition E = E2 o E1 is also strictly CPTP.
    Kraus operators of composition are {K_j^(2) K_i^(1)}.
    """
    composed_ops = []
    for k2 in c2_ops:
        for k1 in c1_ops:
            composed_ops.append(k2 @ k1)

    return validate_cptp(composed_ops, tol=tol)
