"""
Test Stage 4 & 5: CPTP Noise Channels and Distributed Execution.
"""

import numpy as np
import pytest
from invariantq.noise.channels import build_kraus_channel
from invariantq.noise.cptp_validator import validate_cptp, verify_channel_composition
from invariantq.noise.readout import ReadoutError
from invariantq.language.qasm_parser import parse_iq_lang
from invariantq.distributed.scheduler import DistributedScheduler
from invariantq.distributed.planner import DistributedPlanner

def test_depolarizing_cptp():
    kraus = build_kraus_channel("depolarizing", [0.1])
    val = validate_cptp(kraus)
    assert val["is_cptp"] is True
    assert val["is_trace_preserving"] is True
    assert val["is_completely_positive"] is True
    assert val["random_density_tests_passed"] is True

def test_amplitude_damping_cptp():
    kraus = build_kraus_channel("amp_damping", [0.15])
    val = validate_cptp(kraus)
    assert val["is_cptp"] is True
    assert val["is_trace_preserving"] is True
    assert val["is_completely_positive"] is True

def test_phase_damping_cptp():
    kraus = build_kraus_channel("phase_damping", [0.08])
    val = validate_cptp(kraus)
    assert val["is_cptp"] is True

def test_channel_composition():
    # Depolarizing o Amplitude Damping
    c1 = build_kraus_channel("depolarizing", [0.05])
    c2 = build_kraus_channel("amp_damping", [0.05])
    val = verify_channel_composition(c1, c2)
    assert val["is_cptp"] is True

def test_readout_error_and_mitigation():
    ro = ReadoutError(p01=0.03, p10=0.04)
    # Ideal Bell state counts
    ideal_counts = {"00": 5000, "11": 5000}
    noisy_counts = ro.apply_to_counts(ideal_counts, seed=42)

    # Noisy counts should now contain spurious states like 01 and 10
    assert "01" in noisy_counts or "10" in noisy_counts

    # Mitigate
    mitigated = ro.mitigate_counts(noisy_counts, num_qubits=2)
    assert np.isclose(mitigated.get("00", 0.0), 0.5, atol=0.04)
    assert np.isclose(mitigated.get("11", 0.0), 0.5, atol=0.04)

def test_distributed_execution_and_aggregation():
    circ = parse_iq_lang("qubit q[2]; h q[0]; cx q[0], q[1];")
    scheduler = DistributedScheduler(num_workers=4)

    res = scheduler.execute_job("test_dist_job", circ, total_shots=4000, master_seed=42)
    assert res.total_shots == 4000
    assert res.num_tasks == 4

    p00 = res.counts["00"] / 4000.0
    p11 = res.counts["11"] / 4000.0
    assert np.isclose(p00, 0.5, atol=0.03)
    assert np.isclose(p11, 0.5, atol=0.03)
    # 95% Confidence interval must bound the true expectation
    ci_low, ci_high = res.confidence_interval_95
    assert ci_low <= res.z_expectation <= ci_high
