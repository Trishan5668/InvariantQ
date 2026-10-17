"""
Independent Reference Quantum State Engine for Differential Cross-Validation.
Evaluates quantum circuits using pure NumPy einsum multi-linear algebra contractions
independently of the C++ numerical kernels, MPS, or Stabilizer engines.
"""

from __future__ import annotations
import math
from typing import List, Dict, Any, Tuple
import numpy as np
from ..ir.qir import CircuitIR, GateOp

class IndependentTensorContractionRef:
    """
    Independent reference simulation engine implemented entirely via
    NumPy multi-linear algebra einsum tensor contractions.
    Serves as an independent cross-check for C++ numerical kernels.
    """
    def __init__(self, num_qubits: int):
        self.num_qubits = num_qubits
        self.state_tensor = np.zeros([2] * num_qubits, dtype=np.complex128)
        self.state_tensor[tuple([0] * num_qubits)] = 1.0

    def apply_gate(self, matrix: np.ndarray, qubits: List[int]):
        k = len(qubits)
        n = self.num_qubits
        out_letters = [chr(ord('a') + i) for i in range(n)]

        if k == 1:
            q = qubits[0]
            in_letters = list(out_letters)
            in_letters[q] = 'Z'
            eq = f"{out_letters[q]}Z,{''.join(in_letters)}->{''.join(out_letters)}"
            self.state_tensor = np.einsum(eq, matrix, self.state_tensor)

        elif k == 2:
            q0, q1 = qubits[0], qubits[1]
            u_4d = matrix.reshape((2, 2, 2, 2))
            in_letters = list(out_letters)
            in_letters[q0] = 'Y'
            in_letters[q1] = 'Z'
            eq = f"{out_letters[q0]}{out_letters[q1]}YZ,{''.join(in_letters)}->{''.join(out_letters)}"
            self.state_tensor = np.einsum(eq, u_4d, self.state_tensor)

        elif k == 3:
            q0, q1, q2 = qubits[0], qubits[1], qubits[2]
            u_6d = matrix.reshape((2, 2, 2, 2, 2, 2))
            in_letters = list(out_letters)
            in_letters[q0] = 'X'
            in_letters[q1] = 'Y'
            in_letters[q2] = 'Z'
            eq = f"{out_letters[q0]}{out_letters[q1]}{out_letters[q2]}XYZ,{''.join(in_letters)}->{''.join(out_letters)}"
            self.state_tensor = np.einsum(eq, u_6d, self.state_tensor)

    def get_statevector(self) -> np.ndarray:
        return self.state_tensor.flatten(order='F')

    def get_probabilities(self) -> np.ndarray:
        sv = self.get_statevector()
        return np.abs(sv) ** 2


def run_independent_reference(circuit: CircuitIR) -> np.ndarray:
    """
    Executes a CircuitIR using the independent NumPy tensor contraction engine
    and returns the resulting length-2^n statevector.
    """
    ref = IndependentTensorContractionRef(circuit.num_qubits)
    for op in circuit.ops:
        if isinstance(op, GateOp) and op.matrix is not None:
            qubits = [circuit.get_qubit_index(q) for q in op.qubits]
            ref.apply_gate(op.matrix, qubits)
    return ref.get_statevector()
