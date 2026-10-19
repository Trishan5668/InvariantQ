"""Validated aggregation for independently executed shot partitions."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Mapping, Optional, Tuple


@dataclass
class AggregatedResult:
    job_id: str
    total_shots: int
    counts: Dict[str, int]
    probabilities: Dict[str, float]
    z_expectation: float
    variance: float
    standard_error: float
    confidence_interval_95: Tuple[float, float]
    num_tasks: int
    total_execution_time_ms: float
    fault_recovery_events: int = 0
    status: str = "SUCCEEDED"
    is_complete: bool = True
    requested_total_shots: int = 0
    completed_task_ids: List[str] = field(default_factory=list)
    failed_task_ids: List[str] = field(default_factory=list)
    cancelled_task_ids: List[str] = field(default_factory=list)
    duplicate_results_discarded: int = 0
    execution_mode: str = "inprocess"
    worker_process_ids: Dict[str, int] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


class ResultAggregator:
    """Combine only one validated result for each logical task identifier."""

    @staticmethod
    def aggregate(
        job_id: str,
        task_results: Iterable[Mapping[str, Any]],
        recovery_events: int = 0,
        *,
        status: str = "SUCCEEDED",
        requested_total_shots: int = 0,
        expected_task_ids: Optional[Iterable[str]] = None,
        failed_task_ids: Optional[Iterable[str]] = None,
        cancelled_task_ids: Optional[Iterable[str]] = None,
        duplicate_results_discarded: int = 0,
        execution_mode: str = "inprocess",
        worker_process_ids: Optional[Mapping[str, int]] = None,
        metadata: Optional[Mapping[str, Any]] = None,
    ) -> AggregatedResult:
        total_counts: Dict[str, int] = {}
        total_shots = 0
        total_time = 0.0
        completed_task_ids: List[str] = []
        seen_task_ids = set()
        expected = set(expected_task_ids) if expected_task_ids is not None else None
        duplicate_count = int(duplicate_results_discarded)

        for result in task_results:
            if not isinstance(result, Mapping):
                raise ValueError("task result must be a mapping")
            task_id = result.get("task_id")
            if not isinstance(task_id, str) or not task_id:
                raise ValueError("task result is missing a task_id")
            if expected is not None and task_id not in expected:
                raise ValueError(f"result references unknown task {task_id!r}")
            if task_id in seen_task_ids:
                duplicate_count += 1
                continue
            shots = result.get("shots")
            if isinstance(shots, bool) or not isinstance(shots, int) or shots <= 0:
                raise ValueError(f"result {task_id!r} has invalid shot count")
            counts = result.get("counts")
            if not isinstance(counts, Mapping):
                raise ValueError(f"result {task_id!r} has invalid counts")
            normalized_counts: Dict[str, int] = {}
            for bitstring, count in counts.items():
                if not isinstance(bitstring, str) or any(bit not in "01" for bit in bitstring):
                    raise ValueError(f"result {task_id!r} has invalid bitstring")
                if isinstance(count, bool) or not isinstance(count, int) or count < 0:
                    raise ValueError(f"result {task_id!r} has invalid count")
                normalized_counts[bitstring] = count
            if sum(normalized_counts.values()) != shots:
                raise ValueError(
                    f"result {task_id!r} counts do not sum to its declared shots"
                )

            elapsed = result.get("execution_time_ms", 0.0)
            if isinstance(elapsed, bool) or not isinstance(elapsed, (int, float)) or elapsed < 0:
                raise ValueError(f"result {task_id!r} has invalid execution time")
            if not math.isfinite(float(elapsed)):
                raise ValueError(f"result {task_id!r} has non-finite execution time")

            seen_task_ids.add(task_id)
            completed_task_ids.append(task_id)
            total_shots += shots
            total_time += float(elapsed)
            for bitstring, count in normalized_counts.items():
                total_counts[bitstring] = total_counts.get(bitstring, 0) + count

        probabilities = (
            {bitstring: count / total_shots for bitstring, count in total_counts.items()}
            if total_shots
            else {}
        )
        expectation = 0.0
        if total_shots:
            for bitstring, count in total_counts.items():
                sign = -1.0 if bitstring.count("1") % 2 else 1.0
                expectation += sign * (count / total_shots)
        variance = max(0.0, 1.0 - expectation**2)
        standard_error = math.sqrt(variance / total_shots) if total_shots else 0.0
        confidence_interval = (
            expectation - 1.96 * standard_error,
            expectation + 1.96 * standard_error,
        )
        failed = list(failed_task_ids or [])
        cancelled = list(cancelled_task_ids or [])
        return AggregatedResult(
            job_id=job_id,
            total_shots=total_shots,
            counts=total_counts,
            probabilities=probabilities,
            z_expectation=expectation,
            variance=variance,
            standard_error=standard_error,
            confidence_interval_95=confidence_interval,
            num_tasks=len(completed_task_ids),
            total_execution_time_ms=total_time,
            fault_recovery_events=recovery_events,
            status=status,
            is_complete=status == "SUCCEEDED",
            requested_total_shots=requested_total_shots or total_shots,
            completed_task_ids=completed_task_ids,
            failed_task_ids=failed,
            cancelled_task_ids=cancelled,
            duplicate_results_discarded=duplicate_count,
            execution_mode=execution_mode,
            worker_process_ids=dict(worker_process_ids or {}),
            metadata=dict(metadata or {}),
        )
