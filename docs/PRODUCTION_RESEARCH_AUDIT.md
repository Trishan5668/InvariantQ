# Production/research audit baseline

## Baseline evidence

The audit was performed against the current checkout on Windows, Python 3.12,
with the portable NumPy path active (no compatible native shared library was
loaded).

| Area | Confirmed implementation | Main risk/gap | Existing evidence |
|---|---|---|---|
| Statevector | Dense exact statevector; strict unitary validation; isolated opt-in non-unitary path | Exponential memory; no generic mid-circuit conditional execution | `tests/test_statevector.py`, `tests/test_core_math.py` |
| Density matrix | Dense Kraus evolution and trace/purity diagnostics | Exponential-squared memory; limited operation/noise combinations | `tests/test_statevector.py`, `tests/test_noise_cptp.py` |
| Stabilizer | Genuine portable Aaronson-Gottesman tableau and optional native binding | Clifford-only; native path needs platform build validation | `tests/test_statevector.py`, `tests/test_core_math.py` |
| MPS | Genuine rank-three tensor chain, SVD truncation, bond diagnostics | Approximation/resource behavior needs broader scaling measurements | `tests/test_core_math.py`, `tests/test_independent_reference.py` |
| Capabilities/planner | Runtime capability descriptions, fail-closed scalable-backend selection, memory preflight | Capability conformance is not yet generated from one registry | `tests/test_core_diagnostics.py` |
| Noise | Kraus channels, CPTP/Choi validation, density-matrix application | Readout errors are a separate classical layer; no universal channel contract | `tests/test_noise_cptp.py` |
| Fault sandbox | Explicit noisy statevector path and fault telemetry | Runtime-fault taxonomy and cancellation are not a complete public API | `tests/test_core_diagnostics.py` |
| Verification | Independent NumPy tensor contraction; optional Qiskit differential tests; metamorphic tests | Qiskit is optional and not part of the core install | `tests/test_independent_reference.py`, `tests/test_qiskit_differential.py` |
| Distributed execution | Separate worker/process paths, retries, duplicate-result handling, scheduler tests | External network deployment and durable restart recovery are not validated | `tests/test_distributed_scheduler.py` |
| Reproducibility | Ledger with environment, git, seed, checksum, circuit, result, and replay fields | Cross-version/hardware bit-for-bit equivalence is not promised | `invariantq/reproducibility/ledger.py` |
| Release engineering | setuptools install metadata, frontend Vite build, runnable pytest suite | CI workflow and clean-install evidence were missing | `setup.py`, build command, test suite |

## Implementation plan and status

1. **Integrity foundations:** runtime provenance, fail-closed scalable
   selection, overflow-safe memory estimates, and malformed-Kraus rejection —
   implemented and regression tested.
2. **Independent validation:** retain the independent NumPy reference and
   optional Qiskit adapter; add analytical/property coverage incrementally.
3. **Research reproducibility:** version and validate manifests, export stable
   JSON, and replay completed circuits.
4. **Release discipline:** add CI for Python tests and the frontend build,
   and document optional native/Qiskit boundaries.
5. **Distributed boundary:** document tested local process guarantees separately
   from unvalidated external network deployment.

This is an evidence baseline, not a production-readiness claim.
