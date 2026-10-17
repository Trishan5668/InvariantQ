"""
OpenQASM 2.0 / 3.0 Parser and IQ-Lang Lowerer into CircuitIR.
"""

from __future__ import annotations
import math
from typing import List, Dict, Optional
from ..ir.qir import CircuitIR, GateOp, MeasureOp, ResetOp, BarrierOp, NoiseOp, QWire, CWire
from .lexer import Lexer
from .parser import Parser
from .type_checker import TypeChecker
from .ast import (
    Program, QubitDecl, ClassicalDecl, GateCall, MeasureStmt,
    ResetStmt, BarrierStmt, NoiseStmt, IfStmt, ForLoop
)

def parse_iq_lang(source: str) -> CircuitIR:
    """
    Parses IQ-Lang source code into a verified typed CircuitIR.
    """
    lexer = Lexer(source)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    program = parser.parse()

    # Type check
    checker = TypeChecker()
    checker.check(program)

    # Lower to CircuitIR
    circuit = CircuitIR(name="iq_circuit")
    for reg_name, size in checker.qubit_registers.items():
        circuit.add_qubit_register(reg_name, size)
    for reg_name, size in checker.clbit_registers.items():
        circuit.add_clbit_register(reg_name, size)

    def lower_stmt(stmt):
        if isinstance(stmt, GateCall):
            params = [checker.eval_expr(p) for p in stmt.params]
            qubits = [QWire(q.name, q.index) for q in stmt.qubits]
            circuit.add_op(GateOp(name=stmt.name, qubits=qubits, params=params))
        elif isinstance(stmt, MeasureStmt):
            q = QWire(stmt.qubit.name, stmt.qubit.index)
            c = CWire(stmt.clbit.name, stmt.clbit.index)
            circuit.add_op(MeasureOp(qubit=q, clbit=c))
        elif isinstance(stmt, ResetStmt):
            q = QWire(stmt.qubit.name, stmt.qubit.index)
            circuit.add_op(ResetOp(qubit=q))
        elif isinstance(stmt, BarrierStmt):
            qubits = [QWire(q.name, q.index) for q in stmt.qubits]
            circuit.add_op(BarrierOp(qubits=qubits))
        elif isinstance(stmt, NoiseStmt):
            params = [checker.eval_expr(p) for p in stmt.params]
            qubits = [QWire(q.name, q.index) for q in stmt.qubits]
            circuit.add_op(NoiseOp(channel_name=stmt.channel_name, params=params, qubits=qubits))
        elif isinstance(stmt, ForLoop):
            for i in range(stmt.start, stmt.end):
                checker.variables[stmt.var_name] = float(i)
                for s in stmt.body:
                    lower_stmt(s)

    for stmt in program.statements:
        lower_stmt(stmt)

    return circuit


def parse_qasm(source: str) -> CircuitIR:
    """
    Parses standard OpenQASM 2.0 / 3.0 strings into CircuitIR.
    """
    return parse_iq_lang(source)
