"""Truthful, runtime-derived simulator capability descriptions.

This module is deliberately separate from planner heuristics: callers can
inspect what an installed build can actually execute before submitting work.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict, FrozenSet, Optional

from ..core.binding import HAS_NATIVE_CORE, NativeMPS, NativeStabilizer, native_core_status
from ..ir.qir import CircuitIR, ConditionalOp, FusedGateOp, GateOp, NoiseOp


@dataclass(frozen=True)
class BackendCapability:
    name: str
    implementation: str
    exact: bool
    supports_noise: bool
    supports_mid_circuit_measurement: bool
    supported_gate_families: FrozenSet[str]
    max_qubits: Optional[int]
    complexity: str
    independently_validated: bool
    limitations: str

    def to_dict(self) -> Dict[str, Any]:
        value = asdict(self)
        value["supported_gate_families"] = sorted(self.supported_gate_families)
        return value


_CLIFFORD = frozenset({"i", "id", "h", "s", "sdg", "x", "y", "z", "cx", "cnot", "cy", "cz", "swap"})


def backend_capabilities() -> Dict[str, BackendCapability]:
    """Describe paths selected by *this* Python process, not advertised paths."""
    core = native_core_status()
    native = core["active"]
    stabilizer_is_tableau = native or bool(getattr(NativeStabilizer, "is_genuine_tableau", False))
    mps_is_genuine = native or bool(getattr(NativeMPS, "is_genuine_mps", False))
    return {
        "statevector": BackendCapability(
            name="statevector", implementation="native-cpp" if native else "numpy-statevector",
            exact=True, supports_noise=False, supports_mid_circuit_measurement=True,
            supported_gate_families=frozenset({"arbitrary finite unitary matrices", "reset"}),
            max_qubits=None if native else 24, complexity="O(2^n) memory and per gate",
            independently_validated=True,
            limitations="Noise operations are unsupported; fallback allocation is capped at 24 qubits.",
        ),
        "density_matrix": BackendCapability(
            name="density_matrix", implementation="native-cpp" if native else "numpy-density-matrix",
            exact=True, supports_noise=True, supports_mid_circuit_measurement=True,
            supported_gate_families=frozenset({"one/two-qubit unitaries", "one-qubit Kraus channels", "reset"}),
            max_qubits=14 if native else 12, complexity="O(4^n) memory and gate work",
            independently_validated=False,
            limitations="Two-qubit noise-model application is not exposed by the portable binding.",
        ),
        "stabilizer": BackendCapability(
            name="stabilizer",
            implementation=("native-binary-tableau" if native else
                            "python-binary-tableau" if stabilizer_is_tableau else "dense compatibility fallback"),
            exact=stabilizer_is_tableau, supports_noise=False, supports_mid_circuit_measurement=True,
            supported_gate_families=_CLIFFORD,
            max_qubits=None if stabilizer_is_tableau else 24,
            complexity="O(n^2) tableau storage; O(n^2) Clifford update / O(n^2) measurement",
            independently_validated=False,
            limitations=("Non-Clifford gates and noise are rejected." if stabilizer_is_tableau else
                         "This fallback allocates a dense statevector and is not scalable."),
        ),
        "tensor_network": BackendCapability(
            name="tensor_network",
            implementation=("native-mps" if native else "python-mps" if mps_is_genuine else "dense compatibility fallback"),
            exact=False, supports_noise=False, supports_mid_circuit_measurement=True,
            supported_gate_families=frozenset({"one/two-qubit unitaries", "measurement"}),
            max_qubits=None if mps_is_genuine else 24,
            complexity="O(n χ²) storage; local two-qubit updates scale with χ³",
            independently_validated=False,
            limitations=("Approximate when bond truncation discards weight; non-unitary noise is unsupported."
                         if mps_is_genuine else "This fallback allocates a dense statevector and is not scalable."),
        ),
    }


def compatibility_reason(circuit: CircuitIR, capability: BackendCapability) -> Optional[str]:
    """Return a user-facing incompatibility reason, or ``None`` if supported."""
    if capability.max_qubits is not None and circuit.num_qubits > capability.max_qubits:
        return f"{capability.name} {capability.implementation} supports at most {capability.max_qubits} qubits"
    if any(isinstance(op, NoiseOp) for op in circuit.ops) and not capability.supports_noise:
        return f"{capability.name} does not implement NoiseOp evolution"
    if capability.name == "stabilizer":
        for op in circuit.ops:
            if isinstance(op, GateOp) and op.name not in _CLIFFORD:
                return f"stabilizer does not support non-Clifford gate '{op.name}'"
            if isinstance(op, (ConditionalOp, FusedGateOp)):
                return f"stabilizer does not support {type(op).__name__}"
    if any(isinstance(op, ConditionalOp) for op in circuit.ops):
        return f"{capability.name} does not currently implement ConditionalOp execution"
    return None
