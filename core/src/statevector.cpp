#include "statevector.hpp"
#include <iostream>
#include <algorithm>
#include <cstring>
#include <omp.h>

namespace invariantq {

StateVector::StateVector(size_t num_qubits)
    : num_qubits_(num_qubits), dim_(1ULL << num_qubits), amplitudes_(dim_, complex_t(0.0, 0.0)) {
    amplitudes_[0] = complex_t(1.0, 0.0);
}

void StateVector::reset() {
    std::fill(amplitudes_.begin(), amplitudes_.end(), complex_t(0.0, 0.0));
    amplitudes_[0] = complex_t(1.0, 0.0);
}

void StateVector::set_amplitudes(const complex_t* data, size_t size) {
    if (size != dim_) {
        throw std::invalid_argument("Amplitude size does not match state vector dimension");
    }
    std::copy(data, data + size, amplitudes_.begin());
}

void StateVector::apply_1q_gate(size_t target, const complex_t U[4]) {
    if (target >= num_qubits_) {
        throw std::out_of_range("Target qubit index out of range");
    }

    const uint64_t m = 1ULL << target;
    const uint64_t mask_low = m - 1;
    const uint64_t mask_high = ~mask_low;
    const uint64_t half_dim = dim_ >> 1;

    #pragma omp parallel for schedule(static)
    for (uint64_t i = 0; i < half_dim; ++i) {
        uint64_t i0 = ((i & mask_high) << 1) | (i & mask_low);
        uint64_t i1 = i0 | m;

        complex_t a = amplitudes_[i0];
        complex_t b = amplitudes_[i1];

        amplitudes_[i0] = U[0] * a + U[1] * b;
        amplitudes_[i1] = U[2] * a + U[3] * b;
    }
}

void StateVector::apply_2q_gate(size_t q0, size_t q1, const complex_t U[16]) {
    if (q0 >= num_qubits_ || q1 >= num_qubits_ || q0 == q1) {
        throw std::invalid_argument("Invalid qubit indices for 2-qubit gate");
    }

    size_t q_low = std::min(q0, q1);
    size_t q_high = std::max(q0, q1);

    uint64_t quarter_dim = dim_ >> 2;

    #pragma omp parallel for schedule(static)
    for (uint64_t i = 0; i < quarter_dim; ++i) {
        uint64_t low = i & ((1ULL << q_low) - 1);
        uint64_t mid = (i >> q_low) & ((1ULL << (q_high - q_low - 1)) - 1);
        uint64_t high = i >> (q_high - 1);

        uint64_t i00 = (high << (q_high + 1)) | (mid << (q_low + 1)) | low;
        uint64_t idx[4];

        // idx depends on order of q0 and q1
        idx[0] = i00;
        idx[1] = i00 | (1ULL << q1);
        idx[2] = i00 | (1ULL << q0);
        idx[3] = i00 | (1ULL << q0) | (1ULL << q1);

        complex_t v[4];
        for (int k = 0; k < 4; ++k) {
            v[k] = amplitudes_[idx[k]];
        }

        for (int r = 0; r < 4; ++r) {
            complex_t res = U[r * 4 + 0] * v[0] +
                            U[r * 4 + 1] * v[1] +
                            U[r * 4 + 2] * v[2] +
                            U[r * 4 + 3] * v[3];
            amplitudes_[idx[r]] = res;
        }
    }
}

void StateVector::apply_fused_gate(const std::vector<size_t>& qubits, const complex_t* U, size_t k) {
    if (k == 1) {
        apply_1q_gate(qubits[0], U);
        return;
    }
    if (k == 2) {
        apply_2q_gate(qubits[0], qubits[1], U);
        return;
    }

    size_t num_fused = qubits.size();
    if (num_fused > 4) {
        throw std::invalid_argument("Fused gate larger than 4 qubits not supported");
    }

    size_t k_dim = 1ULL << num_fused;
    size_t outer_dim = dim_ >> num_fused;

    // Build qubit masks
    std::vector<uint64_t> q_masks(num_fused);
    for (size_t i = 0; i < num_fused; ++i) {
        q_masks[i] = 1ULL << qubits[i];
    }

    // Identify non-fused qubit indices
    std::vector<size_t> other_qubits;
    for (size_t q = 0; q < num_qubits_; ++q) {
        if (std::find(qubits.begin(), qubits.end(), q) == qubits.end()) {
            other_qubits.push_back(q);
        }
    }

    #pragma omp parallel for schedule(static)
    for (uint64_t i = 0; i < outer_dim; ++i) {
        uint64_t base_idx = 0;
        for (size_t b = 0; b < other_qubits.size(); ++b) {
            if ((i >> b) & 1ULL) {
                base_idx |= (1ULL << other_qubits[b]);
            }
        }

        std::vector<uint64_t> indices(k_dim);
        std::vector<complex_t> vec(k_dim);

        for (size_t s = 0; s < k_dim; ++s) {
            uint64_t idx = base_idx;
            for (size_t bit = 0; bit < num_fused; ++bit) {
                if ((s >> bit) & 1ULL) {
                    idx |= q_masks[bit];
                }
            }
            indices[s] = idx;
            vec[s] = amplitudes_[idx];
        }

        for (size_t r = 0; r < k_dim; ++r) {
            complex_t acc(0.0, 0.0);
            for (size_t c = 0; c < k_dim; ++c) {
                acc += U[r * k_dim + c] * vec[c];
            }
            amplitudes_[indices[r]] = acc;
        }
    }
}

double StateVector::measure_probability(size_t target, int outcome) const {
    if (target >= num_qubits_) {
        throw std::out_of_range("Target qubit index out of range");
    }
    const uint64_t m = 1ULL << target;
    double p = 0.0;

    #pragma omp parallel for reduction(+:p) schedule(static)
    for (uint64_t i = 0; i < dim_; ++i) {
        int bit = (i & m) ? 1 : 0;
        if (bit == outcome) {
            p += std::norm(amplitudes_[i]);
        }
    }
    return p;
}

void StateVector::collapse(size_t target, int outcome) {
    double p = measure_probability(target, outcome);
    if (p < 1e-15) {
        throw std::runtime_error("Attempted to collapse to zero-probability state");
    }
    double factor = 1.0 / std::sqrt(p);
    const uint64_t m = 1ULL << target;

    #pragma omp parallel for schedule(static)
    for (uint64_t i = 0; i < dim_; ++i) {
        int bit = (i & m) ? 1 : 0;
        if (bit == outcome) {
            amplitudes_[i] *= factor;
        } else {
            amplitudes_[i] = complex_t(0.0, 0.0);
        }
    }
}

int StateVector::measure(size_t target, double rand_val) {
    double p0 = measure_probability(target, 0);
    int outcome = (rand_val < p0) ? 0 : 1;
    collapse(target, outcome);
    return outcome;
}

double StateVector::norm_squared() const {
    double sum = 0.0;
    #pragma omp parallel for reduction(+:sum) schedule(static)
    for (uint64_t i = 0; i < dim_; ++i) {
        sum += std::norm(amplitudes_[i]);
    }
    return sum;
}

void StateVector::normalize() {
    double n2 = norm_squared();
    if (n2 > 0.0) {
        double factor = 1.0 / std::sqrt(n2);
        #pragma omp parallel for schedule(static)
        for (uint64_t i = 0; i < dim_; ++i) {
            amplitudes_[i] *= factor;
        }
    }
}

std::vector<double> StateVector::probabilities() const {
    std::vector<double> probs(dim_);
    #pragma omp parallel for schedule(static)
    for (uint64_t i = 0; i < dim_; ++i) {
        probs[i] = std::norm(amplitudes_[i]);
    }
    return probs;
}

std::vector<uint64_t> StateVector::sample(size_t num_shots, uint64_t seed) const {
    std::vector<double> probs = probabilities();
    std::vector<double> cdf(dim_);
    double cum = 0.0;
    for (size_t i = 0; i < dim_; ++i) {
        cum += probs[i];
        cdf[i] = cum;
    }

    std::mt19937_64 rng(seed);
    std::uniform_real_distribution<double> dist(0.0, 1.0);

    std::vector<uint64_t> results(num_shots);
    for (size_t s = 0; s < num_shots; ++s) {
        double r = dist(rng);
        auto it = std::lower_bound(cdf.begin(), cdf.end(), r);
        size_t idx = std::distance(cdf.begin(), it);
        if (idx >= dim_) idx = dim_ - 1;
        results[s] = idx;
    }
    return results;
}

complex_t StateVector::expectation_value_pauli(const std::string& pauli_str, const std::vector<size_t>& qubits) const {
    if (pauli_str.size() != qubits.size()) {
        throw std::invalid_argument("Pauli string length must match qubits size");
    }

    complex_t exp_val(0.0, 0.0);

    for (uint64_t i = 0; i < dim_; ++i) {
        complex_t a_i = amplitudes_[i];
        if (std::norm(a_i) < 1e-18) continue;

        uint64_t j = i;
        complex_t phase(1.0, 0.0);

        for (size_t p = 0; p < pauli_str.size(); ++p) {
            char op = pauli_str[p];
            size_t q = qubits[p];
            uint64_t bit = (i >> q) & 1ULL;

            if (op == 'X') {
                j ^= (1ULL << q);
            } else if (op == 'Y') {
                j ^= (1ULL << q);
                phase *= (bit == 0) ? complex_t(0, 1) : complex_t(0, -1);
            } else if (op == 'Z') {
                if (bit == 1) phase *= -1.0;
            }
        }

        exp_val += std::conj(amplitudes_[j]) * phase * a_i;
    }

    return exp_val;
}

std::vector<complex_t> StateVector::partial_trace(const std::vector<size_t>& keep_qubits) const {
    size_t k = keep_qubits.size();
    size_t k_dim = 1ULL << k;
    std::vector<complex_t> rho(k_dim * k_dim, complex_t(0.0, 0.0));

    std::vector<size_t> traced_qubits;
    for (size_t q = 0; q < num_qubits_; ++q) {
        if (std::find(keep_qubits.begin(), keep_qubits.end(), q) == keep_qubits.end()) {
            traced_qubits.push_back(q);
        }
    }
    size_t t_dim = 1ULL << traced_qubits.size();

    for (uint64_t r = 0; r < k_dim; ++r) {
        for (uint64_t c = 0; c < k_dim; ++c) {
            complex_t sum(0.0, 0.0);
            for (uint64_t env = 0; env < t_dim; ++env) {
                uint64_t idx_r = 0;
                uint64_t idx_c = 0;

                for (size_t bit = 0; bit < k; ++bit) {
                    if ((r >> bit) & 1ULL) idx_r |= (1ULL << keep_qubits[bit]);
                    if ((c >> bit) & 1ULL) idx_c |= (1ULL << keep_qubits[bit]);
                }
                for (size_t bit = 0; bit < traced_qubits.size(); ++bit) {
                    if ((env >> bit) & 1ULL) {
                        idx_r |= (1ULL << traced_qubits[bit]);
                        idx_c |= (1ULL << traced_qubits[bit]);
                    }
                }

                sum += amplitudes_[idx_r] * std::conj(amplitudes_[idx_c]);
            }
            rho[r * k_dim + c] = sum;
        }
    }
    return rho;
}

// Jacobi eigenvalue algorithm for Hermitian matrix
static std::vector<double> hermitian_eigenvalues(const std::vector<complex_t>& mat, size_t n) {
    // For small subsystems (up to 4 qubits: n <= 16)
    // Convert to real symmetric if diagonal or use standard Jacobi
    std::vector<double> d(n);
    std::vector<std::vector<complex_t>> A(n, std::vector<complex_t>(n));
    for (size_t i = 0; i < n; ++i) {
        for (size_t j = 0; j < n; ++j) {
            A[i][j] = mat[i * n + j];
        }
    }

    // Jacobi rotations for Hermitian matrix
    for (int iter = 0; iter < 100; ++iter) {
        double max_offdiag = 0.0;
        size_t p = 0, q = 1;
        for (size_t i = 0; i < n; ++i) {
            for (size_t j = i + 1; j < n; ++j) {
                double val = std::abs(A[i][j]);
                if (val > max_offdiag) {
                    max_offdiag = val;
                    p = i;
                    q = j;
                }
            }
        }
        if (max_offdiag < 1e-12) break;

        // Diagonalize 2x2 submatrix at (p, q)
        double app = A[p][p].real();
        double aqq = A[q][q].real();
        complex_t apq = A[p][q];

        double theta = 0.5 * std::atan2(2.0 * std::abs(apq), app - aqq);
        complex_t phase = apq / std::abs(apq);
        double c = std::cos(theta);
        complex_t s = std::sin(theta) * phase;

        // Apply rotation
        for (size_t i = 0; i < n; ++i) {
            if (i != p && i != q) {
                complex_t aip = A[i][p];
                complex_t aiq = A[i][q];
                A[i][p] = c * aip + std::conj(s) * aiq;
                A[p][i] = std::conj(A[i][p]);
                A[i][q] = -s * aip + c * aiq;
                A[q][i] = std::conj(A[i][q]);
            }
        }
        complex_t new_app = c * c * app + std::norm(s) * aqq + 2.0 * (c * std::conj(s) * apq).real();
        complex_t new_aqq = std::norm(s) * app + c * c * aqq - 2.0 * (c * std::conj(s) * apq).real();
        A[p][p] = new_app.real();
        A[q][q] = new_aqq.real();
        A[p][q] = complex_t(0, 0);
        A[q][p] = complex_t(0, 0);
    }

    for (size_t i = 0; i < n; ++i) {
        d[i] = A[i][i].real();
    }
    return d;
}

double StateVector::von_neumann_entropy(const std::vector<size_t>& subsystem_qubits) const {
    size_t k = subsystem_qubits.size();
    if (k == 0 || k == num_qubits_) return 0.0;

    std::vector<complex_t> rho = partial_trace(subsystem_qubits);
    size_t k_dim = 1ULL << k;

    std::vector<double> eigs = hermitian_eigenvalues(rho, k_dim);
    double entropy = 0.0;
    for (double lam : eigs) {
        if (lam > 1e-14) {
            entropy -= lam * std::log2(lam);
        }
    }
    return std::max(0.0, entropy);
}

} // namespace invariantq
