"""
Verification of Quantum Phase Estimation (QPE), Deutsch-Jozsa,
Randomized Benchmarking, Two-Qubit Noise Channels, and Mid-Circuit Reset operations.
"""

import numpy as np
import pytest
from invariantq.language.qasm_parser import parse_iq_lang
from invariantq.benchmarks.deutsch_jozsa import create_deutsch_jozsa_circuit
from invariantq.benchmarks.qpe import create_qpe_circuit
from invariantq.benchmarks.randomized_benchmarking import run_randomized_benchmarking
from invariantq.simulator.statevector import StateVectorSimulator
from invariantq.simulator.density_matrix import DensityMatrixSimulator
from invariantq.simulator.stabilizer import StabilizerSimulator
from invariantq.noise.channels import depolarizing_2q, thermal_relaxation, build_kraus_channel
from invariantq.noise.cptp_validator import validate_cptp

def test_deutsch_jozsa_constant():
    sim = StateVectorSimulator()
    circ = create_deutsch_jozsa_circuit(num_qubits=3, oracle_type="constant_one")
    res = sim.run(circ, shots=500)
    # The 3 input qubits (bits 0, 1, 2) must all measure 0
    p_zeros = sum(cnt for bs, cnt in res.counts.items() if bs[-3:] == "000") / 500.0
    assert p_zeros == 1.0

def test_deutsch_jozsa_balanced():
    sim = StateVectorSimulator()
    circ = create_deutsch_jozsa_circuit(num_qubits=3, oracle_type="balanced")
    res = sim.run(circ, shots=500)
    # The 3 input qubits can never measure 000
    p_zeros = sum(cnt for bs, cnt in res.counts.items() if bs[-3:] == "000") / 500.0
    assert p_zeros == 0.0

def test_quantum_phase_estimation():
    sim = StateVectorSimulator()
    # Phase = 0.375 = 3/8 = 0.011_2 in 3 counting bits
    circ = create_qpe_circuit(phase=0.375, num_counting_qubits=3)
    res = sim.run(circ, shots=500)
    # Target qubit is at index 3 (|1>), counting qubits at indices 0, 1, 2 should read 011 (3)
    p_011 = sum(cnt for bs, cnt in res.counts.items() if bs[-3:] == "011") / 500.0
    assert p_011 == 1.0

def test_randomized_benchmarking_noiseless():
    res = run_randomized_benchmarking(sequence_lengths=[2, 4, 8], num_seeds=5)
    assert res["is_perfect_identity_noiseless"] is True
    for m, surv in res["avg_survival"].items():
        assert np.isclose(surv, 1.0, atol=1e-5)

def test_randomized_benchmarking_noisy_decay():
    noisy_kraus = build_kraus_channel("depolarizing", [0.03])
    noise_dict = {g: noisy_kraus for g in ["h", "s", "x", "y", "z", "u_inv"]}
    res = run_randomized_benchmarking(sequence_lengths=[2, 8, 16], num_seeds=4, noise_model=noise_dict)
    # Decaying survival probability
    assert res["avg_survival"][2] > res["avg_survival"][8] > res["avg_survival"][16]

def test_two_qubit_depolarizing_cptp():
    chan = depolarizing_2q(p=0.08)
    val = validate_cptp(chan)
    assert val["is_cptp"] is True
    assert val["is_trace_preserving"] is True
    assert val["is_completely_positive"] is True
    assert val["choi_min_eigenvalue"] >= -1e-10

def test_thermal_relaxation_cptp():
    chan = thermal_relaxation(t1=50.0, t2=40.0, gate_time=0.1)
    val = validate_cptp(chan)
    assert val["is_cptp"] is True
    assert val["is_trace_preserving"] is True
    assert val["is_completely_positive"] is True
    assert val["choi_min_eigenvalue"] >= -1e-10

def test_mid_circuit_reset_statevector():
    # Prepare |1>, reset to |0>, should end in |0>
    circ = parse_iq_lang("""
    qubit q[1];
    x q[0];
    reset q[0];
    """)
    sim = StateVectorSimulator()
    res = sim.run(circ, shots=100)
    assert np.isclose(res.probabilities.get("0", 0.0), 1.0)

def test_mid_circuit_reset_stabilizer():
    circ = parse_iq_lang("""
    qubit q[2];
    h q[0];
    cx q[0], q[1];
    reset q[0];
    """)
    sim = StabilizerSimulator()
    res = sim.run(circ, shots=100)
    # After resetting q0 to |0>, bit 0 is always 0
    for bs in res.counts.keys():
        assert bs[0] == "0"
