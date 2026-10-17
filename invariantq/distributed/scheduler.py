"""
Distributed Scheduler.
Orchestrates worker pool, dispatches partitioned tasks, and recovers from worker failures.
"""

from __future__ import annotations
import time
from typing import Dict, List, Optional
from .planner import DistributedPlanner, DistributedPlan, TaskUnit
from .worker import WorkerNode
from .fault_tolerance import FaultToleranceManager
from .aggregation import ResultAggregator, AggregatedResult
from ..ir.qir import CircuitIR

class DistributedScheduler:
    def __init__(self, num_workers: int = 4):
        self.workers: Dict[str, WorkerNode] = {
            f"worker_{i}": WorkerNode(f"worker_{i}", cores=2)
            for i in range(num_workers)
        }
        self.planner = DistributedPlanner()
        self.ft_manager = FaultToleranceManager(max_retries=3)

    def register_worker(self, worker: WorkerNode):
        self.workers[worker.worker_id] = worker

    def execute_job(
        self,
        job_id: str,
        circuit: CircuitIR,
        total_shots: int = 1000,
        master_seed: int = 42
    ) -> AggregatedResult:
        plan: DistributedPlan = self.planner.plan_job(
            job_id=job_id,
            circuit=circuit,
            total_shots=total_shots,
            master_seed=master_seed,
            num_workers=len(self.workers)
        )

        completed_task_results = []
        pending_tasks = list(plan.tasks)
        recovery_events = 0

        worker_ids = list(self.workers.keys())
        worker_idx = 0

        while pending_tasks:
            task = pending_tasks.pop(0)

            # Pick next healthy worker
            assigned_worker = None
            for _ in range(len(worker_ids)):
                candidate = self.workers[worker_ids[worker_idx % len(worker_ids)]]
                worker_idx += 1
                if candidate.status != "FAILED":
                    assigned_worker = candidate
                    break

            if assigned_worker is None:
                # All workers failed; reset one for recovery
                assigned_worker = self.workers[worker_ids[0]]
                assigned_worker.status = "IDLE"

            task.assigned_worker_id = assigned_worker.worker_id
            task.attempt += 1

            try:
                res = assigned_worker.execute_task(task)
                task.status = "COMPLETED"
                completed_task_results.append(res)
            except Exception as e:
                task.status = "FAILED"
                recovery_events += 1
                self.ft_manager.record_failure(
                    worker_id=assigned_worker.worker_id,
                    task_id=task.task_id,
                    attempt=task.attempt,
                    error_message=str(e)
                )

                if self.ft_manager.can_retry(task.attempt):
                    # Re-queue task to another healthy worker
                    pending_tasks.append(task)
                else:
                    raise RuntimeError(f"Task {task.task_id} failed after {task.attempt} attempts: {e}")

        return ResultAggregator.aggregate(job_id, completed_task_results, recovery_events)
