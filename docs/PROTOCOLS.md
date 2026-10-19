# Quantum information protocols

The protocol service exposes three real simulator-backed demonstrations:

- `POST /api/protocols/entanglement` with `{"state":"product|bell|ghz"}`.
  It returns the reduced density matrix, eigenvalues, state probabilities, and
  von Neumann entropy in bits for qubit 0. The entropy interpretation is
  explicitly for the returned pure states and selected bipartition; it is not a
  general mixed-state entanglement witness.
- `POST /api/protocols/superdense` with optional positive integer `shots` and
  non-negative `seed`. Every two-bit message is encoded into a Bell pair,
  decoded by Bob, and measured. The response contains measured counts and
  success probabilities for all four messages.
- `POST /api/protocols/teleportation` with optional complex amplitudes encoded
  as `[real, imaginary]` pairs (`alpha`, `beta`), positive `shots`, and
  non-negative `seed`. The input is normalized by the service. The Bell-basis
  measurements and conditional X/Z corrections are executed on the
  statevector, and the response reports per-shot and aggregate fidelity.

These endpoints use explicit protocol orchestration because the generic
IQ-Lang statevector execution path currently parses measurement and conditional
qIR operations but does not yet execute mid-circuit classical feed-forward.
They do not fabricate decoded bits or teleportation results.
