"""
Test Stage 2: Quantum Language (IQ-Lang), Type-Checking, IR, and Compiler Passes.
"""

import math
import pytest
from invariantq.language.qasm_parser import parse_iq_lang
from invariantq.language.type_checker import LinearTypeError, TypeCheckError
from invariantq.compiler.optimizer import Compiler
from invariantq.compiler.mapping import DeviceTopology

def test_linear_type_checker_prevents_cloning():
    # Attempting to use identical qubit for control and target in CX
    invalid_code = """
    qubit q[2];
    cx q[0], q[0];
    """
    with pytest.raises(LinearTypeError) as excinfo:
        parse_iq_lang(invalid_code)
    assert "Linear Type Violation" in str(excinfo.value)
    assert "No-Cloning theorem" in str(excinfo.value)

def test_type_checker_bounds_checking():
    out_of_bounds = """
    qubit q[2];
    h q[5];
    """
    with pytest.raises(TypeCheckError) as excinfo:
        parse_iq_lang(out_of_bounds)
    assert "out of bounds" in str(excinfo.value)

def test_gate_cancellation_pass():
    code = """
    qubit q[2];
    h q[0];
    h q[0];
    x q[1];
    x q[1];
    cx q[0], q[1];
    cx q[0], q[1];
    """
    circ = parse_iq_lang(code)
    compiler = Compiler(opt_level=1, enable_fusion=False)
    res = compiler.compile(circ)

    # All self-inverses cancel out
    assert res.optimized_gate_count == 0
    assert res.is_equivalent is True

def test_rotation_merging_pass():
    code = """
    qubit q[1];
    rz(0.4) q[0];
    rz(0.6) q[0];
    """
    circ = parse_iq_lang(code)
    compiler = Compiler(opt_level=1, enable_fusion=False)
    res = compiler.compile(circ)

    assert res.optimized_gate_count == 1
    assert math.isclose(res.circuit.ops[0].params[0], 1.0, rel_tol=1e-5)
    assert res.is_equivalent is True

def test_rotation_cancelling_to_zero():
    code = """
    qubit q[1];
    rz(0.5) q[0];
    rz(-0.5) q[0];
    """
    circ = parse_iq_lang(code)
    compiler = Compiler(opt_level=1, enable_fusion=False)
    res = compiler.compile(circ)

    assert res.optimized_gate_count == 0

def test_qubit_routing_on_linear_topology():
    # Interaction between q[0] and q[2] on linear chain requires SWAPs
    code = """
    qubit q[3];
    cx q[0], q[2];
    """
    circ = parse_iq_lang(code)
    topo = DeviceTopology.linear(3)
    compiler = Compiler(opt_level=2, topology=topo, enable_fusion=False)
    res = compiler.compile(circ)

    # SWAP gate should have been inserted
    op_names = [op.name for op in res.circuit.ops]
    assert "swap" in op_names

def test_gate_fusion_pass():
    code = """
    qubit q[1];
    h q[0];
    t q[0];
    s q[0];
    """
    circ = parse_iq_lang(code)
    compiler = Compiler(opt_level=3, enable_fusion=True)
    res = compiler.compile(circ)

    # 3 single-qubit gates fused into 1
    assert res.optimized_gate_count == 1
    assert res.is_equivalent is True
