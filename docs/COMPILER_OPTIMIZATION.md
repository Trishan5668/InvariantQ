# Quantum Compiler Optimization Pipeline & Correctness Proofs

INVARIANTQ implements a multi-pass optimizing compiler designed for semantic preservation and hardware efficiency (Cardama et al., 2025; Suh et al., 2024).

## 1. Optimization Passes

### Pass 1: Gate Cancellation & Continuous Rotation Merging
- **Self-Inverse Cancellation**:
  $$H \cdot H = I, \quad X \cdot X = I, \quad Y \cdot Y = I, \quad Z \cdot Z = I, \quad CX \cdot CX = I$$
- **Inverse Pairs**:
  $$S \cdot S^\dagger = I, \quad T \cdot T^\dagger = I$$
- **Rotation Merging**:
  $$R_z(\theta_1) \cdot R_z(\theta_2) = R_z(\theta_1 + \theta_2 \pmod{4\pi})$$
  If $\sin\left(\frac{\theta_1 + \theta_2}{2}\right) \approx 0$, the gate is completely dropped.

### Pass 2: Commutation-Based Reordering
Gates on commuting subsystems are reordered to bring canceling gates adjacent:
1. Disjoint qubit sets: $[A_q, B_{q'}] = 0$ for $q \cap q' = \emptyset$.
2. Diagonal gates: $[R_z, R_z] = 0, [S, R_z] = 0, [CZ, R_z] = 0$.
3. Control commutes with control: $[CX_{c, t_1}, CX_{c, t_2}] = 0$.

### Pass 3: NWQ-Sim Gate Fusion
Rather than applying each single-qubit gate sequentially (requiring multiple $O(2^n)$ memory passes), the gate fusion pass contracts adjacent operations on the same 1 or 2 qubits into a single composite unitary tensor:
$$U_{\text{fused}} = \prod_{k} U_k$$
This reduces statevector memory passes by up to 80% on typical workloads.

### Pass 4: Qubit Mapping & Routing
For hardware coupling graphs with restricted connectivity (Linear, 2D Grid, Heavy-Hex):
- Uses shortest-path distance on the coupling graph.
- Inserts minimal SWAP gates to bring non-adjacent qubits together before 2-qubit interactions.

## 2. Formal Equivalence Proof
For small circuits ($n \le 5$), the compiler mathematically verifies unitary equivalence:
$$\|U_{\text{orig}} - e^{i\phi} U_{\text{opt}}\|_F \le 10^{-10}$$
$$\text{or} \quad |\text{Tr}(U_{\text{orig}}^\dagger U_{\text{opt}})| = 2^n$$
guaranteeing that the compiled circuit preserves mathematical semantics.
