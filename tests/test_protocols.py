import numpy as np

from invariantq.protocols import (
    entanglement_explorer,
    quantum_teleportation,
    superdense_coding,
)


def test_entanglement_entropy_distinguishes_product_and_bell_states():
    assert entanglement_explorer("product")["von_neumann_entropy_bits"] == 0.0
    assert np.isclose(
        entanglement_explorer("bell")["von_neumann_entropy_bits"], 1.0
    )
    assert np.isclose(
        entanglement_explorer("bell")["reduced_eigenvalues"][0], 0.5
    )


def test_superdense_coding_recovers_every_message():
    result = superdense_coding(shots=8, seed=7)
    assert all(message_result["correct"] for message_result in result["messages"].values())
    assert all(
        message_result["success_probability"] == 1.0
        for message_result in result["messages"].values()
    )


def test_teleportation_preserves_complex_phase():
    result = quantum_teleportation(
        alpha=1 / np.sqrt(2), beta=1j / np.sqrt(2), shots=16, seed=9
    )
    assert result["verified"] is True
    assert result["minimum_fidelity"] > 1 - 1e-10
