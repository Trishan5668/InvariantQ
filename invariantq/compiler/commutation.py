"""
Commutation-Based Reordering Optimization Pass.
Identifies commuting gates and reorders them to unlock cancellation opportunities.
"""

from __future__ import annotations
from typing import List, Set, Tuple
from ..ir.qir import CircuitIR, IROp, GateOp, QWire

DIAGONAL_GATES = {"z", "s", "sdg", "t", "tdg", "rz", "p", "phase", "cz"}

def gates_commute(op1: GateOp, op2: GateOp) -> bool:
    q1 = set(op1.qubits)
    q2 = set(op2.qubits)

    # Disjoint qubits commute trivially
    if not (q1 & q2):
        return True

    # Both diagonal gates commute
    if op1.name in DIAGONAL_GATES and op2.name in DIAGONAL_GATES:
        return True

    # Controls of multiple CX gates commute
    if op1.name in ("cx", "cnot") and op2.name in ("cx", "cnot"):
        # Shared control qubit, distinct targets
        if len(op1.qubits) == 2 and len(op2.qubits) == 2:
            if op1.qubits[0] == op2.qubits[0] and op1.qubits[1] != op2.qubits[1]:
                return True
            # Shared target with X on target commutes? No, control must commute
            if op1.qubits[1] == op2.qubits[1] and op1.qubits[0] != op2.qubits[0]:
                return True

    # CX control commutes with Z on control
    if op1.name in ("cx", "cnot") and op2.name in ("z", "rz", "s", "sdg", "t", "tdg"):
        if len(op1.qubits) == 2 and op2.qubits == [op1.qubits[0]]:
            return True
    if op2.name in ("cx", "cnot") and op1.name in ("z", "rz", "s", "sdg", "t", "tdg"):
        if len(op2.qubits) == 2 and op1.qubits == [op2.qubits[0]]:
            return True

    # CX target commutes with X on target
    if op1.name in ("cx", "cnot") and op2.name in ("x", "rx"):
        if len(op1.qubits) == 2 and op2.qubits == [op1.qubits[1]]:
            return True
    if op2.name in ("cx", "cnot") and op1.name in ("x", "rx"):
        if len(op2.qubits) == 2 and op1.qubits == [op2.qubits[1]]:
            return True

    return False


class CommutationPass:
    def __init__(self, max_bubble_distance: int = 10):
        self.max_bubble_distance = max_bubble_distance

    def run(self, circuit: CircuitIR) -> CircuitIR:
        ops = list(circuit.ops)
        changed = True
        iterations = 0

        # Bubble-sort-like pass to bring commuting identical or inverse gates together
        while changed and iterations < 5:
            changed = False
            iterations += 1

            for i in range(len(ops) - 1):
                if not isinstance(ops[i], GateOp) or not isinstance(ops[i + 1], GateOp):
                    continue

                op1 = ops[i]
                op2 = ops[i + 1]

                # If they are on disjoint qubits or commute, see if swapping brings op1 closer to a cancellation
                if gates_commute(op1, op2):
                    # Lookahead: is there a gate ahead that cancels op1?
                    can_cancel_ahead = False
                    for k in range(i + 2, min(len(ops), i + 2 + self.max_bubble_distance)):
                        if isinstance(ops[k], GateOp) and ops[k].qubits == op1.qubits and ops[k].name == op1.name:
                            can_cancel_ahead = True
                            break

                    if can_cancel_ahead:
                        # Swap op1 and op2
                        ops[i], ops[i + 1] = ops[i + 1], ops[i]
                        changed = True

        new_circuit = CircuitIR(name=f"{circuit.name}_commuted")
        new_circuit.qubit_regs = dict(circuit.qubit_regs)
        new_circuit.clbit_regs = dict(circuit.clbit_regs)
        for op in ops:
            new_circuit.add_op(op)

        return new_circuit
