# Production blocker closure plan

| Blocker | Current gap | Planned closure | Validation |
|---|---|---|---|
| Runtime deadlines/cancellation/accounting | Simulators only validate static memory limits; no shared cancellation/deadline or aggregate reservations | Add a shared cooperative execution context and race-safe resource pool; propagate it through the Python statevector path and expose typed failures | Focused execution-context tests plus full pytest |
| Typed runtime-fault sandbox | Fault checks exist only as tester methods and non-unitary execution is not a typed experiment result | Add an opt-in, isolated sandbox API with typed scenario/report models and baseline/fault separation | Sandbox isolation/reproducibility tests |
| Native build/runtime | Native code and shell build exist, but no host artifact was built in this Windows session | Add explicit build documentation/CI jobs and preserve truthful unavailable status | Native build command where toolchain exists; CI evidence otherwise |
| Clean install/packaging | Source tests pass; clean wheel install has not been exercised | Add package build/install CI and package smoke test | `build`, isolated install, import/CLI checks |
| Security/dependency scanning | No security workflow or policy document | Add repeatable pip/npm audit, Bandit, and security policy workflow | Scanner command outputs, with findings recorded |
| Durable distributed recovery | Local process retries are tested; scheduler state is in-memory | Add optional durable job journal and restart recovery tests without claiming exactly-once execution | Multi-process/local journal tests; external network remains unverified |

This plan distinguishes locally verifiable closures from platform or
infrastructure boundaries that require CI runners or external deployment.
