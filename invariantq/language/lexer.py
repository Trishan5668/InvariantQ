"""
Lexer for InvariantQ programming language.
"""

from __future__ import annotations
import re
from dataclasses import dataclass
from typing import List, Optional

class TokenType:
    KEYWORD = "KEYWORD"
    IDENT = "IDENT"
    NUMBER = "NUMBER"
    ARROW = "ARROW"         # ->
    EQ_EQ = "EQ_EQ"         # ==
    DOT_DOT = "DOT_DOT"     # ..
    LPAREN = "LPAREN"       # (
    RPAREN = "RPAREN"       # )
    LBRACKET = "LBRACKET"   # [
    RBRACKET = "RBRACKET"   # ]
    LBRACE = "LBRACE"       # {
    RBRACE = "RBRACE"       # }
    COMMA = "COMMA"         # ,
    SEMICOLON = "SEMICOLON" # ;
    PLUS = "PLUS"           # +
    MINUS = "MINUS"         # -
    STAR = "STAR"           # *
    SLASH = "SLASH"         # /
    EOF = "EOF"

KEYWORDS = {
    "qubit", "qreg", "creg", "gate", "measure", "reset", "barrier",
    "noise", "if", "for", "in", "OPENQASM", "include"
}

@dataclass
class Token:
    type: str
    value: str
    line: int
    col: int

class Lexer:
    def __init__(self, source: str):
        self.source = source
        self.pos = 0
        self.line = 1
        self.col = 1
        self.length = len(source)

    def tokenize(self) -> List[Token]:
        tokens = []
        while self.pos < self.length:
            ch = self.source[self.pos]

            # Whitespace
            if ch in " \t\r":
                self.pos += 1
                self.col += 1
                continue
            if ch == "\n":
                self.pos += 1
                self.line += 1
                self.col = 1
                continue

            # Comments
            if ch == "/" and self.pos + 1 < self.length and self.source[self.pos + 1] == "/":
                while self.pos < self.length and self.source[self.pos] != "\n":
                    self.pos += 1
                continue
            if ch == "#":
                while self.pos < self.length and self.source[self.pos] != "\n":
                    self.pos += 1
                continue

            start_col = self.col

            # Two-character operators
            if self.source.startswith("->", self.pos):
                tokens.append(Token(TokenType.ARROW, "->", self.line, start_col))
                self.pos += 2
                self.col += 2
                continue
            if self.source.startswith("==", self.pos):
                tokens.append(Token(TokenType.EQ_EQ, "==", self.line, start_col))
                self.pos += 2
                self.col += 2
                continue
            if self.source.startswith("..", self.pos):
                tokens.append(Token(TokenType.DOT_DOT, "..", self.line, start_col))
                self.pos += 2
                self.col += 2
                continue

            # Single-character tokens
            single_map = {
                "(": TokenType.LPAREN,
                ")": TokenType.RPAREN,
                "[": TokenType.LBRACKET,
                "]": TokenType.RBRACKET,
                "{": TokenType.LBRACE,
                "}": TokenType.RBRACE,
                ",": TokenType.COMMA,
                ";": TokenType.SEMICOLON,
                "+": TokenType.PLUS,
                "-": TokenType.MINUS,
                "*": TokenType.STAR,
                "/": TokenType.SLASH,
            }
            if ch in single_map:
                tokens.append(Token(single_map[ch], ch, self.line, start_col))
                self.pos += 1
                self.col += 1
                continue

            # Numbers
            if ch.isdigit() or (ch == "." and self.pos + 1 < self.length and self.source[self.pos + 1].isdigit()):
                num_str = ""
                while self.pos < self.length and (self.source[self.pos].isdigit() or self.source[self.pos] in ".eE+-"):
                    # Check for .. range operator
                    if self.source.startswith("..", self.pos):
                        break
                    num_str += self.source[self.pos]
                    self.pos += 1
                    self.col += 1
                tokens.append(Token(TokenType.NUMBER, num_str, self.line, start_col))
                continue

            # Identifiers and keywords
            if ch.isalpha() or ch == "_":
                ident_str = ""
                while self.pos < self.length and (self.source[self.pos].isalnum() or self.source[self.pos] == "_"):
                    ident_str += self.source[self.pos]
                    self.pos += 1
                    self.col += 1
                if ident_str in KEYWORDS:
                    tokens.append(Token(TokenType.KEYWORD, ident_str, self.line, start_col))
                else:
                    tokens.append(Token(TokenType.IDENT, ident_str, self.line, start_col))
                continue

            # Unknown char - advance
            self.pos += 1
            self.col += 1

        tokens.append(Token(TokenType.EOF, "", self.line, self.col))
        return tokens
