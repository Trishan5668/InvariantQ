from invariantq.core.binding import HAS_NATIVE_CORE, native_core_status
from invariantq.language.qasm_parser import parse_iq_lang
from invariantq.simulator.statevector import StateVectorSimulator
from invariantq.simulator.stabilizer import StabilizerSimulator
from invariantq.simulator.tensor_network import TensorNetworkSimulator
from invariantq.verification.fault_injection import FaultInjectionTester
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
