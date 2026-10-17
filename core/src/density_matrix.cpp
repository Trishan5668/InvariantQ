#include "density_matrix.hpp"
#include <algorithm>
#include <cmath>
#include <omp.h>

namespace invariantq {

DensityMatrix::DensityMatrix(size_t num_qubits)
    : num_qubits_(num_qubits), dim_(1ULL << num_qubits), rho_(dim_ * dim_, complex_t(0.0, 0.0)) {
    rho_[0] = complex_t(1.0, 0.0);
}

void DensityMatrix::reset() {
    std::fill(rho_.begin(), rho_.end(), complex_t(0.0, 0.0));
    rho_[0] = complex_t(1.0, 0.0);
}

void DensityMatrix::apply_1q_unitary(size_t target, const complex_t U[4]) {
    if (target >= num_qubits_) {
        throw std::out_of_range("Target qubit out of range");
    }

    const uint64_t m = 1ULL << target;
    const uint64_t mask_low = m - 1;
    const uint64_t mask_high = ~mask_low;
    const uint64_t half_dim = dim_ >> 1;

    std::vector<complex_t> next_rho(dim_ * dim_, complex_t(0.0, 0.0));

    // Left multiplication: rho' = U * rho
    // For each column c:
    #pragma omp parallel for schedule(static)
    for (uint64_t c = 0; c < dim_; ++c) {
        for (uint64_t i = 0; i < half_dim; ++i) {
            uint64_t r0 = ((i & mask_high) << 1) | (i & mask_low);
            uint64_t r1 = r0 | m;

            complex_t a = rho_[r0 * dim_ + c];
            complex_t b = rho_[r1 * dim_ + c];

            next_rho[r0 * dim_ + c] = U[0] * a + U[1] * b;
            next_rho[r1 * dim_ + c] = U[2] * a + U[3] * b;
        }
    }

    // Right multiplication: rho'' = rho' * U^\dagger
    // For each row r:
    complex_t Udag[4] = {
        std::conj(U[0]), std::conj(U[2]),
        std::conj(U[1]), std::conj(U[3])
    };

    #pragma omp parallel for schedule(static)
    for (uint64_t r = 0; r < dim_; ++r) {
        for (uint64_t i = 0; i < half_dim; ++i) {
            uint64_t c0 = ((i & mask_high) << 1) | (i & mask_low);
            uint64_t c1 = c0 | m;

            complex_t a = next_rho[r * dim_ + c0];
            complex_t b = next_rho[r * dim_ + c1];

            // row vector [a, b] * Udag
            rho_[r * dim_ + c0] = a * Udag[0] + b * Udag[2];
            rho_[r * dim_ + c1] = a * Udag[1] + b * Udag[3];
        }
    }
}

void DensityMatrix::apply_2q_unitary(size_t q0, size_t q1, const complex_t U[16]) {
    if (q0 >= num_qubits_ || q1 >= num_qubits_ || q0 == q1) {
        throw std::invalid_argument("Invalid qubit indices");
    }

    size_t q_low = std::min(q0, q1);
    size_t q_high = std::max(q0, q1);
    uint64_t quarter_dim = dim_ >> 2;

    std::vector<complex_t> next_rho(dim_ * dim_, complex_t(0.0, 0.0));

    // Left mult
    #pragma omp parallel for schedule(static)
    for (uint64_t c = 0; c < dim_; ++c) {
        for (uint64_t i = 0; i < quarter_dim; ++i) {
            uint64_t low = i & ((1ULL << q_low) - 1);
            uint64_t mid = (i >> q_low) & ((1ULL << (q_high - q_low - 1)) - 1);
            uint64_t high = i >> (q_high - 1);

            uint64_t i00 = (high << (q_high + 1)) | (mid << (q_low + 1)) | low;

            uint64_t idx[4];
            idx[0] = i00;
            idx[1] = i00 | (1ULL << q1);
            idx[2] = i00 | (1ULL << q0);
            idx[3] = i00 | (1ULL << q0) | (1ULL << q1);

            complex_t v[4];
            for (int k = 0; k < 4; ++k) v[k] = rho_[idx[k] * dim_ + c];

            for (int r = 0; r < 4; ++r) {
                complex_t res = U[r * 4 + 0] * v[0] +
                                U[r * 4 + 1] * v[1] +
                                U[r * 4 + 2] * v[2] +
                                U[r * 4 + 3] * v[3];
                next_rho[idx[r] * dim_ + c] = res;
            }
        }
    }

    // Compute U^\dagger
    complex_t Udag[16];
    for (int r = 0; r < 4; ++r) {
        for (int col = 0; col < 4; ++col) {
            Udag[r * 4 + col] = std::conj(U[col * 4 + r]);
        }
    }

    // Right mult: rho = next_rho * U^\dagger
    #pragma omp parallel for schedule(static)
    for (uint64_t r = 0; r < dim_; ++r) {
        for (uint64_t i = 0; i < quarter_dim; ++i) {
            uint64_t low = i & ((1ULL << q_low) - 1);
            uint64_t mid = (i >> q_low) & ((1ULL << (q_high - q_low - 1)) - 1);
            uint64_t high = i >> (q_high - 1);

            uint64_t i00 = (high << (q_high + 1)) | (mid << (q_low + 1)) | low;

            uint64_t idx[4];
            idx[0] = i00;
            idx[1] = i00 | (1ULL << q1);
            idx[2] = i00 | (1ULL << q0);
            idx[3] = i00 | (1ULL << q0) | (1ULL << q1);

            complex_t v[4];
            for (int k = 0; k < 4; ++k) v[k] = next_rho[r * dim_ + idx[k]];

            for (int col = 0; col < 4; ++col) {
                complex_t res = v[0] * Udag[0 * 4 + col] +
                                v[1] * Udag[1 * 4 + col] +
                                v[2] * Udag[2 * 4 + col] +
                                v[3] * Udag[3 * 4 + col];
                rho_[r * dim_ + idx[col]] = res;
            }
        }
    }
}

void DensityMatrix::apply_1q_kraus(size_t target, const std::vector<Gate1Q>& kraus_ops) {
    if (target >= num_qubits_) {
        throw std::out_of_range("Target qubit out of range");
    }

    std::vector<complex_t> result(dim_ * dim_, complex_t(0.0, 0.0));
    std::vector<complex_t> initial_rho = rho_;

    for (const auto& k_op : kraus_ops) {
        rho_ = initial_rho;
        apply_1q_unitary(target, k_op.m);
        for (size_t i = 0; i < dim_ * dim_; ++i) {
            result[i] += rho_[i];
        }
    }
    rho_ = std::move(result);
}

void DensityMatrix::apply_kraus(const std::vector<size_t>& qubits, const std::vector<std::vector<complex_t>>& kraus_ops, size_t k) {
    if (k == 1) {
        std::vector<Gate1Q> ops;
        for (const auto& vec : kraus_ops) {
            Gate1Q g;
            for (int i = 0; i < 4; ++i) g.m[i] = vec[i];
            ops.push_back(g);
        }
        apply_1q_kraus(qubits[0], ops);
        return;
    }
    // For multi-qubit Kraus channels, sum over K_i rho K_i^\dagger
    // implemented similarly via unitary projection summation
    std::vector<complex_t> result(dim_ * dim_, complex_t(0.0, 0.0));
    std::vector<complex_t> initial_rho = rho_;

    for (const auto& k_mat : kraus_ops) {
        rho_ = initial_rho;
        if (k == 2) {
            apply_2q_unitary(qubits[0], qubits[1], k_mat.data());
        }
        for (size_t i = 0; i < dim_ * dim_; ++i) {
            result[i] += rho_[i];
        }
    }
    rho_ = std::move(result);
}

double DensityMatrix::trace() const {
    complex_t tr(0.0, 0.0);
    for (size_t i = 0; i < dim_; ++i) {
        tr += rho_[i * dim_ + i];
    }
    return tr.real();
}

double DensityMatrix::purity() const {
    double pur = 0.0;
    #pragma omp parallel for reduction(+:pur) schedule(static)
    for (size_t i = 0; i < dim_ * dim_; ++i) {
        pur += std::norm(rho_[i]);
    }
    return pur;
}

std::vector<double> DensityMatrix::diagonal_probabilities() const {
    std::vector<double> probs(dim_);
    for (size_t i = 0; i < dim_; ++i) {
        probs[i] = std::max(0.0, rho_[i * dim_ + i].real());
    }
    return probs;
}

double DensityMatrix::measure_probability(size_t target, int outcome) const {
    if (target >= num_qubits_) throw std::out_of_range("Qubit out of range");
    uint64_t m = 1ULL << target;
    double p = 0.0;
    for (uint64_t i = 0; i < dim_; ++i) {
        int bit = (i & m) ? 1 : 0;
        if (bit == outcome) {
            p += rho_[i * dim_ + i].real();
        }
    }
    return std::max(0.0, p);
}

void DensityMatrix::collapse(size_t target, int outcome) {
    double p = measure_probability(target, outcome);
    if (p < 1e-15) throw std::runtime_error("Cannot collapse to zero-probability outcome");
    double factor = 1.0 / p;
    uint64_t m = 1ULL << target;

    #pragma omp parallel for schedule(static)
    for (uint64_t r = 0; r < dim_; ++r) {
        int bit_r = (r & m) ? 1 : 0;
        for (uint64_t c = 0; c < dim_; ++c) {
            int bit_c = (c & m) ? 1 : 0;
            if (bit_r == outcome && bit_c == outcome) {
                rho_[r * dim_ + c] *= factor;
            } else {
                rho_[r * dim_ + c] = complex_t(0.0, 0.0);
            }
        }
    }
}

int DensityMatrix::measure(size_t target, double rand_val) {
    double p0 = measure_probability(target, 0);
    int outcome = (rand_val < p0) ? 0 : 1;
    collapse(target, outcome);
    return outcome;
}

std::vector<complex_t> DensityMatrix::partial_trace(const std::vector<size_t>& keep_qubits) const {
    size_t k = keep_qubits.size();
    size_t k_dim = 1ULL << k;
    std::vector<complex_t> reduced(k_dim * k_dim, complex_t(0.0, 0.0));

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

                sum += rho_[idx_r * dim_ + idx_c];
            }
            reduced[r * k_dim + c] = sum;
        }
    }
    return reduced;
}

double DensityMatrix::von_neumann_entropy() const {
    // For small dimensions, diagonalize
    if (dim_ > 64) {
        // Approximate via diagonal for large systems if needed
        double s = 0.0;
        for (size_t i = 0; i < dim_; ++i) {
            double p = std::max(0.0, rho_[i * dim_ + i].real());
            if (p > 1e-14) s -= p * std::log2(p);
        }
        return s;
    }

    // Jacobi eigenvalue algorithm on rho_
    std::vector<std::vector<complex_t>> A(dim_, std::vector<complex_t>(dim_));
    for (size_t i = 0; i < dim_; ++i) {
        for (size_t j = 0; j < dim_; ++j) {
            A[i][j] = rho_[i * dim_ + j];
        }
    }

    for (int iter = 0; iter < 120; ++iter) {
        double max_offdiag = 0.0;
        size_t p = 0, q = 1;
        for (size_t i = 0; i < dim_; ++i) {
            for (size_t j = i + 1; j < dim_; ++j) {
                double val = std::abs(A[i][j]);
                if (val > max_offdiag) {
                    max_offdiag = val;
                    p = i;
                    q = j;
                }
            }
        }
        if (max_offdiag < 1e-13) break;

        double app = A[p][p].real();
        double aqq = A[q][q].real();
        complex_t apq = A[p][q];

        double theta = 0.5 * std::atan2(2.0 * std::abs(apq), app - aqq);
        complex_t phase = apq / std::abs(apq);
        double c = std::cos(theta);
        complex_t s = std::sin(theta) * phase;

        for (size_t i = 0; i < dim_; ++i) {
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

    double entropy = 0.0;
    for (size_t i = 0; i < dim_; ++i) {
        double lam = A[i][i].real();
        if (lam > 1e-14) {
            entropy -= lam * std::log2(lam);
        }
    }
    return std::max(0.0, entropy);
}

} // namespace invariantq
