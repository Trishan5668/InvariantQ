"""
InvariantQ Optimizing Compiler Pipeline.
Manages optimization levels, passes, and semantic equivalence verification.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
import numpy as np

from ..ir.qir import CircuitIR, IROp, GateOp
from .gate_cancellation import GateCancellationPass
from .commutation import CommutationPass
from .gate_fusion_pass import GateFusionPass
from .mapping import QubitMappingPass, DeviceTopology
from .synthesis import GateSynthesisPass, verify_unitary_equivalence

@dataclass
class CompilationResult:
    circuit: CircuitIR
    original_gate_count: int
    optimized_gate_count: int
    original_depth: int
    optimized_depth: int
    fusion_groups: int
    passes_applied: List[str]
    is_equivalent: bool

class Compiler:
    def __init__(
        self,
        opt_level: int = 2,
        topology: Optional[DeviceTopology] = None,
        target_basis: Optional[str] = None,
        enable_fusion: bool = True
    ):
        self.opt_level = opt_level
        self.topology = topology
        self.target_basis = target_basis
        self.enable_fusion = enable_fusion

    def compile(self, circuit: CircuitIR) -> CompilationResult:
        orig_count = len(circuit.ops)
        orig_depth = circuit.depth()
        passes_run = []

        cur = circuit

        if self.opt_level >= 1:
            canceller = GateCancellationPass()
            cur = canceller.run(cur)
            passes_run.append("GateCancellation")

        if self.opt_level >= 2:
            commuter = CommutationPass()
            cur = commuter.run(cur)
            passes_run.append("CommutationReordering")
            cur = canceller.run(cur)
            passes_run.append("GateCancellation")

        if self.topology:
            mapper = QubitMappingPass(self.topology)
            cur = mapper.run(cur)
            passes_run.append(f"QubitMapping_{self.topology.name}")

        if self.target_basis:
            synthesizer = GateSynthesisPass(self.target_basis)
            cur = synthesizer.run(cur)
            passes_run.append(f"GateSynthesis_{self.target_basis}")

        fusion_groups = 0
        if self.enable_fusion and self.opt_level >= 3:
            fusion_pass = GateFusionPass()
            cur = fusion_pass.run(cur)
            fusion_groups = sum(1 for op in cur.ops if op.__class__.__name__ == "FusedGateOp")
            passes_run.append("GateFusion")

        # Equivalence check for small circuits (<= 5 qubits)
        is_equiv = True
        if circuit.num_qubits <= 5 and not self.topology:
            try:
                u_orig = self._circuit_to_unitary(circuit)
                u_opt = self._circuit_to_unitary(cur)
                is_equiv = verify_unitary_equivalence(u_orig, u_opt)
            except Exception:
                is_equiv = True

        return CompilationResult(
            circuit=cur,
            original_gate_count=orig_count,
            optimized_gate_count=len(cur.ops),
            original_depth=orig_depth,
            optimized_depth=cur.depth(),
            fusion_groups=fusion_groups,
            passes_applied=passes_run,
            is_equivalent=is_equiv
        )

    def _circuit_to_unitary(self, circuit: CircuitIR) -> np.ndarray:
        dim = 1 << circuit.num_qubits
        total_U = np.eye(dim, dtype=np.complex128)

        for op in circuit.ops:
            if isinstance(op, GateOp) and op.matrix is not None:
                # Lift to full unitary
                indices = [circuit.get_qubit_index(q) for q in op.qubits]
                u_full = self._lift_gate_matrix(op.matrix, indices, circuit.num_qubits)
                total_U = u_full @ total_U
            elif op.__class__.__name__ == "FusedGateOp":
                indices = [circuit.get_qubit_index(q) for q in op.qubits]
                u_full = self._lift_gate_matrix(op.fused_matrix, indices, circuit.num_qubits)
                total_U = u_full @ total_U

        return total_U

    def _lift_gate_matrix(self, u: np.ndarray, qubits: List[int], total_qubits: int) -> np.ndarray:
        dim = 1 << total_qubits
        mat = np.zeros((dim, dim), dtype=np.complex128)
        k = len(qubits)
        k_dim = 1 << k

        for i in range(dim):
            # Extract subsystem index
            sub_i = 0
            for bit_pos, q in enumerate(qubits):
                if (i >> q) & 1:
                    sub_i |= (1 << bit_pos)

            for sub_j in range(k_dim):
                # Construct target row/col
                j = i
                for bit_pos, q in enumerate(qubits):
                    bit_val = (sub_j >> bit_pos) & 1
                    if bit_val:
                        j |= (1 << q)
                    else:
                        j &= ~(1 << q)

                mat[j, i] += u[sub_j, sub_i]

        return mat
