"""
Adaptive Simulation Planner.
Dynamically routes circuits to the optimal simulation formalism based on circuit invariants,
qubit count, gate classifications, noise specifications, and memory budgets.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any, Tuple, Optional
import numpy as np

from .base import BaseSimulator, ExecutionResult
from .statevector import StateVectorSimulator
from .density_matrix import DensityMatrixSimulator
from .tensor_network import TensorNetworkSimulator
from .stabilizer import StabilizerSimulator
from .capabilities import backend_capabilities, compatibility_reason
from ..ir.qir import CircuitIR, GateOp, NoiseOp

@dataclass
class PlannerDecision:
    backend_name: str
    reason: str
    estimated_memory_bytes: int
    is_exact: bool
    capability: Optional[Dict[str, Any]] = None

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
        capabilities = backend_capabilities()

        def decision(name: str, reason: str, memory: int, exact: bool) -> PlannerDecision:
            capability = capabilities[name]
            incompatible = compatibility_reason(circuit, capability)
            if incompatible:
                raise ValueError(f"Cannot select {name}: {incompatible}")
            return PlannerDecision(name, reason, memory, exact, capability.to_dict())

        # Rule 1: Noisy circuit
        if has_noise:
            dm_mem = (1 << (2 * n)) * 16
            if dm_mem > self.max_memory_bytes:
                raise MemoryError(
                    f"No compatible exact noisy backend: density matrix requires {dm_mem} bytes, "
                    f"above planner limit {self.max_memory_bytes}; trajectory simulation is not implemented."
                )
            return decision(
                "density_matrix",
                f"Open quantum system with {n} qubits; density-matrix estimate {dm_mem / (1024**2):.1f} MB",
                dm_mem,
                True,
            )

        # Rule 2: Strictly Clifford circuit
        if is_clifford:
            stab_mem = (2 * n) * (2 * n + 1)
            return decision(
                "stabilizer",
                "All operations are Clifford; selecting the declared stabilizer implementation.",
                stab_mem,
                capabilities["stabilizer"].exact,
            )

        # Rule 3: Memory calculation for StateVector
        sv_mem = (1 << n) * 16
        if sv_mem <= self.max_memory_bytes and compatibility_reason(circuit, capabilities["statevector"]) is None:
            return decision(
                "statevector",
                f"Exact statevector estimate {sv_mem / (1024**2):.2f} MB fits the configured budget.",
                sv_mem,
                True,
            )

        # Rule 4: Large qubit count (> 28) or exceeding memory budget -> MPS Tensor Network
        mps_mem = n * 2 * (64**2) * 16
        return decision(
            "tensor_network",
            "Statevector path is infeasible; selecting an MPS representation with configured bond limit.",
            mps_mem,
            False,
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
        res.metadata["backend_capability"] = decision.capability
        return res
