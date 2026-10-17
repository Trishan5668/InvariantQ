"""
Differential, Metamorphic, and Property-Based Verification Test Suite.
"""

import numpy as np
import pytest
from invariantq.language.qasm_parser import parse_iq_lang
from invariantq.verification.metamorphic import MetamorphicTester
from invariantq.verification.differential import DifferentialTester
from invariantq.verification.fault_injection import FaultInjectionTester
from invariantq.benchmarks.suite import create_ghz_circuit, create_random_circuit

def test_metamorphic_identity_insertion():
    circ = create_ghz_circuit(4)
    tester = MetamorphicTester(tolerance=1e-4)
    res = tester.test_identity_insertion(circ, shots=1000)
    assert res.passed is True
    assert res.distance <= 1e-4

def test_metamorphic_commutation_reordering():
    circ = parse_iq_lang("""
    qubit q[3];
    rz(0.5) q[0];
    rz(0.2) q[1];
    cx q[0], q[2];
    cx q[1], q[2];
    """)
    tester = MetamorphicTester(tolerance=1e-4)
    res = tester.test_commutation_reordering(circ, shots=1000)
    assert res.passed is True

def test_metamorphic_bit_inversion():
    circ = create_ghz_circuit(3)
    tester = MetamorphicTester(tolerance=1e-4)
    res = tester.test_bit_reversal(circ, shots=1000)
    assert res.passed is True

def test_differential_ghz():
    circ = create_ghz_circuit(3)
    tester = DifferentialTester(tolerance=1e-3)
    res = tester.compare_circuits(circ, shots=2000)
    assert res["passed"] is True
    assert "statevector" in res["backends_compared"]
    assert "mps" in res["backends_compared"]
    assert "density_matrix" in res["backends_compared"]

def test_property_unitary_preservation():
    # Verify that randomly generated circuits preserve statevector norm ||psi|| == 1.0
    from invariantq.simulator.statevector import StateVectorSimulator
    sim = StateVectorSimulator()
    for seed in range(5):
        circ = create_random_circuit(num_qubits=4, depth=10, seed=seed)
        res = sim.run(circ, shots=100)
        norm_sq = np.sum(np.abs(res.statevector)**2)
        assert np.isclose(norm_sq, 1.0, atol=1e-9)

def test_property_density_matrix_psd():
    # Verify density matrix remains positive semidefinite and trace=1 after multiple noisy gates
    from invariantq.simulator.density_matrix import DensityMatrixSimulator
    circ = parse_iq_lang("""
    qubit q[2];
    h q[0];
    noise depolarizing(0.05) q[0];
    cx q[0], q[1];
    noise amp_damping(0.04) q[1];
    """)
    dm_sim = DensityMatrixSimulator()
    res = dm_sim.run(circ, shots=100)
    mat = res.density_matrix

    # Trace == 1
    assert np.isclose(np.trace(mat).real, 1.0, atol=1e-9)
    # Eigenvalues >= 0
    eigs = np.linalg.eigvalsh(mat)
    assert np.all(eigs >= -1e-10)
    # Hermitian rho == rho^\dagger
    assert np.allclose(mat, mat.conj().T, atol=1e-9)
