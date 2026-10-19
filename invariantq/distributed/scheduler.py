"""Deterministic scheduling for the local distributed execution engine."""

from __future__ import annotations

import threading
import time
from typing import Any, Dict, List, Optional

from ..ir.qir import CircuitIR
from .aggregation import AggregatedResult, ResultAggregator
from .fault_tolerance import FaultToleranceManager
from .planner import (
    TASK_COMPLETED,
    TASK_FAILED,
    DistributedPlan,
    DistributedPlanner,
    TaskUnit,
)
from .protocol import result_from_json, task_to_json
from .worker import LocalProcessWorkerPool, WorkerNode


class DistributedScheduler:
    """Plan and execute shot partitions with deterministic retry semantics.

    ``inprocess`` preserves the original public API and is useful for
    deterministic tests and fault-injection through :class:`WorkerNode`.
    ``process`` uses the validated JSON protocol and isolated worker
    processes.  Both modes aggregate at most one result per logical task.
    """

    def __init__(
        self,
        num_workers: int = 4,
        *,
        max_retries: int = 3,
        worker_timeout_sec: float = 10.0,
        execution_mode: str = "inprocess",
        planner: Optional[DistributedPlanner] = None,
    ):
        if isinstance(num_workers, bool) or not isinstance(num_workers, int) or num_workers <= 0:
            raise ValueError("num_workers must be a positive integer")
        if worker_timeout_sec <= 0:
            raise ValueError("worker_timeout_sec must be positive")
        if execution_mode not in {"inprocess", "process"}:
            raise ValueError("execution_mode must be 'inprocess' or 'process'")
        self.workers: Dict[str, WorkerNode] = {
            f"worker_{index}": WorkerNode(f"worker_{index}", cores=2)
            for index in range(num_workers)
        }
        self.planner = planner or DistributedPlanner()
        self.ft_manager = FaultToleranceManager(
            max_retries=max_retries, heartbeat_timeout_sec=worker_timeout_sec
        )
        self.worker_timeout_sec = worker_timeout_sec
        self.execution_mode = execution_mode
        self._pool: Optional[LocalProcessWorkerPool] = None
        self._jobs: Dict[str, str] = {}
        self._lock = threading.RLock()
        self._closed = False

    def register_worker(self, worker: WorkerNode) -> None:
        if not isinstance(worker, WorkerNode):
            raise TypeError("worker must be a WorkerNode")
        with self._lock:
            if self._closed:
                raise RuntimeError("scheduler is shut down")
            if worker.worker_id in self.workers:
                raise ValueError(f"worker {worker.worker_id!r} is already registered")
            self.workers[worker.worker_id] = worker

    def _plan(self, job_id: str, circuit: CircuitIR, total_shots: int, master_seed: int) -> DistributedPlan:
        with self._lock:
            if self._closed:
                raise RuntimeError("scheduler is shut down")
            if job_id in self._jobs:
                raise ValueError(f"job {job_id!r} has already been submitted")
            plan = self.planner.plan_job(
                job_id=job_id,
                circuit=circuit,
                total_shots=total_shots,
                master_seed=master_seed,
                num_workers=len(self.workers),
            )
            self._jobs[job_id] = "RUNNING"
            return plan

    def _record_failure(self, worker_id: str, task: TaskUnit, message: str) -> None:
        task.status = TASK_FAILED
        task.last_error = message
        self.ft_manager.record_failure(
            worker_id=worker_id,
            task_id=task.task_id,
            attempt=task.attempt,
            error_message=message,
        )

    def _healthy_worker(self, worker_ids: List[str], cursor: int) -> tuple[WorkerNode, int]:
        for offset in range(len(worker_ids)):
            index = (cursor + offset) % len(worker_ids)
            worker = self.workers[worker_ids[index]]
            if worker.status not in {"FAILED", "OFFLINE"}:
                return worker, index + 1
        # A failed in-process worker can be retried after it has been selected
        # again; this avoids silently losing all work when the pool is small.
        worker = self.workers[worker_ids[cursor % len(worker_ids)]]
        worker.status = "IDLE"
        return worker, cursor + 1

    def _execute_inprocess(self, plan: DistributedPlan) -> tuple[List[Dict[str, Any]], int]:
        results: List[Dict[str, Any]] = []
        pending = list(plan.tasks)
        worker_ids = list(self.workers)
        cursor = 0
        recovery_events = 0
        while pending:
            task = pending.pop(0)
            worker, cursor = self._healthy_worker(worker_ids, cursor)
            task.assigned_worker_id = worker.worker_id
            task.attempt += 1
            try:
                result = worker.execute_task(task)
                task.status = TASK_COMPLETED
                results.append(result)
                if worker.duplicate_result_next_task:
                    worker.duplicate_result_next_task = False
                    results.append(dict(result))
            except Exception as exc:
                recovery_events += 1
                self._record_failure(worker.worker_id, task, str(exc))
                if self.ft_manager.can_retry(task.attempt):
                    pending.append(task)
                else:
                    raise RuntimeError(
                        f"Task {task.task_id} failed after {task.attempt} attempts: {exc}"
                    ) from exc
        return results, recovery_events

    def _execute_process(self, plan: DistributedPlan) -> tuple[List[Dict[str, Any]], int, Dict[str, int]]:
        worker_ids = list(self.workers)
        if self._pool is None:
            self._pool = LocalProcessWorkerPool(worker_ids)
        pending = list(plan.tasks)
        results: List[Dict[str, Any]] = []
        process_ids = {
            worker_id: pid
            for worker_id in worker_ids
            if (pid := self._pool.process_id(worker_id)) is not None
        }
        recovery_events = 0
        cursor = 0
        while pending:
            task = pending.pop(0)
            worker_id = worker_ids[cursor % len(worker_ids)]
            cursor += 1
            task.assigned_worker_id = worker_id
            task.attempt += 1
            context = {
                "task_id": task.task_id,
                "job_id": task.job_id,
                "attempt": task.attempt,
                "seed": task.seed,
            }
            try:
                self._pool.submit(worker_id, task_to_json(task), context)
                message = self._pool.poll(self.worker_timeout_sec)
                if message is None:
                    raise TimeoutError(f"worker {worker_id} timed out")
                result = result_from_json(message["payload"])
                if result.get("task_id") != task.task_id:
                    raise RuntimeError("worker returned a result for a different task")
                if result.get("status") != "COMPLETED":
                    raise RuntimeError(str(result.get("error", "worker execution failed")))
                task.status = TASK_COMPLETED
                results.append(result)
            except Exception as exc:
                recovery_events += 1
                self._record_failure(worker_id, task, str(exc))
                # A timed-out process may still be executing the old task.
                # Replace it before retrying so a late result cannot be
                # mistaken for the retry's result.
                if isinstance(exc, TimeoutError) or not self._pool.is_alive(worker_id):
                    self._pool.restart_worker(worker_id)
                    process_ids[worker_id] = self._pool.process_id(worker_id) or 0
                if self.ft_manager.can_retry(task.attempt):
                    pending.append(task)
                else:
                    raise RuntimeError(
                        f"Task {task.task_id} failed after {task.attempt} attempts: {exc}"
                    ) from exc
        return results, recovery_events, process_ids

    def execute_job(
        self, job_id: str, circuit: CircuitIR, total_shots: int = 1000, master_seed: int = 42
    ) -> AggregatedResult:
        plan = self._plan(job_id, circuit, total_shots, master_seed)
        try:
            if self.execution_mode == "process":
                results, recovery_events, process_ids = self._execute_process(plan)
            else:
                results, recovery_events = self._execute_inprocess(plan)
                process_ids = {}
            aggregate = ResultAggregator.aggregate(
                job_id,
                results,
                recovery_events,
                requested_total_shots=plan.total_shots,
                expected_task_ids=[task.task_id for task in plan.tasks],
                execution_mode=self.execution_mode,
                worker_process_ids=process_ids,
            )
            with self._lock:
                self._jobs[job_id] = aggregate.status
            return aggregate
        except Exception:
            with self._lock:
                self._jobs[job_id] = "FAILED"
            raise

    def shutdown(self) -> None:
        with self._lock:
            if self._closed:
                return
            self._closed = True
            if self._pool is not None:
                self._pool.close()
                self._pool = None

    close = shutdown

    def __enter__(self) -> "DistributedScheduler":
        return self

    def __exit__(self, exc_type: Any, exc: Any, traceback: Any) -> None:
        self.shutdown()
