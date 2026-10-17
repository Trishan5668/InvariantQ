# CPTP Quantum Noise Channels and Verification

A quantum operation $\mathcal{E}$ mapping density operators to density operators $\mathcal{E}: \mathcal{S}(\mathcal{H}) \to \mathcal{S}(\mathcal{H})$ must be **Completely Positive and Trace-Preserving (CPTP)** (Choi 1975; Jamiołkowski 1972; Coecke et al. 2016).

## 1. Mathematical Formulations

1. **Kraus Representation**:
   $$\mathcal{E}(\rho) = \sum_k K_k \rho K_k^\dagger$$
   Trace preservation requires:
   $$\sum_k K_k^\dagger K_k = I$$

2. **Standard Channels**:
   - **Depolarizing Channel** (parameter $p$):
     $$\mathcal{E}(\rho) = (1 - p)\rho + \frac{p}{3}(X\rho X + Y\rho Y + Z\rho Z)$$
   - **Amplitude Damping Channel** ($T_1$ relaxation, parameter $\gamma = 1 - e^{-t/T_1}$):
     $$K_0 = \begin{pmatrix} 1 & 0 \\ 0 & \sqrt{1 - \gamma} \end{pmatrix}, \quad K_1 = \begin{pmatrix} 0 & \sqrt{\gamma} \\ 0 & 0 \end{pmatrix}$$
   - **Phase Damping Channel** ($T_2$ pure dephasing, parameter $\lambda = 1 - e^{-t/T_2}$):
     $$K_0 = \begin{pmatrix} 1 & 0 \\ 0 & \sqrt{1 - \lambda} \end{pmatrix}, \quad K_1 = \begin{pmatrix} 0 & 0 \\ 0 & \sqrt{\lambda} \end{pmatrix}$$

## 2. Rigorous CPTP Verification Criteria

1. **Choi-Jamiolkowski Isomorphism**:
   The Choi matrix $J(\mathcal{E})$ is constructed via:
   $$J(\mathcal{E}) = (\mathcal{I} \otimes \mathcal{E})(|\Phi^+\rangle\langle\Phi^+|) = \sum_k (I \otimes K_k) |\Phi^+\rangle\langle\Phi^+| (I \otimes K_k)^\dagger$$
   where $|\Phi^+\rangle = \frac{1}{\sqrt{d}}\sum_i |i\rangle|i\rangle$.
   - **Complete Positivity**: $J(\mathcal{E})$ is positive semidefinite, i.e., $\lambda_{\min}(J) \ge -10^{-10}$.
   - **Trace Preservation**: $\text{Tr}_B(J(\mathcal{E})) = \frac{1}{d} I_A$.

2. **Action on Random Density Matrices**:
   For random Ginibre states $\rho = \frac{G G^\dagger}{\text{Tr}(G G^\dagger)}$, the validator proves:
   $$|\text{Tr}(\mathcal{E}(\rho)) - 1.0| \le 10^{-10}, \quad \lambda_{\min}(\mathcal{E}(\rho)) \ge -10^{-10}, \quad \mathcal{E}(\rho) = \mathcal{E}(\rho)^\dagger$$

3. **Channel Composition**:
   Given two CPTP channels $\mathcal{E}_1$ and $\mathcal{E}_2$, the composed map $\mathcal{E} = \mathcal{E}_2 \circ \mathcal{E}_1$ with Kraus set $\{K_j^{(2)} K_i^{(1)}\}$ is guaranteed to be CPTP.
