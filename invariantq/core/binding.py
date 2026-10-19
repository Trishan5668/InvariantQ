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

    class NativeMPS(NativeStateVector):
        def __init__(self, num_qubits, max_bond_dim=64, cutoff=1e-12):
            self.max_bond_dim, self.cutoff = max_bond_dim, cutoff
            super().__init__(num_qubits)
        def entanglement_entropy(self, bond_idx): return self.von_neumann_entropy(list(range(bond_idx + 1)))
        def to_statevector(self): return self.get_amplitudes()

    class NativeStabilizer(NativeStateVector):
        def h(self, a): self.apply_1q(a, np.array([[1, 1], [1, -1]], dtype=np.complex128) / np.sqrt(2))
        def s(self, a): self.apply_1q(a, np.diag([1, 1j]))
        def sdg(self, a): self.apply_1q(a, np.diag([1, -1j]))
        def x(self, a): self.apply_1q(a, np.array([[0, 1], [1, 0]], dtype=np.complex128))
        def y(self, a): self.apply_1q(a, np.array([[0, -1j], [1j, 0]], dtype=np.complex128))
        def z(self, a): self.apply_1q(a, np.diag([1, -1]))
        def cnot(self, a, b): self.apply_2q(a, b, np.array([[1,0,0,0],[0,1,0,0],[0,0,0,1],[0,0,1,0]], dtype=np.complex128))
        def cz(self, a, b): self.apply_2q(a, b, np.diag([1,1,1,-1]))
        def swap(self, a, b): self.apply_2q(a, b, np.array([[1,0,0,0],[0,0,1,0],[0,1,0,0],[0,0,0,1]], dtype=np.complex128))
        def to_string(self): return "python-statevector fallback"
