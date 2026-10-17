"""
InvariantQ Research-Grade REST and Static Web Server.
Binds to 0.0.0.0, provides full JSON API for compilation, multi-modal simulation,
distributed job scheduling, CPTP validation, and performance benchmarks.
"""

from __future__ import annotations
import json
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
        if self.path == "/api/health":
            self._send_json({"status": "ok", "platform": "InvariantQ", "version": "1.0.0"})
            return

        if self.path == "/api/cluster":
            workers_info = []
            for w_id, w in self.scheduler.workers.items():
                workers_info.append({
                    "id": w_id,
                    "host": w.host,
                    "status": w.status,
                    "tasks_completed": w.tasks_completed,
                    "cores": w.cores,
                    "last_heartbeat": w.last_heartbeat
                })
            self._send_json({"workers": workers_info})
            return

        if self.path == "/api/benchmarks":
            scaling = self.runner.benchmark_qubit_scaling([6, 8, 10, 12])
            fusion = self.runner.benchmark_gate_fusion_speedup(num_qubits=12, depth=16)
            self._send_json({"scaling": scaling, "fusion": fusion})
            return

        # Serve static frontend if directory exists
        web_dist = Path(__file__).parent.parent.parent / "web" / "dist"
        if web_dist.exists() and not self.path.startswith("/api"):
            requested_file = web_dist / (self.path.lstrip("/") or "index.html")
            if requested_file.exists() and requested_file.is_file():
                self.directory = str(web_dist)
                return super().do_GET()
            else:
                # SPA fallback
                self.directory = str(web_dist)
                self.path = "/index.html"
                return super().do_GET()

        super().do_GET()

    def do_POST(self):
        content_len = int(self.headers.get("Content-Length", 0))
        post_data = self.rfile.read(content_len).decode("utf-8") if content_len > 0 else "{}"
        try:
            body = json.loads(post_data) if post_data else {}
        except Exception:
            body = {}

        if self.path == "/api/compile":
            self._handle_compile(body)
        elif self.path == "/api/run":
            self._handle_run(body)
        elif self.path == "/api/distributed/run":
            self._handle_distributed_run(body)
        elif self.path == "/api/verify":
            self._handle_verify(body)
        elif self.path == "/api/cptp/validate":
            self._handle_cptp_validate(body)
        else:
            self.send_response(404)
            self._send_json({"error": f"Endpoint {self.path} not found"})

    def _send_json(self, data: Any, code: int = 200):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode("utf-8"))

    def _handle_compile(self, body: Dict[str, Any]):
        code = body.get("code", "qubit q[2]; h q[0]; cx q[0], q[1];")
        opt_level = int(body.get("opt_level", 2))
        topo_name = body.get("topology", "all_to_all")

        try:
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
        code = body.get("code", "qubit q[2]; h q[0]; cx q[0], q[1];")
        backend = body.get("backend", "adaptive")
        shots = int(body.get("shots", 1024))
        seed = int(body.get("seed", 42))

        try:
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
        code = body.get("code", "qubit q[2]; h q[0]; cx q[0], q[1];")
        shots = int(body.get("shots", 2000))
        seed = int(body.get("seed", 42))

        try:
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
        ch_name = body.get("channel", "depolarizing")
        param = float(body.get("param", 0.05))
        try:
            kraus = build_kraus_channel(ch_name, [param])
            res = validate_cptp(kraus)
            self._send_json({"status": "success", "channel": ch_name, "param": param, "validation": res})
        except Exception as e:
            self._send_json({"status": "error", "message": str(e)}, code=400)


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
