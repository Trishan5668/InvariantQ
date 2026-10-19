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
from ..core.binding import NativeMPS, HAS_NATIVE_CORE, native_core_status

class TensorNetworkSimulator(BaseSimulator):
    def __init__(self, max_bond_dim: int = 64, cutoff: float = 1e-12,
                 max_memory_bytes: Optional[int] = None):
        super().__init__(name="tensor_network")
        self.max_bond_dim = max_bond_dim
        self.cutoff = cutoff
        self.max_memory_bytes = max_memory_bytes

    def run(self, circuit: CircuitIR, shots: int = 1024, seed: int = 42) -> ExecutionResult:
        t0 = time.perf_counter()
        if isinstance(shots, bool) or not isinstance(shots, (int, np.integer)) or shots <= 0:
            raise ValueError("shots must be a positive integer")
        if isinstance(seed, bool) or not isinstance(seed, (int, np.integer)) or seed < 0:
            raise ValueError("seed must be a non-negative integer")
        n = circuit.num_qubits
        if not bool(getattr(NativeMPS, "is_genuine_mps", False)):
            raise RuntimeError(
                "tensor-network backend unavailable: a genuine MPS implementation is required"
            )

        mps = NativeMPS(n, max_bond_dim=self.max_bond_dim, cutoff=self.cutoff)
        mem_bytes = n * 2 * (self.max_bond_dim ** 2) * 16
        if self.max_memory_bytes is not None and mem_bytes > self.max_memory_bytes:
            raise MemoryError(
                f"MPS resource estimate {mem_bytes} bytes exceeds configured limit "
                f"{self.max_memory_bytes}"
            )

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
            raw_sv = mps.to_statevector()
            # Convert MPS big-endian representation (site 0 = MSB) to canonical little-endian (qubit k = 1 << k)
            if n > 1 and HAS_NATIVE_CORE:
                t = raw_sv.reshape([2] * n)
                statevector = np.transpose(t, list(reversed(range(n)))).flatten()
            else:
                statevector = raw_sv
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
            metadata={"num_qubits": n, "max_bond_dim": self.max_bond_dim,
                      "algorithm": "matrix_product_state",
                      "implementation": "native-mps" if HAS_NATIVE_CORE else "python-mps",
                      "is_approximate": bool(getattr(mps, "is_approximate", True)),
                      "bond_dimensions": list(getattr(mps, "bond_dimensions", ())),
                      "provenance": {
                          "requested_backend": self.name,
                          "selected_backend": "tensor_network",
                          "implementation": "matrix_product_state",
                          "native": HAS_NATIVE_CORE,
                          "exact": not bool(getattr(mps, "is_approximate", True)),
                          "resource_limit_bytes": self.max_memory_bytes,
                          "completion": "completed",
                      },
                      "core": native_core_status()}
        )
