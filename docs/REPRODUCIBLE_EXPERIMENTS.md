# Reproducible experiments

## Install and run

```powershell
.\.venv\Scripts\python.exe -m pytest -q
Set-Location web
npm run build
```

The native C++ library is optional. When it is unavailable, runtime metadata
reports the portable implementation and does not claim native execution.

## Manifest lifecycle

`ReproducibilityLedger.record_experiment` stores the circuit, backend, seed,
shot count, environment, git revision, result metadata, status, and schema
version. `export_manifest` writes deterministic JSON; `load_manifest` validates
it; `replay_manifest` reruns completed IQ-Lang circuits with the recorded
backend and seed.

```python
from invariantq.reproducibility.ledger import ReproducibilityLedger

ledger = ReproducibilityLedger(".invariantq_ledger")
manifest = ledger.record_experiment(
    experiment_id="bell-001",
    circuit_name="bell",
    num_qubits=2,
    gate_count=2,
    backend="statevector",
    compiler_opt_level=0,
    master_seed=42,
    shots=128,
    execution_time_ms=0.0,
    circuit_qasm="qubit q[2]; h q[0]; cx q[0], q[1];",
)
ledger.export_manifest(manifest, "bell-001.json")
replayed = ledger.replay_manifest(ledger.load_manifest("bell-001.json"))
```

Replay is deterministic for the same implementation and environment. It is
not a promise of bit-for-bit equality across hardware, library versions,
parallel execution orders, or different native builds.

## Integrity and limitations

Manifests reject unsupported schema versions, missing circuit data, invalid
seeds/shots, and non-terminal statuses. Do not place credentials or secrets in
metadata. Distributed and fault-injected executions must record their actual
status rather than converting failures into successful scientific results.
