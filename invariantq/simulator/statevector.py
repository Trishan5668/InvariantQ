"""
Exact State-Vector Simulator backend.
High performance simulation with multithreading and gate fusion support.
"""

from __future__ import annotations
import time
from typing import Dict, List, Optional
import numpy as np

from .base import BaseSimulator, ExecutionResult, checked_power_of_two
from ..ir.qir import CircuitIR, GateOp, MeasureOp, ResetOp, FusedGateOp
from ..core.binding import NativeStateVector, HAS_NATIVE_CORE, native_core_status
from ..execution import ExecutionContext

class StateVectorSimulator(BaseSimulator):
    def __init__(self, max_memory_bytes: Optional[int] = None):
        super().__init__(name="statevector")
        self.max_memory_bytes = max_memory_bytes

    def run(
        self,
        circuit: CircuitIR,
        shots: int = 1024,
        seed: int = 42,
        *,
        allow_non_unitary: bool = False,
        execution_context: Optional[ExecutionContext] = None,
    ) -> ExecutionResult:
        t0 = time.perf_counter()
        if isinstance(shots, bool) or not isinstance(shots, (int, np.integer)) or shots <= 0:
            raise ValueError("shots must be a positive integer")
        if isinstance(seed, bool) or not isinstance(seed, (int, np.integer)) or seed < 0:
            raise ValueError("seed must be a non-negative integer")
        n = circuit.num_qubits
        if n == 0:
            raise ValueError("Circuit has 0 qubits")

        mem_bytes = checked_power_of_two(n, 16, copies=2)
        if self.max_memory_bytes is not None and mem_bytes > self.max_memory_bytes:
            raise MemoryError(
                f"statevector requires approximately {mem_bytes} bytes including a working copy, "
                f"above configured limit {self.max_memory_bytes}"
            )


        context = execution_context or ExecutionContext()
        with context:
            sv = NativeStateVector(n)
            for op in circuit.ops:
                context.check()
                if isinstance(op, GateOp):
                    qubits = [circuit.get_qubit_index(q) for q in op.qubits]
                    expected_dim = 1 << len(qubits)
                    matrix = np.asarray(op.matrix, dtype=np.complex128)
                    is_valid_unitary = (
                        matrix.shape == (expected_dim, expected_dim)
                        and np.isfinite(matrix).all()
                        and np.allclose(
                            matrix.conj().T @ matrix,
                            np.eye(expected_dim),
                            atol=1e-10,
                            rtol=1e-10,
                        )
                    )
                    if not is_valid_unitary and not allow_non_unitary:
                        raise ValueError(f"Gate '{op.name}' is not a finite unitary matrix")
                    if len(qubits) == 1:
                        sv.apply_1q(qubits[0], matrix)
                    elif len(qubits) == 2:
                        sv.apply_2q(qubits[0], qubits[1], matrix)
                    else:
                        sv.apply_fused(qubits, matrix)
                elif isinstance(op, FusedGateOp):
                    qubits = [circuit.get_qubit_index(q) for q in op.qubits]
                    sv.apply_fused(qubits, op.fused_matrix)
                elif isinstance(op, ResetOp):
                    q_idx = circuit.get_qubit_index(op.qubit)
                    sv.reset_qubit(q_idx)

        context.check()
        # Get final statevector & probabilities
        amps = sv.get_amplitudes()
        probs_vec = sv.get_probabilities()

        # Compute entanglement entropy across half bipartition if n >= 2
        entropy = 0.0
        if n >= 2:
            subsystem = list(range(n // 2))
            entropy = sv.von_neumann_entropy(subsystem)

        # Sample shots
        if allow_non_unitary:
            total_probability = float(np.sum(probs_vec))
            if not np.isfinite(total_probability) or total_probability <= 0.0:
                raise ValueError("non-unitary trajectory produced an invalid state norm")
            samples = np.random.default_rng(seed).choice(
                1 << n,
                size=shots,
                p=np.asarray(probs_vec, dtype=np.float64) / total_probability,
            )
        else:
            samples = sv.sample(shots, seed)
        context.check()
        counts: Dict[str, int] = {}
        for s in samples:
            # format as binary string
            bitstr = f"{s:0{n}b}"
            counts[bitstr] = counts.get(bitstr, 0) + 1

        probs: Dict[str, float] = {}
        for i, p in enumerate(probs_vec):
            if p > 1e-7:
                probs[f"{i:0{n}b}"] = float(p)

        t1 = time.perf_counter()
        exec_ms = (t1 - t0) * 1000.0

        return ExecutionResult(
            counts=counts,
            probabilities=probs,
            statevector=amps,
            entanglement_entropy=entropy,
            execution_time_ms=exec_ms,
            backend_used="statevector",
            memory_used_bytes=mem_bytes,
            shots=shots,
            metadata={
                "num_qubits": n,
                "dimension": 1 << n,
                "allow_non_unitary": allow_non_unitary,
                "state_norm": float(np.sum(probs_vec)),
                "core": native_core_status(),
                "provenance": {
                    "requested_backend": self.name,
                    "selected_backend": "statevector",
                    "implementation": "dense_statevector",
                    "native": HAS_NATIVE_CORE,
                    "exact": not allow_non_unitary,
                    "resource_limit_bytes": self.max_memory_bytes,
                    "completion": "completed",
                },
            }
        )


class NoisyStatevectorSimulator(StateVectorSimulator):
    """Isolated fault-analysis statevector path allowing unphysical gates."""

    def run(
        self,
        circuit: CircuitIR,
        shots: int = 1024,
        seed: int = 42,
        *,
        allow_non_unitary: bool = True,
    ) -> ExecutionResult:
        return super().run(
            circuit,
            shots=shots,
            seed=seed,
            allow_non_unitary=True,
        )
