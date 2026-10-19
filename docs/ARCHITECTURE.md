# INVARIANTQ System Architecture

> Validation note: this document describes intended component boundaries. Actual
> validated capability, active native/fallback status, and known gaps are in
> [VALIDATION_STATUS.md](VALIDATION_STATUS.md). The portable fallback is not a
> scalable tableau or MPS implementation.

INVARIANTQ implements an orchestrated hybrid stack combining C++ numerical kernels, Python orchestration, and a React + TypeScript user interface:

```
┌────────────────────────────────────────────────────────┐
│               Interactive Web Studio (React+TS)        │
│    Circuit Studio | Visualizer | Noise Lab | Cluster   │
└──────────────────────────┬─────────────────────────────┘
                           │ HTTP / REST / WebSocket
┌──────────────────────────▼─────────────────────────────┐
│             Python Orchestration & Runtime             │
│  - Language Frontend (Lexer, Parser, Type Checker)     │
│  - Optimizing Compiler (Cancellation, Commute, Fusion) │
│  - Distributed Scheduler & Fault-Tolerant Planner      │
│  - CPTP Noise Validation & Readout Mitigation          │
│  - Metamorphic, Differential & Property Verification   │
└──────────────────────────┬─────────────────────────────┘
                           │ C ABI / ctypes / OpenMP
┌──────────────────────────▼─────────────────────────────┐
│          High-Performance C++ Core Engine              │
│  - StateVector (Bit-indexing, 2^n wave function)       │
│  - DensityMatrix (4^n open system, Kraus operators)    │
│  - Stabilizer (Gottesman-Knill binary tableau)         │
│  - Tensor Network (Matrix Product State Jacobi SVD)    │
└────────────────────────────────────────────────────────┘
```

## 1. C++ Numerical Core Engine (`core/`)
- Compiled with `-O3 -march=native -fopenmp -fPIC -std=c++17` into `libinvariantq.so`.
- Zero external runtime dependencies: incorporates self-contained Jacobi eigenvalue and singular value decomposition routines.
- OpenMP multi-threading parallelizes state evolution across available CPU cores.

## 2. Multi-Modal Formalisms
1. **Exact State-Vector**: Full $2^n$ state representation with $O(2^{n-1})$ parallel bit-twiddling gate application.
2. **Density Matrix**: $2^n \times 2^n$ matrix $\rho$ evolving under Kraus channels $\mathcal{E}(\rho) = \sum_k K_k \rho K_k^\dagger$.
3. **Stabilizer Simulator**: Aaronson-Gottesman $2n \times (2n+1)$ binary tableau tracking Pauli generators $R_i$. Runs in polynomial time $O(n^2)$ gate, $O(n^3)$ measurement.
4. **Tensor Network (MPS)**: 3-index tensor chains $A^{[i]} \in \mathbb{C}^{d_{l} \times 2 \times d_{r}}$ truncated to bond dimension $\chi \le 64$ via singular value decomposition.

## 3. Distributed Scheduler & Worker Fault Tolerance
- Slices shot batches across parallel worker processes.
- Cryptographically derives per-task RNG seeds: $\text{seed}_k = \text{SHA256}(\text{master\_seed} : \text{job\_id} : k)$.
- Automatically detects worker failure and reschedules tasks on surviving workers without statistical bias.
