"""
Qubit Mapping and Routing Pass.
Maps logical qubits to physical device topology and routes 2-qubit interactions via SWAP insertion.
"""

from __future__ import annotations
from typing import List, Dict, Set, Tuple, Optional
from collections import deque
from ..ir.qir import CircuitIR, IROp, GateOp, QWire

class DeviceTopology:
    def __init__(self, num_qubits: int, edges: List[Tuple[int, int]], name: str = "custom"):
        self.num_qubits = num_qubits
        self.edges = set(edges)
        self.name = name
        self.adj: Dict[int, List[int]] = {i: [] for i in range(num_qubits)}
        for u, v in edges:
            self.adj[u].append(v)
            self.adj[v].append(u)

    def is_connected(self, u: int, v: int) -> bool:
        return (u, v) in self.edges or (v, u) in self.edges

    def shortest_path(self, start: int, target: int) -> List[int]:
        if start == target:
            return [start]
        queue = deque([(start, [start])])
        visited = {start}
        while queue:
            node, path = queue.popleft()
            for neighbor in self.adj[node]:
                if neighbor == target:
                    return path + [neighbor]
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, path + [neighbor]))
        return []

    @classmethod
    def linear(cls, n: int) -> DeviceTopology:
        edges = [(i, i + 1) for i in range(n - 1)]
        return cls(n, edges, name="linear")

    @classmethod
    def grid(cls, rows: int, cols: int) -> DeviceTopology:
        edges = []
        for r in range(rows):
            for c in range(cols):
                idx = r * cols + c
                if c + 1 < cols:
                    edges.append((idx, idx + 1))
                if r + 1 < rows:
                    edges.append((idx, idx + cols))
        return cls(rows * cols, edges, name=f"grid_{rows}x{cols}")

    @classmethod
    def all_to_all(cls, n: int) -> DeviceTopology:
        edges = [(i, j) for i in range(n) for j in range(i + 1, n)]
        return cls(n, edges, name="all_to_all")

    @classmethod
    def star(cls, n: int) -> DeviceTopology:
        """Star topology with qubit 0 at center and qubits 1..n-1 on periphery."""
        edges = [(0, i) for i in range(1, n)]
        return cls(n, edges, name=f"star_{n}")

    @classmethod
    def heavy_hex(cls, distance: int = 3) -> DeviceTopology:
        """
        Heavy-hex lattice topology (IBM Eagle / Heron architecture).
        Consists of hexagonal rings with bridge qubits on edges.
        """
        edges = []
        num_qubits = distance * distance * 3
        for r in range(distance):
            for c in range(distance):
                idx = (r * distance + c) * 3
                if idx + 1 < num_qubits:
                    edges.append((idx, idx + 1))
                if idx + 2 < num_qubits:
                    edges.append((idx + 1, idx + 2))
                if c + 1 < distance and idx + 3 < num_qubits:
                    edges.append((idx + 2, idx + 3))
                if r + 1 < distance and idx + distance * 3 < num_qubits:
                    edges.append((idx, idx + distance * 3))
        return cls(num_qubits, edges, name=f"heavy_hex_d{distance}")


class QubitMappingPass:
    def __init__(self, topology: DeviceTopology):
        self.topology = topology

    def run(self, circuit: CircuitIR) -> CircuitIR:
        if self.topology.name == "all_to_all":
            return circuit

        new_circuit = CircuitIR(name=f"{circuit.name}_routed_{self.topology.name}")
        new_circuit.qubit_regs = dict(circuit.qubit_regs)
        new_circuit.clbit_regs = dict(circuit.clbit_regs)

        # Mapping: logical qubit -> physical qubit
        # Initially identity mapping
        num_q = circuit.num_qubits
        logical_to_phys: Dict[int, int] = {i: i for i in range(num_q)}
        phys_to_logical: Dict[int, int] = {i: i for i in range(num_q)}

        wire_name = list(circuit.qubit_regs.keys())[0] if circuit.qubit_regs else "q"

        for op in circuit.ops:
            if not isinstance(op, GateOp) or len(op.qubits) < 2:
                # 1-qubit op or non-gate
                if isinstance(op, GateOp) and len(op.qubits) == 1:
                    log_idx = circuit.get_qubit_index(op.qubits[0])
                    phys_idx = logical_to_phys[log_idx]
                    mapped_op = GateOp(
                        name=op.name,
                        qubits=[QWire(wire_name, phys_idx)],
                        params=list(op.params),
                        matrix=op.matrix
                    )
                    new_circuit.add_op(mapped_op)
                else:
                    new_circuit.add_op(op)
                continue

            # 2-qubit gate
            log0 = circuit.get_qubit_index(op.qubits[0])
            log1 = circuit.get_qubit_index(op.qubits[1])
            phys0 = logical_to_phys[log0]
            phys1 = logical_to_phys[log1]

            if self.topology.is_connected(phys0, phys1):
                mapped_op = GateOp(
                    name=op.name,
                    qubits=[QWire(wire_name, phys0), QWire(wire_name, phys1)],
                    params=list(op.params),
                    matrix=op.matrix
                )
                new_circuit.add_op(mapped_op)
            else:
                # Find path on hardware coupling graph
                path = self.topology.shortest_path(phys0, phys1)
                # Route phys0 closer to phys1 along path using SWAPs
                for k in range(len(path) - 2):
                    u, v = path[k], path[k + 1]
                    swap_op = GateOp(
                        name="swap",
                        qubits=[QWire(wire_name, u), QWire(wire_name, v)]
                    )
                    new_circuit.add_op(swap_op)
                    # Update layout
                    l_u, l_v = phys_to_logical[u], phys_to_logical[v]
                    logical_to_phys[l_u], logical_to_phys[l_v] = v, u
                    phys_to_logical[u], phys_to_logical[v] = l_v, l_u

                cur_p0 = path[-2]
                cur_p1 = path[-1]
                mapped_op = GateOp(
                    name=op.name,
                    qubits=[QWire(wire_name, cur_p0), QWire(wire_name, cur_p1)],
                    params=list(op.params),
                    matrix=op.matrix
                )
                new_circuit.add_op(mapped_op)

        return new_circuit
