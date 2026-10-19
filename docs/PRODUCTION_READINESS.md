# Production readiness evidence

This document reports observed evidence only. InvariantQ is **not** declared
production–research grade across all seven workstreams.

| Requirement | Implementation location | Validation command | Observed result | Evidence | Status | Remaining limitations |
|---|---|---|---|---|---|---|
| Independent reference validation | `invariantq/verification/independent_reference.py` | `python -m pytest -q tests/test_independent_reference.py` | Passed in baseline suite | `tests/test_independent_reference.py` | Implemented | Optional external reference coverage depends on Qiskit |
| Truthful scalable backends | `simulator/capabilities.py`, `adaptive.py`, `binding.py` | `python -m pytest -q tests/test_statevector.py tests/test_core_math.py` | Passed | backend metadata and fallback tests | Implemented | Native C++ builds not validated on this Windows checkout |
| Physical channel validation | `noise/cptp_validator.py` | `python -m pytest -q tests/test_noise_cptp.py` | Passed | CPTP/channel tests | Implemented | Channel support remains backend-specific |
| Resource preflight | `simulator/base.py`, statevector/density/MPS simulators | `python -m pytest -q tests/test_core_diagnostics.py` | Passed | budget rejection tests | Implemented | Runtime deadline/cancellation is not complete |
| Reproducible manifests | `reproducibility/ledger.py` | `python -m pytest -q tests/test_reproducibility.py` | Added and validated | manifest regression tests | Implemented | Cross-platform binary reproducibility not promised |
| Distributed recovery | `distributed/scheduler.py` | `python -m pytest -q tests/test_distributed_scheduler.py` | Passed local process/in-process tests | scheduler tests | Partially implemented | External network and durable restart recovery unvalidated |
| CI and clean install | `setup.py`, `.github/workflows/ci.yml` | CI workflow / local commands | Local tests/build pass | workflow and build logs | Partially implemented | Native matrix and clean isolated install remain to be exercised |
| Frontend production build | `web/` | `Set-Location web; npm run build` | Passed | Vite build output | Implemented | Browser E2E is not part of this evidence |
| Cooperative deadline/cancellation | `invariantq/execution.py`, `simulator/statevector.py` | `python -m pytest -q tests/test_execution_controls.py` | 3 passed | execution-control regression tests | Partially implemented | Native work and vectorized sampling are not forcibly interruptible |
| Typed runtime fault sandbox | `invariantq/faults.py` | `python -m pytest -q tests/test_execution_controls.py` | 3 passed | opt-in isolation/reproducibility tests | Partially implemented | Recovery and distributed fault stages remain separate concerns |
| Clean wheel install | `setup.py`, CI package job | `python setup.py bdist_wheel` | Wheel built; dependency smoke was blocked by the temporary environment | package artifact and CI config | Partially implemented | Full isolated import needs a clean dependency environment |
| Security scanning | `.github/workflows/security.yml`, `docs/SECURITY.md` | `npm audit --audit-level=high` | 0 frontend vulnerabilities; Python scanners unavailable locally | workflow and audit output | Partially implemented | pip-audit/Bandit not installed/executed locally |

## Current conclusion

The repository has a validated local research scope with truthful portable
backend reporting, cooperative Python execution controls, and opt-in fault
experiments. It is not yet evidence-supported for all-platform native
deployment, external distributed deployment, durable restart recovery,
forceful interruption of native work, or production operational SLAs.
