"""
Base Simulator interface and ExecutionResult definition.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
import numpy as np
from ..ir.qir import CircuitIR

@dataclass
class ExecutionResult:
    counts: Dict[str, int] = field(default_factory=dict)
    probabilities: Dict[str, float] = field(default_factory=dict)
    statevector: Optional[np.ndarray] = None
    density_matrix: Optional[np.ndarray] = None
    entanglement_entropy: Optional[float] = None
    execution_time_ms: float = 0.0
    backend_used: str = ""
    memory_used_bytes: int = 0
    shots: int = 1024
    metadata: Dict[str, Any] = field(default_factory=dict)

    def expectation_value(self, observable: str) -> float:
        """Helper to calculate <Z...Z> expectation value from counts."""
        if not self.counts:
            return 0.0
        val = 0.0
        total = sum(self.counts.values())
        for bitstring, count in self.counts.items():
            parity = bitstring.count("1") % 2
            sign = -1.0 if parity == 1 else 1.0
            val += sign * (count / total)
        return val

class BaseSimulator:
    def __init__(self, name: str = "base"):
        self.name = name

    def run(self, circuit: CircuitIR, shots: int = 1024, seed: int = 42) -> ExecutionResult:
        raise NotImplementedError


def checked_power_of_two(qubits: int, bytes_per_amplitude: int, *,
                         copies: int = 1) -> int:
    """Return an overflow-safe dense allocation estimate."""
    if isinstance(qubits, bool) or not isinstance(qubits, int) or qubits < 0:
        raise ValueError("qubits must be a non-negative integer")
    if copies <= 0 or bytes_per_amplitude <= 0:
        raise ValueError("allocation estimate parameters must be positive")
    if qubits >= 62:
        raise MemoryError("requested dense allocation exceeds supported integer range")
    return (1 << qubits) * bytes_per_amplitude * copies
