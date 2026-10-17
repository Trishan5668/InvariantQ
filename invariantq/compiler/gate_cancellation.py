"""
Gate Cancellation and Parametric Rotation Merging Pass.
Eliminates adjacent self-inverses and combines continuous rotations.
"""

from __future__ import annotations
import math
from typing import List, Optional
from ..ir.qir import CircuitIR, IROp, GateOp, MeasureOp, BarrierOp, ResetOp, QWire

SELF_INVERSES = {"h", "x", "y", "z", "cx", "cnot", "cz", "swap"}

INVERSE_PAIRS = {
    ("s", "sdg"), ("sdg", "s"),
    ("t", "tdg"), ("tdg", "t"),
}

ROTATION_GATES = {"rx", "ry", "rz", "p", "phase"}

class GateCancellationPass:
    def __init__(self, tolerance: float = 1e-9):
        self.tolerance = tolerance

    def run(self, circuit: CircuitIR) -> CircuitIR:
        new_circuit = CircuitIR(name=f"{circuit.name}_cancelled")
        new_circuit.qubit_regs = dict(circuit.qubit_regs)
        new_circuit.clbit_regs = dict(circuit.clbit_regs)

        # Wire-by-wire stack reduction
        # Track pending gate for each wire
        wire_stacks: dict[QWire, List[GateOp]] = {
            QWire(reg, idx): []
            for reg, size in circuit.qubit_regs.items()
            for idx in range(size)
        }

        # We will process sequentially through a stack-based algorithm
        optimized_ops: List[IROp] = []

        for op in circuit.ops:
            if not isinstance(op, GateOp):
                optimized_ops.append(op)
                continue

            # Check for cancellation on top of stack
            if len(op.qubits) == 1:
                q = op.qubits[0]
                if optimized_ops and isinstance(optimized_ops[-1], GateOp) and optimized_ops[-1].qubits == [q]:
                    prev = optimized_ops[-1]
                    # Check 1: Self-inverses (e.g. H H = I, X X = I)
                    if op.name == prev.name and op.name in SELF_INVERSES and not op.params and not prev.params:
                        optimized_ops.pop() # Cancelled!
                        continue

                    # Check 2: Inverse pairs (e.g. S Sdg = I, T Tdg = I)
                    if (prev.name, op.name) in INVERSE_PAIRS and not op.params and not prev.params:
                        optimized_ops.pop() # Cancelled!
                        continue

                    # Check 3: Continuous rotation merging (e.g. Rz(a) Rz(b) = Rz(a+b))
                    if op.name == prev.name and op.name in ROTATION_GATES and op.params and prev.params:
                        new_theta = (prev.params[0] + op.params[0]) % (4.0 * math.pi)
                        optimized_ops.pop()
                        # If theta ~ 0 (or multiple of 2pi for non-SU2 / 4pi), drop gate
                        if abs(math.sin(new_theta / 2.0)) > self.tolerance:
                            merged = GateOp(
                                name=op.name,
                                qubits=[q],
                                params=[new_theta]
                            )
                            optimized_ops.append(merged)
                        continue

            elif len(op.qubits) == 2:
                q0, q1 = op.qubits[0], op.qubits[1]
                if optimized_ops and isinstance(optimized_ops[-1], GateOp) and optimized_ops[-1].qubits == [q0, q1]:
                    prev = optimized_ops[-1]
                    if op.name == prev.name and op.name in SELF_INVERSES and not op.params and not prev.params:
                        optimized_ops.pop() # CX CX = I, CZ CZ = I, SWAP SWAP = I
                        continue

            optimized_ops.append(op)

        for op in optimized_ops:
            new_circuit.add_op(op)

        return new_circuit
