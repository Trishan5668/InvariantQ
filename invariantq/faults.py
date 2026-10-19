"""Opt-in, isolated runtime fault experiments."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional
import copy

from .execution import ExecutionContext, ExecutionLimitError


class FaultCategory(str, Enum):
    BACKEND_EXCEPTION = "backend_exception"
    RESULT_CORRUPTION = "result_corruption"
    RESOURCE_REJECTION = "resource_rejection"


@dataclass(frozen=True)
class FaultScenario:
    category: FaultCategory
    injection_point: str = "before_execution"
    message: str = "injected runtime fault"
    enabled: bool = True


@dataclass(frozen=True)
class FaultReport:
    status: str
    category: str
    injection_point: str
    seed: int
    baseline_status: str
    fault_status: str
    recovered: bool
    error: Optional[str]
    baseline_result: Any = None
    fault_result: Any = None


class RuntimeFaultSandbox:
    """Run a baseline and an explicitly injected experiment in isolation."""

    def run(self, execute, *, scenario: FaultScenario, seed: int = 42,
            context: Optional[ExecutionContext] = None) -> FaultReport:
        if not scenario.enabled:
            raise ValueError("fault scenarios require explicit opt-in")
        if not isinstance(seed, int) or isinstance(seed, bool) or seed < 0:
            raise ValueError("seed must be a non-negative integer")
        baseline = execute(seed=seed)
        baseline_copy = copy.deepcopy(baseline)
        fault_result = None
        error = None
        try:
            if scenario.injection_point == "before_execution":
                raise RuntimeError(scenario.message)
            fault_result = execute(seed=seed, fault=scenario)
            if scenario.category is FaultCategory.RESULT_CORRUPTION:
                raise RuntimeError("injected result failed integrity validation")
            fault_status = "completed"
        except Exception as exc:
            fault_status = "failed"
            error = f"{type(exc).__name__}: {exc}"
        return FaultReport(
            status="fault_detected" if error else "completed",
            category=scenario.category.value,
            injection_point=scenario.injection_point,
            seed=seed,
            baseline_status="completed",
            fault_status=fault_status,
            recovered=False,
            error=error,
            baseline_result=baseline_copy,
            fault_result=fault_result,
        )
