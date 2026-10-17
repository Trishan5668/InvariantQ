"""
Suite of standard reference quantum circuits for benchmarking and regression testing.
"""

from __future__ import annotations
import numpy as np
from ..ir.qir import CircuitIR, GateOp, QWire

def create_ghz_circuit(num_qubits: int) -> CircuitIR:
    circuit = CircuitIR(name=f"ghz_{num_qubits}q")
    circuit.add_qubit_register("q", num_qubits)
    circuit.add_clbit_register("c", num_qubits)

    circuit.add_op(GateOp(name="h", qubits=[QWire("q", 0)]))
    for i in range(num_qubits - 1):
        circuit.add_op(GateOp(name="cx", qubits=[QWire("q", i), QWire("q", i + 1)]))

    return circuit


def create_random_clifford_circuit(num_qubits: int, depth: int = 10, seed: int = 42) -> CircuitIR:
    rng = np.random.default_rng(seed)
    circuit = CircuitIR(name=f"random_clifford_{num_qubits}q_d{depth}")
    circuit.add_qubit_register("q", num_qubits)
    circuit.add_clbit_register("c", num_qubits)

    single_q_gates = ["h", "s", "x", "y", "z"]

    for _ in range(depth):
        for q in range(num_qubits):
            g = rng.choice(single_q_gates)
            circuit.add_op(GateOp(name=g, qubits=[QWire("q", q)]))

        if num_qubits > 1:
            q0, q1 = rng.choice(num_qubits, size=2, replace=False)
            circuit.add_op(GateOp(name="cx", qubits=[QWire("q", int(q0)), QWire("q", int(q1))]))

    return circuit


def create_random_circuit(num_qubits: int, depth: int = 8, seed: int = 42) -> CircuitIR:
    rng = np.random.default_rng(seed)
    circuit = CircuitIR(name=f"random_{num_qubits}q_d{depth}")
    circuit.add_qubit_register("q", num_qubits)
    circuit.add_clbit_register("c", num_qubits)

    single_q_gates = ["rx", "ry", "rz", "h", "t"]

    for _ in range(depth):
        for q in range(num_qubits):
            g = rng.choice(single_q_gates)
            params = [float(rng.uniform(0, 2 * np.pi))] if g in ("rx", "ry", "rz") else []
            circuit.add_op(GateOp(name=g, qubits=[QWire("q", q)], params=params))

        if num_qubits > 1:
            q0, q1 = rng.choice(num_qubits, size=2, replace=False)
            circuit.add_op(GateOp(name="cx", qubits=[QWire("q", int(q0)), QWire("q", int(q1))]))

    return circuit
