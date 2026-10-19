from invariantq.core.binding import HAS_NATIVE_CORE, native_core_status
from invariantq.language.qasm_parser import parse_iq_lang
from invariantq.simulator.statevector import StateVectorSimulator


def test_core_status_is_explicit_and_attached_to_results():
    status = native_core_status()
    assert status["active"] is HAS_NATIVE_CORE
    assert status["implementation"] in {"native-cpp", "portable-numpy-fallback"}
    result = StateVectorSimulator().run(parse_iq_lang("qubit q[1]; h q[0];"), shots=4)
    assert result.metadata["core"] == status
