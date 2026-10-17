# INVARIANTQ Language (IQ-Lang) and Intermediate Representation (qIR) Specification

## 1. Syntax Grammar (EBNF)

The INVARIANTQ programming language (`IQ-Lang`) provides a statically-checked quantum-classical syntax with affine linear typing to enforce the quantum No-Cloning Theorem.

```ebnf
Program         ::= Statement* EOF
Statement       ::= QubitDecl
                  | ClassicalDecl
                  | GateCall
                  | MeasureStmt
                  | ResetStmt
                  | BarrierStmt
                  | NoiseStmt
                  | IfStmt
                  | ForLoop
                  | GateDef

QubitDecl       ::= ("qubit" | "qreg") IDENT "[" NUMBER "]" ";"
ClassicalDecl   ::= "creg" IDENT "[" NUMBER "]" ";"

QubitRef        ::= IDENT "[" NUMBER "]"
ClbitRef        ::= IDENT "[" NUMBER "]"

GateCall        ::= IDENT ("(" ParamList? ")")? QubitList ";"
ParamList       ::= Expression ("," Expression)*
QubitList       ::= QubitRef ("," QubitRef)*

MeasureStmt     ::= "measure" QubitRef "->" ClbitRef ";"
ResetStmt       ::= "reset" QubitRef ";"
BarrierStmt     ::= "barrier" QubitList ";"

NoiseStmt       ::= "noise" IDENT ("(" ParamList? ")")? QubitList ";"
IfStmt          ::= "if" "(" ClbitRef "==" NUMBER ")" (Statement | "{" Statement* "}")
ForLoop         ::= "for" IDENT "in" NUMBER ".." NUMBER "{" Statement* "}"

GateDef         ::= "gate" IDENT ("(" IdentList? ")")? IdentList "{" Statement* "}"
```

## 2. Linear Type Checking & No-Cloning Enforcement

1. **Affine / Linear Qubit Typings**:
   In any unitary transformation $U(q_0, q_1, \dots, q_{k-1})$, the operands must satisfy:
   $$\forall i \neq j, \quad q_i \neq q_j$$
   Aliasing or passing the same physical or logical qubit multiple times to an entangling operation (e.g. `cx q[0], q[0];`) violates the quantum no-cloning theorem and is rejected statically at compile time with a `LinearTypeError`.

2. **Register Bounds Checking**:
   Accessing $q[i]$ where $i \ge \text{size}(q)$ or $i < 0$ produces a compile-time `TypeCheckError`.

3. **Parametric Soundness**:
   Rotations ($R_x, R_y, R_z, U_3$) take expressions strictly evaluated to real floating-point numbers ($\mathbb{R}$).

## 3. Typed Intermediate Representation (qIR)

The Intermediate Representation is structured as an operation list or Directed Acyclic Graph (`DAGCircuit`):
- `GateOp`: Name, qubit operands, numeric parameter list, $2^k \times 2^k$ matrix representation, Clifford classification flag.
- `FusedGateOp`: Consolidated unitary block of size $2^k \times 2^k$ replacing contiguous subcircuits (NWQ-Sim model).
- `MeasureOp`: Projective $Z$-basis measurement.
- `ResetOp`: Resets qubit to $|0\rangle$.
- `BarrierOp`: Serialization barrier preventing compiler optimization reordering across boundaries.
- `NoiseOp`: Channel name and error parameter vector (e.g. $p, T_1, T_2, t_{\text{gate}}$).
- `ConditionalOp`: Classically controlled quantum gate conditioned on measurement outcomes.
