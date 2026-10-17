"""
INVARIANTQ: A Research-Grade Quantum Computing Platform.
Integrating a custom quantum programming language, optimizing compiler,
multi-modal simulators, CPTP noise channels, and a distributed execution planner.
"""

from .language.qasm_parser import parse_iq_lang, parse_qasm
from .ir.qir import CircuitIR, GateOp, MeasureOp, ResetOp, BarrierOp, NoiseOp, QWire, CWire
from .compiler.optimizer import Compiler, CompilationResult
from .compiler.mapping import DeviceTopology
from .simulator.statevector import StateVectorSimulator
from .simulator.density_matrix import DensityMatrixSimulator
from .simulator.stabilizer import StabilizerSimulator
from .simulator.tensor_network import TensorNetworkSimulator
from .simulator.adaptive import AdaptivePlannerSimulator
from .noise.channels import build_kraus_channel, compute_choi_matrix
from .noise.cptp_validator import validate_cptp, verify_channel_composition
from .noise.readout import ReadoutError
from .noise.hardware_model import HardwareModel
from .distributed.planner import DistributedPlanner
from .distributed.scheduler import DistributedScheduler
from .distributed.aggregation import ResultAggregator
from .verification.differential import DifferentialTester
from .verification.metamorphic import MetamorphicTester
from .verification.fault_injection import FaultInjectionTester
from .benchmarks.runner import BenchmarkRunner
from .benchmarks.qft import create_qft_circuit
from .benchmarks.grover import create_grover_circuit
from .benchmarks.vqe import VQESolver
from .benchmarks.suite import create_ghz_circuit, create_random_clifford_circuit, create_random_circuit
from .reproducibility.ledger import ReproducibilityLedger

__version__ = "1.0.0"

__all__ = [
    "parse_iq_lang",
    "parse_qasm",
    "CircuitIR",
    "GateOp",
    "MeasureOp",
    "ResetOp",
    "BarrierOp",
    "NoiseOp",
    "QWire",
    "CWire",
    "Compiler",
    "CompilationResult",
    "DeviceTopology",
    "StateVectorSimulator",
    "DensityMatrixSimulator",
    "StabilizerSimulator",
    "TensorNetworkSimulator",
    "AdaptivePlannerSimulator",
    "build_kraus_channel",
    "compute_choi_matrix",
    "validate_cptp",
    "verify_channel_composition",
    "ReadoutError",
    "HardwareModel",
    "DistributedPlanner",
    "DistributedScheduler",
    "ResultAggregator",
    "DifferentialTester",
    "MetamorphicTester",
    "FaultInjectionTester",
    "BenchmarkRunner",
    "create_qft_circuit",
    "create_grover_circuit",
    "VQESolver",
    "create_ghz_circuit",
    "create_random_clifford_circuit",
    "create_random_circuit",
    "ReproducibilityLedger",
]
