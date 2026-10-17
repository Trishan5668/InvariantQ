"""
Gottesman-Knill Clifford Stabilizer Simulator backend.
Simulates Clifford circuits in polynomial time (O(n^2) gate, O(n^3) measurement).
"""

from __future__ import annotations
import time
from typing import Dict, List, Optional
import numpy as np

from .base import BaseSimulator, ExecutionResult
from ..ir.qir import CircuitIR, GateOp, MeasureOp, ResetOp
from ..core.binding import NativeStabilizer

class StabilizerSimulator(BaseSimulator):
    def __init__(self):
        super().__init__(name="stabilizer")

    def run(self, circuit: CircuitIR, shots: int = 1024, seed: int = 42) -> ExecutionResult:
        t0 = time.perf_counter()
        n = circuit.num_qubits

        # Check if circuit is strictly Clifford
        for op in circuit.ops:
            if isinstance(op, GateOp) and not op.is_clifford():
                raise ValueError(
                    f"Gate '{op.name}' is non-Clifford. StabilizerSimulator only supports Clifford circuits."
                )

        rng = np.random.default_rng(seed)
        counts: Dict[str, int] = {}

        # Memory used: 2n * (2n+1) bytes for tableau
        mem_bytes = (2 * n) * (2 * n + 1)

        # Run multiple shots with measurement collapse
        for s in range(shots):
            stab = NativeStabilizer(n)
            shot_bits: Dict[int, int] = {}

            for op in circuit.ops:
                if isinstance(op, GateOp):
                    qubits = [circuit.get_qubit_index(q) for q in op.qubits]
                    gname = op.name.lower()
                    if gname == "h":
                        stab.h(qubits[0])
                    elif gname == "s":
                        stab.s(qubits[0])
                    elif gname == "sdg":
                        stab.sdg(qubits[0])
                    elif gname in ("cx", "cnot"):
                        stab.cnot(qubits[0], qubits[1])
                    elif gname == "cz":
                        stab.cz(qubits[0], qubits[1])
                    elif gname == "swap":
                        stab.swap(qubits[0], qubits[1])
                    elif gname == "x":
                        stab.x(qubits[0])
                    elif gname == "y":
                        stab.y(qubits[0])
                    elif gname == "z":
                        stab.z(qubits[0])

                elif isinstance(op, MeasureOp):
                    q_idx = circuit.get_qubit_index(op.qubit)
                    r_val = rng.random()
                    outcome = stab.measure(q_idx, r_val)
                    shot_bits[q_idx] = outcome

            # If no explicit measurements in circuit, measure all qubits
            if not shot_bits:
                for q_idx in range(n):
                    r_val = rng.random()
                    shot_bits[q_idx] = stab.measure(q_idx, r_val)

            # Format bitstring
            bitstr = "".join(str(shot_bits.get(i, 0)) for i in range(n))
            counts[bitstr] = counts.get(bitstr, 0) + 1

        probs: Dict[str, float] = {k: v / shots for k, v in counts.items()}

        t1 = time.perf_counter()
        exec_ms = (t1 - t0) * 1000.0

        # Extract final tableau representation
        stab_repr = ""
        try:
            stab_final = NativeStabilizer(n)
            for op in circuit.ops:
                if isinstance(op, GateOp):
                    qubits = [circuit.get_qubit_index(q) for q in op.qubits]
                    gname = op.name.lower()
                    if gname == "h": stab_final.h(qubits[0])
                    elif gname == "s": stab_final.s(qubits[0])
                    elif gname == "sdg": stab_final.sdg(qubits[0])
                    elif gname in ("cx", "cnot"): stab_final.cnot(qubits[0], qubits[1])
                    elif gname == "cz": stab_final.cz(qubits[0], qubits[1])
                    elif gname == "swap": stab_final.swap(qubits[0], qubits[1])
                    elif gname == "x": stab_final.x(qubits[0])
                    elif gname == "y": stab_final.y(qubits[0])
                    elif gname == "z": stab_final.z(qubits[0])
            stab_repr = stab_final.to_string()
        except Exception:
            pass

        return ExecutionResult(
            counts=counts,
            probabilities=probs,
            execution_time_ms=exec_ms,
            backend_used="stabilizer",
            memory_used_bytes=mem_bytes,
            shots=shots,
            metadata={"num_qubits": n, "tableau": stab_repr}
        )
