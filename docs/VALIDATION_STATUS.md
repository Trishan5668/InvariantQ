# Validation status

Last audited: 2026-10-19 (Windows, Python 3.12, NumPy fallback; no native C++ shared library loaded).

## Reproduction

From a source checkout with the declared dependencies installed:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -u scripts\run_benchmarks.py
```

The audit baseline was **18 passed, 33 failed**. Every failure was caused by the bindings looking only for `libinvariantq.so`, which is not loadable on Windows. The current suite result is **51 passed**.

## Traceability

| Claim / component | Evidence | Status |
| --- | --- | --- |
| Portable statevector semantics | `invariantq/core/binding.py`; `tests/test_core_math.py`, `tests/test_statevector.py` | Verified |
| Density-matrix unitary and 1-qubit Kraus evolution | `binding.py`; `tests/test_statevector.py`, `tests/test_noise_cptp.py` | Verified |
| Clifford and MPS result agreement on tested small circuits | `tests/test_independent_reference.py`, `tests/test_verification_metamorphic.py` | Verified for tested inputs |
| Compiler transforms | `tests/test_compiler.py`, `tests/test_acceptance_criteria.py` | Verified for included finite/random fixtures; not a proof for all circuits |
| CPTP channel conditions | `tests/test_noise_cptp.py`, `tests/test_algorithms_and_channels.py` | Verified for implemented channel fixtures |
| Distributed scheduling and aggregation | `tests/test_noise_cptp.py`, `tests/test_acceptance_criteria.py` | Experimental: in-process worker model only |
| Native C++ acceleration / large stabilizer scale | `core/`, `invariantq/core/binding.py` | Blocked on this Windows environment: only a Linux `.so` build path is supplied |
| External Qiskit/Cirq/QuTiP differential testing | none | Missing (no independent external dependency was installed) |

## Mathematical and operational limits

- Global amplitudes use little-endian indexing (`q[k]` is global bit `k`); multi-qubit matrices retain listed-wire tensor order. Statevector result strings are formatted most-significant bit first. The stabilizer backend reports `q[0]` first for compatibility with its existing API.
- The portable statevector fallback limits allocations to 24 qubits; the portable density-matrix fallback limits them to 12 qubits. These are explicit correctness/resource boundaries, not performance claims.
- The portable `NativeMPS` and `NativeStabilizer` compatibility implementations use dense statevectors, so they do not provide the advertised polynomial/tableau or tensor-network scaling. They are suitable only within their stated fallback limits.
- `StateVectorSimulator` rejects non-finite or non-unitary gate matrices. Invalid operations are not renormalized into plausible results.
- Benchmark timings are machine- and run-dependent. The benchmark script records a provenance manifest but should not be interpreted as a cross-platform performance comparison.

## Acceptance gates

| Gate | Result | Evidence / limitation |
| --- | --- | --- |
| Build and installation | Partial | Python source workflow works; native Windows build/package path is not supplied |
| Core correctness | Verified | 51-test suite and analytic fixtures |
| Compiler correctness | Partial | Finite test coverage, no formal proof |
| Simulator correctness | Partial | Small-circuit tests pass; native/backends have stated fallback limits |
| Noise correctness | Verified for implemented 1/2-qubit fixtures | CPTP and analytic tests |
| Runtime reliability | Experimental | In-process scheduler tests only |
| Integration | Partial | CLI/tests exist; browser workflow not exercised in this audit |
| Performance evidence | Experimental | Repeatable local benchmark script, not comparative evidence |
| Security safeguards | Partial | Input/unitarity checks improved; no full security review |
| Research reproducibility | Partial | Seeds/tests/ledger exist; no external differential reference installed |
| Release readiness | Blocked | Native cross-platform packaging and independent validation remain outstanding |
