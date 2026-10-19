import json

import pytest

from invariantq.reproducibility.ledger import ReproducibilityLedger


def test_manifest_export_validation_and_replay(tmp_path):
    ledger = ReproducibilityLedger(str(tmp_path / "ledger"))
    manifest = ledger.record_experiment(
        experiment_id="bell",
        circuit_name="bell",
        num_qubits=2,
        gate_count=2,
        backend="statevector",
        compiler_opt_level=0,
        master_seed=11,
        shots=8,
        execution_time_ms=0.0,
        circuit_qasm="qubit q[2]; h q[0]; cx q[0], q[1];",
    )
    path = tmp_path / "bell.json"
    digest = ledger.export_manifest(manifest, str(path))
    loaded = ledger.load_manifest(str(path))
    assert len(digest) == 64
    replayed = ledger.replay_manifest(loaded)
    assert sum(replayed.counts.values()) == 8


def test_manifest_rejects_unknown_schema_and_invalid_sampling(tmp_path):
    path = tmp_path / "invalid.json"
    path.write_text(json.dumps({
        "schema_version": "9.0",
        "experiment_id": "bad",
        "backend": "statevector",
        "master_seed": 0,
        "shots": 1,
        "circuit_qasm": "qubit q[1];",
        "status": "completed",
    }))
    with pytest.raises(ValueError, match="unsupported experiment manifest schema"):
        ReproducibilityLedger.load_manifest(str(path))
