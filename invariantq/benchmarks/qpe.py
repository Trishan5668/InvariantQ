"""
Quantum Phase Estimation (QPE) Benchmark Circuit Generator.
Estimates the phase theta of unitary U |psi> = exp(2 pi i theta) |psi> using an inverse QFT.
"""

from __future__ import annotations
import math
from ..ir.qir import CircuitIR, GateOp, QWire

def create_qpe_circuit(phase: float = 0.375, num_counting_qubits: int = 3) -> CircuitIR:
    """
    Creates QPE circuit to estimate phase theta in U = P(2 pi theta).
    Target state is |1> on the target qubit.
    num_counting_qubits: number of precision bits.
    Total qubits = num_counting_qubits + 1 (target qubit).
    """
    total_qubits = num_counting_qubits + 1
    target_qubit = num_counting_qubits

    circuit = CircuitIR(name=f"qpe_{num_counting_qubits}q_phase_{phase}")
    circuit.add_qubit_register("q", total_qubits)
    circuit.add_clbit_register("c", num_counting_qubits)

    # 1. Prepare target qubit in eigenstate |1>
    circuit.add_op(GateOp(name="x", qubits=[QWire("q", target_qubit)]))

    # 2. Put counting qubits in superposition
    for i in range(num_counting_qubits):
        circuit.add_op(GateOp(name="h", qubits=[QWire("q", i)]))

    # 3. Controlled-U^(2^j) operations
    # Here U is phase gate P(2 pi theta).
    # Controlled-U^(2^j) is Controlled-P(2 pi theta * 2^j)
    for j in range(num_counting_qubits):
        angle = 2.0 * math.pi * phase * (2 ** j)
        circuit.add_op(GateOp(
            name="cp",
            qubits=[QWire("q", j), QWire("q", target_qubit)],
            params=[angle]
        ))

    # 4. Inverse QFT on counting qubits
    # Swaps
    for i in range(num_counting_qubits // 2):
        circuit.add_op(GateOp(
            name="swap",
            qubits=[QWire("q", i), QWire("q", num_counting_qubits - 1 - i)]
        ))

    # Inverse Hadamard & Controlled Phase sequence
    for i in range(num_counting_qubits):
        for j in range(i):
            theta = -math.pi / (2 ** (i - j))
            circuit.add_op(GateOp(
                name="cp",
                qubits=[QWire("q", j), QWire("q", i)],
                params=[theta]
            ))
        circuit.add_op(GateOp(name="h", qubits=[QWire("q", i)]))

    return circuit
