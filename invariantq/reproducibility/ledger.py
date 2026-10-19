"""
Experiment Tracking, Provenance, and Reproducibility Ledger.
Records environmental parameters, code commit, RNG seeds, compiler passes, and execution telemetry.
"""

from __future__ import annotations
import os
import sys
import time
import platform
import subprocess
import hashlib
import json
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, Optional

@dataclass
class ExperimentManifest:
    experiment_id: str
    timestamp: str
    git_commit: str
    git_branch: str
    python_version: str
    platform_info: str
    cpu_info: str
    compiler_opt_level: int
    backend: str
    master_seed: int
    circuit_name: str
    num_qubits: int
    gate_count: int
    shots: int
    execution_time_ms: float
    hash_digest: str = ""
    schema_version: str = "1.0"
    circuit_qasm: str = ""
    result: Dict[str, Any] = field(default_factory=dict)
    status: str = "completed"
    metadata: Dict[str, Any] = field(default_factory=dict)

class ReproducibilityLedger:
    def __init__(self, ledger_dir: str = ".invariantq_ledger"):
        self.ledger_dir = ledger_dir
        os.makedirs(self.ledger_dir, exist_ok=True)

    def record_experiment(
        self,
        experiment_id: str,
        circuit_name: str,
        num_qubits: int,
        gate_count: int,
        backend: str,
        compiler_opt_level: int,
        master_seed: int,
        shots: int,
        execution_time_ms: float,
        extra_metadata: Optional[Dict[str, Any]] = None,
        circuit_qasm: str = "",
        result: Optional[Dict[str, Any]] = None,
        status: str = "completed",
    ) -> ExperimentManifest:
        # Determine git commit
        git_commit = "unknown"
        git_branch = "unknown"
        try:
            git_commit = subprocess.check_output(
                ["git", "rev-parse", "HEAD"], stderr=subprocess.DEVNULL
            ).decode().strip()
            git_branch = subprocess.check_output(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"], stderr=subprocess.DEVNULL
            ).decode().strip()
        except Exception:
            pass

        manifest_data = {
            "experiment_id": experiment_id,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
            "git_commit": git_commit,
            "git_branch": git_branch,
            "python_version": sys.version.split()[0],
            "platform_info": platform.platform(),
            "cpu_info": platform.processor() or "x86_64",
            "compiler_opt_level": compiler_opt_level,
            "backend": backend,
            "master_seed": master_seed,
            "circuit_name": circuit_name,
            "num_qubits": num_qubits,
            "gate_count": gate_count,
            "shots": shots,
            "execution_time_ms": execution_time_ms,
            "schema_version": "1.0",
            "circuit_qasm": circuit_qasm,
            "result": result or {},
            "status": status,
            "metadata": extra_metadata or {},
        }

        # SHA256 digest
        digest_input = json.dumps(manifest_data, sort_keys=True).encode("utf-8")
        manifest_data["hash_digest"] = hashlib.sha256(digest_input).hexdigest()

        manifest = ExperimentManifest(**manifest_data)

        # Write to JSON ledger
        filepath = os.path.join(self.ledger_dir, f"{experiment_id}_{int(time.time())}.json")
        with open(filepath, "w") as f:
            json.dump(asdict(manifest), f, indent=2)

        return manifest

    @staticmethod
    def validate_manifest(manifest: Dict[str, Any]) -> None:
        """Validate the stable fields required for replay."""
        required = {
            "schema_version", "experiment_id", "backend", "master_seed",
            "shots", "circuit_qasm", "status",
        }
        missing = sorted(required.difference(manifest))
        if missing:
            raise ValueError(f"manifest is missing required fields: {', '.join(missing)}")
        if manifest["schema_version"] != "1.0":
            raise ValueError(f"unsupported experiment manifest schema: {manifest['schema_version']}")
        if not isinstance(manifest["circuit_qasm"], str) or not manifest["circuit_qasm"].strip():
            raise ValueError("manifest circuit_qasm must be a non-empty string")
        if isinstance(manifest["shots"], bool) or not isinstance(manifest["shots"], int) or manifest["shots"] <= 0:
            raise ValueError("manifest shots must be a positive integer")
        if isinstance(manifest["master_seed"], bool) or not isinstance(manifest["master_seed"], int) or manifest["master_seed"] < 0:
            raise ValueError("manifest master_seed must be a non-negative integer")
        if manifest["status"] not in {"completed", "failed", "cancelled"}:
            raise ValueError("manifest status must be completed, failed, or cancelled")

    def export_manifest(self, manifest: ExperimentManifest, path: str) -> str:
        """Write deterministic JSON and return its SHA-256 checksum."""
        payload = asdict(manifest)
        self.validate_manifest(payload)
        encoded = json.dumps(payload, sort_keys=True, indent=2).encode("utf-8")
        digest = hashlib.sha256(encoded).hexdigest()
        with open(path, "wb") as handle:
            handle.write(encoded)
        return digest

    @staticmethod
    def load_manifest(path: str) -> Dict[str, Any]:
        with open(path, encoding="utf-8") as handle:
            manifest = json.load(handle)
        if not isinstance(manifest, dict):
            raise ValueError("experiment manifest must contain a JSON object")
        ReproducibilityLedger.validate_manifest(manifest)
        return manifest

    @staticmethod
    def replay_manifest(manifest: Dict[str, Any]) -> Any:
        """Replay a stored circuit using the recorded backend and seed."""
        ReproducibilityLedger.validate_manifest(manifest)
        if manifest["status"] != "completed":
            raise ValueError("only completed manifests can be replayed")
        from ..language.qasm_parser import parse_iq_lang
        from ..simulator.adaptive import AdaptivePlannerSimulator
        from ..simulator.density_matrix import DensityMatrixSimulator
        from ..simulator.statevector import StateVectorSimulator
        from ..simulator.stabilizer import StabilizerSimulator
        from ..simulator.tensor_network import TensorNetworkSimulator

        backends = {
            "adaptive": AdaptivePlannerSimulator,
            "statevector": StateVectorSimulator,
            "density_matrix": DensityMatrixSimulator,
            "stabilizer": StabilizerSimulator,
            "tensor_network": TensorNetworkSimulator,
        }
        backend = manifest["backend"]
        if backend not in backends:
            raise ValueError(f"unsupported replay backend: {backend}")
        circuit = parse_iq_lang(manifest["circuit_qasm"])
        return backends[backend]().run(
            circuit, shots=manifest["shots"], seed=manifest["master_seed"]
        )
