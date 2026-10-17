"""
Type Checker and Linear Type Verifier for InvariantQ.
Enforces no-cloning theorem, qubit linearity, and register bounds.
"""

from __future__ import annotations
import math
from typing import Dict, Set, List, Optional
from .ast import (
    Program, Statement, QubitDecl, ClassicalDecl, GateCall,
    MeasureStmt, ResetStmt, BarrierStmt, NoiseStmt, IfStmt,
    ForLoop, GateDef, Expression, NumberExpr, IdentExpr,
    BinaryExpr, UnaryExpr, QubitRef, ClbitRef
)

class TypeCheckError(Exception):
    pass

class LinearTypeError(TypeCheckError):
    pass

class TypeChecker:
    def __init__(self):
        self.qubit_registers: Dict[str, int] = {}
        self.clbit_registers: Dict[str, int] = {}
        self.gate_definitions: Dict[str, GateDef] = {}
        self.variables: Dict[str, float] = {"pi": math.pi}

    def check(self, program: Program):
        for stmt in program.statements:
            self.check_statement(stmt)

    def check_statement(self, stmt: Statement):
        if isinstance(stmt, QubitDecl):
            if stmt.size <= 0:
                raise TypeCheckError(f"Qubit register '{stmt.name}' must have size > 0 (got {stmt.size})")
            if stmt.name in self.qubit_registers:
                raise TypeCheckError(f"Duplicate qubit register '{stmt.name}' declaration")
            self.qubit_registers[stmt.name] = stmt.size

        elif isinstance(stmt, ClassicalDecl):
            if stmt.size <= 0:
                raise TypeCheckError(f"Classical register '{stmt.name}' must have size > 0 (got {stmt.size})")
            if stmt.name in self.clbit_registers:
                raise TypeCheckError(f"Duplicate classical register '{stmt.name}' declaration")
            self.clbit_registers[stmt.name] = stmt.size

        elif isinstance(stmt, GateDef):
            self.gate_definitions[stmt.name] = stmt

        elif isinstance(stmt, GateCall):
            self.check_gate_call(stmt)

        elif isinstance(stmt, MeasureStmt):
            self.check_qubit_ref(stmt.qubit)
            self.check_clbit_ref(stmt.clbit)

        elif isinstance(stmt, ResetStmt):
            self.check_qubit_ref(stmt.qubit)

        elif isinstance(stmt, BarrierStmt):
            seen = set()
            for q in stmt.qubits:
                self.check_qubit_ref(q)
                key = (q.name, q.index)
                if key in seen:
                    raise LinearTypeError(f"Duplicate qubit {q.name}[{q.index}] in barrier statement")
                seen.add(key)

        elif isinstance(stmt, NoiseStmt):
            for q in stmt.qubits:
                self.check_qubit_ref(q)
            for p in stmt.params:
                val = self.eval_expr(p)
                if not isinstance(val, (int, float)):
                    raise TypeCheckError(f"Noise parameter must evaluate to a real number, got {val}")

        elif isinstance(stmt, IfStmt):
            self.check_clbit_ref(stmt.clbit)
            for s in stmt.body:
                self.check_statement(s)

        elif isinstance(stmt, ForLoop):
            old_val = self.variables.get(stmt.var_name)
            for i in range(stmt.start, stmt.end):
                self.variables[stmt.var_name] = float(i)
                for s in stmt.body:
                    self.check_statement(s)
            if old_val is not None:
                self.variables[stmt.var_name] = old_val
            else:
                self.variables.pop(stmt.var_name, None)

    def check_qubit_ref(self, q: QubitRef):
        if q.name not in self.qubit_registers:
            raise TypeCheckError(f"Undeclared qubit register '{q.name}' at line {q.line}:{q.col}")
        size = self.qubit_registers[q.name]
        if q.index < 0 or q.index >= size:
            raise TypeCheckError(
                f"Qubit index out of bounds: {q.name}[{q.index}], size is {size} at line {q.line}:{q.col}"
            )

    def check_clbit_ref(self, c: ClbitRef):
        if c.name not in self.clbit_registers:
            raise TypeCheckError(f"Undeclared classical register '{c.name}' at line {c.line}:{c.col}")
        size = self.clbit_registers[c.name]
        if c.index < 0 or c.index >= size:
            raise TypeCheckError(
                f"Classical bit index out of bounds: {c.name}[{c.index}], size is {size} at line {c.line}:{c.col}"
            )

    def check_gate_call(self, call: GateCall):
        # Linear type check: all qubits in a multi-qubit gate MUST be distinct
        seen_qubits = set()
        for q in call.qubits:
            self.check_qubit_ref(q)
            key = (q.name, q.index)
            if key in seen_qubits:
                raise LinearTypeError(
                    f"Linear Type Violation: Qubit {q.name}[{q.index}] is referenced multiple times in gate '{call.name}'. "
                    f"Quantum No-Cloning theorem forbids aliasing or duplicate qubit operands."
                )
            seen_qubits.add(key)

        # Check params
        for p in call.params:
            self.eval_expr(p)

    def eval_expr(self, expr: Expression) -> float:
        if isinstance(expr, NumberExpr):
            return expr.value
        elif isinstance(expr, IdentExpr):
            if expr.name in self.variables:
                return self.variables[expr.name]
            raise TypeCheckError(f"Undefined variable '{expr.name}' in expression")
        elif isinstance(expr, UnaryExpr):
            val = self.eval_expr(expr.expr)
            if expr.op == "-":
                return -val
            return val
        elif isinstance(expr, BinaryExpr):
            l = self.eval_expr(expr.left)
            r = self.eval_expr(expr.right)
            if expr.op == "+":
                return l + r
            elif expr.op == "-":
                return l - r
            elif expr.op == "*":
                return l * r
            elif expr.op == "/":
                if r == 0:
                    raise ZeroDivisionError("Division by zero in quantum gate parameter")
                return l / r
            raise TypeCheckError(f"Unknown operator {expr.op}")
        return 0.0
