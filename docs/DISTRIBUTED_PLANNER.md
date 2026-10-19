# Distributed Execution, Scheduling & Fault-Tolerance Architecture

> Current validation covers the in-process scheduler and its fault-injection
> fixtures only. It does not establish networked delivery or exactly-once
> execution guarantees; see [VALIDATION_STATUS.md](VALIDATION_STATUS.md).

INVARIANTQ's distributed engine enables execution across networked nodes with fault tolerance and statistical consistency (Cisco Systems, 2025; Caleffi et al., 2024).

## 1. Task Slicing & Seed Derivation

Given total shots $N$ and $M$ worker nodes:
- Each node receives a partition $N_i \approx \lfloor N/M \rfloor$.
- To ensure reproducible simulation without inter-worker correlation:
  $$\text{task\_seed}_i = \text{SHA256}(\text{master\_seed} : \text{job\_id} : i) \pmod{2^{64}}$$
- This deterministic seed tree guarantees identical results whether running on 1 worker or 100 workers.

## 2. Worker Lifecycle & Fault Recovery

1. **Heartbeat & Liveness**:
   Workers emit periodic heartbeats. If a worker process fails or crashes, the scheduler flags the node as `FAILED`.
2. **Deterministic Rescheduling**:
   The aborted task is reassigned to a healthy worker with its original task seed.
3. **Statistical Integrity**:
   Because the task seed is fixed, retrying an aborted sub-batch does not introduce sampling bias or drop measurement shots.
4. **Result Aggregation**:
   The aggregator collects bitstring histograms and computes:
   - Pauli observable expectation value $\langle Z \dots Z \rangle$
   - Variance $\text{Var}(O) = 1 - \langle O \rangle^2$
   - Standard Error of the Mean $\text{SEM} = \sqrt{\text{Var}/N}$
   - 95% Confidence Interval $[\mu - 1.96 \cdot \text{SEM}, \mu + 1.96 \cdot \text{SEM}]$.
