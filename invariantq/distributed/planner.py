"""Deterministic shot partitioning and local-worker preflight checks."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from ..ir.qir import CircuitIR


TASK_PENDING = "PENDING"
TASK_RUNNING = "RUNNING"
TASK_COMPLETED = "COMPLETED"
TASK_FAILED = "FAILED"
TASK_CANCELLED = "CANCELLED"


class ResourceLimitError(ValueError):
    """Raised before dispatch when a worker resource limit would be exceeded."""


@dataclass
class TaskUnit:
    """One logical shot partition.

    ``task_id`` and ``seed`` identify logical work, not an individual attempt.
    Retrying a task therefore reproduces the exact same samples rather than
    adding a second stochastic contribution to a job.
    """

    task_id: str
    circuit: CircuitIR
    shots: int
    seed: int
    job_id: str = ""
    attempt: int = 0
    assigned_worker_id: Optional[str] = None
    status: str = TASK_PENDING
    last_error: Optional[str] = None


@dataclass
class DistributedPlan:
    job_id: str
    total_shots: int
    master_seed: int
    tasks: List[TaskUnit]
    num_workers_requested: int
    estimated_memory_per_worker_mb: float
    resource_limits: Dict[str, float | int | None] = field(default_factory=dict)


class DistributedPlanner:
    """Build reproducible, bounded local-process execution plans.

    This planner partitions by worker intentionally: each task has an
    independent, deterministic random stream, and retries retain that stream.
    A caller can use more scheduler workers than shots; zero-shot tasks are
    simply omitted.
    """

    def __init__(
        self,
        default_batch_size: int = 250,
        max_memory_per_worker_mb: Optional[float] = None,
        max_qubits: Optional[int] = None,
    ):
        if default_batch_size <= 0:
            raise ValueError("default_batch_size must be positive")
        if max_memory_per_worker_mb is not None and max_memory_per_worker_mb <= 0:
            raise ValueError("max_memory_per_worker_mb must be positive")
        if max_qubits is not None and max_qubits <= 0:
            raise ValueError("max_qubits must be positive")
        self.default_batch_size = default_batch_size
        self.max_memory_per_worker_mb = max_memory_per_worker_mb
        self.max_qubits = max_qubits

    @staticmethod
    def estimate_statevector_memory_mb(num_qubits: int) -> float:
        """Return the exact complex128 amplitude storage estimate in MiB."""
        if num_qubits <= 0:
            raise ValueError("circuit must contain at least one qubit")
        # Python integers make this safe as an estimate even for an invalidly
        # large request; no allocation takes place here.
        return float((1 << num_qubits) * 16) / (1024.0 * 1024.0)

    def _preflight(self, circuit: CircuitIR) -> float:
        if not isinstance(circuit, CircuitIR):
            raise TypeError("circuit must be a CircuitIR")
        n = circuit.num_qubits
        if n <= 0:
            raise ValueError("circuit must contain at least one qubit")
        if self.max_qubits is not None and n > self.max_qubits:
            raise ResourceLimitError(
                f"circuit has {n} qubits; local worker limit is {self.max_qubits}"
            )
        estimated_mb = self.estimate_statevector_memory_mb(n)
        if (
            self.max_memory_per_worker_mb is not None
            and estimated_mb > self.max_memory_per_worker_mb
        ):
            raise ResourceLimitError(
                "statevector preflight requires "
                f"{estimated_mb:.2f} MiB per worker, exceeding the configured "
                f"{self.max_memory_per_worker_mb:.2f} MiB limit"
            )
        return estimated_mb

    @staticmethod
    def _task_seed(master_seed: int, job_id: str, partition_index: int) -> int:
        seed_bytes = hashlib.sha256(
            f"{master_seed}:{job_id}:{partition_index}".encode("utf-8")
        ).digest()
        return int.from_bytes(seed_bytes[:8], byteorder="big")

    def plan_job(
        self,
        job_id: str,
        circuit: CircuitIR,
        total_shots: int,
        master_seed: int = 42,
        num_workers: int = 4,
    ) -> DistributedPlan:
        if not isinstance(job_id, str) or not job_id:
            raise ValueError("job_id must be a non-empty string")
        if isinstance(total_shots, bool) or not isinstance(total_shots, int) or total_shots <= 0:
            raise ValueError("total_shots must be a positive integer")
        if isinstance(master_seed, bool) or not isinstance(master_seed, int) or master_seed < 0:
            raise ValueError("master_seed must be a non-negative integer")
        if isinstance(num_workers, bool) or not isinstance(num_workers, int) or num_workers <= 0:
            raise ValueError("num_workers must be a positive integer")

        estimated_mb = self._preflight(circuit)
        shots_per_worker, remainder = divmod(total_shots, num_workers)

        tasks: List[TaskUnit] = []
        for partition_index in range(num_workers):
            task_shots = shots_per_worker + (1 if partition_index < remainder else 0)
            if task_shots == 0:
                continue
            tasks.append(
                TaskUnit(
                    task_id=f"{job_id}_task_{partition_index}",
                    job_id=job_id,
                    circuit=circuit,
                    shots=task_shots,
                    seed=self._task_seed(master_seed, job_id, partition_index),
                )
            )

        return DistributedPlan(
            job_id=job_id,
            total_shots=total_shots,
            master_seed=master_seed,
            tasks=tasks,
            num_workers_requested=num_workers,
            estimated_memory_per_worker_mb=max(1.0, estimated_mb),
            resource_limits={
                "max_memory_per_worker_mb": self.max_memory_per_worker_mb,
                "max_qubits": self.max_qubits,
            },
        )
