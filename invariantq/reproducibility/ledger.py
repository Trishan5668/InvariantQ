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
        extra_metadata: Optional[Dict[str, Any]] = None
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
