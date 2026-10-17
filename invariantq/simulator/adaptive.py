"""
Adaptive Simulation Planner.
Dynamically routes circuits to the optimal simulation formalism based on circuit invariants,
qubit count, gate classifications, noise specifications, and memory budgets.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any, Tuple
import numpy as np

from .base import BaseSimulator, ExecutionResult
from .statevector import StateVectorSimulator
from .density_matrix import DensityMatrixSimulator
from .tensor_network import TensorNetworkSimulator
from .stabilizer import StabilizerSimulator
from ..ir.qir import CircuitIR, GateOp, NoiseOp

@dataclass
class PlannerDecision:
    backend_name: str
    reason: str
    estimated_memory_bytes: int
    is_exact: bool

class AdaptivePlannerSimulator(BaseSimulator):
    def __init__(self, max_memory_bytes: int = 16 * (1024**3)): # 16 GB default RAM budget
        super().__init__(name="adaptive")
        self.max_memory_bytes = max_memory_bytes
        self.sv_sim = StateVectorSimulator()
        self.dm_sim = DensityMatrixSimulator()
        self.mps_sim = TensorNetworkSimulator()
        self.stab_sim = StabilizerSimulator()

    def plan(self, circuit: CircuitIR) -> PlannerDecision:
        n = circuit.num_qubits
        has_noise = any(isinstance(op, NoiseOp) for op in circuit.ops)
        is_clifford = circuit.is_all_clifford()

        # Rule 1: Noisy circuit
        if has_noise:
            dm_mem = (1 << (2 * n)) * 16
            if n <= 10 and dm_mem <= self.max_memory_bytes:
                return PlannerDecision(
                    backend_name="density_matrix",
                    reason=f"Open quantum system with noise channels and {n} qubits (fits in {dm_mem / (1024**2):.1f} MB)",
                    estimated_memory_bytes=dm_mem,
                    is_exact=True
                )
            else:
                # Use Monte Carlo trajectory simulation with StateVector
                sv_mem = (1 << n) * 16
                return PlannerDecision(
                    backend_name="statevector",
                    reason=f"Noisy circuit with {n} qubits routed to StateVector trajectory backend to prevent density-matrix memory explosion",
                    estimated_memory_bytes=sv_mem,
                    is_exact=False
                )

        # Rule 2: Strictly Clifford circuit
        if is_clifford:
            stab_mem = (2 * n) * (2 * n + 1)
            return PlannerDecision(
                backend_name="stabilizer",
                reason=f"All gates belong to the Clifford group. Simulating in polynomial time via Gottesman-Knill stabilizer tableau",
                estimated_memory_bytes=stab_mem,
                is_exact=True
            )

        # Rule 3: Memory calculation for StateVector
        sv_mem = (1 << n) * 16
        if sv_mem <= self.max_memory_bytes and n <= 28:
            return PlannerDecision(
                backend_name="statevector",
                reason=f"Exact statevector simulation fits within memory budget ({sv_mem / (1024**2):.2f} MB <= {self.max_memory_bytes / (1024**3):.1f} GB)",
                estimated_memory_bytes=sv_mem,
                is_exact=True
            )

        # Rule 4: Large qubit count (> 28) or exceeding memory budget -> MPS Tensor Network
        mps_mem = n * 2 * (64**2) * 16
        return PlannerDecision(
            backend_name="tensor_network",
            reason=f"Circuit with {n} qubits exceeds statevector memory limit. Routing to Matrix Product State (MPS) tensor network with bond dimension 64",
            estimated_memory_bytes=mps_mem,
            is_exact=False
        )

    def run(self, circuit: CircuitIR, shots: int = 1024, seed: int = 42) -> ExecutionResult:
        decision = self.plan(circuit)

        if decision.backend_name == "stabilizer":
            res = self.stab_sim.run(circuit, shots=shots, seed=seed)
        elif decision.backend_name == "density_matrix":
            res = self.dm_sim.run(circuit, shots=shots, seed=seed)
        elif decision.backend_name == "tensor_network":
            res = self.mps_sim.run(circuit, shots=shots, seed=seed)
        else:
            res = self.sv_sim.run(circuit, shots=shots, seed=seed)

        res.metadata["planner_decision"] = decision.reason
        res.metadata["estimated_memory_bytes"] = decision.estimated_memory_bytes
        res.metadata["is_exact"] = decision.is_exact
        return res
