"""Versioned wire protocol for local distributed workers.

The local worker pool deliberately sends JSON rather than Python objects over
its process queues.  That keeps the process boundary honest, makes payloads
inspectable, and gives the scheduler a single place to reject malformed work
before it reaches a simulator.
"""

from __future__ import annotations

import json
import math
from typing import Any, Dict, Iterable, List, Mapping

import numpy as np

from ..ir.qir import (
    BarrierOp,
    CircuitIR,
    CWire,
    FusedGateOp,
    GateOp,
    MeasureOp,
    QWire,
    ResetOp,
)


TASK_SCHEMA = "invariantq.distributed.task"
RESULT_SCHEMA = "invariantq.distributed.result"
PROTOCOL_VERSION = 1


class ProtocolValidationError(ValueError):
    """Raised when a worker protocol payload is invalid or unsupported."""


def _mapping(value: Any, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ProtocolValidationError(f"{label} must be an object")
    return value


def _text(value: Any, label: str, *, allow_empty: bool = False) -> str:
    if not isinstance(value, str) or (not allow_empty and not value):
        raise ProtocolValidationError(f"{label} must be a non-empty string")
    return value


def _integer(value: Any, label: str, *, minimum: int | None = None) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ProtocolValidationError(f"{label} must be an integer")
    if minimum is not None and value < minimum:
        raise ProtocolValidationError(f"{label} must be at least {minimum}")
    return value


def _finite_number(value: Any, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ProtocolValidationError(f"{label} must be a finite number")
    value = float(value)
    if not math.isfinite(value):
        raise ProtocolValidationError(f"{label} must be finite")
    return value


def _json_value(value: Any, label: str) -> Any:
    try:
        # Round-tripping also normalizes tuples and NumPy scalar values that
        # a caller may have placed in otherwise ordinary metadata.
        return json.loads(json.dumps(value, allow_nan=False))
    except (TypeError, ValueError) as exc:
        raise ProtocolValidationError(f"{label} is not JSON serializable") from exc


def _wire_to_dict(wire: QWire | CWire) -> Dict[str, Any]:
    return {"name": wire.name, "index": int(wire.index)}


def _wire_from_dict(payload: Any, label: str, wire_type: type[QWire] | type[CWire]):
    obj = _mapping(payload, label)
    return wire_type(
        _text(obj.get("name"), f"{label}.name"),
        _integer(obj.get("index"), f"{label}.index", minimum=0),
    )


def _matrix_to_data(matrix: Any, label: str) -> List[List[List[float]]]:
    try:
        arr = np.asarray(matrix, dtype=np.complex128)
    except (TypeError, ValueError) as exc:
        raise ProtocolValidationError(f"{label} is not a complex matrix") from exc
    if arr.ndim != 2 or arr.shape[0] != arr.shape[1] or arr.shape[0] == 0:
        raise ProtocolValidationError(f"{label} must be a non-empty square matrix")
    if not np.isfinite(arr).all():
        raise ProtocolValidationError(f"{label} contains non-finite values")
    return [
        [[float(value.real), float(value.imag)] for value in row]
        for row in arr
    ]


def _matrix_from_data(payload: Any, label: str) -> np.ndarray:
    if not isinstance(payload, list) or not payload:
        raise ProtocolValidationError(f"{label} must be a non-empty matrix array")
    size = len(payload)
    rows: List[List[complex]] = []
    for row_index, row in enumerate(payload):
        if not isinstance(row, list) or len(row) != size:
            raise ProtocolValidationError(f"{label} must be square")
        parsed_row: List[complex] = []
        for col_index, value in enumerate(row):
            if not isinstance(value, list) or len(value) != 2:
                raise ProtocolValidationError(
                    f"{label}[{row_index}][{col_index}] must be [real, imag]"
                )
            parsed_row.append(
                complex(
                    _finite_number(value[0], f"{label}[{row_index}][{col_index}][0]"),
                    _finite_number(value[1], f"{label}[{row_index}][{col_index}][1]"),
                )
            )
        rows.append(parsed_row)
    return np.asarray(rows, dtype=np.complex128)


def _is_unitary(matrix: np.ndarray) -> bool:
    return bool(
        np.allclose(
            matrix.conj().T @ matrix,
            np.eye(matrix.shape[0], dtype=np.complex128),
            atol=1e-10,
            rtol=1e-10,
        )
    )


def _serialize_operation(op: Any) -> Dict[str, Any]:
    common = {
        "id": _integer(op.id, "operation.id", minimum=0),
        "metadata": _json_value(op.metadata, "operation.metadata"),
    }
    if isinstance(op, GateOp):
        return {
            **common,
            "type": "gate",
            "name": _text(op.name, "gate.name"),
            "params": [_finite_number(value, "gate.params") for value in op.params],
            "qubits": [_wire_to_dict(wire) for wire in op.qubits],
            "matrix": _matrix_to_data(op.matrix, "gate.matrix"),
        }
    if isinstance(op, FusedGateOp):
        return {
            **common,
            "type": "fused_gate",
            "qubits": [_wire_to_dict(wire) for wire in op.qubits],
            "matrix": _matrix_to_data(op.fused_matrix, "fused_gate.matrix"),
        }
    if isinstance(op, MeasureOp):
        return {
            **common,
            "type": "measure",
            "qubit": _wire_to_dict(op.qubit),
            "clbit": _wire_to_dict(op.clbit),
        }
    if isinstance(op, ResetOp):
        return {
            **common,
            "type": "reset",
            "qubit": _wire_to_dict(op.qubit),
        }
    if isinstance(op, BarrierOp):
        return {
            **common,
            "type": "barrier",
            "qubits": [_wire_to_dict(wire) for wire in op.qubits],
        }
    raise ProtocolValidationError(
        f"distributed statevector workers do not support {type(op).__name__}"
    )


def _deserialize_operation(payload: Any):
    obj = _mapping(payload, "operation")
    operation_type = _text(obj.get("type"), "operation.type")
    operation_id = _integer(obj.get("id"), "operation.id", minimum=0)
    metadata = _json_value(obj.get("metadata", {}), "operation.metadata")
    if not isinstance(metadata, dict):
        raise ProtocolValidationError("operation.metadata must be an object")

    if operation_type == "gate":
        params = obj.get("params", [])
        if not isinstance(params, list):
            raise ProtocolValidationError("gate.params must be an array")
        qubits = obj.get("qubits")
        if not isinstance(qubits, list) or not qubits:
            raise ProtocolValidationError("gate.qubits must be a non-empty array")
        op = GateOp(
            id=operation_id,
            name=_text(obj.get("name"), "gate.name"),
            params=[_finite_number(value, "gate.params") for value in params],
            qubits=[_wire_from_dict(item, "gate.qubit", QWire) for item in qubits],
            metadata=metadata,
            matrix=_matrix_from_data(obj.get("matrix"), "gate.matrix"),
        )
        return op
    if operation_type == "fused_gate":
        qubits = obj.get("qubits")
        if not isinstance(qubits, list) or not qubits:
            raise ProtocolValidationError("fused_gate.qubits must be a non-empty array")
        return FusedGateOp(
            id=operation_id,
            qubits=[_wire_from_dict(item, "fused_gate.qubit", QWire) for item in qubits],
            metadata=metadata,
            fused_matrix=_matrix_from_data(obj.get("matrix"), "fused_gate.matrix"),
        )
    if operation_type == "measure":
        return MeasureOp(
            id=operation_id,
            qubit=_wire_from_dict(obj.get("qubit"), "measure.qubit", QWire),
            clbit=_wire_from_dict(obj.get("clbit"), "measure.clbit", CWire),
            metadata=metadata,
        )
    if operation_type == "reset":
        return ResetOp(
            id=operation_id,
            qubit=_wire_from_dict(obj.get("qubit"), "reset.qubit", QWire),
            metadata=metadata,
        )
    if operation_type == "barrier":
        qubits = obj.get("qubits", [])
        if not isinstance(qubits, list):
            raise ProtocolValidationError("barrier.qubits must be an array")
        return BarrierOp(
            id=operation_id,
            qubits=[_wire_from_dict(item, "barrier.qubit", QWire) for item in qubits],
            metadata=metadata,
        )
    raise ProtocolValidationError(f"unsupported distributed operation type {operation_type!r}")


def _validate_wires(circuit: CircuitIR) -> None:
    def check_qwire(wire: QWire) -> None:
        if wire.name not in circuit.qubit_regs:
            raise ProtocolValidationError(f"unknown qubit register {wire.name!r}")
        if not 0 <= wire.index < circuit.qubit_regs[wire.name]:
            raise ProtocolValidationError(f"qubit index out of range: {wire}")

    def check_cwire(wire: CWire) -> None:
        if wire.name not in circuit.clbit_regs:
            raise ProtocolValidationError(f"unknown classical register {wire.name!r}")
        if not 0 <= wire.index < circuit.clbit_regs[wire.name]:
            raise ProtocolValidationError(f"classical index out of range: {wire}")

    measurements_started = False
    for op in circuit.ops:
        if isinstance(op, MeasureOp):
            measurements_started = True
            check_qwire(op.qubit)
            check_cwire(op.clbit)
            continue
        if measurements_started and not isinstance(op, BarrierOp):
            raise ProtocolValidationError(
                "distributed workers only support terminal measurements; "
                "mid-circuit measurement is unsupported"
            )
        for wire in op.qubits:
            check_qwire(wire)
        for wire in op.clbits:
            check_cwire(wire)
        if isinstance(op, (GateOp, FusedGateOp)):
            matrix = op.matrix if isinstance(op, GateOp) else op.fused_matrix
            expected_dimension = 1 << len(op.qubits)
            arr = np.asarray(matrix, dtype=np.complex128)
            if arr.shape != (expected_dimension, expected_dimension):
                raise ProtocolValidationError(
                    f"{type(op).__name__} matrix dimension does not match its qubits"
                )
            if not _is_unitary(arr):
                raise ProtocolValidationError(f"{type(op).__name__} matrix is not unitary")


def circuit_to_dict(circuit: CircuitIR) -> Dict[str, Any]:
    if not isinstance(circuit, CircuitIR):
        raise ProtocolValidationError("task.circuit must be a CircuitIR")
    if circuit.num_qubits <= 0:
        raise ProtocolValidationError("distributed circuits must contain at least one qubit")
    payload = {
        "name": _text(circuit.name, "circuit.name", allow_empty=True),
        "qubit_registers": [
            {"name": _text(name, "qubit_register.name"), "size": _integer(size, "qubit_register.size", minimum=1)}
            for name, size in circuit.qubit_regs.items()
        ],
        "classical_registers": [
            {"name": _text(name, "classical_register.name"), "size": _integer(size, "classical_register.size", minimum=1)}
            for name, size in circuit.clbit_regs.items()
        ],
        "operations": [_serialize_operation(op) for op in circuit.ops],
    }
    # Validate the same representation that a worker will deserialize.
    _validate_wires(circuit_from_dict(payload))
    return payload


def _registers_from_data(payload: Any, label: str) -> List[tuple[str, int]]:
    if not isinstance(payload, list):
        raise ProtocolValidationError(f"{label} must be an array")
    registers: List[tuple[str, int]] = []
    seen = set()
    for index, entry in enumerate(payload):
        obj = _mapping(entry, f"{label}[{index}]")
        name = _text(obj.get("name"), f"{label}[{index}].name")
        if name in seen:
            raise ProtocolValidationError(f"duplicate register name {name!r}")
        seen.add(name)
        registers.append((name, _integer(obj.get("size"), f"{label}[{index}].size", minimum=1)))
    return registers


def circuit_from_dict(payload: Any) -> CircuitIR:
    obj = _mapping(payload, "circuit")
    circuit = CircuitIR(name=_text(obj.get("name", ""), "circuit.name", allow_empty=True))
    for name, size in _registers_from_data(obj.get("qubit_registers"), "qubit_registers"):
        circuit.add_qubit_register(name, size)
    if circuit.num_qubits <= 0:
        raise ProtocolValidationError("distributed circuits must contain at least one qubit")
    for name, size in _registers_from_data(obj.get("classical_registers", []), "classical_registers"):
        circuit.add_clbit_register(name, size)
    operations = obj.get("operations")
    if not isinstance(operations, list):
        raise ProtocolValidationError("circuit.operations must be an array")
    seen_ids = set()
    for item in operations:
        operation = _deserialize_operation(item)
        if operation.id in seen_ids:
            raise ProtocolValidationError(f"duplicate operation id {operation.id}")
        seen_ids.add(operation.id)
        circuit.ops.append(operation)
    circuit._next_op_id = max(seen_ids, default=-1) + 1
    _validate_wires(circuit)
    return circuit


def serialize_task(task: Any) -> Dict[str, Any]:
    task_id = _text(getattr(task, "task_id", None), "task.task_id")
    job_id = _text(getattr(task, "job_id", ""), "task.job_id", allow_empty=True)
    return {
        "schema": TASK_SCHEMA,
        "version": PROTOCOL_VERSION,
        "task_id": task_id,
        "job_id": job_id,
        "shots": _integer(getattr(task, "shots", None), "task.shots", minimum=1),
        "seed": _integer(getattr(task, "seed", None), "task.seed", minimum=0),
        "attempt": _integer(getattr(task, "attempt", None), "task.attempt", minimum=1),
        "circuit": circuit_to_dict(getattr(task, "circuit", None)),
    }


def deserialize_task(payload: Any):
    obj = _mapping(payload, "task")
    if obj.get("schema") != TASK_SCHEMA or obj.get("version") != PROTOCOL_VERSION:
        raise ProtocolValidationError("unsupported task protocol version")
    from .planner import TaskUnit  # Avoid a module import cycle.

    return TaskUnit(
        task_id=_text(obj.get("task_id"), "task.task_id"),
        job_id=_text(obj.get("job_id", ""), "task.job_id", allow_empty=True),
        circuit=circuit_from_dict(obj.get("circuit")),
        shots=_integer(obj.get("shots"), "task.shots", minimum=1),
        seed=_integer(obj.get("seed"), "task.seed", minimum=0),
        attempt=_integer(obj.get("attempt"), "task.attempt", minimum=1),
    )


def task_to_json(task: Any) -> str:
    return json.dumps(serialize_task(task), allow_nan=False, sort_keys=True, separators=(",", ":"))


def task_from_json(payload: Any):
    if not isinstance(payload, str):
        raise ProtocolValidationError("serialized task must be JSON text")
    try:
        return deserialize_task(json.loads(payload))
    except json.JSONDecodeError as exc:
        raise ProtocolValidationError("serialized task is not valid JSON") from exc


def serialize_result(result: Mapping[str, Any]) -> Dict[str, Any]:
    obj = _mapping(result, "result")
    status = _text(obj.get("status"), "result.status")
    if status not in {"COMPLETED", "FAILED"}:
        raise ProtocolValidationError("result.status must be COMPLETED or FAILED")
    payload: Dict[str, Any] = {
        "schema": RESULT_SCHEMA,
        "version": PROTOCOL_VERSION,
        "status": status,
        "task_id": _text(obj.get("task_id"), "result.task_id"),
        "job_id": _text(obj.get("job_id", ""), "result.job_id", allow_empty=True),
        "worker_id": _text(obj.get("worker_id"), "result.worker_id"),
        "attempt": _integer(obj.get("attempt"), "result.attempt", minimum=1),
        "seed": _integer(obj.get("seed"), "result.seed", minimum=0),
        "process_id": _integer(obj.get("process_id"), "result.process_id", minimum=1),
    }
    if status == "FAILED":
        payload["error"] = _text(obj.get("error"), "result.error")
        return payload

    shots = _integer(obj.get("shots"), "result.shots", minimum=1)
    counts = _mapping(obj.get("counts"), "result.counts")
    parsed_counts: Dict[str, int] = {}
    for bitstring, count in counts.items():
        bitstring = _text(bitstring, "result.counts key")
        if any(bit not in "01" for bit in bitstring):
            raise ProtocolValidationError("result count keys must be binary bitstrings")
        parsed_counts[bitstring] = _integer(count, f"result.counts[{bitstring!r}]", minimum=0)
    if sum(parsed_counts.values()) != shots:
        raise ProtocolValidationError("result counts must sum exactly to result.shots")
    payload.update(
        {
            "shots": shots,
            "counts": parsed_counts,
            "execution_time_ms": _finite_number(
                obj.get("execution_time_ms", 0.0), "result.execution_time_ms"
            ),
        }
    )
    if payload["execution_time_ms"] < 0:
        raise ProtocolValidationError("result.execution_time_ms must not be negative")
    return payload


def deserialize_result(payload: Any) -> Dict[str, Any]:
    obj = _mapping(payload, "result")
    if obj.get("schema") != RESULT_SCHEMA or obj.get("version") != PROTOCOL_VERSION:
        raise ProtocolValidationError("unsupported result protocol version")
    # Run the same exhaustive validation and return the normalized dictionary.
    return serialize_result({key: value for key, value in obj.items() if key not in {"schema", "version"}})


def result_to_json(result: Mapping[str, Any]) -> str:
    return json.dumps(serialize_result(result), allow_nan=False, sort_keys=True, separators=(",", ":"))


def result_from_json(payload: Any) -> Dict[str, Any]:
    if not isinstance(payload, str):
        raise ProtocolValidationError("serialized result must be JSON text")
    try:
        return deserialize_result(json.loads(payload))
    except json.JSONDecodeError as exc:
        raise ProtocolValidationError("serialized result is not valid JSON") from exc
