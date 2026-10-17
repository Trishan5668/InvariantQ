"""
Deutsch-Jozsa Algorithm Benchmark Circuit Generator.
Distinguishes constant vs balanced boolean oracles in a single query with 100% certainty.
"""

from __future__ import annotations
import numpy as np
from ..ir.qir import CircuitIR, GateOp, QWire

def create_deutsch_jozsa_circuit(num_qubits: int = 3, oracle_type: str = "balanced") -> CircuitIR:
    """
    Creates Deutsch-Jozsa circuit for n input qubits + 1 ancilla qubit (total n + 1 qubits).
    oracle_type: 'constant' (returns 0 or 1 for all inputs) or 'balanced' (returns 0 for half, 1 for half).
    """
    total_qubits = num_qubits + 1
    ancilla = num_qubits

    circuit = CircuitIR(name=f"deutsch_jozsa_{oracle_type}_{num_qubits}q")
    circuit.add_qubit_register("q", total_qubits)
    circuit.add_clbit_register("c", num_qubits)

    # Prepare ancilla in |-> = (|0> - |1>) / sqrt(2)
    circuit.add_op(GateOp(name="x", qubits=[QWire("q", ancilla)]))
    circuit.add_op(GateOp(name="h", qubits=[QWire("q", ancilla)]))

    # Apply H to all input qubits
    for i in range(num_qubits):
        circuit.add_op(GateOp(name="h", qubits=[QWire("q", i)]))

    # Oracle implementation
    if oracle_type == "balanced":
        # XOR sum oracle: CNOT from each input qubit to ancilla
        for i in range(num_qubits):
            circuit.add_op(GateOp(name="cx", qubits=[QWire("q", i), QWire("q", ancilla)]))
    elif oracle_type == "constant_one":
        circuit.add_op(GateOp(name="x", qubits=[QWire("q", ancilla)]))
    # constant_zero: identity (does nothing)

    # Final Hadamard on all input qubits
    for i in range(num_qubits):
        circuit.add_op(GateOp(name="h", qubits=[QWire("q", i)]))

    return circuit
