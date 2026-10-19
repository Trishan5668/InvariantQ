"""Shared cooperative execution limits, cancellation, and resource admission."""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from typing import Optional


class ExecutionLimitError(RuntimeError):
    """Base class for rejected or interrupted work."""


class DeadlineExceededError(ExecutionLimitError):
    pass


class ExecutionCancelledError(ExecutionLimitError):
    pass


class ResourceLimitError(ExecutionLimitError):
    pass


@dataclass(frozen=True)
class ExecutionLimits:
    deadline_seconds: Optional[float] = None
    memory_bytes: Optional[int] = None
    max_operations: Optional[int] = None


class CancellationToken:
    def __init__(self) -> None:
        self._event = threading.Event()

    def cancel(self) -> None:
        self._event.set()

    @property
    def cancelled(self) -> bool:
        return self._event.is_set()


class ResourcePool:
    """Race-safe reservation pool for estimated concurrent resources."""

    def __init__(self, memory_bytes: int, max_jobs: int) -> None:
        if memory_bytes <= 0 or max_jobs <= 0:
            raise ValueError("resource pool limits must be positive")
        self.capacity = memory_bytes
        self.max_jobs = max_jobs
        self._memory = 0
        self._jobs = 0
        self._lock = threading.Lock()

    def reserve(self, memory_bytes: int) -> None:
        if memory_bytes < 0:
            raise ValueError("memory reservation must be non-negative")
        with self._lock:
            if self._jobs >= self.max_jobs or self._memory + memory_bytes > self.capacity:
                raise ResourceLimitError("aggregate execution resource budget exceeded")
            self._jobs += 1
            self._memory += memory_bytes

    def release(self, memory_bytes: int) -> None:
        with self._lock:
            if self._jobs <= 0 or memory_bytes < 0 or memory_bytes > self._memory:
                raise RuntimeError("resource reservation release does not match an active reservation")
            self._jobs -= 1
            self._memory -= memory_bytes

    @property
    def active_jobs(self) -> int:
        with self._lock:
            return self._jobs

    @property
    def reserved_memory_bytes(self) -> int:
        with self._lock:
            return self._memory


class ExecutionContext:
    def __init__(
        self,
        limits: Optional[ExecutionLimits] = None,
        cancellation: Optional[CancellationToken] = None,
        resource_pool: Optional[ResourcePool] = None,
        reservation_bytes: int = 0,
    ) -> None:
        self.limits = limits or ExecutionLimits()
        self.cancellation = cancellation or CancellationToken()
        self._started = time.monotonic()
        self._pool = resource_pool
        self._reservation = reservation_bytes
        self._reserved = False
        if self.limits.deadline_seconds is not None and self.limits.deadline_seconds < 0:
            raise ValueError("deadline_seconds must be non-negative")
        if self.limits.max_operations is not None and self.limits.max_operations <= 0:
            raise ValueError("max_operations must be positive")

    def __enter__(self) -> "ExecutionContext":
        if self._pool is not None:
            self._pool.reserve(self._reservation)
            self._reserved = True
        self.check()
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        if self._reserved:
            self._pool.release(self._reservation)
            self._reserved = False

    def check(self) -> None:
        if self.cancellation.cancelled:
            raise ExecutionCancelledError("execution was cancelled")
        if (
            self.limits.deadline_seconds is not None
            and time.monotonic() - self._started >= self.limits.deadline_seconds
        ):
            raise DeadlineExceededError("execution deadline exceeded")
