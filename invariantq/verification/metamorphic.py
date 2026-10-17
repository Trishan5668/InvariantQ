"""
Metamorphic Testing Framework for Quantum Compilers and Simulators (Chen 2018).
Generates morphed test circuits via mathematical invariants and asserts behavioral consistency.
"""

from __future__ import annotations
import math
from typing import Dict, List, Any, Tuple
import numpy as np

from ..ir.qir import CircuitIR, GateOp, QWire
from ..simulator.statevector import StateVectorSimulator

class MetamorphicTestResult:
    def __init__(self, relation_name: str, passed: bool, distance: float, details: str):
        self.relation_name = relation_name
        self.passed = passed
        self.distance = distance
        self.details = details

class MetamorphicTester:
    def __init__(self, tolerance: float = 1e-4):
        self.tolerance = tolerance
        self.sim = StateVectorSimulator()

    def test_identity_insertion(self, circuit: CircuitIR, shots: int = 2000, seed: int = 42) -> MetamorphicTestResult:
        """
        MR 1: Identity Insertion.
        Inserting self-inverse pairs (H-H, X-X, CX-CX) must preserve the output state and probabilities.
        """
        morphed = CircuitIR(name=f"{circuit.name}_id_morphed")
        morphed.qubit_regs = dict(circuit.qubit_regs)
        morphed.clbit_regs = dict(circuit.clbit_regs)

        # Insert H-H on qubit 0 at the beginning and end
        w0 = QWire("q", 0)
        morphed.add_op(GateOp(name="h", qubits=[w0]))
        morphed.add_op(GateOp(name="h", qubits=[w0]))
        for op in circuit.ops:
            morphed.add_op(op)
        morphed.add_op(GateOp(name="x", qubits=[w0]))
        morphed.add_op(GateOp(name="x", qubits=[w0]))

        res_orig = self.sim.run(circuit, shots=shots, seed=seed)
        res_morphed = self.sim.run(morphed, shots=shots, seed=seed)

        # Compare statevectors
        fidelity = abs(np.vdot(res_orig.statevector, res_morphed.statevector)) ** 2
        diff = 1.0 - fidelity
        passed = bool(diff <= self.tolerance)

        return MetamorphicTestResult(
            relation_name="IdentityInsertion",
            passed=passed,
            distance=float(diff),
            details=f"Fidelity between original and identity-inserted circuit: {fidelity:.6f}"
        )

    def test_commutation_reordering(self, circuit: CircuitIR, shots: int = 2000, seed: int = 42) -> MetamorphicTestResult:
        """
        MR 2: Commutation Reordering.
        Reordering commuting gates (e.g. diagonal gates Rz, S, T or disjoint qubits) must preserve state.
        """
        morphed = CircuitIR(name=f"{circuit.name}_commuted_morphed")
        morphed.qubit_regs = dict(circuit.qubit_regs)
        morphed.clbit_regs = dict(circuit.clbit_regs)

        ops = list(circuit.ops)
        # Find adjacent commuting pair and swap
        swapped = False
        for i in range(len(ops) - 1):
            op1, op2 = ops[i], ops[i + 1]
            if isinstance(op1, GateOp) and isinstance(op2, GateOp):
                # Disjoint qubits commute
                if set(op1.qubits).isdisjoint(set(op2.qubits)):
                    ops[i], ops[i + 1] = op2, op1
                    swapped = True
                    break

        for op in ops:
            morphed.add_op(op)

        res_orig = self.sim.run(circuit, shots=shots, seed=seed)
        res_morphed = self.sim.run(morphed, shots=shots, seed=seed)

        fidelity = abs(np.vdot(res_orig.statevector, res_morphed.statevector)) ** 2
        diff = 1.0 - fidelity
        passed = bool(diff <= self.tolerance)

        return MetamorphicTestResult(
            relation_name="CommutationReordering",
            passed=passed,
            distance=float(diff),
            details=f"Fidelity after commuting gate reorder: {fidelity:.6f} (swapped: {swapped})"
        )

    def test_bit_reversal(self, circuit: CircuitIR, shots: int = 2000, seed: int = 42) -> MetamorphicTestResult:
        """
        MR 3: Bit Inversion Invariance.
        Appending Pauli X to all qubits must invert all bitstrings in the outcome distribution:
        P(x) for original equals P(~x) for morphed!
        """
        morphed = CircuitIR(name=f"{circuit.name}_inverted_morphed")
        morphed.qubit_regs = dict(circuit.qubit_regs)
        morphed.clbit_regs = dict(circuit.clbit_regs)

        for op in circuit.ops:
            morphed.add_op(op)

        # Append X to all qubits
        for reg_name, size in circuit.qubit_regs.items():
            for idx in range(size):
                morphed.add_op(GateOp(name="x", qubits=[QWire(reg_name, idx)]))

        res_orig = self.sim.run(circuit, shots=shots, seed=seed)
        res_morphed = self.sim.run(morphed, shots=shots, seed=seed)

        n = circuit.num_qubits
        max_diff = 0.0

        for bitstr, p_orig in res_orig.probabilities.items():
            inverted_bitstr = "".join("1" if b == "0" else "0" for b in bitstr)
            p_morphed = res_morphed.probabilities.get(inverted_bitstr, 0.0)
            max_diff = max(max_diff, abs(p_orig - p_morphed))

        passed = bool(max_diff <= self.tolerance)
        return MetamorphicTestResult(
            relation_name="BitInversionInvariance",
            passed=passed,
            distance=float(max_diff),
            details=f"Max difference between original P(x) and morphed P(~x): {max_diff:.6e}"
        )
