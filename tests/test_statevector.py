"""
Test Stage 3: Multi-Modal Simulators (StateVector, Density Matrix, Stabilizer, MPS).
"""

import numpy as np
import pytest
from invariantq.language.qasm_parser import parse_iq_lang
from invariantq.simulator.statevector import StateVectorSimulator
from invariantq.simulator.density_matrix import DensityMatrixSimulator
from invariantq.simulator.stabilizer import StabilizerSimulator
from invariantq.simulator.tensor_network import TensorNetworkSimulator
from invariantq.simulator.adaptive import AdaptivePlannerSimulator

def test_statevector_ghz():
    code = """
    qubit q[3];
    h q[0];
    cx q[0], q[1];
    cx q[1], q[2];
    """
    circ = parse_iq_lang(code)
    sim = StateVectorSimulator()
    res = sim.run(circ, shots=2000, seed=42)

    # GHZ state (|000> + |111>) / sqrt(2)
    assert "000" in res.counts
    assert "111" in res.counts
    # Should not have any 001, 010, 100, etc.
    for k in res.counts:
        assert k in ("000", "111")
    assert np.isclose(res.probabilities["000"], 0.5, atol=1e-5)
    assert np.isclose(res.probabilities["111"], 0.5, atol=1e-5)

def test_density_matrix_purity():
    code = """
    qubit q[2];
    h q[0];
    cx q[0], q[1];
    """
    circ = parse_iq_lang(code)
    sim = DensityMatrixSimulator()
    res = sim.run(circ, shots=1000)

    # Pure state must have trace=1.0 and purity=1.0
    assert np.isclose(res.metadata["trace"], 1.0, atol=1e-9)
    assert np.isclose(res.metadata["purity"], 1.0, atol=1e-9)

def test_density_matrix_noisy_decoherence():
    code = """
    qubit q[1];
    h q[0];
    noise depolarizing(0.2) q[0];
    """
    circ = parse_iq_lang(code)
    sim = DensityMatrixSimulator()
    res = sim.run(circ, shots=1000)

    # After noise, trace remains 1.0, but purity drops < 1.0
    assert np.isclose(res.metadata["trace"], 1.0, atol=1e-9)
    assert res.metadata["purity"] < 1.0

def test_stabilizer_ghz_scaling():
    # 20-qubit GHZ state in Clifford stabilizer simulator
    n = 20
    gates = ["qubit q[20];", "h q[0];"]
    for i in range(n - 1):
        gates.append(f"cx q[{i}], q[{i+1}];")
    code = "\n".join(gates)
    circ = parse_iq_lang(code)

    sim = StabilizerSimulator()
    res = sim.run(circ, shots=500, seed=123)

    # All outcomes must be all-zeros or all-ones
    all_zeros = "0" * n
    all_ones = "1" * n
    for k in res.counts:
        assert k in (all_zeros, all_ones)

def test_mps_bell_overlap():
    code = """
    qubit q[2];
    h q[0];
    cx q[0], q[1];
    """
    circ = parse_iq_lang(code)
    mps_sim = TensorNetworkSimulator()
    res = mps_sim.run(circ, shots=1000)

    # Overlap with true Bell state
    expected = np.array([1/np.sqrt(2), 0, 0, 1/np.sqrt(2)], dtype=np.complex128)
    fid = abs(np.vdot(expected, res.statevector)) ** 2
    assert np.isclose(fid, 1.0, atol=1e-5)
    assert np.isclose(res.entanglement_entropy, 1.0, atol=1e-4)

def test_adaptive_planner_routing():
    planner = AdaptivePlannerSimulator()

    # Clifford circuit -> Stabilizer
    cliff_circ = parse_iq_lang("qubit q[10]; h q[0]; cx q[0], q[1];")
    d1 = planner.plan(cliff_circ)
    assert d1.backend_name == "stabilizer"

    # Small non-Clifford circuit -> StateVector
    rot_circ = parse_iq_lang("qubit q[4]; rx(0.3) q[0];")
    d2 = planner.plan(rot_circ)
    assert d2.backend_name == "statevector"

    # Small noisy circuit -> Density Matrix
    noise_circ = parse_iq_lang("qubit q[3]; h q[0]; noise depolarizing(0.05) q[0];")
    d3 = planner.plan(noise_circ)
    assert d3.backend_name == "density_matrix"
