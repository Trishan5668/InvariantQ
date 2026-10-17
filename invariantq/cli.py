"""
InvariantQ Unified Command Line Interface.
"""

from __future__ import annotations
import argparse
import sys
import json
from pathlib import Path

from .language.qasm_parser import parse_iq_lang
from .compiler.optimizer import Compiler
from .compiler.mapping import DeviceTopology
from .simulator.adaptive import AdaptivePlannerSimulator
from .simulator.statevector import StateVectorSimulator
from .simulator.density_matrix import DensityMatrixSimulator
from .simulator.stabilizer import StabilizerSimulator
from .simulator.tensor_network import TensorNetworkSimulator
from .verification.differential import DifferentialTester
from .verification.metamorphic import MetamorphicTester
from .verification.fault_injection import FaultInjectionTester
from .benchmarks.runner import BenchmarkRunner

def main():
    parser = argparse.ArgumentParser(
        prog="invariantq",
        description="INVARIANTQ: Research-Grade Quantum Computing Platform"
    )
    subparsers = parser.add_subparsers(dest="command", help="Sub-commands")

    # Run command
    run_parser = subparsers.add_parser("run", help="Run a quantum circuit file")
    run_parser.add_argument("file", type=str, help="Path to .iq or .qasm file")
    run_parser.add_argument("--backend", type=str, default="adaptive", choices=["adaptive", "statevector", "density_matrix", "stabilizer", "tensor_network"])
    run_parser.add_argument("--shots", type=int, default=1024, help="Number of measurement shots")
    run_parser.add_argument("--opt", type=int, default=2, help="Compiler optimization level (0-3)")
    run_parser.add_argument("--seed", type=int, default=42, help="RNG seed")

    # Compile command
    compile_parser = subparsers.add_parser("compile", help="Compile and optimize a quantum circuit")
    compile_parser.add_argument("file", type=str, help="Path to .iq or .qasm file")
    compile_parser.add_argument("--opt", type=int, default=2, help="Optimization level (0-3)")
    compile_parser.add_argument("--topology", type=str, default="all_to_all", choices=["all_to_all", "linear", "grid"])
    compile_parser.add_argument("--output", "-o", type=str, default=None, help="Output QASM file")

    # Benchmark command
    bench_parser = subparsers.add_parser("benchmark", help="Run quantum performance benchmarks")
    bench_parser.add_argument("--fusion", action="store_true", help="Run gate fusion speedup benchmark")
    bench_parser.add_argument("--scaling", action="store_true", help="Run qubit scaling benchmark")

    # Verify command
    verify_parser = subparsers.add_parser("verify", help="Run verification and testing suites")
    verify_parser.add_argument("--metamorphic", action="store_true", help="Run metamorphic relation suite")
    verify_parser.add_argument("--differential", action="store_true", help="Run differential testing across backends")
    verify_parser.add_argument("--fault-injection", action="store_true", help="Run fault injection test")

    # Serve command
    serve_parser = subparsers.add_parser("serve", help="Start InvariantQ REST API and UI server")
    serve_parser.add_argument("--port", type=int, default=8000, help="Server port (default: 8000)")
    serve_parser.add_argument("--host", type=str, default="0.0.0.0", help="Host interface (default: 0.0.0.0)")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    if args.command == "run":
        path = Path(args.file)
        if not path.exists():
            print(f"Error: File {args.file} not found.", file=sys.stderr)
            sys.exit(1)
        source = path.read_text()
        circ = parse_iq_lang(source)

        compiler = Compiler(opt_level=args.opt)
        comp_res = compiler.compile(circ)

        backend_map = {
            "adaptive": AdaptivePlannerSimulator(),
            "statevector": StateVectorSimulator(),
            "density_matrix": DensityMatrixSimulator(),
            "stabilizer": StabilizerSimulator(),
            "tensor_network": TensorNetworkSimulator(),
        }
        sim = backend_map[args.backend]
        res = sim.run(comp_res.circuit, shots=args.shots, seed=args.seed)

        print(f"=== InvariantQ Execution Summary ===")
        print(f"Circuit: {path.name} ({circ.num_qubits} qubits, {len(circ.ops)} -> {len(comp_res.circuit.ops)} gates)")
        print(f"Backend Used: {res.backend_used}")
        print(f"Execution Time: {res.execution_time_ms:.3f} ms")
        print(f"Memory Allocated: {res.memory_used_bytes / 1024:.2f} KB")
        if res.entanglement_entropy is not None:
            print(f"Entanglement Entropy: {res.entanglement_entropy:.4f} bits")
        print("\nMeasurement Histogram:")
        for bitstr, count in sorted(res.counts.items()):
            bar = "#" * int(40 * count / args.shots)
            print(f"  |{bitstr}>: {count:5d} ({count/args.shots:6.2%}) {bar}")

    elif args.command == "compile":
        path = Path(args.file)
        source = path.read_text()
        circ = parse_iq_lang(source)

        topo = None
        if args.topology == "linear":
            topo = DeviceTopology.linear(circ.num_qubits)
        elif args.topology == "grid":
            rows = int(circ.num_qubits ** 0.5)
            cols = (circ.num_qubits + rows - 1) // rows
            topo = DeviceTopology.grid(rows, cols)

        compiler = Compiler(opt_level=args.opt, topology=topo)
        res = compiler.compile(circ)

        print(f"=== Compilation Result ===")
        print(f"Original Gates: {res.original_gate_count} (Depth: {res.original_depth})")
        print(f"Optimized Gates: {res.optimized_gate_count} (Depth: {res.optimized_depth})")
        print(f"Gate Reduction: {(1 - res.optimized_gate_count/max(1,res.original_gate_count)):.1%}")
        print(f"Passes Applied: {', '.join(res.passes_applied)}")
        print(f"Semantic Equivalence: {'VERIFIED' if res.is_equivalent else 'UNCHECKED'}")

        if args.output:
            Path(args.output).write_text(res.circuit.to_qasm())
            print(f"Saved optimized QASM to {args.output}")

    elif args.command == "benchmark":
        runner = BenchmarkRunner()
        if args.fusion or not args.scaling:
            print("Running Gate Fusion Speedup Benchmark...")
            f_res = runner.benchmark_gate_fusion_speedup(num_qubits=14, depth=24)
            print(json.dumps(f_res, indent=2))
        if args.scaling:
            print("Running Qubit Scaling Benchmark...")
            s_res = runner.benchmark_qubit_scaling()
            print(json.dumps(s_res, indent=2))

    elif args.command == "verify":
        if args.metamorphic or (not args.differential and not args.fault_injection):
            from .benchmarks.suite import create_ghz_circuit
            meta = MetamorphicTester()
            circ = create_ghz_circuit(4)
            r1 = meta.test_identity_insertion(circ)
            r2 = meta.test_commutation_reordering(circ)
            r3 = meta.test_bit_reversal(circ)
            print("=== Metamorphic Testing Results ===")
            print(f"MR1 Identity Insertion: {'PASSED' if r1.passed else 'FAILED'} ({r1.details})")
            print(f"MR2 Commutation:        {'PASSED' if r2.passed else 'FAILED'} ({r2.details})")
            print(f"MR3 Bit Inversion:      {'PASSED' if r3.passed else 'FAILED'} ({r3.details})")

        if args.fault_injection:
            fi = FaultInjectionTester()
            print("\n=== Fault Injection & Bug Detection Test ===")
            g_det = fi.test_corrupted_gate_detection()
            print(f"Corrupted Gate Detected by Metamorphic Suite: {'YES (PASS)' if g_det['bug_caught'] else 'NO (FAIL)'}")
            c_det = fi.test_broken_cptp_channel_detection()
            print(f"Broken CPTP Channel Detected: {'YES (PASS)' if c_det['bug_caught'] else 'NO (FAIL)'}")

    elif args.command == "serve":
        from .distributed.server import start_server
        start_server(host=args.host, port=args.port)

if __name__ == "__main__":
    main()
