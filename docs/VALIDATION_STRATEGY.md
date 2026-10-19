# Validation strategy

## Independent correctness

Small unitary circuits are checked against the independent NumPy tensor
contraction engine in `invariantq.verification.independent_reference`. Pure
state comparisons use fidelity or global-phase-aware comparisons; density
matrices use matrix norms. Optional Qiskit tests are skipped when Qiskit is not
installed and are never required for package import.

Analytical cases include identity/inverse behavior, Bell/GHZ states, product
states, known Kraus completeness, and teleportation/superdense protocol
correctness. Sampling tests compare distributions with fixed seeds and do not
require identical random draws across implementations.

## Numerical policy

- Unitary validation uses absolute and relative tolerance `1e-10`.
- CPTP and Choi checks use the validator tolerance (`1e-10` by default).
- MPS fidelity checks use `1e-5` where truncation can affect amplitudes.
- Entropy tests use tolerances appropriate to the logarithm calculation.
- Invalid, non-finite, dimension-mismatched, and over-budget inputs fail
  explicitly; no silent projection or repair is performed.

## Fault and boundary coverage

Regression tests exercise invalid gates, malformed Kraus lists, zero shots,
negative seeds, resource limits, fallback provenance, and isolated
non-unitary trajectories. The fault-injection suite checks that representative
corrupted gates and broken channels are detected.

The test suite does not claim to kill every possible mutation. Representative
mutations and their observed results are recorded in the fault telemetry
returned by `FaultInjectionTester`.
