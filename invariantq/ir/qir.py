"""
Typed Intermediate Representation (qIR) for InvariantQ.
Encodes gate operations, measurements, noise primitives, classical control, and resource annotations.
"""

from __future__ import annotations
import math
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Tuple, Union
import numpy as np

CLIFFORD_GATES = {"h", "s", "sdg", "x", "y", "z", "cx", "cz", "swap", "cnot"}

@dataclass
class QWire:
    name: str
    index: int

    def __hash__(self):
        return hash((self.name, self.index))

    def __eq__(self, other):
        return isinstance(other, QWire) and self.name == other.name and self.index == other.index

    def __repr__(self):
        return f"{self.name}[{self.index}]"

@dataclass
class CWire:
    name: str
    index: int

    def __hash__(self):
        return hash((self.name, self.index))

    def __eq__(self, other):
        return isinstance(other, CWire) and self.name == other.name and self.index == other.index

    def __repr__(self):
        return f"{self.name}[{self.index}]"

@dataclass
class IROp:
    """Base IR Operation node."""
    id: int = 0
    qubits: List[QWire] = field(default_factory=list)
    clbits: List[CWire] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def is_clifford(self) -> bool:
        return False

@dataclass
class GateOp(IROp):
    name: str = "h"
    params: List[float] = field(default_factory=list)
    matrix: Optional[np.ndarray] = None

    def __post_init__(self):
        self.name = self.name.lower()
        if self.matrix is None:
            self.matrix = self._compute_matrix()

    def is_clifford(self) -> bool:
        return self.name in CLIFFORD_GATES

    def _compute_matrix(self) -> np.ndarray:
        inv_sqrt2 = 1.0 / math.sqrt(2.0)
        n = self.name
        p = self.params

        if n == "i" or n == "id":
            return np.eye(2, dtype=np.complex128)
        elif n == "x":
            return np.array([[0, 1], [1, 0]], dtype=np.complex128)
        elif n == "y":
            return np.array([[0, -1j], [1j, 0]], dtype=np.complex128)
        elif n == "z":
            return np.array([[1, 0], [0, -1]], dtype=np.complex128)
        elif n == "h":
            return np.array([[inv_sqrt2, inv_sqrt2], [inv_sqrt2, -inv_sqrt2]], dtype=np.complex128)
        elif n == "s":
            return np.array([[1, 0], [0, 1j]], dtype=np.complex128)
        elif n == "sdg":
            return np.array([[1, 0], [0, -1j]], dtype=np.complex128)
        elif n == "t":
            return np.array([[1, 0], [0, np.exp(1j * math.pi / 4)]], dtype=np.complex128)
        elif n == "tdg":
            return np.array([[1, 0], [0, np.exp(-1j * math.pi / 4)]], dtype=np.complex128)
        elif n == "rx":
            theta = p[0] if p else 0.0
            c = math.cos(theta / 2.0)
            s = math.sin(theta / 2.0)
            return np.array([[c, -1j * s], [-1j * s, c]], dtype=np.complex128)
        elif n == "ry":
            theta = p[0] if p else 0.0
            c = math.cos(theta / 2.0)
            s = math.sin(theta / 2.0)
            return np.array([[c, -s], [s, c]], dtype=np.complex128)
        elif n == "rz":
            theta = p[0] if p else 0.0
            return np.array([[np.exp(-1j * theta / 2.0), 0], [0, np.exp(1j * theta / 2.0)]], dtype=np.complex128)
        elif n == "p" or n == "phase":
            theta = p[0] if p else 0.0
            return np.array([[1, 0], [0, np.exp(1j * theta)]], dtype=np.complex128)
        elif n == "u3":
            theta = p[0] if len(p) > 0 else 0.0
            phi = p[1] if len(p) > 1 else 0.0
            lam = p[2] if len(p) > 2 else 0.0
            c = math.cos(theta / 2.0)
            s = math.sin(theta / 2.0)
            return np.array([
                [c, -np.exp(1j * lam) * s],
                [np.exp(1j * phi) * s, np.exp(1j * (phi + lam)) * c]
            ], dtype=np.complex128)
        elif n == "cx" or n == "cnot":
            return np.array([
                [1, 0, 0, 0],
                [0, 1, 0, 0],
                [0, 0, 0, 1],
                [0, 0, 1, 0]
            ], dtype=np.complex128)
        elif n == "cz":
            return np.array([
                [1, 0, 0, 0],
                [0, 1, 0, 0],
                [0, 0, 1, 0],
                [0, 0, 0, -1]
            ], dtype=np.complex128)
        elif n == "swap":
            return np.array([
                [1, 0, 0, 0],
                [0, 0, 1, 0],
                [0, 1, 0, 0],
                [0, 0, 0, 1]
            ], dtype=np.complex128)
        return np.eye(2 ** len(self.qubits), dtype=np.complex128)

@dataclass
class MeasureOp(IROp):
    qubit: QWire = field(default_factory=lambda: QWire("q", 0))
    clbit: CWire = field(default_factory=lambda: CWire("c", 0))

    def __post_init__(self):
        self.qubits = [self.qubit]
        self.clbits = [self.clbit]

@dataclass
class ResetOp(IROp):
    qubit: QWire = field(default_factory=lambda: QWire("q", 0))

    def __post_init__(self):
        self.qubits = [self.qubit]

@dataclass
class BarrierOp(IROp):
    pass

@dataclass
class NoiseOp(IROp):
    channel_name: str = "depolarizing"
    params: List[float] = field(default_factory=list)

@dataclass
class ConditionalOp(IROp):
    condition_clbit: CWire = field(default_factory=lambda: CWire("c", 0))
    condition_val: int = 1
    sub_op: IROp = field(default_factory=IROp)

    def __post_init__(self):
        self.qubits = self.sub_op.qubits
        self.clbits = [self.condition_clbit] + self.sub_op.clbits

@dataclass
class FusedGateOp(IROp):
    """Fused gate operation representing a consolidated unitary block (NWQ-Sim style)."""
    fused_matrix: np.ndarray = field(default_factory=lambda: np.eye(4, dtype=np.complex128))
    original_ops: List[GateOp] = field(default_factory=list)

    def is_clifford(self) -> bool:
        return False


class CircuitIR:
    """
    Complete Quantum Circuit Intermediate Representation (qIR).
    Maintains registers, instruction sequence, and resource estimation metadata.
    """
    def __init__(self, name: str = "circuit"):
        self.name = name
        self.qubit_regs: Dict[str, int] = {}
        self.clbit_regs: Dict[str, int] = {}
        self.ops: List[IROp] = []
        self._next_op_id = 0

    def add_qubit_register(self, name: str, size: int):
        self.qubit_regs[name] = size

    def add_clbit_register(self, name: str, size: int):
        self.clbit_regs[name] = size

    @property
    def num_qubits(self) -> int:
        return sum(self.qubit_regs.values())

    @property
    def num_clbits(self) -> int:
        return sum(self.clbit_regs.values())

    def get_qubit_index(self, wire: QWire) -> int:
        offset = 0
        for reg_name, size in self.qubit_regs.items():
            if reg_name == wire.name:
                return offset + wire.index
            offset += size
        raise KeyError(f"Qubit wire {wire} not found in registers")

    def add_op(self, op: IROp):
        op.id = self._next_op_id
        self._next_op_id += 1
        self.ops.append(op)

    def is_all_clifford(self) -> bool:
        for op in self.ops:
            if isinstance(op, (MeasureOp, BarrierOp, ResetOp)):
                continue
            if isinstance(op, GateOp) and not op.is_clifford():
                return False
            if isinstance(op, (NoiseOp, FusedGateOp, ConditionalOp)):
                return False
        return True

    def count_ops(self) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        for op in self.ops:
            if isinstance(op, GateOp):
                counts[op.name] = counts.get(op.name, 0) + 1
            elif isinstance(op, MeasureOp):
                counts["measure"] = counts.get("measure", 0) + 1
            elif isinstance(op, FusedGateOp):
                counts["fused"] = counts.get("fused", 0) + 1
            elif isinstance(op, NoiseOp):
                counts[f"noise_{op.channel_name}"] = counts.get(f"noise_{op.channel_name}", 0) + 1
            elif isinstance(op, ResetOp):
                counts["reset"] = counts.get("reset", 0) + 1
            elif isinstance(op, BarrierOp):
                counts["barrier"] = counts.get("barrier", 0) + 1
        return counts

    def depth(self) -> int:
        wire_depths: Dict[QWire, int] = {}
        for op in self.ops:
            if isinstance(op, BarrierOp):
                continue
            max_d = 0
            for q in op.qubits:
                max_d = max(max_d, wire_depths.get(q, 0))
            for q in op.qubits:
                wire_depths[q] = max_d + 1
        return max(wire_depths.values()) if wire_depths else 0

    def to_qasm(self) -> str:
        lines = ["OPENQASM 2.0;", 'include "qelib1.inc";']
        for name, size in self.qubit_regs.items():
            lines.append(f"qreg {name}[{size}];")
        for name, size in self.clbit_regs.items():
            lines.append(f"creg {name}[{size}];")

        for op in self.ops:
            if isinstance(op, GateOp):
                q_str = ", ".join(f"{q.name}[{q.index}]" for q in op.qubits)
                if op.params:
                    p_str = ", ".join(str(p) for p in op.params)
                    lines.append(f"{op.name}({p_str}) {q_str};")
                else:
                    lines.append(f"{op.name} {q_str};")
            elif isinstance(op, MeasureOp):
                lines.append(f"measure {op.qubit.name}[{op.qubit.index}] -> {op.clbit.name}[{op.clbit.index}];")
            elif isinstance(op, ResetOp):
                lines.append(f"reset {op.qubit.name}[{op.qubit.index}];")
            elif isinstance(op, BarrierOp):
                q_str = ", ".join(f"{q.name}[{q.index}]" for q in op.qubits)
                lines.append(f"barrier {q_str};")
        return "\n".join(lines)
