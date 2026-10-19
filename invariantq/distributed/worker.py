"""Local worker nodes and an explicitly process-isolated worker pool."""

from __future__ import annotations

import multiprocessing as mp
import os
import time
from typing import Any, Dict, Iterable, Mapping, Optional

from ..simulator.base import ExecutionResult
from ..simulator.statevector import StateVectorSimulator
from .planner import TaskUnit
from .protocol import ProtocolValidationError, result_to_json, task_from_json


class WorkerUnavailableError(RuntimeError):
    """The scheduler attempted to dispatch to a dead local worker process."""


class WorkerNode:
    """Scheduler-side logical view of a worker.

    The simulator instance here is retained for the legacy in-process mode.
    In process mode this object is never sent to the child: only a validated
    JSON task payload crosses the boundary.

    The ``*_next_task`` fields are deterministic fault-injection hooks used by
    tests.  They are consumed by the scheduler before a task is dispatched and
    are not part of normal execution semantics.
    """

    def __init__(self, worker_id: str, host: str = "localhost", cores: int = 4):
        if not worker_id:
            raise ValueError("worker_id must be non-empty")
        if cores <= 0:
            raise ValueError("cores must be positive")
        self.worker_id = worker_id
        self.host = host
        self.cores = cores
        self.status = "IDLE"  # IDLE, BUSY, FAILED, OFFLINE
        self.last_heartbeat = time.time()
        self.tasks_completed = 0
        self.fail_next_task = False
        self.terminate_next_task = False
        self.duplicate_result_next_task = False
        self.delay_next_task_seconds = 0.0
        self.sim = StateVectorSimulator()

    def heartbeat(self) -> None:
        self.last_heartbeat = time.time()

    def execute_task(self, task: TaskUnit) -> Dict[str, Any]:
        """Execute a task in the scheduler process for compatibility mode."""
        self.heartbeat()
        self.status = "BUSY"
        if self.fail_next_task:
            self.fail_next_task = False
            self.status = "FAILED"
            raise RuntimeError(f"simulated hardware failure on worker {self.worker_id}")

        if self.terminate_next_task:
            # A true process termination cannot be emulated in compatibility
            # mode.  Surface it as a regular failure instead.
            self.terminate_next_task = False
            self.status = "FAILED"
            raise RuntimeError(f"simulated worker termination on {self.worker_id}")

        if self.delay_next_task_seconds:
            delay = self.delay_next_task_seconds
            self.delay_next_task_seconds = 0.0
            time.sleep(delay)

        t0 = time.perf_counter()
        try:
            res: ExecutionResult = self.sim.run(task.circuit, shots=task.shots, seed=task.seed)
        except Exception:
            self.status = "FAILED"
            raise
        t1 = time.perf_counter()

        self.tasks_completed += 1
        self.status = "IDLE"
        self.heartbeat()
        return {
            "status": "COMPLETED",
            "task_id": task.task_id,
            "job_id": task.job_id,
            "worker_id": self.worker_id,
            "shots": task.shots,
            "counts": res.counts,
            "execution_time_ms": (t1 - t0) * 1000.0,
            "seed": task.seed,
            "attempt": task.attempt,
            "process_id": os.getpid(),
        }


def _failure_payload(worker_id: str, context: Mapping[str, Any], error: BaseException) -> str:
    """Build a protocol-valid failure message without leaking a traceback."""
    return result_to_json(
        {
            "status": "FAILED",
            "task_id": str(context["task_id"]),
            "job_id": str(context.get("job_id", "")),
            "worker_id": worker_id,
            "attempt": int(context["attempt"]),
            "seed": int(context["seed"]),
            "process_id": os.getpid(),
            "error": f"{type(error).__name__}: {error}",
        }
    )


def _local_worker_main(worker_id: str, task_queue: Any, result_queue: Any) -> None:
    """Child-process entry point.  It must remain module-level for spawn mode."""
    simulator = StateVectorSimulator()
    while True:
        message = task_queue.get()
        if message is None:
            return

        context = message.get("context", {}) if isinstance(message, dict) else {}
        control = message.get("control", {}) if isinstance(message, dict) else {}
        try:
            if control.get("failure_mode") == "terminate":
                # Deliberately bypass cleanup: this is how tests exercise the
                # scheduler's real dead-worker detection and replacement path.
                os._exit(86)
            delay = control.get("delay_seconds", 0.0)
            if isinstance(delay, (int, float)) and delay > 0:
                time.sleep(float(delay))
            if control.get("failure_mode") == "exception":
                raise RuntimeError(f"injected worker failure on {worker_id}")

            task = task_from_json(message["task_json"])
            t0 = time.perf_counter()
            execution: ExecutionResult = simulator.run(task.circuit, shots=task.shots, seed=task.seed)
            t1 = time.perf_counter()
            result_json = result_to_json(
                {
                    "status": "COMPLETED",
                    "task_id": task.task_id,
                    "job_id": task.job_id,
                    "worker_id": worker_id,
                    "shots": task.shots,
                    "counts": execution.counts,
                    "execution_time_ms": (t1 - t0) * 1000.0,
                    "seed": task.seed,
                    "attempt": task.attempt,
                    "process_id": os.getpid(),
                }
            )
            result_queue.put({"worker_id": worker_id, "payload": result_json})
            if control.get("duplicate_result"):
                # Models at-least-once delivery.  The scheduler must accept
                # the logical task at most once.
                result_queue.put({"worker_id": worker_id, "payload": result_json})
        except BaseException as exc:
            try:
                result_queue.put(
                    {"worker_id": worker_id, "payload": _failure_payload(worker_id, context, exc)}
                )
            except BaseException:
                # A malformed parent message cannot be trusted enough to make
                # a valid failure result.  The parent will detect the missing
                # response using its timeout/liveness checks.
                return


class LocalProcessWorkerPool:
    """A bounded, reusable pool of isolated local worker processes.

    This is intentionally a local process runtime, not a remote or multi-node
    service.  Each named worker owns one inbound queue, so the scheduler can
    observe exactly which process received a task and recover a specific dead
    process without relying on executor internals.
    """

    def __init__(self, worker_ids: Iterable[str], start_method: str = "spawn"):
        worker_ids = tuple(worker_ids)
        if not worker_ids:
            raise ValueError("at least one worker is required")
        if len(set(worker_ids)) != len(worker_ids):
            raise ValueError("worker identifiers must be unique")
        if start_method not in mp.get_all_start_methods():
            raise ValueError(f"unsupported multiprocessing start method {start_method!r}")
        self.worker_ids = worker_ids
        self._context = mp.get_context(start_method)
        self._result_queue = self._context.Queue()
        self._task_queues: Dict[str, Any] = {}
        self._processes: Dict[str, Any] = {}
        self._closed = False
        for worker_id in self.worker_ids:
            self._start_worker(worker_id)

    def _start_worker(self, worker_id: str) -> None:
        if self._closed:
            raise RuntimeError("worker pool is closed")
        task_queue = self._context.Queue()
        process = self._context.Process(
            target=_local_worker_main,
            args=(worker_id, task_queue, self._result_queue),
            name=f"invariantq-{worker_id}",
            daemon=True,
        )
        process.start()
        self._task_queues[worker_id] = task_queue
        self._processes[worker_id] = process

    def is_alive(self, worker_id: str) -> bool:
        process = self._processes.get(worker_id)
        return bool(process is not None and process.is_alive())

    def process_id(self, worker_id: str) -> Optional[int]:
        process = self._processes.get(worker_id)
        return None if process is None else process.pid

    def submit(
        self,
        worker_id: str,
        task_json: str,
        context: Mapping[str, Any],
        control: Optional[Mapping[str, Any]] = None,
    ) -> None:
        if self._closed:
            raise WorkerUnavailableError("worker pool is closed")
        if worker_id not in self._processes:
            raise WorkerUnavailableError(f"unknown worker {worker_id!r}")
        if not self.is_alive(worker_id):
            raise WorkerUnavailableError(f"worker {worker_id!r} is not alive")
        self._task_queues[worker_id].put(
            {
                "task_json": task_json,
                "context": dict(context),
                "control": dict(control or {}),
            }
        )

    def poll(self, timeout_sec: float) -> Optional[Dict[str, Any]]:
        try:
            return self._result_queue.get(timeout=max(0.0, timeout_sec))
        except Exception as exc:
            # multiprocessing.Queue raises queue.Empty, but avoiding a direct
            # dependency on its platform-specific implementation keeps the
            # method narrow: only the expected Empty exception is swallowed.
            import queue

            if isinstance(exc, queue.Empty):
                return None
            raise

    def terminate_worker(self, worker_id: str) -> None:
        process = self._processes.get(worker_id)
        if process is None:
            return
        if process.is_alive():
            process.terminate()
        process.join(timeout=1.0)

    def restart_worker(self, worker_id: str) -> None:
        if worker_id not in self._processes:
            raise WorkerUnavailableError(f"unknown worker {worker_id!r}")
        self.terminate_worker(worker_id)
        old_queue = self._task_queues.pop(worker_id, None)
        if old_queue is not None:
            old_queue.close()
        self._processes.pop(worker_id, None)
        self._start_worker(worker_id)

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        for worker_id, task_queue in list(self._task_queues.items()):
            process = self._processes.get(worker_id)
            if process is not None and process.is_alive():
                try:
                    task_queue.put(None)
                except Exception:
                    pass
        for worker_id in self.worker_ids:
            process = self._processes.get(worker_id)
            if process is not None:
                process.join(timeout=1.0)
                if process.is_alive():
                    process.terminate()
                    process.join(timeout=1.0)
        for task_queue in self._task_queues.values():
            task_queue.close()
        self._result_queue.close()

    def __enter__(self) -> "LocalProcessWorkerPool":
        return self

    def __exit__(self, exc_type: Any, exc: Any, traceback: Any) -> None:
        self.close()
