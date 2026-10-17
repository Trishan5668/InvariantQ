"""
Distributed Circuit and Shot Planner.
Partitions shots and large workloads across distributed worker clusters (Cisco 2025 network-aware model).
"""

from __future__ import annotations
import hashlib
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from ..ir.qir import CircuitIR

@dataclass
class TaskUnit:
    task_id: str
    circuit: CircuitIR
    shots: int
    seed: int
    attempt: int = 0
    assigned_worker_id: Optional[str] = None
    status: str = "PENDING" # PENDING, RUNNING, COMPLETED, FAILED

@dataclass
class DistributedPlan:
    job_id: str
    total_shots: int
    master_seed: int
    tasks: List[TaskUnit]
    num_workers_requested: int
    estimated_memory_per_worker_mb: float

class DistributedPlanner:
    def __init__(self, default_batch_size: int = 250):
        self.default_batch_size = default_batch_size

    def plan_job(
        self,
        job_id: str,
        circuit: CircuitIR,
        total_shots: int,
        master_seed: int = 42,
        num_workers: int = 4
    ) -> DistributedPlan:
        shots_per_worker = total_shots // num_workers
        remainder = total_shots % num_workers

        tasks: List[TaskUnit] = []
        for i in range(num_workers):
            task_shots = shots_per_worker + (1 if i < remainder else 0)
            if task_shots <= 0:
                continue

            # Deterministic reproducible seed per task via SHA256
            seed_bytes = hashlib.sha256(f"{master_seed}:{job_id}:{i}".encode("utf-8")).digest()
            task_seed = int.from_bytes(seed_bytes[:8], byteorder="big")

            task = TaskUnit(
                task_id=f"{job_id}_task_{i}",
                circuit=circuit,
                shots=task_shots,
                seed=task_seed
            )
            tasks.append(task)

        # Estimate memory per worker
        n = circuit.num_qubits
        est_mem_mb = ((1 << n) * 16) / (1024 * 1024) if n <= 28 else (n * 2 * (64**2) * 16) / (1024 * 1024)

        return DistributedPlan(
            job_id=job_id,
            total_shots=total_shots,
            master_seed=master_seed,
            tasks=tasks,
            num_workers_requested=num_workers,
            estimated_memory_per_worker_mb=max(1.0, est_mem_mb)
        )
