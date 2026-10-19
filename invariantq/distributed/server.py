"""
InvariantQ Research-Grade REST and Static Web Server.
Binds to 0.0.0.0, provides full JSON API for compilation, multi-modal simulation,
distributed job scheduling, CPTP validation, and performance benchmarks.
"""

from __future__ import annotations
import json
import logging
import time
import os
import sys
from pathlib import Path
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from typing import Dict, Any

from ..language.qasm_parser import parse_iq_lang
from ..compiler.optimizer import Compiler
from ..compiler.mapping import DeviceTopology
from ..simulator.statevector import StateVectorSimulator
from ..simulator.density_matrix import DensityMatrixSimulator
from ..simulator.stabilizer import StabilizerSimulator
from ..simulator.tensor_network import TensorNetworkSimulator
from ..simulator.adaptive import AdaptivePlannerSimulator
from ..noise.channels import build_kraus_channel
from ..noise.cptp_validator import validate_cptp
from ..distributed.scheduler import DistributedScheduler
from ..verification.differential import DifferentialTester
from ..verification.metamorphic import MetamorphicTester
from ..verification.fault_injection import FaultInjectionTester
from ..benchmarks.runner import BenchmarkRunner

logger = logging.getLogger(__name__)

class InvariantQServerHandler(SimpleHTTPRequestHandler):
    scheduler = DistributedScheduler(num_workers=4)
    runner = BenchmarkRunner()

    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        try:
            if self.path == "/api/health":
                self._send_json({"status": "ok", "platform": "InvariantQ",
                                 "version": "1.0.0", "workers": len(self.scheduler.workers)})
                return
            if self.path == "/api/cluster":
                self._send_json({"workers": [self._worker_info(w_id, worker)
                    for w_id, worker in self.scheduler.workers.items()]})
                return
            if self.path == "/api/benchmarks":
                scaling = self.runner.benchmark_qubit_scaling([6, 8, 10, 12])
                fusion = self.runner.benchmark_gate_fusion_speedup(num_qubits=12, depth=16)
                self._send_json({"scaling": scaling, "fusion": fusion})
                return

            web_dist = Path(__file__).parent.parent.parent / "web" / "dist"
            if web_dist.exists() and not self.path.startswith("/api"):
                requested_file = web_dist / (self.path.lstrip("/") or "index.html")
                self.directory = str(web_dist)
                if not requested_file.exists() or not requested_file.is_file():
                    self.path = "/index.html"
                return super().do_GET()
            self._send_json({"status": "error", "message": f"Endpoint {self.path} not found"}, code=404)
        except Exception:
            logger.exception("GET request failed: %s", self.path)
            self._send_json({"status": "error", "message": "Internal server error"}, code=500)

    def do_POST(self):
        try:
            content_len = int(self.headers.get("Content-Length", 0))
            if content_len < 0 or content_len > 10 * 1024 * 1024:
                self._send_json({"status": "error", "message": "Request body is too large"}, code=413)
                return
            post_data = self.rfile.read(content_len).decode("utf-8") if content_len else ""
            body = json.loads(post_data) if post_data else {}
            if not isinstance(body, dict):
                raise ValueError("JSON request body must be an object")
        except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
            self._send_json({"status": "error", "message": f"Invalid JSON request: {exc}"}, code=400)
            return

        try:
            handlers = {
                "/api/compile": self._handle_compile,
                "/api/run": self._handle_run,
                "/api/distributed/run": self._handle_distributed_run,
                "/api/verify": self._handle_verify,
                "/api/cptp/validate": self._handle_cptp_validate,
            }
            handler = handlers.get(self.path)
            if handler is None:
                self._send_json({"status": "error", "message": f"Endpoint {self.path} not found"}, code=404)
            else:
                handler(body)
        except Exception:
            logger.exception("POST request failed: %s", self.path)
            self._send_json({"status": "error", "message": "Internal server error"}, code=500)

    @staticmethod
    def _worker_info(worker_id: str, worker: Any) -> Dict[str, Any]:
        return {"id": worker_id, "host": worker.host, "status": worker.status,
                "tasks_completed": worker.tasks_completed, "cores": worker.cores,
                "last_heartbeat": worker.last_heartbeat}

    def _send_json(self, data: Any, code: int = 200):
        payload = json.dumps(data).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def _handle_compile(self, body: Dict[str, Any]):
        try:
            code = body.get("code")
            if not isinstance(code, str) or not code.strip():
                raise ValueError("code must be a non-empty string")
            opt_level = self._validated_int(body.get("opt_level", 2), "opt_level", minimum=0)
            topo_name = body.get("topology", "all_to_all")
            if topo_name not in {"all_to_all", "linear", "grid"}:
                raise ValueError("topology must be one of: all_to_all, linear, grid")
            circ = parse_iq_lang(code)
            topo = None
            if topo_name == "linear":
                topo = DeviceTopology.linear(circ.num_qubits)
            elif topo_name == "grid":
                rows = int(circ.num_qubits ** 0.5)
                cols = (circ.num_qubits + rows - 1) // max(1, rows)
                topo = DeviceTopology.grid(rows, cols)

            compiler = Compiler(opt_level=opt_level, topology=topo)
            comp_res = compiler.compile(circ)

            self._send_json({
                "status": "success",
                "num_qubits": circ.num_qubits,
                "original_gate_count": comp_res.original_gate_count,
                "optimized_gate_count": comp_res.optimized_gate_count,
                "original_depth": comp_res.original_depth,
                "optimized_depth": comp_res.optimized_depth,
                "passes_applied": comp_res.passes_applied,
                "is_equivalent": comp_res.is_equivalent,
                "qasm": comp_res.circuit.to_qasm()
            })
        except Exception as e:
            self._send_json({"status": "error", "message": str(e)}, code=400)

    def _handle_run(self, body: Dict[str, Any]):
        try:
            code = body.get("code")
            if not isinstance(code, str) or not code.strip():
                raise ValueError("code must be a non-empty string")
            backend = body.get("backend", "adaptive")
            if backend not in {"adaptive", "statevector", "density_matrix", "stabilizer", "tensor_network"}:
                raise ValueError(f"unsupported backend: {backend}")
            shots = self._validated_int(body.get("shots", 1024), "shots", minimum=1)
            seed = self._validated_int(body.get("seed", 42), "seed", minimum=0)
            circ = parse_iq_lang(code)
            backend_map = {
                "adaptive": AdaptivePlannerSimulator(),
                "statevector": StateVectorSimulator(),
                "density_matrix": DensityMatrixSimulator(),
                "stabilizer": StabilizerSimulator(),
                "tensor_network": TensorNetworkSimulator(),
            }
            sim = backend_map.get(backend, AdaptivePlannerSimulator())
            res = sim.run(circ, shots=shots, seed=seed)

            # Format statevector amplitudes if available
            amps_list = None
            if res.statevector is not None and len(res.statevector) <= 64:
                amps_list = [
                    {"index": i, "bitstring": f"{i:0{circ.num_qubits}b}", "real": float(a.real), "imag": float(a.imag), "prob": float(abs(a)**2)}
                    for i, a in enumerate(res.statevector)
                ]

            self._send_json({
                "status": "success",
                "backend_used": res.backend_used,
                "execution_time_ms": res.execution_time_ms,
                "memory_used_bytes": res.memory_used_bytes,
                "entanglement_entropy": res.entanglement_entropy,
                "counts": res.counts,
                "probabilities": res.probabilities,
                "amplitudes": amps_list,
                "metadata": res.metadata
            })
        except Exception as e:
            self._send_json({"status": "error", "message": str(e)}, code=400)

    def _handle_distributed_run(self, body: Dict[str, Any]):
        try:
            code = body.get("code")
            if not isinstance(code, str) or not code.strip():
                raise ValueError("code must be a non-empty string")
            shots = self._validated_int(body.get("shots", 2000), "shots", minimum=1)
            seed = self._validated_int(body.get("seed", 42), "seed", minimum=0)
            circ = parse_iq_lang(code)
            job_id = f"job_{int(time.time() * 1000)}"
            dist_res = self.scheduler.execute_job(job_id, circ, total_shots=shots, master_seed=seed)

            self._send_json({
                "status": "success",
                "job_id": dist_res.job_id,
                "total_shots": dist_res.total_shots,
                "counts": dist_res.counts,
                "probabilities": dist_res.probabilities,
                "z_expectation": dist_res.z_expectation,
                "variance": dist_res.variance,
                "confidence_interval_95": dist_res.confidence_interval_95,
                "fault_recovery_events": dist_res.fault_recovery_events,
                "execution_time_ms": dist_res.total_execution_time_ms
            })
        except Exception as e:
            self._send_json({"status": "error", "message": str(e)}, code=400)

    def _handle_verify(self, body: Dict[str, Any]):
        v_type = body.get("type", "metamorphic")
        try:
            if v_type == "metamorphic":
                from ..benchmarks.suite import create_ghz_circuit
                meta = MetamorphicTester()
                circ = create_ghz_circuit(3)
                r1 = meta.test_identity_insertion(circ)
                r2 = meta.test_commutation_reordering(circ)
                r3 = meta.test_bit_reversal(circ)
                self._send_json({
                    "status": "success",
                    "results": [
                        {"relation": "Identity Insertion", "passed": r1.passed, "distance": r1.distance, "details": r1.details},
                        {"relation": "Commutation Reordering", "passed": r2.passed, "distance": r2.distance, "details": r2.details},
                        {"relation": "Bit Reversal Invariance", "passed": r3.passed, "distance": r3.distance, "details": r3.details},
                    ]
                })
            elif v_type == "fault_injection":
                fi = FaultInjectionTester()
                g_det = fi.test_corrupted_gate_detection()
                c_det = fi.test_broken_cptp_channel_detection()
                self._send_json({
                    "status": "success",
                    "corrupted_gate_caught": g_det["bug_caught"],
                    "broken_cptp_caught": c_det["bug_caught"],
                    "details": g_det["flawed_details"]
                })
            else:
                from ..benchmarks.suite import create_ghz_circuit
                diff = DifferentialTester()
                res = diff.compare_circuits(create_ghz_circuit(3))
                self._send_json({"status": "success", "differential": res})
        except Exception as e:
            self._send_json({"status": "error", "message": str(e)}, code=400)

    def _handle_cptp_validate(self, body: Dict[str, Any]):
        try:
            ch_name = body.get("channel", "depolarizing")
            param = float(body.get("param", 0.05))
            kraus = build_kraus_channel(ch_name, [param])
            res = validate_cptp(kraus)
            self._send_json({"status": "success", "channel": ch_name, "param": param, "validation": res})
        except Exception as e:
            self._send_json({"status": "error", "message": str(e)}, code=400)

    @staticmethod
    def _validated_int(value: Any, label: str, *, minimum: int) -> int:
        if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
            qualifier = "positive" if minimum else "non-negative"
            raise ValueError(f"{label} must be a {qualifier} integer")
        return value


def start_server(host: str = "0.0.0.0", port: int = 8000):
    server = ThreadingHTTPServer((host, port), InvariantQServerHandler)
    print(f"InvariantQ Server listening on http://{host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server.")
        server.server_close()

if __name__ == "__main__":
    start_server()
