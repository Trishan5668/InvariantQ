import pytest

from invariantq.distributed.scheduler import DistributedScheduler
from invariantq.distributed.worker import WorkerNode
from invariantq.language.qasm_parser import parse_iq_lang


def _circuit():
    return parse_iq_lang("qubit q[1]; h q[0];")


def test_scheduler_retries_failed_worker_and_preserves_shots():
    scheduler = DistributedScheduler(num_workers=2, max_retries=2)
    scheduler.workers["worker_0"].fail_next_task = True

    result = scheduler.execute_job("retry-job", _circuit(), total_shots=20, master_seed=7)

    assert result.total_shots == 20
    assert result.fault_recovery_events == 1
    assert result.status == "SUCCEEDED"


def test_scheduler_reports_retry_exhaustion():
    scheduler = DistributedScheduler(num_workers=1, max_retries=2)
    scheduler.workers["worker_0"].fail_next_task = True

    # The worker fails once and remains failed, so the second attempt exhausts
    # the configured policy.
    scheduler.workers["worker_0"].execute_task = lambda task: (_ for _ in ()).throw(
        RuntimeError("permanent failure")
    )
    with pytest.raises(RuntimeError, match="failed after 2 attempts"):
        scheduler.execute_job("failed-job", _circuit(), total_shots=2)


def test_scheduler_discards_duplicate_logical_results():
    scheduler = DistributedScheduler(num_workers=1)
    scheduler.workers["worker_0"].duplicate_result_next_task = True

    result = scheduler.execute_job("duplicate-job", _circuit(), total_shots=20)

    assert result.total_shots == 20
    assert result.num_tasks == 1
    assert result.duplicate_results_discarded == 1


def test_scheduler_rejects_duplicate_job_and_invalid_worker_registration():
    scheduler = DistributedScheduler(num_workers=1)
    scheduler.execute_job("one-job", _circuit(), total_shots=2)

    with pytest.raises(ValueError, match="already been submitted"):
        scheduler.execute_job("one-job", _circuit(), total_shots=2)
    with pytest.raises(ValueError, match="already registered"):
        scheduler.register_worker(WorkerNode("worker_0"))
    with pytest.raises(ValueError, match="positive integer"):
        DistributedScheduler(num_workers=0)


def test_scheduler_shutdown_rejects_new_jobs():
    scheduler = DistributedScheduler(num_workers=1)
    scheduler.shutdown()

    with pytest.raises(RuntimeError, match="shut down"):
        scheduler.execute_job("closed-job", _circuit(), total_shots=2)


def test_process_mode_uses_wire_protocol_and_reports_workers():
    with DistributedScheduler(num_workers=2, execution_mode="process") as scheduler:
        result = scheduler.execute_job("process-job", _circuit(), total_shots=4)

    assert result.execution_mode == "process"
    assert result.total_shots == 4
    assert set(result.worker_process_ids) == {"worker_0", "worker_1"}
