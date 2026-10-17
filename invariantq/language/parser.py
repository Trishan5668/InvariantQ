"""
Parser for InvariantQ quantum programming language.
"""

from __future__ import annotations
import math
from typing import List, Optional
from .lexer import Token, TokenType, Lexer
from .ast import (
    Program, Statement, QubitDecl, ClassicalDecl, GateCall,
    MeasureStmt, ResetStmt, BarrierStmt, NoiseStmt, IfStmt,
    ForLoop, GateDef, QubitRef, ClbitRef, Expression,
    NumberExpr, IdentExpr, BinaryExpr, UnaryExpr
)

class Parser:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0

    def current(self) -> Token:
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return self.tokens[-1]

    def peek(self, offset: int = 1) -> Token:
        idx = self.pos + offset
        if idx < len(self.tokens):
            return self.tokens[idx]
        return self.tokens[-1]

    def match(self, token_type: str, value: Optional[str] = None) -> bool:
        tok = self.current()
        if tok.type == token_type:
            if value is None or tok.value == value:
                self.pos += 1
                return True
        return False

    def expect(self, token_type: str, value: Optional[str] = None) -> Token:
        tok = self.current()
        if tok.type != token_type or (value is not None and tok.value != value):
            raise SyntaxError(
                f"Expected {token_type} '{value or ''}' but got {tok.type} '{tok.value}' at line {tok.line}:{tok.col}"
            )
        self.pos += 1
        return tok

    def parse(self) -> Program:
        statements = []
        while not self.match(TokenType.EOF):
            stmt = self.parse_statement()
            if stmt:
                statements.append(stmt)
        return Program(statements=statements)

    def parse_statement(self) -> Optional[Statement]:
        tok = self.current()

        # Ignore OPENQASM or include headers if present
        if tok.type == TokenType.KEYWORD and tok.value in ("OPENQASM", "include"):
            while self.current().type not in (TokenType.SEMICOLON, TokenType.EOF):
                self.pos += 1
            self.match(TokenType.SEMICOLON)
            return None

        if tok.type == TokenType.KEYWORD:
            if tok.value in ("qubit", "qreg"):
                return self.parse_qubit_decl()
            elif tok.value == "creg":
                return self.parse_classical_decl()
            elif tok.value == "measure":
                return self.parse_measure()
            elif tok.value == "reset":
                return self.parse_reset()
            elif tok.value == "barrier":
                return self.parse_barrier()
            elif tok.value == "noise":
                return self.parse_noise()
            elif tok.value == "if":
                return self.parse_if()
            elif tok.value == "for":
                return self.parse_for()
            elif tok.value == "gate":
                return self.parse_gate_def()

        if tok.type == TokenType.IDENT:
            return self.parse_gate_call()

        # Semicolon skip
        if self.match(TokenType.SEMICOLON):
            return None

        self.pos += 1
        return None

    def parse_qubit_decl(self) -> QubitDecl:
        self.pos += 1 # skip 'qubit' or 'qreg'
        name_tok = self.expect(TokenType.IDENT)
        size = 1
        if self.match(TokenType.LBRACKET):
            size_tok = self.expect(TokenType.NUMBER)
            size = int(size_tok.value)
            self.expect(TokenType.RBRACKET)
        self.match(TokenType.SEMICOLON)
        return QubitDecl(name=name_tok.value, size=size, line=name_tok.line, col=name_tok.col)

    def parse_classical_decl(self) -> ClassicalDecl:
        self.pos += 1 # skip 'creg'
        name_tok = self.expect(TokenType.IDENT)
        size = 1
        if self.match(TokenType.LBRACKET):
            size_tok = self.expect(TokenType.NUMBER)
            size = int(size_tok.value)
            self.expect(TokenType.RBRACKET)
        self.match(TokenType.SEMICOLON)
        return ClassicalDecl(name=name_tok.value, size=size, line=name_tok.line, col=name_tok.col)

    def parse_qubit_ref(self) -> QubitRef:
        name_tok = self.expect(TokenType.IDENT)
        idx = 0
        if self.match(TokenType.LBRACKET):
            idx_tok = self.expect(TokenType.NUMBER)
            idx = int(idx_tok.value)
            self.expect(TokenType.RBRACKET)
        return QubitRef(name=name_tok.value, index=idx, line=name_tok.line, col=name_tok.col)

    def parse_clbit_ref(self) -> ClbitRef:
        name_tok = self.expect(TokenType.IDENT)
        idx = 0
        if self.match(TokenType.LBRACKET):
            idx_tok = self.expect(TokenType.NUMBER)
            idx = int(idx_tok.value)
            self.expect(TokenType.RBRACKET)
        return ClbitRef(name=name_tok.value, index=idx, line=name_tok.line, col=name_tok.col)

    def parse_gate_call(self) -> GateCall:
        gate_name_tok = self.expect(TokenType.IDENT)
        gate_name = gate_name_tok.value
        params = []

        if self.match(TokenType.LPAREN):
            while not self.match(TokenType.RPAREN):
                params.append(self.parse_expression())
                if not self.match(TokenType.COMMA):
                    self.expect(TokenType.RPAREN)
                    break

        qubits = []
        while True:
            qubits.append(self.parse_qubit_ref())
            if not self.match(TokenType.COMMA):
                break

        self.match(TokenType.SEMICOLON)
        return GateCall(
            name=gate_name,
            qubits=qubits,
            params=params,
            line=gate_name_tok.line,
            col=gate_name_tok.col
        )

    def parse_measure(self) -> MeasureStmt:
        meas_tok = self.expect(TokenType.KEYWORD, "measure")
        qref = self.parse_qubit_ref()
        self.expect(TokenType.ARROW)
        cref = self.parse_clbit_ref()
        self.match(TokenType.SEMICOLON)
        return MeasureStmt(qubit=qref, clbit=cref, line=meas_tok.line, col=meas_tok.col)

    def parse_reset(self) -> ResetStmt:
        tok = self.expect(TokenType.KEYWORD, "reset")
        qref = self.parse_qubit_ref()
        self.match(TokenType.SEMICOLON)
        return ResetStmt(qubit=qref, line=tok.line, col=tok.col)

    def parse_barrier(self) -> BarrierStmt:
        tok = self.expect(TokenType.KEYWORD, "barrier")
        qubits = []
        while True:
            qubits.append(self.parse_qubit_ref())
            if not self.match(TokenType.COMMA):
                break
        self.match(TokenType.SEMICOLON)
        return BarrierStmt(qubits=qubits, line=tok.line, col=tok.col)

    def parse_noise(self) -> NoiseStmt:
        tok = self.expect(TokenType.KEYWORD, "noise")
        ch_tok = self.expect(TokenType.IDENT)
        params = []
        if self.match(TokenType.LPAREN):
            while not self.match(TokenType.RPAREN):
                params.append(self.parse_expression())
                if not self.match(TokenType.COMMA):
                    self.expect(TokenType.RPAREN)
                    break
        qubits = []
        while True:
            qubits.append(self.parse_qubit_ref())
            if not self.match(TokenType.COMMA):
                break
        self.match(TokenType.SEMICOLON)
        return NoiseStmt(
            channel_name=ch_tok.value,
            params=params,
            qubits=qubits,
            line=tok.line,
            col=tok.col
        )

    def parse_if(self) -> IfStmt:
        tok = self.expect(TokenType.KEYWORD, "if")
        self.expect(TokenType.LPAREN)
        cref = self.parse_clbit_ref()
        self.expect(TokenType.EQ_EQ)
        val_tok = self.expect(TokenType.NUMBER)
        val = int(val_tok.value)
        self.expect(TokenType.RPAREN)

        body = []
        if self.match(TokenType.LBRACE):
            while not self.match(TokenType.RBRACE):
                s = self.parse_statement()
                if s: body.append(s)
        else:
            s = self.parse_statement()
            if s: body.append(s)

        return IfStmt(clbit=cref, value=val, body=body, line=tok.line, col=tok.col)

    def parse_for(self) -> ForLoop:
        tok = self.expect(TokenType.KEYWORD, "for")
        var_tok = self.expect(TokenType.IDENT)
        self.expect(TokenType.KEYWORD, "in")
        start_tok = self.expect(TokenType.NUMBER)
        self.expect(TokenType.DOT_DOT)
        end_tok = self.expect(TokenType.NUMBER)

        body = []
        self.expect(TokenType.LBRACE)
        while not self.match(TokenType.RBRACE):
            s = self.parse_statement()
            if s: body.append(s)

        return ForLoop(
            var_name=var_tok.value,
            start=int(start_tok.value),
            end=int(end_tok.value),
            body=body,
            line=tok.line,
            col=tok.col
        )

    def parse_gate_def(self) -> GateDef:
        tok = self.expect(TokenType.KEYWORD, "gate")
        name_tok = self.expect(TokenType.IDENT)
        params = []
        if self.match(TokenType.LPAREN):
            while not self.match(TokenType.RPAREN):
                p = self.expect(TokenType.IDENT).value
                params.append(p)
                if not self.match(TokenType.COMMA):
                    self.expect(TokenType.RPAREN)
                    break
        qubits = []
        while True:
            qubits.append(self.expect(TokenType.IDENT).value)
            if not self.match(TokenType.COMMA):
                break

        body = []
        self.expect(TokenType.LBRACE)
        while not self.match(TokenType.RBRACE):
            s = self.parse_statement()
            if s: body.append(s)

        return GateDef(name=name_tok.value, params=params, qubits=qubits, body=body, line=tok.line, col=tok.col)

    def parse_expression(self) -> Expression:
        return self.parse_add_sub()

    def parse_add_sub(self) -> Expression:
        expr = self.parse_mul_div()
        while self.current().type in (TokenType.PLUS, TokenType.MINUS):
            op = self.current().value
            self.pos += 1
            right = self.parse_mul_div()
            expr = BinaryExpr(op=op, left=expr, right=right)
        return expr

    def parse_mul_div(self) -> Expression:
        expr = self.parse_unary()
        while self.current().type in (TokenType.STAR, TokenType.SLASH):
            op = self.current().value
            self.pos += 1
            right = self.parse_unary()
            expr = BinaryExpr(op=op, left=expr, right=right)
        return expr

    def parse_unary(self) -> Expression:
        if self.current().type == TokenType.MINUS:
            self.pos += 1
            return UnaryExpr(op="-", expr=self.parse_primary())
        return self.parse_primary()

    def parse_primary(self) -> Expression:
        tok = self.current()
        if tok.type == TokenType.NUMBER:
            self.pos += 1
            return NumberExpr(value=float(tok.value), line=tok.line, col=tok.col)
        if tok.type == TokenType.IDENT:
            self.pos += 1
            if tok.value.lower() == "pi":
                return NumberExpr(value=math.pi, line=tok.line, col=tok.col)
            return IdentExpr(name=tok.value, line=tok.line, col=tok.col)
        if self.match(TokenType.LPAREN):
            expr = self.parse_expression()
            self.expect(TokenType.RPAREN)
            return expr

        raise SyntaxError(f"Unexpected token in expression: {tok.type} '{tok.value}' at {tok.line}:{tok.col}")
