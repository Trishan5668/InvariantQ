"""
InvariantQ Native C++ Core Bindings via ctypes with NumPy/Pure-Python fallback.
"""

from __future__ import annotations
import ctypes
import os
import sys
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
for directory in _LIB_DIRS:
    lib_path = directory / "libinvariantq.so"
    if lib_path.exists():
        try:
            _NATIVE_LIB = ctypes.CDLL(str(lib_path))
            break
        except Exception as e:
            pass

HAS_NATIVE_CORE = _NATIVE_LIB is not None

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
