import threading

import pytest

from invariantq.execution import (
    CancellationToken,
    ExecutionCancelledError,
    ExecutionContext,
    DeadlineExceededError,
    ExecutionLimits,
    ResourceLimitError,
    ResourcePool,
)
from invariantq.faults import FaultCategory, FaultScenario, RuntimeFaultSandbox
from invariantq.language.qasm_parser import parse_iq_lang
from invariantq.simulator.statevector import StateVectorSimulator


def test_deadline_and_cancellation_are_cooperative():
    circuit = parse_iq_lang("qubit q[1]; h q[0];")
    expired = ExecutionContext(ExecutionLimits(deadline_seconds=0))
    with pytest.raises(DeadlineExceededError):
        StateVectorSimulator().run(circuit, shots=2, execution_context=expired)
    token = CancellationToken()
    token.cancel()
    with pytest.raises(ExecutionCancelledError):
        StateVectorSimulator().run(
            circuit,
            shots=2,
            execution_context=ExecutionContext(cancellation=token),
        )


def test_resource_pool_releases_after_failure_and_rejects_aggregate_capacity():
    pool = ResourcePool(memory_bytes=100, max_jobs=1)
    context = ExecutionContext(resource_pool=pool, reservation_bytes=80)
    with context:
        assert pool.active_jobs == 1
        with pytest.raises(ResourceLimitError):
            with ExecutionContext(resource_pool=pool, reservation_bytes=20):
                pass
    assert pool.active_jobs == 0
    assert pool.reserved_memory_bytes == 0


def test_fault_sandbox_is_opt_in_isolated_and_reproducible():
    sandbox = RuntimeFaultSandbox()

    def execute(**kwargs):
        return {"seed": kwargs["seed"], "value": 1}

    report = sandbox.run(
        execute,
        scenario=FaultScenario(FaultCategory.BACKEND_EXCEPTION),
        seed=7,
    )
    assert report.status == "fault_detected"
    assert report.baseline_status == "completed"
    assert report.baseline_result == {"seed": 7, "value": 1}
