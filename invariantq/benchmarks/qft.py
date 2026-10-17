"""
Quantum Fourier Transform (QFT) Benchmark Circuit Generator.
"""

from __future__ import annotations
import math
from ..ir.qir import CircuitIR, GateOp, QWire

def create_qft_circuit(num_qubits: int) -> CircuitIR:
    circuit = CircuitIR(name=f"qft_{num_qubits}q")
    circuit.add_qubit_register("q", num_qubits)
    circuit.add_clbit_register("c", num_qubits)

    for i in range(num_qubits):
        circuit.add_op(GateOp(name="h", qubits=[QWire("q", i)]))
        for j in range(i + 1, num_qubits):
            theta = math.pi / (2 ** (j - i))
            # Controlled phase gate represented as standard sequence or p gate
            circuit.add_op(GateOp(name="rz", qubits=[QWire("q", j)], params=[theta / 2.0]))
            circuit.add_op(GateOp(name="cx", qubits=[QWire("q", i), QWire("q", j)]))
            circuit.add_op(GateOp(name="rz", qubits=[QWire("q", j)], params=[-theta / 2.0]))
            circuit.add_op(GateOp(name="cx", qubits=[QWire("q", i), QWire("q", j)]))

    # Swaps
    for i in range(num_qubits // 2):
        circuit.add_op(GateOp(name="swap", qubits=[QWire("q", i), QWire("q", num_qubits - 1 - i)]))

    return circuit
