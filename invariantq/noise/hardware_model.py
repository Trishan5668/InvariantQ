"""
Realistic Hardware Device and Calibration Digital Twins.
Models IBM Eagle (127Q), Google Sycamore (53Q), and Rigetti Aspen architectures.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Tuple
from ..compiler.mapping import DeviceTopology
from .readout import ReadoutError

@dataclass
class HardwareModel:
    name: str
    num_qubits: int
    topology: DeviceTopology
    t1_avg_us: float = 80.0
    t2_avg_us: float = 90.0
    single_qubit_error: float = 0.0003
    two_qubit_error: float = 0.008
    readout_error: ReadoutError = field(default_factory=lambda: ReadoutError(0.015, 0.02))

    @classmethod
    def ibm_eagle_127(cls) -> HardwareModel:
        # Simplified linear/hex backbone representation
        topo = DeviceTopology.linear(127)
        return cls(
            name="IBM_Eagle_127",
            num_qubits=127,
            topology=topo,
            t1_avg_us=100.0,
            t2_avg_us=120.0,
            single_qubit_error=0.0002,
            two_qubit_error=0.007,
            readout_error=ReadoutError(0.012, 0.018)
        )

    @classmethod
    def google_sycamore_53(cls) -> HardwareModel:
        topo = DeviceTopology.grid(6, 9)
        return cls(
            name="Google_Sycamore_53",
            num_qubits=54,
            topology=topo,
            t1_avg_us=25.0,
            t2_avg_us=30.0,
            single_qubit_error=0.001,
            two_qubit_error=0.006,
            readout_error=ReadoutError(0.02, 0.03)
        )

    @classmethod
    def rigetti_aspen_80(cls) -> HardwareModel:
        topo = DeviceTopology.grid(8, 10)
        return cls(
            name="Rigetti_Aspen_80",
            num_qubits=80,
            topology=topo,
            t1_avg_us=40.0,
            t2_avg_us=35.0,
            single_qubit_error=0.0015,
            two_qubit_error=0.015,
            readout_error=ReadoutError(0.03, 0.04)
        )
