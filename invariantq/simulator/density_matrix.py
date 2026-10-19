"""
Density Matrix Simulator backend for open quantum systems and CPTP noise channels.
"""

from __future__ import annotations
import time
from typing import Dict, List, Optional
import numpy as np

from .base import BaseSimulator, ExecutionResult
from ..ir.qir import CircuitIR, GateOp, NoiseOp, ResetOp
from ..core.binding import NativeDensityMatrix, native_core_status
from ..noise.channels import build_kraus_channel

class DensityMatrixSimulator(BaseSimulator):
    def __init__(self, noise_model: Optional[Dict[str, List[np.ndarray]]] = None):
        super().__init__(name="density_matrix")
        self.noise_model = noise_model

    def run(self, circuit: CircuitIR, shots: int = 1024, seed: int = 42) -> ExecutionResult:
        t0 = time.perf_counter()
        n = circuit.num_qubits
        if n > 14:
            raise MemoryError(
                f"Density matrix requires 16^{n} bytes ({((1 << (2*n)) * 16) / (1024**3):.2f} GB). "
                f"For n > 14, please use StateVector or TensorNetwork (MPS) backend."
            )

        dm = NativeDensityMatrix(n)
        dim = 1 << n
        mem_bytes = (dim * dim) * 16

        for op in circuit.ops:
            if isinstance(op, GateOp):
                qubits = [circuit.get_qubit_index(q) for q in op.qubits]
                if len(qubits) == 1:
                    dm.apply_1q_unitary(qubits[0], op.matrix)
                    if self.noise_model and op.name in self.noise_model:
                        dm.apply_1q_kraus(qubits[0], self.noise_model[op.name])
                elif len(qubits) == 2:
                    dm.apply_2q_unitary(qubits[0], qubits[1], op.matrix)
                    if self.noise_model and op.name in self.noise_model:
                        kraus = self.noise_model[op.name]
                        if kraus[0].shape == (4, 4):
                            dm.apply_2q_kraus(qubits[0], qubits[1], kraus)
                        else:
                            dm.apply_1q_kraus(qubits[0], kraus)
                            dm.apply_1q_kraus(qubits[1], kraus)
            elif isinstance(op, ResetOp):
                q_idx = circuit.get_qubit_index(op.qubit)
                dm.reset_qubit(q_idx)
            elif isinstance(op, NoiseOp):
                qubits = [circuit.get_qubit_index(q) for q in op.qubits]
                kraus_ops = build_kraus_channel(op.channel_name, op.params)
                for q in qubits:
                    dm.apply_1q_kraus(q, kraus_ops)

        mat = dm.get_matrix()
        trace = dm.trace()
        purity = dm.purity()
        entropy = dm.von_neumann_entropy()

        # Extract diagonal probabilities
        diag_probs = np.maximum(0.0, np.real(np.diag(mat)))
        diag_sum = np.sum(diag_probs)
        if diag_sum > 0:
            diag_probs /= diag_sum

        # Sample shots based on diagonal
        rng = np.random.default_rng(seed)
        samples = rng.choice(dim, size=shots, p=diag_probs)
        counts: Dict[str, int] = {}
        for s in samples:
            bitstr = f"{s:0{n}b}"
            counts[bitstr] = counts.get(bitstr, 0) + 1

        probs: Dict[str, float] = {}
        for i, p in enumerate(diag_probs):
            if p > 1e-7:
                probs[f"{i:0{n}b}"] = float(p)

        t1 = time.perf_counter()
        exec_ms = (t1 - t0) * 1000.0

        return ExecutionResult(
            counts=counts,
            probabilities=probs,
            density_matrix=mat,
            entanglement_entropy=entropy,
            execution_time_ms=exec_ms,
            backend_used="density_matrix",
            memory_used_bytes=mem_bytes,
            shots=shots,
            metadata={
                "num_qubits": n,
                "dimension": dim,
                "trace": trace,
                "purity": purity,
                "core": native_core_status(),
            }
        )
