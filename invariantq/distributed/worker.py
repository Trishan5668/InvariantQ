"""
Distributed Worker Node execution model.
Executes partitioned tasks and reports telemetry, memory usage, and execution results.
"""

from __future__ import annotations
import time
from typing import Dict, Any, Optional
from ..simulator.statevector import StateVectorSimulator
from ..simulator.base import ExecutionResult
from .planner import TaskUnit

class WorkerNode:
    def __init__(self, worker_id: str, host: str = "localhost", cores: int = 4):
        self.worker_id = worker_id
        self.host = host
        self.cores = cores
        self.status = "IDLE" # IDLE, BUSY, FAILED, OFFLINE
        self.last_heartbeat = time.time()
        self.tasks_completed = 0
        self.fail_next_task = False # For fault-tolerance testing
        self.sim = StateVectorSimulator()

    def heartbeat(self):
        self.last_heartbeat = time.time()

    def execute_task(self, task: TaskUnit) -> Dict[str, Any]:
        self.heartbeat()
        self.status = "BUSY"

        if self.fail_next_task:
            self.fail_next_task = False
            self.status = "FAILED"
            raise RuntimeError(f"Simulated hardware failure on worker {self.worker_id}!")

        t0 = time.perf_counter()
        res: ExecutionResult = self.sim.run(task.circuit, shots=task.shots, seed=task.seed)
        t1 = time.perf_counter()

        self.tasks_completed += 1
        self.status = "IDLE"
        self.heartbeat()

        return {
            "task_id": task.task_id,
            "worker_id": self.worker_id,
            "shots": task.shots,
            "counts": res.counts,
            "execution_time_ms": (t1 - t0) * 1000.0,
            "seed": task.seed
        }
