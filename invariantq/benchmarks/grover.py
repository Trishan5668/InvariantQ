"""
Grover's Search Algorithm Benchmark Circuit Generator.
Constructs exact oracle and diffusion operator circuits.
"""

from __future__ import annotations
import math
import numpy as np
from ..ir.qir import CircuitIR, GateOp, QWire

def create_grover_circuit(num_qubits: int = 3, target_bitstring: str = "101") -> CircuitIR:
    circuit = CircuitIR(name=f"grover_{num_qubits}q")
    circuit.add_qubit_register("q", num_qubits)
    circuit.add_clbit_register("c", num_qubits)

    # 1. State preparation (Hadamard on all qubits)
    for i in range(num_qubits):
        circuit.add_op(GateOp(name="h", qubits=[QWire("q", i)]))

    # Construct multi-qubit CCZ gate
    dim = 1 << num_qubits
    ccz_mat = np.eye(dim, dtype=np.complex128)
    ccz_mat[dim - 1, dim - 1] = -1.0 # Phase flip on |1...1>
    all_qwires = [QWire("q", i) for i in range(num_qubits)]

    # Optimal iterations ~ (pi / 4) * sqrt(2^n)
    num_iterations = max(1, int(round((math.pi / 4.0) * math.sqrt(dim))))

    for _ in range(num_iterations):
        # --- Oracle Phase Inversion ---
        # Invert bits that are '0' in target
        for idx, bit in enumerate(target_bitstring):
            # Target string: index 0 is q0 (or leftmost/rightmost)
            q_idx = num_qubits - 1 - idx
            if bit == "0":
                circuit.add_op(GateOp(name="x", qubits=[QWire("q", q_idx)]))

        circuit.add_op(GateOp(name="ccz", qubits=all_qwires, matrix=ccz_mat))

        for idx, bit in enumerate(target_bitstring):
            q_idx = num_qubits - 1 - idx
            if bit == "0":
                circuit.add_op(GateOp(name="x", qubits=[QWire("q", q_idx)]))

        # --- Diffusion Operator 2|s><s| - I ---
        for i in range(num_qubits):
            circuit.add_op(GateOp(name="h", qubits=[QWire("q", i)]))
            circuit.add_op(GateOp(name="x", qubits=[QWire("q", i)]))

        circuit.add_op(GateOp(name="ccz", qubits=all_qwires, matrix=ccz_mat))

        for i in range(num_qubits):
            circuit.add_op(GateOp(name="x", qubits=[QWire("q", i)]))
            circuit.add_op(GateOp(name="h", qubits=[QWire("q", i)]))

    return circuit
