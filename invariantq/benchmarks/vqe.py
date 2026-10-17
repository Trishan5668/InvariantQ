"""
Variational Quantum Eigensolver (VQE) benchmark with Transverse Field Ising Model (TFIM) Hamiltonian.
"""

from __future__ import annotations
import math
from typing import List, Tuple, Dict, Any
import numpy as np
from scipy.optimize import minimize

from ..ir.qir import CircuitIR, GateOp, QWire
from ..simulator.statevector import StateVectorSimulator

class VQESolver:
    def __init__(self, num_qubits: int = 4, J: float = 1.0, h: float = 0.5, layers: int = 2):
        self.num_qubits = num_qubits
        self.J = J
        self.h = h
        self.layers = layers
        self.sim = StateVectorSimulator()

    def build_ansatz(self, params: np.ndarray) -> CircuitIR:
        circuit = CircuitIR(name=f"vqe_ansatz_{self.num_qubits}q")
        circuit.add_qubit_register("q", self.num_qubits)
        circuit.add_clbit_register("c", self.num_qubits)

        idx = 0
        for layer in range(self.layers):
            # Ry rotations
            for q in range(self.num_qubits):
                circuit.add_op(GateOp(name="ry", qubits=[QWire("q", q)], params=[float(params[idx])]))
                idx += 1
            # Entangling CZ/CX chain
            for q in range(self.num_qubits - 1):
                circuit.add_op(GateOp(name="cx", qubits=[QWire("q", q), QWire("q", q + 1)]))

        # Final Ry layer
        for q in range(self.num_qubits):
            circuit.add_op(GateOp(name="ry", qubits=[QWire("q", q)], params=[float(params[idx])]))
            idx += 1

        return circuit

    def energy(self, params: np.ndarray) -> float:
        circuit = self.build_ansatz(params)
        res = self.sim.run(circuit, shots=1024)
        sv = res.statevector

        # Calculate exact <psi|H|psi>
        # H = -J sum Z_i Z_{i+1} - h sum X_i
        e = 0.0
        for i in range(self.num_qubits - 1):
            exp_zz = self.sim.sv_sim if hasattr(self.sim, "sv_sim") else None
            # Compute Pauli ZZ
            val_zz = self._compute_pauli_exp(sv, [("Z", i), ("Z", i + 1)])
            e -= self.J * val_zz.real

        for i in range(self.num_qubits):
            val_x = self._compute_pauli_exp(sv, [("X", i)])
            e -= self.h * val_x.real

        return float(e)

    def _compute_pauli_exp(self, sv: np.ndarray, paulis: List[Tuple[str, int]]) -> complex:
        n = self.num_qubits
        dim = 1 << n
        target = np.copy(sv)

        for p_name, q in paulis:
            new_target = np.zeros(dim, dtype=np.complex128)
            for i in range(dim):
                bit = (i >> q) & 1
                if p_name == "Z":
                    new_target[i] = (-1.0 if bit == 1 else 1.0) * target[i]
                elif p_name == "X":
                    new_target[i ^ (1 << q)] = target[i]
            target = new_target

        return np.vdot(sv, target)

    def optimize(self, max_iter: int = 25) -> Dict[str, Any]:
        num_params = (self.layers + 1) * self.num_qubits
        init_params = np.random.default_rng(42).uniform(-np.pi, np.pi, num_params)

        opt_res = minimize(
            self.energy,
            init_params,
            method="COBYLA",
            options={"maxiter": max_iter, "disp": False}
        )

        return {
            "num_qubits": self.num_qubits,
            "ground_state_energy": float(opt_res.fun),
            "converged": bool(opt_res.success),
            "iterations": int(opt_res.nfev),
            "optimal_parameters": opt_res.x.tolist()
        }
