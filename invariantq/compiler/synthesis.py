"""
Gate Synthesis and Mathematical Equivalence Verification.
Decomposes arbitrary unitaries into target gate sets and verifies semantic equivalence.
"""

from __future__ import annotations
import math
from typing import List, Tuple
import numpy as np
from ..ir.qir import CircuitIR, IROp, GateOp, QWire

def verify_unitary_equivalence(u1: np.ndarray, u2: np.ndarray, tol: float = 1e-9) -> bool:
    """
    Verifies that two unitary matrices are equal up to a global phase.
    ||U1 - e^(i phi) U2||_F <= tol
    """
    if u1.shape != u2.shape:
        return False

    dim = u1.shape[0]
    prod = u1.conj().T @ u2
    tr = np.trace(prod)

    # If U1 and U2 are equivalent up to global phase, |Tr(U1^\dagger U2)| == dim
    diff = abs(abs(tr) - dim)
    return bool(diff <= (tol * dim))


class GateSynthesisPass:
    def __init__(self, target_basis: str = "u3_cx"):
        self.target_basis = target_basis

    def run(self, circuit: CircuitIR) -> CircuitIR:
        new_circuit = CircuitIR(name=f"{circuit.name}_synth_{self.target_basis}")
        new_circuit.qubit_regs = dict(circuit.qubit_regs)
        new_circuit.clbit_regs = dict(circuit.clbit_regs)

        for op in circuit.ops:
            if not isinstance(op, GateOp):
                new_circuit.add_op(op)
                continue

            # If target basis is u3_cx
            if self.target_basis == "u3_cx":
                if len(op.qubits) == 1:
                    u = op.matrix
                    theta, phi, lam = self._matrix_to_u3_params(u)
                    u3_op = GateOp(
                        name="u3",
                        qubits=list(op.qubits),
                        params=[theta, phi, lam]
                    )
                    new_circuit.add_op(u3_op)
                else:
                    new_circuit.add_op(op)
            else:
                new_circuit.add_op(op)

        return new_circuit

    def _matrix_to_u3_params(self, u: np.ndarray) -> Tuple[float, float, float]:
        # Global phase normalization
        det = np.linalg.det(u)
        phase = np.angle(det) / 2.0
        u_su2 = u * np.exp(-1j * phase)

        # U = [[cos(t/2), -e^(i lam) sin(t/2)], [e^(i phi) sin(t/2), e^(i(phi+lam)) cos(t/2)]]
        cos_t_half = min(1.0, max(0.0, abs(u_su2[0, 0])))
        theta = 2.0 * math.acos(cos_t_half)

        if abs(math.sin(theta / 2.0)) < 1e-7:
            # Diagonal: theta = 0
            phi_plus_lam = np.angle(u_su2[1, 1]) - np.angle(u_su2[0, 0])
            return theta, phi_plus_lam, 0.0

        phi = np.angle(u_su2[1, 0])
        lam = np.angle(-u_su2[0, 1])
        return float(theta), float(phi), float(lam)
