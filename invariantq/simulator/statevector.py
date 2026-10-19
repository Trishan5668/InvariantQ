"""
Exact State-Vector Simulator backend.
High performance simulation with multithreading and gate fusion support.
"""

from __future__ import annotations
import time
from typing import Dict, List, Optional
import numpy as np

from .base import BaseSimulator, ExecutionResult
from ..ir.qir import CircuitIR, GateOp, MeasureOp, ResetOp, FusedGateOp
from ..core.binding import NativeStateVector, HAS_NATIVE_CORE, native_core_status

class StateVectorSimulator(BaseSimulator):
    def __init__(self):
        super().__init__(name="statevector")

    def run(self, circuit: CircuitIR, shots: int = 1024, seed: int = 42) -> ExecutionResult:
        t0 = time.perf_counter()
        n = circuit.num_qubits
        if n == 0:
            raise ValueError("Circuit has 0 qubits")

        sv = NativeStateVector(n)
        mem_bytes = (1 << n) * 16 # 16 bytes per complex128

        # Execute operations
        for op in circuit.ops:
            if isinstance(op, GateOp):
                qubits = [circuit.get_qubit_index(q) for q in op.qubits]
                expected_dim = 1 << len(qubits)
                matrix = np.asarray(op.matrix, dtype=np.complex128)
                if (matrix.shape != (expected_dim, expected_dim) or
                        not np.isfinite(matrix).all() or
                        not np.allclose(matrix.conj().T @ matrix, np.eye(expected_dim), atol=1e-10, rtol=1e-10)):
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

        # Get final statevector & probabilities
        amps = sv.get_amplitudes()
        probs_vec = sv.get_probabilities()

        # Compute entanglement entropy across half bipartition if n >= 2
        entropy = 0.0
        if n >= 2:
            subsystem = list(range(n // 2))
            entropy = sv.von_neumann_entropy(subsystem)

        # Sample shots
        samples = sv.sample(shots, seed)
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
            metadata={"num_qubits": n, "dimension": 1 << n, "core": native_core_status()}
        )
