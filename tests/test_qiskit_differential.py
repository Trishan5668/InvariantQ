"""Optional differential tests against Qiskit's independently implemented Statevector.

Qiskit and INVARIANTQ both number q[0] as the least-significant global
amplitude bit. Their *matrix local-bit* ordering differs: INVARIANTQ's first
listed wire is the matrix MSB, while Qiskit's first ``qargs`` wire is its local
LSB. Multi-qubit qargs are therefore reversed at the adapter boundary.
"""

import numpy as np
import pytest

qiskit = pytest.importorskip("qiskit", reason="install requirements-dev.txt for external differential tests")
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector

from invariantq.benchmarks.suite import create_random_circuit
from invariantq.simulator.statevector import StateVectorSimulator


def _equivalent_up_to_global_phase(actual: np.ndarray, reference: np.ndarray, atol: float = 1e-10):
    index = int(np.argmax(np.abs(reference)))
    phase = actual[index] / reference[index]
    np.testing.assert_allclose(actual, phase * reference, atol=atol, rtol=atol)


@pytest.mark.parametrize("seed", range(5))
def test_seeded_small_circuits_agree_with_qiskit(seed):
    circuit = create_random_circuit(num_qubits=4, depth=8, seed=seed)
    qiskit_circuit = QuantumCircuit(circuit.num_qubits)
    for op in circuit.ops:
        # The generated fixture contains only GateOp instances; applying the
        # stored matrix avoids accidentally testing a name/parameter adapter.
        qubits = [circuit.get_qubit_index(wire) for wire in op.qubits]
        qiskit_circuit.unitary(op.matrix, list(reversed(qubits)))

    actual = StateVectorSimulator().run(circuit, shots=16, seed=seed).statevector
    reference = Statevector.from_instruction(qiskit_circuit).data
    _equivalent_up_to_global_phase(actual, reference)
