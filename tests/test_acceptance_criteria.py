"""
Comprehensive Acceptance Tests for INVARIANTQ Platform (Section 10 Success Criteria).
"""

import math
import numpy as np
import pytest

from invariantq.language.qasm_parser import parse_iq_lang
from invariantq.compiler.optimizer import Compiler
from invariantq.compiler.synthesis import verify_unitary_equivalence
from invariantq.simulator.statevector import StateVectorSimulator
from invariantq.simulator.density_matrix import DensityMatrixSimulator
from invariantq.simulator.tensor_network import TensorNetworkSimulator
from invariantq.simulator.stabilizer import StabilizerSimulator
from invariantq.noise.channels import build_kraus_channel
from invariantq.noise.cptp_validator import validate_cptp
from invariantq.distributed.scheduler import DistributedScheduler
from invariantq.verification.fault_injection import FaultInjectionTester
from invariantq.verification.metamorphic import MetamorphicTester
from invariantq.verification.differential import DifferentialTester
from invariantq.benchmarks.runner import BenchmarkRunner
from invariantq.benchmarks.qft import create_qft_circuit
from invariantq.benchmarks.grover import create_grover_circuit
from invariantq.benchmarks.vqe import VQESolver
from invariantq.reproducibility.ledger import ReproducibilityLedger

# Criterion 1: Compiler correctness & Semantic Equivalence
def test_acceptance_compiler_correctness():
    circ = parse_iq_lang("""
    qubit q[3];
    h q[0];
    h q[0];
    x q[1];
    x q[1];
    rz(0.3) q[2];
    rz(0.7) q[2];
    cx q[0], q[1];
    cx q[0], q[1];
    """)
    compiler = Compiler(opt_level=2, enable_fusion=False)
    res = compiler.compile(circ)

    assert res.is_equivalent is True
    assert res.optimized_gate_count == 1
    assert math.isclose(res.circuit.ops[0].params[0], 1.0, rel_tol=1e-5)

# Criterion 2: Multi-backend agreement
def test_acceptance_multi_backend_agreement():
    circ = parse_iq_lang("""
    qubit q[3];
    h q[0];
    cx q[0], q[1];
    cx q[1], q[2];
    """)
    tester = DifferentialTester(tolerance=1e-3)
    diff = tester.compare_circuits(circ, shots=2000, seed=42)

    assert diff["passed"] is True
    # Verify StateVector, Density Matrix, and MPS all agree on GHZ probabilities
    p_sv = diff["sv_probabilities"]
    p_mps = diff["mps_probabilities"]
    assert np.isclose(p_sv.get("000", 0.0), 0.5, atol=0.04)
    assert np.isclose(p_sv.get("111", 0.0), 0.5, atol=0.04)
    assert np.isclose(p_mps.get("000", 0.0), 0.5, atol=0.04)
    assert np.isclose(p_mps.get("111", 0.0), 0.5, atol=0.04)

# Criterion 3: CPTP validation (Choi matrix PSD and trace preservation)
def test_acceptance_cptp_validation():
    channels = ["depolarizing", "amp_damping", "phase_damping", "bit_flip", "phase_flip"]
    for ch in channels:
        kraus = build_kraus_channel(ch, [0.05])
        res = validate_cptp(kraus)
        assert res["is_cptp"] is True
        assert res["is_trace_preserving"] is True
        assert res["is_completely_positive"] is True
        assert res["choi_min_eigenvalue"] >= -1e-10

# Criterion 4: Bug detection by tests (Metamorphic & Differential catch flaws)
def test_acceptance_flaw_detection_by_metamorphic_tests():
    fi = FaultInjectionTester()
    g_res = fi.test_corrupted_gate_detection()
    assert g_res["bug_caught"] is True, "Metamorphic testing must detect and flag corrupted gates!"

    c_res = fi.test_broken_cptp_channel_detection()
    assert c_res["bug_caught"] is True, "CPTP verification must detect non-trace-preserving channels!"

# Criterion 5: Distributed consistency (Single-node vs Distributed)
def test_acceptance_distributed_consistency():
    circ = parse_iq_lang("qubit q[2]; h q[0]; cx q[0], q[1];")

    # Single-process
    sim = StateVectorSimulator()
    single_res = sim.run(circ, shots=10000, seed=42)

    # Distributed
    scheduler = DistributedScheduler(num_workers=4)
    dist_res = scheduler.execute_job("acc_dist_job", circ, total_shots=10000, master_seed=42)

    p00_single = single_res.counts["00"] / 10000.0
    p00_dist = dist_res.counts["00"] / 10000.0

    diff = abs(p00_single - p00_dist)
    assert diff < 0.02, f"Single-node and distributed results must statistically agree (diff={diff:.4f})"

# Criterion 6: Performance benchmarks & Gate Fusion evidence
def test_acceptance_performance_benchmarks():
    runner = BenchmarkRunner()
    fusion_bench = runner.benchmark_gate_fusion_speedup(num_qubits=12, depth=16)

    # Verify fusion consolidated gates into fused blocks
    assert fusion_bench["fusion_beneficial"] is True
    assert fusion_bench["fused_ops"] < fusion_bench["unfused_ops"]
    assert fusion_bench["fusion_groups"] > 0

# Criterion 7: Grover algorithm benchmark
def test_acceptance_grover_search():
    target = "101"
    circ = create_grover_circuit(num_qubits=3, target_bitstring=target)
    sim = StateVectorSimulator()
    res = sim.run(circ, shots=2000, seed=42)

    # Marked state |101> must have highest amplification probability (> 70%)
    p_marked = res.counts.get(target, 0) / 2000.0
    assert p_marked > 0.70, f"Grover search should amplify marked state {target} (got {p_marked:.2%})"

# Criterion 8: VQE algorithm benchmark
def test_acceptance_vqe_convergence():
    vqe = VQESolver(num_qubits=2, J=1.0, h=0.5, layers=1)
    res = vqe.optimize(max_iter=30)
    assert res["ground_state_energy"] < 0.0, "VQE must find negative ground state energy for TFIM"

# Criterion 9: Reproducibility Ledger
def test_acceptance_reproducibility_ledger():
    ledger = ReproducibilityLedger(ledger_dir="/tmp/test_ledger")
    manifest = ledger.record_experiment(
        experiment_id="test_exp_001",
        circuit_name="bell_circuit",
        num_qubits=2,
        gate_count=2,
        backend="statevector",
        compiler_opt_level=2,
        master_seed=42,
        shots=1024,
        execution_time_ms=1.23
    )
    assert manifest.hash_digest != ""
    assert manifest.python_version != ""
    assert manifest.experiment_id == "test_exp_001"
