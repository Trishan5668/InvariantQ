"""
Fault-Tolerance and Worker Resilience Manager.
Tracks worker failures, retry ledgers, and automated failover.
"""

from __future__ import annotations
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional

@dataclass
class FailureEvent:
    timestamp: float
    worker_id: str
    task_id: str
    attempt: int
    error_message: str

class FaultToleranceManager:
    def __init__(self, max_retries: int = 3, heartbeat_timeout_sec: float = 10.0):
        self.max_retries = max_retries
        self.heartbeat_timeout_sec = heartbeat_timeout_sec
        self.events: List[FailureEvent] = []

    def record_failure(self, worker_id: str, task_id: str, attempt: int, error: str = "", error_message: str = ""):
        msg = error or error_message
        evt = FailureEvent(
            timestamp=time.time(),
            worker_id=worker_id,
            task_id=task_id,
            attempt=attempt,
            error_message=msg
        )
        self.events.append(evt)

    def can_retry(self, attempt: int) -> bool:
        return attempt < self.max_retries
