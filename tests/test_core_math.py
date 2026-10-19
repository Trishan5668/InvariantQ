"""
Test Stage 1: Core Mathematics, Unitary Evolution, Entanglement, and Entropy.
"""

import math
import numpy as np
import pytest
from invariantq.core.binding import NativeStateVector, NativeDensityMatrix, NativeStabilizer, NativeMPS

def test_single_qubit_gates():
    sv = NativeStateVector(1)
    H = np.array([[1, 1], [1, -1]], dtype=np.complex128) / np.sqrt(2)
    sv.apply_1q(0, H)
    amps = sv.get_amplitudes()
    assert np.isclose(amps[0], 1.0 / np.sqrt(2))
    assert np.isclose(amps[1], 1.0 / np.sqrt(2))

    X = np.array([[0, 1], [1, 0]], dtype=np.complex128)
    sv.apply_1q(0, X)
    amps_x = sv.get_amplitudes()
    assert np.isclose(amps_x[0], 1.0 / np.sqrt(2))
    assert np.isclose(amps_x[1], 1.0 / np.sqrt(2))

def test_bell_state_entanglement():
    sv = NativeStateVector(2)
    H = np.array([[1, 1], [1, -1]], dtype=np.complex128) / np.sqrt(2)
    CX = np.array([[1,0,0,0],[0,1,0,0],[0,0,0,1],[0,0,1,0]], dtype=np.complex128)

    sv.apply_1q(0, H)
    sv.apply_2q(0, 1, CX)

    # Entanglement entropy of maximally entangled Bell state must be exactly 1.0
    entropy = sv.von_neumann_entropy([0])
    assert np.isclose(entropy, 1.0, atol=1e-3)

def test_product_state_zero_entropy():
    sv = NativeStateVector(2)
    H = np.array([[1, 1], [1, -1]], dtype=np.complex128) / np.sqrt(2)
    sv.apply_1q(0, H)
    sv.apply_1q(1, H)
    # Product state |+>|+> has zero entanglement
    entropy = sv.von_neumann_entropy([0])
    assert np.isclose(entropy, 0.0, atol=1e-5)

def test_pauli_expectation_values():
    sv = NativeStateVector(1)
    # State |0>: <Z> = 1, <X> = 0
    exp_z = sv.expectation_value_pauli("Z", [0])
    assert np.isclose(exp_z.real, 1.0)
    assert np.isclose(exp_z.imag, 0.0)

    H = np.array([[1, 1], [1, -1]], dtype=np.complex128) / np.sqrt(2)
    sv.apply_1q(0, H)
    # State |+>: <X> = 1, <Z> = 0
    exp_x = sv.expectation_value_pauli("X", [0])
    assert np.isclose(exp_x.real, 1.0)
    assert np.isclose(exp_x.imag, 0.0)

def test_measurement_collapse():
    sv = NativeStateVector(1)
    H = np.array([[1, 1], [1, -1]], dtype=np.complex128) / np.sqrt(2)
    sv.apply_1q(0, H)

    # Force outcome 0
    outcome = sv.measure(0, 0.1) # rand_val < 0.5 -> 0
    assert outcome == 0
    amps = sv.get_amplitudes()
    assert np.isclose(amps[0], 1.0)
    assert np.isclose(amps[1], 0.0)


def test_fallback_stabilizer_and_mps_are_not_dense_statevectors():
    from invariantq.core import binding

    if binding.HAS_NATIVE_CORE:
        pytest.skip("portable fallback implementation is inactive when the native core is loaded")

    assert not issubclass(binding.NativeStabilizer, binding.NativeStateVector)
    assert not issubclass(binding.NativeMPS, binding.NativeStateVector)

    stabilizer = binding.NativeStabilizer(3)
    assert stabilizer._x.dtype == np.uint8
    assert stabilizer._z.dtype == np.uint8
    assert stabilizer._r.dtype == np.uint8
    assert stabilizer.tableau_memory_bytes == stabilizer._x.nbytes + stabilizer._z.nbytes + stabilizer._r.nbytes

    mps = binding.NativeMPS(3, max_bond_dim=2)
    assert all(tensor.ndim == 3 for tensor in mps.site_tensors)
    assert mps.memory_bytes == sum(tensor.nbytes for tensor in mps.site_tensors)
    assert mps.is_approximate is False
    with pytest.raises(ValueError, match="limited to"):
        binding.NativeMPS(21).to_statevector()


def test_non_unitary_execution_isolated_from_safe_statevector():
    from invariantq.simulator.statevector import NoisyStatevectorSimulator
    from invariantq.ir.qir import CircuitIR, GateOp, QWire

    circuit = CircuitIR("non_unitary")
    circuit.add_qubit_register("q", 1)
    circuit.add_op(
        GateOp(
            name="broken",
            qubits=[QWire("q", 0)],
            matrix=np.array([[2.0, 0.0], [0.0, 1.0]], dtype=np.complex128),
        )
    )

    with pytest.raises(ValueError, match="finite unitary"):
        from invariantq.simulator.statevector import StateVectorSimulator
        StateVectorSimulator().run(circuit, shots=4)

    result = NoisyStatevectorSimulator().run(circuit, shots=4, seed=1)
    assert result.metadata["allow_non_unitary"] is True
    assert result.metadata["state_norm"] == pytest.approx(4.0)
