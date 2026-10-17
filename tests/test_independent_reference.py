"""
Independent Differential Reference Tests.
Validates INVARIANTQ C++ kernels against pure NumPy tensor contraction reference.
"""

import numpy as np
import pytest
from invariantq.language.qasm_parser import parse_iq_lang
from invariantq.simulator.statevector import StateVectorSimulator
from invariantq.simulator.density_matrix import DensityMatrixSimulator
from invariantq.simulator.tensor_network import TensorNetworkSimulator
from invariantq.verification.independent_reference import run_independent_reference
from invariantq.benchmarks.suite import create_random_circuit, create_ghz_circuit

def test_independent_reference_ghz():
    circ = create_ghz_circuit(4)
    ref_sv = run_independent_reference(circ)

    sim = StateVectorSimulator()
    res = sim.run(circ, shots=100)

    # State vectors must match with machine precision
    fidelity = abs(np.vdot(ref_sv, res.statevector)) ** 2
    assert np.isclose(fidelity, 1.0, atol=1e-12)

def test_independent_reference_random_circuits():
    sim = StateVectorSimulator()
    mps_sim = TensorNetworkSimulator()

    for seed in range(5):
        circ = create_random_circuit(num_qubits=4, depth=6, seed=seed)
        ref_sv = run_independent_reference(circ)

        # C++ StateVector comparison
        res_sv = sim.run(circ, shots=100)
        fid_sv = abs(np.vdot(ref_sv, res_sv.statevector)) ** 2
        assert np.isclose(fid_sv, 1.0, atol=1e-10)

        # C++ MPS comparison
        res_mps = mps_sim.run(circ, shots=100)
        fid_mps = abs(np.vdot(ref_sv, res_mps.statevector)) ** 2
        assert np.isclose(fid_mps, 1.0, atol=1e-5)

def test_independent_reference_against_density_matrix():
    circ = parse_iq_lang("""
    qubit q[3];
    h q[0];
    rx(0.4) q[1];
    cx q[0], q[1];
    ry(0.6) q[2];
    cx q[1], q[2];
    """)
    ref_sv = run_independent_reference(circ)
    expected_rho = np.outer(ref_sv, ref_sv.conj())

    dm_sim = DensityMatrixSimulator()
    res_dm = dm_sim.run(circ, shots=100)
    actual_rho = res_dm.density_matrix

    diff = np.linalg.norm(expected_rho - actual_rho)
    assert diff < 1e-10
