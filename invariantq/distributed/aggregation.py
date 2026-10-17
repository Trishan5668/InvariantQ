"""
Distributed Result Aggregator.
Consolidates bitstring counts, computes expectation values, variance, and 95% confidence intervals.
"""

from __future__ import annotations
import math
from typing import List, Dict, Any
from dataclasses import dataclass, field

@dataclass
class AggregatedResult:
    job_id: str
    total_shots: int
    counts: Dict[str, int]
    probabilities: Dict[str, float]
    z_expectation: float
    variance: float
    standard_error: float
    confidence_interval_95: (float, float)
    num_tasks: int
    total_execution_time_ms: float
    fault_recovery_events: int = 0

class ResultAggregator:
    @staticmethod
    def aggregate(job_id: str, task_results: List[Dict[str, Any]], recovery_events: int = 0) -> AggregatedResult:
        total_counts: Dict[str, int] = {}
        total_shots = 0
        total_time = 0.0

        for r in task_results:
            total_shots += r["shots"]
            total_time += r.get("execution_time_ms", 0.0)
            for bitstr, cnt in r["counts"].items():
                total_counts[bitstr] = total_counts.get(bitstr, 0) + cnt

        probs = {k: v / total_shots for k, v in total_counts.items()} if total_shots > 0 else {}

        # Observable Z...Z expectation
        exp_z = 0.0
        if total_shots > 0:
            for bitstr, cnt in total_counts.items():
                parity = bitstr.count("1") % 2
                sign = -1.0 if parity == 1 else 1.0
                exp_z += sign * (cnt / total_shots)

        # Variance for eigenvalue +-1 observable: Var = 1 - <Z>^2
        var_z = max(0.0, 1.0 - (exp_z ** 2))
        sem = math.sqrt(var_z / total_shots) if total_shots > 0 else 0.0
        ci_95 = (exp_z - 1.96 * sem, exp_z + 1.96 * sem)

        return AggregatedResult(
            job_id=job_id,
            total_shots=total_shots,
            counts=total_counts,
            probabilities=probs,
            z_expectation=exp_z,
            variance=var_z,
            standard_error=sem,
            confidence_interval_95=ci_95,
            num_tasks=len(task_results),
            total_execution_time_ms=total_time,
            fault_recovery_events=recovery_events
        )
