"""Failure ledger and retry policy for local process workers."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class FailureEvent:
    timestamp: float
    worker_id: str
    task_id: str
    attempt: int
    error_message: str
    failure_kind: str = "execution_error"


class FaultToleranceManager:
    """Records failures without conflating retries with successful work."""

    def __init__(self, max_retries: int = 3, heartbeat_timeout_sec: float = 10.0):
        if isinstance(max_retries, bool) or not isinstance(max_retries, int) or max_retries < 1:
            raise ValueError("max_retries must be a positive integer")
        if heartbeat_timeout_sec <= 0:
            raise ValueError("heartbeat_timeout_sec must be positive")
        # Preserves the historical API semantics: this is the maximum number
        # of attempts, including the initial attempt.
        self.max_retries = max_retries
        self.heartbeat_timeout_sec = heartbeat_timeout_sec
        self.events: List[FailureEvent] = []

    def record_failure(
        self,
        worker_id: str,
        task_id: str,
        attempt: int,
        error: str = "",
        error_message: str = "",
        failure_kind: str = "execution_error",
    ) -> FailureEvent:
        message = error or error_message or "unknown worker failure"
        event = FailureEvent(
            timestamp=time.time(),
            worker_id=worker_id,
            task_id=task_id,
            attempt=attempt,
            error_message=message,
            failure_kind=failure_kind,
        )
        self.events.append(event)
        return event

    def can_retry(self, attempt: int) -> bool:
        """Whether another attempt is allowed after ``attempt`` has failed."""
        return attempt < self.max_retries
