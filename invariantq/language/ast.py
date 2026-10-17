"""
Abstract Syntax Tree (AST) definitions for InvariantQ (IQ-Lang).
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional, Any, Union

@dataclass
class ASTNode:
    line: int = 1
    col: int = 1

@dataclass
class Expression(ASTNode):
    pass

@dataclass
class NumberExpr(Expression):
    value: float = 0.0

@dataclass
class IdentExpr(Expression):
    name: str = ""

@dataclass
class BinaryExpr(Expression):
    op: str = "+"
    left: Expression = field(default_factory=Expression)
    right: Expression = field(default_factory=Expression)

@dataclass
class UnaryExpr(Expression):
    op: str = "-"
    expr: Expression = field(default_factory=Expression)

@dataclass
class QubitRef(ASTNode):
    name: str = "q"
    index: int = 0

@dataclass
class ClbitRef(ASTNode):
    name: str = "c"
    index: int = 0

@dataclass
class Statement(ASTNode):
    pass

@dataclass
class QubitDecl(Statement):
    name: str = "q"
    size: int = 1

@dataclass
class ClassicalDecl(Statement):
    name: str = "c"
    size: int = 1

@dataclass
class GateCall(Statement):
    name: str = "h"
    qubits: List[QubitRef] = field(default_factory=list)
    params: List[Expression] = field(default_factory=list)

@dataclass
class MeasureStmt(Statement):
    qubit: QubitRef = field(default_factory=QubitRef)
    clbit: ClbitRef = field(default_factory=ClbitRef)

@dataclass
class ResetStmt(Statement):
    qubit: QubitRef = field(default_factory=QubitRef)

@dataclass
class BarrierStmt(Statement):
    qubits: List[QubitRef] = field(default_factory=list)

@dataclass
class NoiseStmt(Statement):
    channel_name: str = "depolarizing"
    params: List[Expression] = field(default_factory=list)
    qubits: List[QubitRef] = field(default_factory=list)

@dataclass
class IfStmt(Statement):
    clbit: ClbitRef = field(default_factory=ClbitRef)
    value: int = 1
    body: List[Statement] = field(default_factory=list)

@dataclass
class ForLoop(Statement):
    var_name: str = "i"
    start: int = 0
    end: int = 0
    body: List[Statement] = field(default_factory=list)

@dataclass
class GateDef(Statement):
    name: str = ""
    params: List[str] = field(default_factory=list)
    qubits: List[str] = field(default_factory=list)
    body: List[Statement] = field(default_factory=list)

@dataclass
class Program(ASTNode):
    statements: List[Statement] = field(default_factory=list)
