"""
InvariantQ Native C++ Core Bindings via ctypes with NumPy/Pure-Python fallback.
"""

from __future__ import annotations
import ctypes
import os
import sys
import platform
from pathlib import Path
from typing import List, Tuple, Optional
import numpy as np

# Locate shared library
_LIB_DIRS = [
    Path(__file__).parent,
    Path(__file__).parent.parent.parent / "core",
    Path("/usr/local/lib"),
    Path("/usr/lib"),
]

_NATIVE_LIB = None
_NATIVE_LOAD_ERRORS: List[str] = []
if sys.platform == "win32":
    _LIB_NAMES = ("invariantq.dll", "libinvariantq.dll")
elif sys.platform == "darwin":
    _LIB_NAMES = ("libinvariantq.dylib",)
else:
    _LIB_NAMES = ("libinvariantq.so",)
for directory in _LIB_DIRS:
    for name in _LIB_NAMES:
        lib_path = directory / name
        if lib_path.exists():
            try:
                _NATIVE_LIB = ctypes.CDLL(str(lib_path))
                break
            except OSError as exc:
                _NATIVE_LOAD_ERRORS.append(f"{lib_path}: {exc}")
    if _NATIVE_LIB is not None:
        break

HAS_NATIVE_CORE = _NATIVE_LIB is not None

def native_core_status() -> dict:
    """Return diagnostic information without pretending that fallback is native."""
    return {
        "active": HAS_NATIVE_CORE,
        "implementation": "native-cpp" if HAS_NATIVE_CORE else "portable-numpy-fallback",
        "platform": platform.platform(),
        "library_names": list(_LIB_NAMES),
        "load_errors": list(_NATIVE_LOAD_ERRORS),
    }

if HAS_NATIVE_CORE:
    # StateVector
    _NATIVE_LIB.iq_statevector_create.argtypes = [ctypes.c_size_t]
    _NATIVE_LIB.iq_statevector_create.restype = ctypes.c_void_p

    _NATIVE_LIB.iq_statevector_free.argtypes = [ctypes.c_void_p]
    _NATIVE_LIB.iq_statevector_free.restype = None

    _NATIVE_LIB.iq_statevector_reset.argtypes = [ctypes.c_void_p]
    _NATIVE_LIB.iq_statevector_reset.restype = None

    _NATIVE_LIB.iq_statevector_apply_1q.argtypes = [
        ctypes.c_void_p,
        ctypes.c_size_t,
        ctypes.POINTER(ctypes.c_double),
        ctypes.POINTER(ctypes.c_double),
    ]
    _NATIVE_LIB.iq_statevector_apply_1q.restype = None

    _NATIVE_LIB.iq_statevector_apply_2q.argtypes = [
        ctypes.c_void_p,
        ctypes.c_size_t,
        ctypes.c_size_t,
        ctypes.POINTER(ctypes.c_double),
        ctypes.POINTER(ctypes.c_double),
    ]
    _NATIVE_LIB.iq_statevector_apply_2q.restype = None

    _NATIVE_LIB.iq_statevector_apply_fused.argtypes = [
        ctypes.c_void_p,
        ctypes.POINTER(ctypes.c_size_t),
        ctypes.c_size_t,
        ctypes.POINTER(ctypes.c_double),
        ctypes.POINTER(ctypes.c_double),
    ]
    _NATIVE_LIB.iq_statevector_apply_fused.restype = None

    _NATIVE_LIB.iq_statevector_measure.argtypes = [
        ctypes.c_void_p,
        ctypes.c_size_t,
        ctypes.c_double,
    ]
    _NATIVE_LIB.iq_statevector_measure.restype = ctypes.c_int

    _NATIVE_LIB.iq_statevector_reset_qubit.argtypes = [
        ctypes.c_void_p,
        ctypes.c_size_t,
        ctypes.c_double,
    ]
    _NATIVE_LIB.iq_statevector_reset_qubit.restype = None

    _NATIVE_LIB.iq_statevector_measure_prob.argtypes = [
        ctypes.c_void_p,
        ctypes.c_size_t,
        ctypes.c_int,
    ]
    _NATIVE_LIB.iq_statevector_measure_prob.restype = ctypes.c_double

    _NATIVE_LIB.iq_statevector_get_amplitudes.argtypes = [
        ctypes.c_void_p,
        ctypes.POINTER(ctypes.c_double),
        ctypes.POINTER(ctypes.c_double),
    ]
    _NATIVE_LIB.iq_statevector_get_amplitudes.restype = None

    _NATIVE_LIB.iq_statevector_get_probabilities.argtypes = [
        ctypes.c_void_p,
        ctypes.POINTER(ctypes.c_double),
    ]
    _NATIVE_LIB.iq_statevector_get_probabilities.restype = None

    _NATIVE_LIB.iq_statevector_sample.argtypes = [
        ctypes.c_void_p,
        ctypes.c_size_t,
        ctypes.c_uint64,
        ctypes.POINTER(ctypes.c_uint64),
    ]
    _NATIVE_LIB.iq_statevector_sample.restype = None

    _NATIVE_LIB.iq_statevector_entropy.argtypes = [
        ctypes.c_void_p,
        ctypes.POINTER(ctypes.c_size_t),
        ctypes.c_size_t,
    ]
    _NATIVE_LIB.iq_statevector_entropy.restype = ctypes.c_double

    _NATIVE_LIB.iq_statevector_expval_pauli.argtypes = [
        ctypes.c_void_p,
        ctypes.c_char_p,
        ctypes.POINTER(ctypes.c_size_t),
        ctypes.c_size_t,
        ctypes.POINTER(ctypes.c_double),
        ctypes.POINTER(ctypes.c_double),
    ]
    _NATIVE_LIB.iq_statevector_expval_pauli.restype = None

    # DensityMatrix
    _NATIVE_LIB.iq_density_matrix_create.argtypes = [ctypes.c_size_t]
    _NATIVE_LIB.iq_density_matrix_create.restype = ctypes.c_void_p

    _NATIVE_LIB.iq_density_matrix_free.argtypes = [ctypes.c_void_p]
    _NATIVE_LIB.iq_density_matrix_free.restype = None

    _NATIVE_LIB.iq_density_matrix_reset.argtypes = [ctypes.c_void_p]
    _NATIVE_LIB.iq_density_matrix_reset.restype = None

    _NATIVE_LIB.iq_density_matrix_apply_1q_unitary.argtypes = [
        ctypes.c_void_p,
        ctypes.c_size_t,
        ctypes.POINTER(ctypes.c_double),
        ctypes.POINTER(ctypes.c_double),
    ]
    _NATIVE_LIB.iq_density_matrix_apply_1q_unitary.restype = None

    _NATIVE_LIB.iq_density_matrix_apply_2q_unitary.argtypes = [
        ctypes.c_void_p,
        ctypes.c_size_t,
        ctypes.c_size_t,
        ctypes.POINTER(ctypes.c_double),
        ctypes.POINTER(ctypes.c_double),
    ]
    _NATIVE_LIB.iq_density_matrix_apply_2q_unitary.restype = None

    _NATIVE_LIB.iq_density_matrix_apply_kraus_1q.argtypes = [
        ctypes.c_void_p,
        ctypes.c_size_t,
        ctypes.c_size_t,
        ctypes.POINTER(ctypes.c_double),
        ctypes.POINTER(ctypes.c_double),
    ]
    _NATIVE_LIB.iq_density_matrix_apply_kraus_1q.restype = None

    _NATIVE_LIB.iq_density_matrix_get_elements.argtypes = [
        ctypes.c_void_p,
        ctypes.POINTER(ctypes.c_double),
        ctypes.POINTER(ctypes.c_double),
    ]
    _NATIVE_LIB.iq_density_matrix_get_elements.restype = None

    _NATIVE_LIB.iq_density_matrix_trace.argtypes = [ctypes.c_void_p]
    _NATIVE_LIB.iq_density_matrix_trace.restype = ctypes.c_double

    _NATIVE_LIB.iq_density_matrix_purity.argtypes = [ctypes.c_void_p]
    _NATIVE_LIB.iq_density_matrix_purity.restype = ctypes.c_double

    _NATIVE_LIB.iq_density_matrix_entropy.argtypes = [ctypes.c_void_p]
    _NATIVE_LIB.iq_density_matrix_entropy.restype = ctypes.c_double

    _NATIVE_LIB.iq_density_matrix_measure.argtypes = [
        ctypes.c_void_p,
        ctypes.c_size_t,
        ctypes.c_double,
    ]
    _NATIVE_LIB.iq_density_matrix_measure.restype = ctypes.c_int

    _NATIVE_LIB.iq_density_matrix_reset_qubit.argtypes = [
        ctypes.c_void_p,
        ctypes.c_size_t,
    ]
    _NATIVE_LIB.iq_density_matrix_reset_qubit.restype = None

    # Stabilizer
    _NATIVE_LIB.iq_stabilizer_create.argtypes = [ctypes.c_size_t]
    _NATIVE_LIB.iq_stabilizer_create.restype = ctypes.c_void_p

    _NATIVE_LIB.iq_stabilizer_free.argtypes = [ctypes.c_void_p]
    _NATIVE_LIB.iq_stabilizer_free.restype = None

    _NATIVE_LIB.iq_stabilizer_reset.argtypes = [ctypes.c_void_p]
    _NATIVE_LIB.iq_stabilizer_reset.restype = None

    _NATIVE_LIB.iq_stabilizer_apply_h.argtypes = [ctypes.c_void_p, ctypes.c_size_t]
    _NATIVE_LIB.iq_stabilizer_apply_h.restype = None

    _NATIVE_LIB.iq_stabilizer_apply_s.argtypes = [ctypes.c_void_p, ctypes.c_size_t]
    _NATIVE_LIB.iq_stabilizer_apply_s.restype = None

    _NATIVE_LIB.iq_stabilizer_apply_sdg.argtypes = [ctypes.c_void_p, ctypes.c_size_t]
    _NATIVE_LIB.iq_stabilizer_apply_sdg.restype = None

    _NATIVE_LIB.iq_stabilizer_apply_cnot.argtypes = [ctypes.c_void_p, ctypes.c_size_t, ctypes.c_size_t]
    _NATIVE_LIB.iq_stabilizer_apply_cnot.restype = None

    _NATIVE_LIB.iq_stabilizer_apply_cz.argtypes = [ctypes.c_void_p, ctypes.c_size_t, ctypes.c_size_t]
    _NATIVE_LIB.iq_stabilizer_apply_cz.restype = None

    _NATIVE_LIB.iq_stabilizer_apply_swap.argtypes = [ctypes.c_void_p, ctypes.c_size_t, ctypes.c_size_t]
    _NATIVE_LIB.iq_stabilizer_apply_swap.restype = None

    _NATIVE_LIB.iq_stabilizer_apply_x.argtypes = [ctypes.c_void_p, ctypes.c_size_t]
    _NATIVE_LIB.iq_stabilizer_apply_x.restype = None

    _NATIVE_LIB.iq_stabilizer_apply_y.argtypes = [ctypes.c_void_p, ctypes.c_size_t]
    _NATIVE_LIB.iq_stabilizer_apply_y.restype = None

    _NATIVE_LIB.iq_stabilizer_apply_z.argtypes = [ctypes.c_void_p, ctypes.c_size_t]
    _NATIVE_LIB.iq_stabilizer_apply_z.restype = None

    _NATIVE_LIB.iq_stabilizer_measure.argtypes = [ctypes.c_void_p, ctypes.c_size_t, ctypes.c_double]
    _NATIVE_LIB.iq_stabilizer_measure.restype = ctypes.c_int

    _NATIVE_LIB.iq_stabilizer_reset_qubit.argtypes = [ctypes.c_void_p, ctypes.c_size_t, ctypes.c_double]
    _NATIVE_LIB.iq_stabilizer_reset_qubit.restype = None

    _NATIVE_LIB.iq_stabilizer_to_string.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_size_t]
    _NATIVE_LIB.iq_stabilizer_to_string.restype = None

    # MPS
    _NATIVE_LIB.iq_mps_create.argtypes = [ctypes.c_size_t, ctypes.c_size_t, ctypes.c_double]
    _NATIVE_LIB.iq_mps_create.restype = ctypes.c_void_p

    _NATIVE_LIB.iq_mps_free.argtypes = [ctypes.c_void_p]
    _NATIVE_LIB.iq_mps_free.restype = None

    _NATIVE_LIB.iq_mps_reset.argtypes = [ctypes.c_void_p]
    _NATIVE_LIB.iq_mps_reset.restype = None

    _NATIVE_LIB.iq_mps_apply_1q.argtypes = [
        ctypes.c_void_p,
        ctypes.c_size_t,
        ctypes.POINTER(ctypes.c_double),
        ctypes.POINTER(ctypes.c_double),
    ]
    _NATIVE_LIB.iq_mps_apply_1q.restype = None

    _NATIVE_LIB.iq_mps_apply_2q.argtypes = [
        ctypes.c_void_p,
        ctypes.c_size_t,
        ctypes.c_size_t,
        ctypes.POINTER(ctypes.c_double),
        ctypes.POINTER(ctypes.c_double),
    ]
    _NATIVE_LIB.iq_mps_apply_2q.restype = None

    _NATIVE_LIB.iq_mps_entropy.argtypes = [ctypes.c_void_p, ctypes.c_size_t]
    _NATIVE_LIB.iq_mps_entropy.restype = ctypes.c_double

    _NATIVE_LIB.iq_mps_to_statevector.argtypes = [
        ctypes.c_void_p,
        ctypes.POINTER(ctypes.c_double),
        ctypes.POINTER(ctypes.c_double),
    ]
    _NATIVE_LIB.iq_mps_to_statevector.restype = None

    _NATIVE_LIB.iq_mps_measure.argtypes = [ctypes.c_void_p, ctypes.c_size_t, ctypes.c_double]
    _NATIVE_LIB.iq_mps_measure.restype = ctypes.c_int


class NativeStateVector:
    def __init__(self, num_qubits: int):
        self.num_qubits = num_qubits
        self.dim = 1 << num_qubits
        if not HAS_NATIVE_CORE:
            raise RuntimeError("Native InvariantQ C++ core library not found")
        self._ptr = _NATIVE_LIB.iq_statevector_create(num_qubits)
        if not self._ptr:
            raise MemoryError("Failed to allocate StateVector in C++ core")

    def __del__(self):
        if hasattr(self, "_ptr") and self._ptr and HAS_NATIVE_CORE:
            _NATIVE_LIB.iq_statevector_free(self._ptr)
            self._ptr = None

    def reset(self):
        _NATIVE_LIB.iq_statevector_reset(self._ptr)

    def apply_1q(self, target: int, matrix: np.ndarray):
        m = np.asarray(matrix, dtype=np.complex128).flatten()
        real = np.ascontiguousarray(m.real, dtype=np.float64)
        imag = np.ascontiguousarray(m.imag, dtype=np.float64)
        r_ptr = real.ctypes.data_as(ctypes.POINTER(ctypes.c_double))
        i_ptr = imag.ctypes.data_as(ctypes.POINTER(ctypes.c_double))
        _NATIVE_LIB.iq_statevector_apply_1q(self._ptr, target, r_ptr, i_ptr)

    def apply_2q(self, q0: int, q1: int, matrix: np.ndarray):
        m = np.asarray(matrix, dtype=np.complex128).flatten()
        real = np.ascontiguousarray(m.real, dtype=np.float64)
        imag = np.ascontiguousarray(m.imag, dtype=np.float64)
        r_ptr = real.ctypes.data_as(ctypes.POINTER(ctypes.c_double))
        i_ptr = imag.ctypes.data_as(ctypes.POINTER(ctypes.c_double))
        _NATIVE_LIB.iq_statevector_apply_2q(self._ptr, q0, q1, r_ptr, i_ptr)

    def apply_fused(self, qubits: List[int], matrix: np.ndarray):
        k = len(qubits)
        m = np.asarray(matrix, dtype=np.complex128).flatten()
        real = np.ascontiguousarray(m.real, dtype=np.float64)
        imag = np.ascontiguousarray(m.imag, dtype=np.float64)
        q_arr = np.ascontiguousarray(qubits, dtype=np.uint64)
        r_ptr = real.ctypes.data_as(ctypes.POINTER(ctypes.c_double))
        i_ptr = imag.ctypes.data_as(ctypes.POINTER(ctypes.c_double))
        q_ptr = q_arr.ctypes.data_as(ctypes.POINTER(ctypes.c_size_t))
        _NATIVE_LIB.iq_statevector_apply_fused(self._ptr, q_ptr, k, r_ptr, i_ptr)

    def measure(self, target: int, rand_val: float) -> int:
        return _NATIVE_LIB.iq_statevector_measure(self._ptr, target, rand_val)

    def reset_qubit(self, target: int, rand_val: float = 0.0):
        _NATIVE_LIB.iq_statevector_reset_qubit(self._ptr, target, rand_val)

    def measure_prob(self, target: int, outcome: int) -> float:
        return _NATIVE_LIB.iq_statevector_measure_prob(self._ptr, target, outcome)

    def get_amplitudes(self) -> np.ndarray:
        real = np.empty(self.dim, dtype=np.float64)
        imag = np.empty(self.dim, dtype=np.float64)
        r_ptr = real.ctypes.data_as(ctypes.POINTER(ctypes.c_double))
        i_ptr = imag.ctypes.data_as(ctypes.POINTER(ctypes.c_double))
        _NATIVE_LIB.iq_statevector_get_amplitudes(self._ptr, r_ptr, i_ptr)
        return real + 1j * imag

    def get_probabilities(self) -> np.ndarray:
        probs = np.empty(self.dim, dtype=np.float64)
        p_ptr = probs.ctypes.data_as(ctypes.POINTER(ctypes.c_double))
        _NATIVE_LIB.iq_statevector_get_probabilities(self._ptr, p_ptr)
        return probs

    def sample(self, num_shots: int, seed: int = 42) -> np.ndarray:
        results = np.empty(num_shots, dtype=np.uint64)
        res_ptr = results.ctypes.data_as(ctypes.POINTER(ctypes.c_uint64))
        _NATIVE_LIB.iq_statevector_sample(self._ptr, num_shots, seed, res_ptr)
        return results

    def von_neumann_entropy(self, subsystem_qubits: List[int]) -> float:
        q_arr = np.ascontiguousarray(subsystem_qubits, dtype=np.uint64)
        q_ptr = q_arr.ctypes.data_as(ctypes.POINTER(ctypes.c_size_t))
        return _NATIVE_LIB.iq_statevector_entropy(self._ptr, q_ptr, len(subsystem_qubits))

    def expectation_value_pauli(self, pauli_str: str, qubits: List[int]) -> complex:
        q_arr = np.ascontiguousarray(qubits, dtype=np.uint64)
        q_ptr = q_arr.ctypes.data_as(ctypes.POINTER(ctypes.c_size_t))
        p_bytes = pauli_str.encode("ascii")
        val_real = ctypes.c_double(0.0)
        val_imag = ctypes.c_double(0.0)
        _NATIVE_LIB.iq_statevector_expval_pauli(
            self._ptr,
            p_bytes,
            q_ptr,
            len(qubits),
            ctypes.byref(val_real),
            ctypes.byref(val_imag),
        )
        return complex(val_real.value, val_imag.value)


class NativeDensityMatrix:
    def __init__(self, num_qubits: int):
        self.num_qubits = num_qubits
        self.dim = 1 << num_qubits
        if not HAS_NATIVE_CORE:
            raise RuntimeError("Native InvariantQ C++ core library not found")
        self._ptr = _NATIVE_LIB.iq_density_matrix_create(num_qubits)
        if not self._ptr:
            raise MemoryError("Failed to allocate DensityMatrix in C++ core")

    def __del__(self):
        if hasattr(self, "_ptr") and self._ptr and HAS_NATIVE_CORE:
            _NATIVE_LIB.iq_density_matrix_free(self._ptr)
            self._ptr = None

    def reset(self):
        _NATIVE_LIB.iq_density_matrix_reset(self._ptr)

    def apply_1q_unitary(self, target: int, matrix: np.ndarray):
        m = np.asarray(matrix, dtype=np.complex128).flatten()
        real = np.ascontiguousarray(m.real, dtype=np.float64)
        imag = np.ascontiguousarray(m.imag, dtype=np.float64)
        _NATIVE_LIB.iq_density_matrix_apply_1q_unitary(
            self._ptr,
            target,
            real.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
            imag.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
        )

    def apply_2q_unitary(self, q0: int, q1: int, matrix: np.ndarray):
        m = np.asarray(matrix, dtype=np.complex128).flatten()
        real = np.ascontiguousarray(m.real, dtype=np.float64)
        imag = np.ascontiguousarray(m.imag, dtype=np.float64)
        _NATIVE_LIB.iq_density_matrix_apply_2q_unitary(
            self._ptr,
            q0,
            q1,
            real.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
            imag.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
        )

    def apply_1q_kraus(self, target: int, kraus_ops: List[np.ndarray]):
        num_k = len(kraus_ops)
        stacked = np.stack([np.asarray(k, dtype=np.complex128).flatten() for k in kraus_ops])
        real = np.ascontiguousarray(stacked.real.flatten(), dtype=np.float64)
        imag = np.ascontiguousarray(stacked.imag.flatten(), dtype=np.float64)
        _NATIVE_LIB.iq_density_matrix_apply_kraus_1q(
            self._ptr,
            target,
            num_k,
            real.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
            imag.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
        )

    def get_matrix(self) -> np.ndarray:
        total = self.dim * self.dim
        real = np.empty(total, dtype=np.float64)
        imag = np.empty(total, dtype=np.float64)
        _NATIVE_LIB.iq_density_matrix_get_elements(
            self._ptr,
            real.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
            imag.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
        )
        return (real + 1j * imag).reshape((self.dim, self.dim))

    def trace(self) -> float:
        return _NATIVE_LIB.iq_density_matrix_trace(self._ptr)

    def purity(self) -> float:
        return _NATIVE_LIB.iq_density_matrix_purity(self._ptr)

    def von_neumann_entropy(self) -> float:
        return _NATIVE_LIB.iq_density_matrix_entropy(self._ptr)

    def measure(self, target: int, rand_val: float) -> int:
        return _NATIVE_LIB.iq_density_matrix_measure(self._ptr, target, rand_val)

    def reset_qubit(self, target: int):
        _NATIVE_LIB.iq_density_matrix_reset_qubit(self._ptr, target)


class NativeStabilizer:
    def __init__(self, num_qubits: int):
        self.num_qubits = num_qubits
        if not HAS_NATIVE_CORE:
            raise RuntimeError("Native InvariantQ C++ core library not found")
        self._ptr = _NATIVE_LIB.iq_stabilizer_create(num_qubits)
        if not self._ptr:
            raise MemoryError("Failed to allocate Stabilizer in C++ core")

    def __del__(self):
        if hasattr(self, "_ptr") and self._ptr and HAS_NATIVE_CORE:
            _NATIVE_LIB.iq_stabilizer_free(self._ptr)
            self._ptr = None

    def reset(self):
        _NATIVE_LIB.iq_stabilizer_reset(self._ptr)

    def h(self, a: int):
        _NATIVE_LIB.iq_stabilizer_apply_h(self._ptr, a)

    def s(self, a: int):
        _NATIVE_LIB.iq_stabilizer_apply_s(self._ptr, a)

    def sdg(self, a: int):
        _NATIVE_LIB.iq_stabilizer_apply_sdg(self._ptr, a)

    def cnot(self, a: int, b: int):
        _NATIVE_LIB.iq_stabilizer_apply_cnot(self._ptr, a, b)

    def cz(self, a: int, b: int):
        _NATIVE_LIB.iq_stabilizer_apply_cz(self._ptr, a, b)

    def swap(self, a: int, b: int):
        _NATIVE_LIB.iq_stabilizer_apply_swap(self._ptr, a, b)

    def x(self, a: int):
        _NATIVE_LIB.iq_stabilizer_apply_x(self._ptr, a)

    def y(self, a: int):
        _NATIVE_LIB.iq_stabilizer_apply_y(self._ptr, a)

    def z(self, a: int):
        _NATIVE_LIB.iq_stabilizer_apply_z(self._ptr, a)

    def measure(self, a: int, rand_val: float) -> int:
        return _NATIVE_LIB.iq_stabilizer_measure(self._ptr, a, rand_val)

    def reset_qubit(self, a: int, rand_val: float = 0.0):
        _NATIVE_LIB.iq_stabilizer_reset_qubit(self._ptr, a, rand_val)

    def to_string(self) -> str:
        buf = ctypes.create_string_buffer(4096)
        _NATIVE_LIB.iq_stabilizer_to_string(self._ptr, buf, 4096)
        return buf.value.decode("utf-8")


class NativeMPS:
    # This binding owns a C++ tensor-network state, not a statevector.
    implementation = "native-cpp-mps"
    is_genuine_mps = True

    def __init__(self, num_qubits: int, max_bond_dim: int = 64, cutoff: float = 1e-12):
        self.num_qubits = num_qubits
        self.max_bond_dim = max_bond_dim
        self.cutoff = cutoff
        if not HAS_NATIVE_CORE:
            raise RuntimeError("Native InvariantQ C++ core library not found")
        self._ptr = _NATIVE_LIB.iq_mps_create(num_qubits, max_bond_dim, cutoff)
        if not self._ptr:
            raise MemoryError("Failed to allocate MPS in C++ core")

    def __del__(self):
        if hasattr(self, "_ptr") and self._ptr and HAS_NATIVE_CORE:
            _NATIVE_LIB.iq_mps_free(self._ptr)
            self._ptr = None

    def reset(self):
        _NATIVE_LIB.iq_mps_reset(self._ptr)

    def apply_1q(self, target: int, matrix: np.ndarray):
        m = np.asarray(matrix, dtype=np.complex128).flatten()
        real = np.ascontiguousarray(m.real, dtype=np.float64)
        imag = np.ascontiguousarray(m.imag, dtype=np.float64)
        _NATIVE_LIB.iq_mps_apply_1q(
            self._ptr,
            target,
            real.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
            imag.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
        )

    def apply_2q(self, q0: int, q1: int, matrix: np.ndarray):
        m = np.asarray(matrix, dtype=np.complex128).flatten()
        real = np.ascontiguousarray(m.real, dtype=np.float64)
        imag = np.ascontiguousarray(m.imag, dtype=np.float64)
        _NATIVE_LIB.iq_mps_apply_2q(
            self._ptr,
            q0,
            q1,
            real.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
            imag.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
        )

    def entanglement_entropy(self, bond_idx: int) -> float:
        return _NATIVE_LIB.iq_mps_entropy(self._ptr, bond_idx)

    def to_statevector(self) -> np.ndarray:
        dim = 1 << self.num_qubits
        real = np.empty(dim, dtype=np.float64)
        imag = np.empty(dim, dtype=np.float64)
        _NATIVE_LIB.iq_mps_to_statevector(
            self._ptr,
            real.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
            imag.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
        )
        return real + 1j * imag

    def measure(self, target: int, rand_val: float) -> int:
        return _NATIVE_LIB.iq_mps_measure(self._ptr, target, rand_val)


# The C++ core is an optional acceleration layer.  Keep the public binding
# usable on platforms where no compatible shared library was built (notably
# Windows) so that correctness does not depend on a particular compiler.
if not HAS_NATIVE_CORE:
    def _apply_unitary(state: np.ndarray, num_qubits: int, qubits: List[int], matrix: np.ndarray) -> np.ndarray:
        """Apply a matrix using the canonical little-endian qubit convention."""
        if len(set(qubits)) != len(qubits) or any(q < 0 or q >= num_qubits for q in qubits):
            raise ValueError("gate qubits must be distinct valid qubit indices")
        k = len(qubits)
        matrix = np.asarray(matrix, dtype=np.complex128)
        if matrix.shape != (1 << k, 1 << k):
            raise ValueError("gate matrix dimension does not match its qubits")
        # In Fortran order axis q corresponds to little-endian global bit q.
        # Move the targeted axes first, apply the local matrix to all remaining
        # amplitudes at once, then restore the original axis order.
        rest = [q for q in range(num_qubits) if q not in qubits]
        axes = list(qubits) + rest
        tensor = state.reshape([2] * num_qubits, order="F")
        moved = np.transpose(tensor, axes).reshape(1 << k, -1)
        transformed = (matrix @ moved).reshape([2] * num_qubits)
        inverse_axes = np.argsort(axes)
        return np.transpose(transformed, inverse_axes).reshape(-1, order="F")

    class NativeStateVector:
        def __init__(self, num_qubits: int):
            if num_qubits < 0 or num_qubits > 24:
                raise ValueError("fallback statevector supports 0 through 24 qubits")
            self.num_qubits, self.dim = num_qubits, 1 << num_qubits
            self.reset()

        def reset(self):
            self._state = np.zeros(self.dim, dtype=np.complex128)
            self._state[0] = 1.0

        def apply_1q(self, target: int, matrix: np.ndarray):
            self._state = _apply_unitary(self._state, self.num_qubits, [target], matrix)

        def apply_2q(self, q0: int, q1: int, matrix: np.ndarray):
            self._state = _apply_unitary(self._state, self.num_qubits, [q0, q1], matrix)

        def apply_fused(self, qubits: List[int], matrix: np.ndarray):
            self._state = _apply_unitary(self._state, self.num_qubits, qubits, matrix)

        def measure_prob(self, target: int, outcome: int) -> float:
            if outcome not in (0, 1):
                raise ValueError("measurement outcome must be 0 or 1")
            return float(np.sum(np.abs(self._state[[i for i in range(self.dim) if ((i >> target) & 1) == outcome]]) ** 2))

        def measure(self, target: int, rand_val: float) -> int:
            if not 0.0 <= rand_val < 1.0:
                raise ValueError("random value must be in [0, 1)")
            p0 = self.measure_prob(target, 0)
            outcome = 0 if rand_val < p0 else 1
            mask = np.array([((i >> target) & 1) == outcome for i in range(self.dim)])
            self._state[~mask] = 0
            norm = np.linalg.norm(self._state)
            if norm == 0:
                raise RuntimeError("measurement selected a zero-probability outcome")
            self._state /= norm
            return outcome

        def reset_qubit(self, target: int, rand_val: float = 0.0):
            if self.measure(target, rand_val) == 1:
                self.apply_1q(target, np.array([[0, 1], [1, 0]], dtype=np.complex128))

        def get_amplitudes(self) -> np.ndarray:
            return self._state.copy()

        def get_probabilities(self) -> np.ndarray:
            return np.abs(self._state) ** 2

        def sample(self, num_shots: int, seed: int = 42) -> np.ndarray:
            if num_shots < 0:
                raise ValueError("num_shots must be non-negative")
            return np.random.default_rng(seed).choice(self.dim, size=num_shots, p=self.get_probabilities())

        def von_neumann_entropy(self, subsystem_qubits: List[int]) -> float:
            subsystem_qubits = list(subsystem_qubits)
            if len(set(subsystem_qubits)) != len(subsystem_qubits):
                raise ValueError("subsystem qubits must be unique")
            rest = [q for q in range(self.num_qubits) if q not in subsystem_qubits]
            tensor = self._state.reshape([2] * self.num_qubits, order="F")
            matrix = np.transpose(tensor, subsystem_qubits + rest).reshape(1 << len(subsystem_qubits), -1)
            eigvals = np.linalg.eigvalsh(matrix @ matrix.conj().T)
            eigvals = eigvals[eigvals > 1e-15]
            return float(-np.sum(eigvals * np.log2(eigvals)))

        def expectation_value_pauli(self, pauli_str: str, qubits: List[int]) -> complex:
            matrices = {"I": np.eye(2), "X": np.array([[0, 1], [1, 0]]),
                        "Y": np.array([[0, -1j], [1j, 0]]), "Z": np.array([[1, 0], [0, -1]])}
            if len(pauli_str) != len(qubits) or any(p not in matrices for p in pauli_str):
                raise ValueError("invalid Pauli observable")
            operated = self._state.copy()
            for p, q in zip(pauli_str, qubits):
                operated = _apply_unitary(operated, self.num_qubits, [q], matrices[p])
            return complex(np.vdot(self._state, operated))

    class NativeDensityMatrix:
        def __init__(self, num_qubits: int):
            if num_qubits < 0 or num_qubits > 12:
                raise ValueError("fallback density matrix supports 0 through 12 qubits")
            self.num_qubits, self.dim = num_qubits, 1 << num_qubits
            self.reset()

        def reset(self):
            self._matrix = np.zeros((self.dim, self.dim), dtype=np.complex128)
            self._matrix[0, 0] = 1.0

        def _apply(self, qubits, matrix):
            # Apply U rho U† by applying U to each column, then to each row.
            left = np.column_stack([_apply_unitary(self._matrix[:, j], self.num_qubits, qubits, matrix) for j in range(self.dim)])
            self._matrix = np.vstack([_apply_unitary(left[i, :].conj(), self.num_qubits, qubits, matrix).conj() for i in range(self.dim)])

        def apply_1q_unitary(self, target, matrix): self._apply([target], matrix)
        def apply_2q_unitary(self, q0, q1, matrix): self._apply([q0, q1], matrix)
        def apply_1q_kraus(self, target, kraus_ops):
            original = self._matrix.copy()
            accumulated = np.zeros_like(original)
            for op in kraus_ops:
                self._matrix = original.copy()
                self._apply([target], op)
                accumulated += self._matrix
            self._matrix = accumulated

        def get_matrix(self): return self._matrix.copy()
        def trace(self): return float(np.real(np.trace(self._matrix)))
        def purity(self): return float(np.real(np.trace(self._matrix @ self._matrix)))
        def von_neumann_entropy(self):
            vals = np.linalg.eigvalsh(self._matrix)
            vals = vals[vals > 1e-15]
            return float(-np.sum(vals * np.log2(vals)))
        def measure(self, target, rand_val):
            p0 = float(sum(self._matrix[i, i].real for i in range(self.dim) if not ((i >> target) & 1)))
            outcome = 0 if rand_val < p0 else 1
            keep = np.array([((i >> target) & 1) == outcome for i in range(self.dim)])
            self._matrix[~keep, :] = self._matrix[:, ~keep] = 0
            self._matrix /= (p0 if outcome == 0 else 1 - p0)
            return outcome
        def reset_qubit(self, target):
            if self.measure(target, 0.0) == 1:
                self.apply_1q_unitary(target, np.array([[0, 1], [1, 0]], dtype=np.complex128))

    class NativeMPS:
        """A portable NumPy matrix-product-state engine.

        The state is a chain of rank-three tensors with layout ``(Dl, 2,
        Dr)``.  It is intentionally independent of ``NativeStateVector``:
        dense statevectors are only constructed by the explicitly guarded
        ``to_statevector`` diagnostic export for small differential tests.

        Site ``i`` is canonical little-endian qubit ``i``.  Therefore
        ``apply_2q(q0, q1, U)`` uses a matrix whose local row/column index is
        ``2 * bit(q0) + bit(q1)``, matching the portable statevector binding.
        """

        implementation = "python-mps"
        is_genuine_mps = True
        supports_dense_statevector_export = True
        MAX_STATEVECTOR_EXPORT_QUBITS = 20
        _SWAP = np.array(
            [[1, 0, 0, 0],
             [0, 0, 1, 0],
             [0, 1, 0, 0],
             [0, 0, 0, 1]],
            dtype=np.complex128,
        )

        def __init__(self, num_qubits: int, max_bond_dim: int = 64, cutoff: float = 1e-12):
            if not isinstance(num_qubits, (int, np.integer)) or num_qubits < 1:
                raise ValueError("MPS requires at least one qubit")
            if not isinstance(max_bond_dim, (int, np.integer)) or max_bond_dim < 1:
                raise ValueError("max_bond_dim must be a positive integer")
            if not np.isfinite(cutoff) or cutoff < 0:
                raise ValueError("cutoff must be a finite non-negative number")
            self.num_qubits = int(num_qubits)
            self.max_bond_dim = int(max_bond_dim)
            self.cutoff = float(cutoff)
            self.reset()

        def reset(self):
            """Reset to |0...0> without allocating a dense vector."""
            self.tensors = []
            for _ in range(self.num_qubits):
                tensor = np.zeros((1, 2, 1), dtype=np.complex128)
                tensor[0, 0, 0] = 1.0
                self.tensors.append(tensor)
            self.discarded_weight = 0.0
            self.last_discarded_weight = 0.0
            self.truncation_events = 0
            self._max_observed_bond_dimension = 1

        @property
        def site_tensors(self):
            """A read-only view of the actual rank-three site tensors."""
            views = []
            for tensor in self.tensors:
                view = tensor.view()
                view.flags.writeable = False
                views.append(view)
            return tuple(views)

        @property
        def bond_dimensions(self):
            """One internal dimension for every cut between adjacent sites."""
            return tuple(int(tensor.shape[2]) for tensor in self.tensors[:-1])

        @property
        def max_observed_bond_dimension(self) -> int:
            return self._max_observed_bond_dimension

        @property
        def memory_bytes(self) -> int:
            """Bytes currently held by the MPS site tensors."""
            return int(sum(tensor.nbytes for tensor in self.tensors))

        @property
        def is_approximate(self) -> bool:
            return bool(self.discarded_weight > 0.0)

        def get_bond_dimensions(self):
            return list(self.bond_dimensions)

        def get_diagnostics(self) -> dict:
            """Expose real representation and approximation information."""
            return {
                "implementation": self.implementation,
                "is_genuine_mps": self.is_genuine_mps,
                "representation": "rank-3 site tensors (Dl, 2, Dr)",
                "num_qubits": self.num_qubits,
                "bond_dimensions": list(self.bond_dimensions),
                "max_bond_dimension": self.max_bond_dim,
                "max_observed_bond_dimension": self.max_observed_bond_dimension,
                "cutoff": self.cutoff,
                "truncation_events": self.truncation_events,
                "discarded_weight": float(self.discarded_weight),
                "last_discarded_weight": float(self.last_discarded_weight),
                "exact": not self.is_approximate,
                "tensor_memory_bytes": self.memory_bytes,
                "dense_statevector_allocated": False,
                "statevector_export_limit_qubits": self.MAX_STATEVECTOR_EXPORT_QUBITS,
            }

        def validate(self, atol: float = 1e-10) -> bool:
            """Validate boundaries, bond shapes, finiteness, and normalization."""
            if len(self.tensors) != self.num_qubits:
                return False
            previous_right = 1
            for index, tensor in enumerate(self.tensors):
                if tensor.ndim != 3 or tensor.shape[1] != 2:
                    return False
                if tensor.shape[0] != previous_right or not np.isfinite(tensor).all():
                    return False
                previous_right = tensor.shape[2]
                if index < self.num_qubits - 1 and previous_right > self.max_bond_dim:
                    return False
            if previous_right != 1:
                return False
            return bool(np.isclose(self._state_norm(), 1.0, atol=atol, rtol=atol))

        @staticmethod
        def _validate_unitary(matrix: np.ndarray, arity: int) -> np.ndarray:
            matrix = np.asarray(matrix, dtype=np.complex128)
            dimension = 1 << arity
            if matrix.shape != (dimension, dimension):
                raise ValueError(f"{arity}-qubit gate matrix must have shape ({dimension}, {dimension})")
            if not np.isfinite(matrix).all():
                raise ValueError("gate matrix must contain only finite values")
            if not np.allclose(
                matrix.conj().T @ matrix,
                np.eye(dimension, dtype=np.complex128),
                atol=1e-10,
                rtol=1e-10,
            ):
                raise ValueError("MPS backend accepts only unitary gate matrices")
            return matrix

        def _check_qubit(self, target: int):
            if not isinstance(target, (int, np.integer)) or not 0 <= int(target) < self.num_qubits:
                raise ValueError(f"qubit index {target!r} is out of range")

        def apply_1q(self, target: int, matrix: np.ndarray):
            self._check_qubit(target)
            matrix = self._validate_unitary(matrix, 1)
            target = int(target)
            self.tensors[target] = np.einsum(
                "oi,lir->lor", matrix, self.tensors[target], optimize=True
            )

        def _apply_2q_adjacent(self, left_site: int, matrix: np.ndarray):
            """Apply a local two-site gate, then split with a truncated SVD."""
            norm_before = self._state_norm()
            left = self.tensors[left_site]
            right = self.tensors[left_site + 1]
            dl, _, middle = left.shape
            right_middle, _, dr = right.shape
            if middle != right_middle:
                raise RuntimeError("inconsistent adjacent MPS bond dimensions")

            # theta[l, a, b, r] stores the two physical indices a and b.
            theta = np.einsum("lar,rbs->labs", left, right, optimize=True)
            unitary = matrix.reshape(2, 2, 2, 2)
            theta = np.einsum("ABab,labr->lABr", unitary, theta, optimize=True)
            unfolded = theta.reshape(dl * 2, 2 * dr)
            try:
                u, singular_values, vh = np.linalg.svd(unfolded, full_matrices=False)
            except np.linalg.LinAlgError as exc:
                raise RuntimeError("MPS two-site SVD did not converge") from exc

            total_weight = float(np.sum(np.square(singular_values)))
            if not np.isfinite(total_weight) or total_weight <= 0.0:
                raise RuntimeError("MPS state became zero or non-finite during a two-site update")

            # ``cutoff`` is an absolute singular-value threshold.  The machine
            # floor avoids retaining artificial bonds when cutoff=0.
            numerical_floor = np.finfo(np.float64).eps * max(unfolded.shape) * singular_values[0]
            by_cutoff = int(np.count_nonzero(singular_values > max(self.cutoff, numerical_floor)))
            keep = max(1, min(self.max_bond_dim, by_cutoff, len(singular_values)))
            kept_weight = float(np.sum(np.square(singular_values[:keep])))
            discarded = max(0.0, total_weight - kept_weight)
            # Do not rescale an exact SVD.  A local tensor is not necessarily
            # in a canonical gauge, so its Frobenius norm is not in general
            # the global state norm.  Rescaling it on every exact gate would
            # silently corrupt amplitudes after non-adjacent SWAP paths.
            material_truncation = (discarded / total_weight) > 1e-15
            retained_s = singular_values[:keep]
            self.tensors[left_site] = u[:, :keep].reshape(dl, 2, keep)
            self.tensors[left_site + 1] = (retained_s[:, None] * vh[:keep, :]).reshape(keep, 2, dr)
            self._max_observed_bond_dimension = max(self._max_observed_bond_dimension, keep)

            self.last_discarded_weight = 0.0
            if material_truncation:
                norm_after = self._state_norm()
                if not np.isfinite(norm_after) or norm_after <= 0.0:
                    raise RuntimeError("MPS truncation retained a zero-norm state")
                # Measure error in the represented global norm rather than
                # treating a gauge-dependent local SVD norm as an error bound.
                self.last_discarded_weight = max(0.0, (norm_before - norm_after) / norm_before)
                self.discarded_weight += self.last_discarded_weight
                self.truncation_events += 1
                # Return to a normalized pure-state representation.  The
                # discarded norm remains available as an explicit diagnostic.
                self.tensors[left_site + 1] /= np.sqrt(norm_after)

        def apply_2q(self, q0: int, q1: int, matrix: np.ndarray):
            """Apply any two-qubit unitary through an explicit reversible SWAP path."""
            self._check_qubit(q0)
            self._check_qubit(q1)
            if int(q0) == int(q1):
                raise ValueError("two-qubit gate targets must be distinct")
            matrix = self._validate_unitary(matrix, 2)
            q0, q1 = int(q0), int(q1)

            if q0 + 1 == q1:
                self._apply_2q_adjacent(q0, matrix)
                return
            if q1 + 1 == q0:
                # Physical site order is (q1, q0), but the matrix was supplied
                # in explicit argument order (q0, q1).
                self._apply_2q_adjacent(q1, self._SWAP @ matrix @ self._SWAP)
                return

            if q0 < q1:
                # Move logical q1 left to q0 + 1, act, then restore ordering.
                for site in range(q1 - 1, q0, -1):
                    self._apply_2q_adjacent(site, self._SWAP)
                self._apply_2q_adjacent(q0, matrix)
                for site in range(q0 + 1, q1):
                    self._apply_2q_adjacent(site, self._SWAP)
            else:
                # Move logical q0 right to q1 + 1.  At the local gate the
                # physical ordering is reversed, hence SWAP U SWAP.
                for site in range(q0 - 1, q1, -1):
                    self._apply_2q_adjacent(site, self._SWAP)
                self._apply_2q_adjacent(q1, self._SWAP @ matrix @ self._SWAP)
                for site in range(q1 + 1, q0):
                    self._apply_2q_adjacent(site, self._SWAP)

        def _left_gram(self, final_site: int) -> np.ndarray:
            """Gram matrix for the prefix ending at ``final_site``."""
            gram = np.ones((1, 1), dtype=np.complex128)
            for tensor in self.tensors[: final_site + 1]:
                gram = np.einsum("ab,asr,bst->rt", gram, tensor.conj(), tensor, optimize=True)
            return gram

        def _right_gram(self, first_site: int) -> np.ndarray:
            """Gram matrix for the suffix starting at ``first_site``."""
            gram = np.ones((1, 1), dtype=np.complex128)
            for tensor in reversed(self.tensors[first_site:]):
                gram = np.einsum("asr,rt,bst->ab", tensor, gram, tensor.conj(), optimize=True)
            return gram

        def _right_grams(self):
            """Suffix Gram matrices at every virtual bond for direct sampling."""
            grams = [None] * (self.num_qubits + 1)
            grams[self.num_qubits] = np.ones((1, 1), dtype=np.complex128)
            for site in range(self.num_qubits - 1, -1, -1):
                tensor = self.tensors[site]
                grams[site] = np.einsum(
                    "asr,rt,bst->ab", tensor, grams[site + 1], tensor.conj(), optimize=True
                )
            return grams

        def _state_norm(self) -> float:
            norm = self._left_gram(self.num_qubits - 1)[0, 0]
            return float(np.real_if_close(norm).real)

        def measure_probability(self, target: int, outcome: int) -> float:
            self._check_qubit(target)
            if outcome not in (0, 1):
                raise ValueError("measurement outcome must be 0 or 1")
            target = int(target)
            left = np.ones((1, 1), dtype=np.complex128) if target == 0 else self._left_gram(target - 1)
            right = self._right_gram(target + 1)
            site = self.tensors[target][:, outcome, :]
            raw = np.einsum("ab,ar,bt,rt->", left, site.conj(), site, right, optimize=True)
            total = self._state_norm()
            if total <= 0.0 or not np.isfinite(total):
                raise RuntimeError("MPS state has invalid norm")
            probability = float(np.real_if_close(raw).real / total)
            if probability < -1e-10 or probability > 1.0 + 1e-10:
                raise RuntimeError("MPS measurement produced an invalid probability")
            return float(np.clip(probability, 0.0, 1.0))

        def measure(self, target: int, rand_val: float) -> int:
            """Project a qubit in-place using local tensor contractions only."""
            self._check_qubit(target)
            if not np.isfinite(rand_val) or not 0.0 <= float(rand_val) < 1.0:
                raise ValueError("random value must be in [0, 1)")
            target = int(target)
            old_norm = self._state_norm()
            p0 = self.measure_probability(target, 0)
            outcome = 0 if float(rand_val) < p0 else 1
            selected_probability = p0 if outcome == 0 else 1.0 - p0
            selected_weight = selected_probability * old_norm
            if selected_weight <= 1e-15:
                raise RuntimeError("measurement selected a zero-probability outcome")
            tensor = self.tensors[target].copy()
            tensor[:, 1 - outcome, :] = 0.0
            tensor[:, outcome, :] /= np.sqrt(selected_weight)
            self.tensors[target] = tensor
            return outcome

        def reset_qubit(self, target: int, rand_val: float = 0.0):
            if self.measure(target, rand_val) == 1:
                self.apply_1q(target, np.array([[0, 1], [1, 0]], dtype=np.complex128))

        def _sample_one(self, rng: np.random.Generator, right_grams=None) -> str:
            """Sample all sites without mutation or dense reconstruction."""
            if right_grams is None:
                right_grams = self._right_grams()
            left = np.ones((1, 1), dtype=np.complex128)
            bits_little_endian = []
            for site_index, tensor in enumerate(self.tensors):
                right = right_grams[site_index + 1]
                raw_probabilities = []
                for outcome in (0, 1):
                    site = tensor[:, outcome, :]
                    raw = np.einsum("ab,ar,bt,rt->", left, site.conj(), site, right, optimize=True)
                    raw_probabilities.append(max(0.0, float(np.real_if_close(raw).real)))
                total = raw_probabilities[0] + raw_probabilities[1]
                if not np.isfinite(total) or total <= 0.0:
                    raise RuntimeError("MPS sampling encountered an invalid conditional norm")
                p0 = raw_probabilities[0] / total
                outcome = 0 if rng.random() < p0 else 1
                selected = raw_probabilities[outcome]
                if selected <= 0.0:
                    outcome = 1 - outcome
                    selected = raw_probabilities[outcome]
                site = tensor[:, outcome, :]
                left = np.einsum("ab,ar,bt->rt", left, site.conj(), site, optimize=True) / selected
                bits_little_endian.append(str(outcome))
            # Public bitstrings follow normal integer formatting q[n-1]...q[0].
            return "".join(reversed(bits_little_endian))

        def sample_bitstrings(self, num_shots: int, seed: int = 42):
            if not isinstance(num_shots, (int, np.integer)) or num_shots < 0:
                raise ValueError("num_shots must be a non-negative integer")
            rng = np.random.default_rng(seed)
            # The MPS does not mutate while sampling, so suffix environments
            # can be shared by every shot.  This avoids an O(shots * n)
            # rebuild of identical environments without using a statevector.
            right_grams = self._right_grams()
            return [self._sample_one(rng, right_grams) for _ in range(int(num_shots))]

        def sample(self, num_shots: int, seed: int = 42) -> np.ndarray:
            """Statevector-compatible samples without allocating a vector."""
            bitstrings = self.sample_bitstrings(num_shots, seed)
            if self.num_qubits <= 63:
                return np.asarray([int(bits, 2) for bits in bitstrings], dtype=np.uint64)
            return np.asarray(bitstrings, dtype=object)

        def entanglement_entropy(self, bond_idx: int) -> float:
            """Entropy across one cut using only bond-dimension Gram matrices."""
            if self.num_qubits < 2:
                return 0.0
            if not isinstance(bond_idx, (int, np.integer)) or not 0 <= int(bond_idx) < self.num_qubits - 1:
                raise ValueError("bond index must identify a cut between adjacent sites")
            left = self._left_gram(int(bond_idx))
            right = self._right_gram(int(bond_idx) + 1)
            left = (left + left.conj().T) / 2.0
            right = (right + right.conj().T) / 2.0
            values, vectors = np.linalg.eigh(left)
            values = np.clip(values.real, 0.0, None)
            sqrt_left = (vectors * np.sqrt(values)) @ vectors.conj().T
            spectrum = np.linalg.eigvalsh(sqrt_left @ right @ sqrt_left)
            spectrum = np.clip(spectrum.real, 0.0, None)
            trace = float(np.sum(spectrum))
            if trace <= 0.0:
                raise RuntimeError("MPS state has zero norm while calculating entropy")
            spectrum /= trace
            spectrum = spectrum[spectrum > 1e-15]
            return float(-np.sum(spectrum * np.log2(spectrum)))

        def to_statevector(self) -> np.ndarray:
            """Export a small MPS for differential tests, in little-endian order."""
            if self.num_qubits > self.MAX_STATEVECTOR_EXPORT_QUBITS:
                raise ValueError(
                    f"dense statevector export is limited to {self.MAX_STATEVECTOR_EXPORT_QUBITS} qubits; "
                    "use sample_bitstrings() or MPS diagnostics for scalable execution"
                )
            contracted = self.tensors[0][0, :, :]
            for tensor in self.tensors[1:]:
                contracted = np.tensordot(contracted, tensor, axes=([-1], [0]))
            state_tensor = np.asarray(contracted[..., 0], dtype=np.complex128)
            return state_tensor.reshape(-1, order="F").copy()

        # Small-system compatibility helpers.  No dense representation is
        # cached or used for gate application, measurement, or sampling.
        def get_amplitudes(self) -> np.ndarray:
            return self.to_statevector()

        def get_probabilities(self) -> np.ndarray:
            statevector = self.to_statevector()
            return np.abs(statevector) ** 2

    class NativeStabilizer:
        """Portable Aaronson--Gottesman binary tableau simulator.

        Rows ``0..n-1`` are destabilizers and rows ``n..2n-1`` are
        stabilizers.  This stores O(n^2) bits and never materializes a state
        vector; it deliberately exposes only Clifford operations.
        """
        implementation = "python-binary-tableau"
        is_genuine_tableau = True

        def __init__(self, num_qubits: int):
            if num_qubits < 0:
                raise ValueError("num_qubits must be non-negative")
            self.num_qubits = num_qubits
            self.reset()

        def reset(self):
            n = self.num_qubits
            self._x = np.zeros((2 * n, n), dtype=np.uint8)
            self._z = np.zeros((2 * n, n), dtype=np.uint8)
            self._r = np.zeros(2 * n, dtype=np.uint8)
            if n:
                idx = np.arange(n)
                self._x[idx, idx] = 1
                self._z[n + idx, idx] = 1

        def copy(self):
            other = type(self).__new__(type(self))
            other.num_qubits = self.num_qubits
            other._x, other._z, other._r = self._x.copy(), self._z.copy(), self._r.copy()
            return other

        @property
        def tableau_memory_bytes(self) -> int:
            return int(self._x.nbytes + self._z.nbytes + self._r.nbytes)

        def _check_qubit(self, q: int):
            if not isinstance(q, (int, np.integer)) or q < 0 or q >= self.num_qubits:
                raise IndexError(f"qubit index {q!r} is outside [0, {self.num_qubits})")

        @staticmethod
        def _g(x1: int, z1: int, x2: int, z2: int) -> int:
            # The tableau represents each Pauli as i**r X**x Z**z.
            # Multiplication contributes (-1)**(z1*x2), i.e. two units
            # in the quarter-turn phase exponent.  Keeping this primitive
            # in the same representation for every row operation avoids
            # lookup-table sign drift during random measurements.
            return 2 * (z1 & x2)

        def _row_mult(self, target: int, source: int):
            total = 2 * int(self._r[target]) + 2 * int(self._r[source])
            for q in range(self.num_qubits):
                total += self._g(int(self._x[target, q]), int(self._z[target, q]),
                                 int(self._x[source, q]), int(self._z[source, q]))
            total %= 4
            if total not in (0, 2):
                raise RuntimeError("invalid non-commuting tableau row multiplication")
            self._r[target] = total // 2
            self._x[target] ^= self._x[source]
            self._z[target] ^= self._z[source]

        def h(self, a: int):
            self._check_qubit(a)
            self._r ^= self._x[:, a] & self._z[:, a]
            self._x[:, a], self._z[:, a] = self._z[:, a].copy(), self._x[:, a].copy()

        def s(self, a: int):
            self._check_qubit(a)
            self._r ^= self._x[:, a] & self._z[:, a]
            self._z[:, a] ^= self._x[:, a]

        def sdg(self, a: int):
            self.s(a)
            self.s(a)
            self.s(a)

        def cnot(self, a: int, b: int):
            self._check_qubit(a)
            self._check_qubit(b)
            if a == b:
                raise ValueError("CNOT control and target must differ")
            xa, za = self._x[:, a].copy(), self._z[:, a].copy()
            xb, zb = self._x[:, b].copy(), self._z[:, b].copy()
            self._r ^= xa & zb & (xb ^ za ^ 1)
            self._x[:, b] ^= xa
            self._z[:, a] ^= zb

        def cz(self, a: int, b: int):
            self._check_qubit(a)
            self._check_qubit(b)
            if a == b:
                raise ValueError("CZ operands must differ")
            self.h(b)
            self.cnot(a, b)
            self.h(b)

        def swap(self, a: int, b: int):
            self._check_qubit(a)
            self._check_qubit(b)
            if a == b:
                raise ValueError("SWAP operands must differ")
            self.cnot(a, b)
            self.cnot(b, a)
            self.cnot(a, b)

        def x_gate(self, a: int):
            self.h(a)
            self.z_gate(a)
            self.h(a)

        def z_gate(self, a: int):
            self._check_qubit(a)
            self._r ^= self._x[:, a]

        def y_gate(self, a: int):
            self.z_gate(a)
            self.x_gate(a)

        # Preserve the native wrapper method names.
        x = x_gate
        y = y_gate
        z = z_gate

        def measure(self, a: int, rand_val: float) -> int:
            self._check_qubit(a)
            if not 0.0 <= rand_val < 1.0:
                raise ValueError("random value must be in [0, 1)")
            n = self.num_qubits
            pivots = np.flatnonzero(self._x[n:, a])
            if pivots.size:
                p = n + int(pivots[0])
                for row in range(2 * n):
                    if row != p and self._x[row, a]:
                        self._row_mult(row, p)
                self._x[p - n] = self._x[p]
                self._z[p - n] = self._z[p]
                self._r[p - n] = self._r[p]
                self._x[p].fill(0)
                self._z[p].fill(0)
                self._z[p, a] = 1
                outcome = 0 if rand_val < 0.5 else 1
                self._r[p] = outcome
                return outcome

            # Deterministic measurement: product of stabilizers selected by
            # destabilizers that anticommute with Z_a.
            acc_x = np.zeros(n, dtype=np.uint8)
            acc_z = np.zeros(n, dtype=np.uint8)
            acc_r = 0
            for i in range(n):
                if not self._x[i, a]:
                    continue
                src = n + i
                total = 2 * acc_r + 2 * int(self._r[src])
                for q in range(n):
                    total += self._g(int(acc_x[q]), int(acc_z[q]), int(self._x[src, q]), int(self._z[src, q]))
                total %= 4
                if total not in (0, 2):
                    raise RuntimeError("invalid deterministic measurement tableau product")
                acc_r = total // 2
                acc_x ^= self._x[src]
                acc_z ^= self._z[src]
            return int(acc_r)

        def reset_qubit(self, a: int, rand_val: float = 0.0):
            if self.measure(a, rand_val):
                self.x_gate(a)

        def sample(self, num_shots: int, seed: int = 42) -> np.ndarray:
            if num_shots < 0:
                raise ValueError("num_shots must be non-negative")
            rng = np.random.default_rng(seed)
            # Python integers preserve outcomes wider than 64 qubits.
            samples = np.empty(num_shots, dtype=object)
            for shot in range(num_shots):
                tableau = self.copy()
                value = 0
                for q in range(self.num_qubits):
                    value |= tableau.measure(q, float(rng.random())) << q
                samples[shot] = value
            return samples

        def to_string(self) -> str:
            labels = ("I", "Z", "X", "Y")
            rows = []
            for row in range(self.num_qubits, 2 * self.num_qubits):
                sign = "-" if self._r[row] else "+"
                body = "".join(labels[int(self._x[row, q]) * 2 + int(self._z[row, q])] for q in range(self.num_qubits))
                rows.append(sign + body)
            return "Stabilizers:\n" + "\n".join(rows)
