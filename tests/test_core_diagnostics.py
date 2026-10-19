from invariantq.core.binding import HAS_NATIVE_CORE, native_core_status
from invariantq.language.qasm_parser import parse_iq_lang
from invariantq.simulator.statevector import StateVectorSimulator
from invariantq.simulator.stabilizer import StabilizerSimulator
from invariantq.simulator.tensor_network import TensorNetworkSimulator
from invariantq.verification.fault_injection import FaultInjectionTester
from invariantq.noise.cptp_validator import validate_cptp
import numpy as np
import pytest


def test_core_status_is_explicit_and_attached_to_results():
    status = native_core_status()
    assert status["active"] is HAS_NATIVE_CORE
    assert status["implementation"] in {"native-cpp", "portable-numpy-fallback"}
    result = StateVectorSimulator().run(parse_iq_lang("qubit q[1]; h q[0];"), shots=4)
    assert result.metadata["core"] == status


def test_fallback_structures_and_fault_rejection_telemetry():
    circuit = parse_iq_lang("qubit q[1]; h q[0];")
    for simulator in (StateVectorSimulator(), StabilizerSimulator(), TensorNetworkSimulator()):
        with pytest.raises(ValueError, match="positive integer"):
            simulator.run(circuit, shots=0)

    telemetry = FaultInjectionTester().test_corrupted_gate_detection()
    assert telemetry["bug_caught"] is True
    assert telemetry["metadata"]["validation"] == "unitarity"
    assert telemetry["metadata"]["is_unitary"] is False
    assert telemetry["metadata"]["allow_non_unitary"] is True
    assert telemetry["metadata"]["state_norm"] != pytest.approx(1.0)


def test_results_report_algorithm_and_resource_provenance():
    circuit = parse_iq_lang("qubit q[1]; h q[0];")
    result = StateVectorSimulator(max_memory_bytes=1024).run(circuit, shots=2)
    assert result.metadata["provenance"]["implementation"] == "dense_statevector"
    assert result.metadata["provenance"]["completion"] == "completed"

    with pytest.raises(MemoryError, match="above configured limit"):
        StateVectorSimulator(max_memory_bytes=16).run(circuit, shots=2)


def test_malformed_kraus_input_fails_closed():
    result = validate_cptp([])
    assert result["is_cptp"] is False
    assert "required" in result["validation_error"]

    result = validate_cptp([np.ones((2, 2)), np.ones((3, 3))])
    assert result["is_cptp"] is False
    assert "equal dimensions" in result["validation_error"]
