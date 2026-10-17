"""
Directed Acyclic Graph (DAG) circuit representation for InvariantQ.
Tracks wire dependencies, gate layers, and commutation relations.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict, Set, Optional, Tuple
from .qir import IROp, GateOp, MeasureOp, BarrierOp, ResetOp, NoiseOp, QWire, CWire, CircuitIR

@dataclass
class DAGNode:
    op: IROp
    node_id: int
    preds: List[DAGNode] = field(default_factory=list)
    succs: List[DAGNode] = field(default_factory=list)
    wire_preds: Dict[QWire, DAGNode] = field(default_factory=dict)
    wire_succs: Dict[QWire, DAGNode] = field(default_factory=dict)

    def __hash__(self):
        return hash(self.node_id)

    def __eq__(self, other):
        return isinstance(other, DAGNode) and self.node_id == other.node_id

class DAGCircuit:
    def __init__(self, circuit_ir: Optional[CircuitIR] = None):
        self.nodes: List[DAGNode] = []
        self._last_wire_node: Dict[QWire, DAGNode] = {}
        self._next_id = 0
        if circuit_ir:
            self.from_circuit_ir(circuit_ir)

    def add_op(self, op: IROp) -> DAGNode:
        node = DAGNode(op=op, node_id=self._next_id)
        self._next_id += 1

        for q in op.qubits:
            if q in self._last_wire_node:
                prev = self._last_wire_node[q]
                if prev not in node.preds:
                    node.preds.append(prev)
                if node not in prev.succs:
                    prev.succs.append(node)
                node.wire_preds[q] = prev
                prev.wire_succs[q] = node
            self._last_wire_node[q] = node

        self.nodes.append(node)
        return node

    def from_circuit_ir(self, ir: CircuitIR):
        self.nodes.clear()
        self._last_wire_node.clear()
        self._next_id = 0
        for op in ir.ops:
            self.add_op(op)

    def to_circuit_ir(self, base_ir: Optional[CircuitIR] = None) -> CircuitIR:
        new_ir = CircuitIR(name=base_ir.name if base_ir else "dag_circuit")
        if base_ir:
            new_ir.qubit_regs = dict(base_ir.qubit_regs)
            new_ir.clbit_regs = dict(base_ir.clbit_regs)

        for node in self.topological_sort():
            new_ir.add_op(node.op)
        return new_ir

    def topological_sort(self) -> List[DAGNode]:
        in_degrees = {n: len(n.preds) for n in self.nodes}
        queue = [n for n in self.nodes if in_degrees[n] == 0]
        sorted_nodes = []

        while queue:
            node = queue.pop(0)
            sorted_nodes.append(node)
            for succ in node.succs:
                in_degrees[succ] -= 1
                if in_degrees[succ] == 0:
                    queue.append(succ)

        if len(sorted_nodes) != len(self.nodes):
            raise RuntimeError("Cycle detected in DAG circuit representation")
        return sorted_nodes

    def layers(self) -> List[List[DAGNode]]:
        """Group independent ops into parallel execution layers."""
        node_depth: Dict[DAGNode, int] = {}
        for node in self.topological_sort():
            d = 0
            for pred in node.preds:
                d = max(d, node_depth[pred] + 1)
            node_depth[node] = d

        max_d = max(node_depth.values()) if node_depth else -1
        layers_list: List[List[DAGNode]] = [[] for _ in range(max_d + 1)]
        for node, d in node_depth.items():
            layers_list[d].append(node)
        return layers_list
