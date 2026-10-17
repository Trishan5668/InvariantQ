"""
Matrix Product State (MPS) Tensor-Network Simulator backend.
Simulates large, weakly-entangled circuits with bond-dimension truncation.
"""

from __future__ import annotations
import time
from typing import Dict, List, Optional
import numpy as np

from .base import BaseSimulator, ExecutionResult
from ..ir.qir import CircuitIR, GateOp, MeasureOp
from ..core.binding import NativeMPS

class TensorNetworkSimulator(BaseSimulator):
    def __init__(self, max_bond_dim: int = 64, cutoff: float = 1e-12):
        super().__init__(name="tensor_network")
        self.max_bond_dim = max_bond_dim
        self.cutoff = cutoff

    def run(self, circuit: CircuitIR, shots: int = 1024, seed: int = 42) -> ExecutionResult:
        t0 = time.perf_counter()
        n = circuit.num_qubits

        mps = NativeMPS(n, max_bond_dim=self.max_bond_dim, cutoff=self.cutoff)
        mem_bytes = n * 2 * (self.max_bond_dim ** 2) * 16

        for op in circuit.ops:
            if isinstance(op, GateOp):
                qubits = [circuit.get_qubit_index(q) for q in op.qubits]
                if len(qubits) == 1:
                    mps.apply_1q(qubits[0], op.matrix)
                elif len(qubits) == 2:
                    mps.apply_2q(qubits[0], qubits[1], op.matrix)

        # Entanglement entropy at middle cut
        mid_cut = (n - 1) // 2 if n > 1 else 0
        entropy = mps.entanglement_entropy(mid_cut) if n > 1 else 0.0

        # Statevector reconstruction for n <= 16
        statevector = None
        counts: Dict[str, int] = {}
        probs: Dict[str, float] = {}

        if n <= 16:
            statevector = mps.to_statevector()
            p_vec = np.abs(statevector) ** 2
            p_sum = np.sum(p_vec)
            if p_sum > 0:
                p_vec /= p_sum

            rng = np.random.default_rng(seed)
            samples = rng.choice(1 << n, size=shots, p=p_vec)
            for s in samples:
                bitstr = f"{s:0{n}b}"
                counts[bitstr] = counts.get(bitstr, 0) + 1
            for i, p in enumerate(p_vec):
                if p > 1e-7:
                    probs[f"{i:0{n}b}"] = float(p)
        else:
            # Measure sequentially using MPS
            rng = np.random.default_rng(seed)
            for _ in range(shots):
                # Sample bitstring by measuring each site
                bit_list = []
                for q in range(n):
                    r_val = rng.random()
                    bit_list.append(str(mps.measure(q, r_val)))
                bitstr = "".join(bit_list)
                counts[bitstr] = counts.get(bitstr, 0) + 1
            probs = {k: v / shots for k, v in counts.items()}

        t1 = time.perf_counter()
        exec_ms = (t1 - t0) * 1000.0

        return ExecutionResult(
            counts=counts,
            probabilities=probs,
            statevector=statevector,
            entanglement_entropy=entropy,
            execution_time_ms=exec_ms,
            backend_used="tensor_network",
            memory_used_bytes=mem_bytes,
            shots=shots,
            metadata={"num_qubits": n, "max_bond_dim": self.max_bond_dim}
        )
