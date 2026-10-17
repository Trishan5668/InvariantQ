"""
NWQ-Sim Style Gate Fusion Pass.
Consolidates adjacent 1-qubit and 2-qubit operations into fused unitary blocks
to minimize memory bandwidth and statevector passes.
"""

from __future__ import annotations
from typing import List, Dict, Optional, Set
import numpy as np
from ..ir.qir import CircuitIR, IROp, GateOp, FusedGateOp, QWire

class GateFusionPass:
    def __init__(self, max_fused_qubits: int = 2):
        self.max_fused_qubits = max_fused_qubits

    def run(self, circuit: CircuitIR) -> CircuitIR:
        # Step 1: Fuse consecutive 1-qubit gates along each wire
        wire_fused_circuit = self._fuse_single_qubit_chains(circuit)

        # Step 2: Fuse 1-qubit gates adjacent to 2-qubit gates into consolidated 4x4 unitaries
        fully_fused_circuit = self._fuse_two_qubit_blocks(wire_fused_circuit)

        return fully_fused_circuit

    def _fuse_single_qubit_chains(self, circuit: CircuitIR) -> CircuitIR:
        new_circuit = CircuitIR(name=f"{circuit.name}_1q_fused")
        new_circuit.qubit_regs = dict(circuit.qubit_regs)
        new_circuit.clbit_regs = dict(circuit.clbit_regs)

        # Track active 1-qubit accumulated matrix for each wire
        wire_accum: Dict[QWire, Optional[GateOp]] = {}

        def flush_wire(w: QWire):
            if w in wire_accum and wire_accum[w] is not None:
                new_circuit.add_op(wire_accum[w])
                wire_accum[w] = None

        for op in circuit.ops:
            if not isinstance(op, GateOp) or op.matrix is None:
                # Flush all affected wires
                for q in op.qubits:
                    flush_wire(q)
                new_circuit.add_op(op)
                continue

            if len(op.qubits) == 1:
                q = op.qubits[0]
                if q not in wire_accum or wire_accum[q] is None:
                    wire_accum[q] = GateOp(name=op.name, qubits=[q], params=list(op.params), matrix=np.copy(op.matrix))
                else:
                    # Accumulate: next_matrix = op.matrix @ current_matrix
                    curr_op = wire_accum[q]
                    merged_matrix = op.matrix @ curr_op.matrix
                    wire_accum[q] = GateOp(
                        name="fused_1q",
                        qubits=[q],
                        params=[],
                        matrix=merged_matrix
                    )
            else:
                # Multi-qubit gate: flush active wires
                for q in op.qubits:
                    flush_wire(q)
                new_circuit.add_op(op)

        # Flush any remaining wires
        for w in list(wire_accum.keys()):
            flush_wire(w)

        return new_circuit

    def _fuse_two_qubit_blocks(self, circuit: CircuitIR) -> CircuitIR:
        new_circuit = CircuitIR(name=f"{circuit.name}_fused")
        new_circuit.qubit_regs = dict(circuit.qubit_regs)
        new_circuit.clbit_regs = dict(circuit.clbit_regs)

        ops = list(circuit.ops)
        i = 0
        n = len(ops)

        while i < n:
            op = ops[i]
            if not isinstance(op, GateOp) or op.matrix is None:
                new_circuit.add_op(op)
                i += 1
                continue

            # Greedy block fusion for contiguous ops affecting the same 1 or 2 qubits
            fusable_group = [op]
            active_qubits = list(op.qubits)
            j = i + 1

            while j < n:
                next_op = ops[j]
                if not isinstance(next_op, GateOp) or next_op.matrix is None:
                    break

                combined = list(set(active_qubits + next_op.qubits))
                if len(combined) <= self.max_fused_qubits and any(q in active_qubits for q in next_op.qubits):
                    fusable_group.append(next_op)
                    active_qubits = combined
                    j += 1
                else:
                    break

            if len(fusable_group) > 1:
                fused_mat = self._contract_group(fusable_group, active_qubits)
                if len(active_qubits) == 1:
                    new_op = GateOp(name="fused_1q", qubits=active_qubits, matrix=fused_mat)
                else:
                    new_op = FusedGateOp(fused_matrix=fused_mat, original_ops=fusable_group)
                    new_op.qubits = active_qubits
                new_circuit.add_op(new_op)
                i = j
            else:
                new_circuit.add_op(op)
                i += 1

        return new_circuit

    def _contract_group(self, ops: List[GateOp], target_qubits: List[QWire]) -> np.ndarray:
        dim = 2 ** len(target_qubits)
        total_U = np.eye(dim, dtype=np.complex128)

        qubit_map = {q: idx for idx, q in enumerate(target_qubits)}

        for op in ops:
            u_op = op.matrix
            op_qubits = [qubit_map[q] for q in op.qubits]

            full_u = self._lift_unitary(u_op, op_qubits, len(target_qubits))
            total_U = full_u @ total_U

        return total_U

    def _lift_unitary(self, u: np.ndarray, qubits: List[int], total_qubits: int) -> np.ndarray:
        if total_qubits == 1:
            return u

        if total_qubits == 2:
            if len(qubits) == 1:
                q = qubits[0]
                if q == 0:
                    return np.kron(u, np.eye(2, dtype=np.complex128))
                else:
                    return np.kron(np.eye(2, dtype=np.complex128), u)
            elif len(qubits) == 2:
                if qubits == [0, 1]:
                    return u
                else:
                    SWAP = np.array([[1,0,0,0],[0,0,1,0],[0,1,0,0],[0,0,0,1]], dtype=np.complex128)
                    return SWAP @ u @ SWAP

        return np.eye(2 ** total_qubits, dtype=np.complex128)
