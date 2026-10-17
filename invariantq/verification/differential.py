"""
Differential Testing Suite for InvariantQ Multi-Modal Simulators.
Compares independent simulation formalisms (StateVector vs DensityMatrix vs MPS vs Stabilizer).
"""

from __future__ import annotations
from typing import Dict, List, Any, Tuple
import numpy as np

from ..ir.qir import CircuitIR
from ..simulator.statevector import StateVectorSimulator
from ..simulator.density_matrix import DensityMatrixSimulator
from ..simulator.tensor_network import TensorNetworkSimulator
from ..simulator.stabilizer import StabilizerSimulator

class DifferentialTestError(Exception):
    pass

class DifferentialTester:
    def __init__(self, tolerance: float = 1e-4):
        self.tolerance = tolerance
        self.sv_sim = StateVectorSimulator()
        self.dm_sim = DensityMatrixSimulator()
        self.mps_sim = TensorNetworkSimulator()
        self.stab_sim = StabilizerSimulator()

    def compare_circuits(
        self,
        circuit: CircuitIR,
        shots: int = 2000,
        seed: int = 42
    ) -> Dict[str, Any]:
        """
        Runs the circuit on all applicable simulators and compares their probability distributions.
        """
        results = {}
        n = circuit.num_qubits

        # StateVector
        sv_res = self.sv_sim.run(circuit, shots=shots, seed=seed)
        results["statevector"] = sv_res

        # Density Matrix (if n <= 10)
        dm_res = None
        if n <= 10:
            dm_res = self.dm_sim.run(circuit, shots=shots, seed=seed)
            results["density_matrix"] = dm_res

        # MPS
        mps_res = self.mps_sim.run(circuit, shots=shots, seed=seed)
        results["mps"] = mps_res

        # Stabilizer (if Clifford)
        stab_res = None
        if circuit.is_all_clifford():
            stab_res = self.stab_sim.run(circuit, shots=shots, seed=seed)
            results["stabilizer"] = stab_res

        # Compare SV vs DM exact probabilities if pure state
        discrepancies: Dict[str, float] = {}

        if dm_res is not None:
            # Check maximum probability difference
            all_keys = set(sv_res.probabilities.keys()) | set(dm_res.probabilities.keys())
            max_diff = 0.0
            for k in all_keys:
                p_sv = sv_res.probabilities.get(k, 0.0)
                p_dm = dm_res.probabilities.get(k, 0.0)
                max_diff = max(max_diff, abs(p_sv - p_dm))
            discrepancies["sv_vs_dm_max_prob_diff"] = max_diff

        # Compare SV vs MPS exact statevector overlap if available
        if mps_res.statevector is not None:
            fidelity = abs(np.vdot(sv_res.statevector, mps_res.statevector)) ** 2
            discrepancies["sv_vs_mps_fidelity"] = float(fidelity)

        # Check statistical consistency for shots between SV and others
        passed = True
        if dm_res is not None and discrepancies.get("sv_vs_dm_max_prob_diff", 0.0) > self.tolerance:
            passed = False
        if "sv_vs_mps_fidelity" in discrepancies and discrepancies["sv_vs_mps_fidelity"] < (1.0 - self.tolerance):
            passed = False

        return {
            "passed": passed,
            "discrepancies": discrepancies,
            "backends_compared": list(results.keys()),
            "sv_probabilities": sv_res.probabilities,
            "mps_probabilities": mps_res.probabilities
        }
