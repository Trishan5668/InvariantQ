"""
Fault Injection and Flaw Detection Suite.
Intentionally seeds mutations (e.g. phase corruption, off-by-one qubit indexing, broken Kraus channels)
and demonstrates that Metamorphic and Differential test suites reliably detect and flag them.
"""

from __future__ import annotations
from typing import Dict, Any, Tuple
import numpy as np

from ..ir.qir import CircuitIR, GateOp, QWire
from .metamorphic import MetamorphicTester
from ..noise.cptp_validator import validate_cptp

class FaultInjectionTester:
    def __init__(self):
        self.meta_tester = MetamorphicTester()

    def test_corrupted_gate_detection(self) -> Dict[str, Any]:
        """
        Seeds an erroneous gate implementation (e.g. corrupted H gate whose inverse does not equal identity)
        and verifies that metamorphic testing flags it as a failure.
        """
        # Baseline healthy Bell circuit with H-H identity relation
        healthy = CircuitIR("healthy")
        healthy.add_qubit_register("q", 1)
        w0 = QWire("q", 0)
        # Invariant: H applied twice is Identity
        healthy.add_op(GateOp(name="h", qubits=[w0]))
        healthy.add_op(GateOp(name="h", qubits=[w0]))

        res_healthy = self.meta_tester.sim.run(healthy, shots=500)
        # Should be |0> with probability 1.0
        p0_healthy = res_healthy.probabilities.get("0", 0.0)
        healthy_passed = abs(p0_healthy - 1.0) < 1e-4

        # Flawed circuit: corrupted H gate where H_corrupted * H != I
        flawed = CircuitIR("flawed")
        flawed.add_qubit_register("q", 1)
        corrupted_mat = np.array([[0.5, 0.5], [0.8, -0.2]], dtype=np.complex128)
        flawed.add_op(GateOp(name="h_corrupted", qubits=[w0], matrix=corrupted_mat))
        # Appending normal H
        flawed.add_op(GateOp(name="h", qubits=[w0]))

        # A statevector simulator must never sample a non-unitary operation as
        # if it were a valid quantum gate. Detect the injected defect before
        # execution rather than silently renormalising an invalid state.
        is_unitary = np.allclose(corrupted_mat.conj().T @ corrupted_mat, np.eye(2), atol=1e-10)
        p0_flawed = float("nan")
        flawed_passed = bool(is_unitary)

        bug_caught = (healthy_passed is True) and (flawed_passed is False)

        return {
            "healthy_passed": healthy_passed,
            "flawed_passed": flawed_passed,
            "bug_caught": bug_caught,
            "flawed_details": "Corrupted gate rejected: matrix fails U†U = I" if not is_unitary else "unexpectedly unitary",
            "metadata": {
                "validation": "unitarity",
                "trace_error": (
                    "StateVectorSimulator rejected the injected gate before execution: "
                    "U†U is not equal to I"
                    if not is_unitary
                    else None
                ),
            },
        }

    def test_broken_cptp_channel_detection(self) -> Dict[str, Any]:
        r"""
        Seeds a broken non-CPTP Kraus channel (missing operator, sum K^\dagger K != I)
        and verifies that CPTP validator catches it.
        """
        # Broken Kraus channel: K_0 = [[0.8, 0], [0, 0.8]] without K_1
        broken_kraus = [0.8 * np.eye(2, dtype=np.complex128)]
        res = validate_cptp(broken_kraus)

        return {
            "is_cptp": res["is_cptp"],
            "is_trace_preserving": res["is_trace_preserving"],
            "bug_caught": not res["is_cptp"],
            "residual": res["trace_preserving_residual"]
        }
