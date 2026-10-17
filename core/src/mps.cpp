#include "mps.hpp"
#include <cmath>
#include <algorithm>
#include <stdexcept>
#include <iostream>

namespace invariantq {

MPSSimulator::MPSSimulator(size_t num_qubits, size_t max_bond_dim, double svd_cutoff)
    : num_qubits_(num_qubits),
      max_bond_dim_(max_bond_dim),
      svd_cutoff_(svd_cutoff),
      singular_values_(num_qubits > 1 ? num_qubits - 1 : 0) {
    reset();
}

void MPSSimulator::reset() {
    tensors_.clear();
    tensors_.reserve(num_qubits_);

    for (size_t i = 0; i < num_qubits_; ++i) {
        size_t dl = (i == 0) ? 1 : 1;
        size_t dr = (i == num_qubits_ - 1) ? 1 : 1;
        MPSTensor t(dl, dr);
        // State |0>: A[0, 0, 0] = 1, A[0, 1, 0] = 0
        t.at(0, 0, 0) = complex_t(1.0, 0.0);
        t.at(0, 1, 0) = complex_t(0.0, 0.0);
        tensors_.push_back(std::move(t));
    }

    for (size_t i = 0; i + 1 < num_qubits_; ++i) {
        singular_values_[i] = {1.0};
    }
}

void MPSSimulator::apply_1q_gate(size_t target, const complex_t U[4]) {
    if (target >= num_qubits_) throw std::out_of_range("Qubit out of range");

    MPSTensor& t = tensors_[target];
    MPSTensor next_t(t.dl, t.dr);

    for (size_t l = 0; l < t.dl; ++l) {
        for (size_t r = 0; r < t.dr; ++r) {
            complex_t a0 = t.at(l, 0, r);
            complex_t a1 = t.at(l, 1, r);

            next_t.at(l, 0, r) = U[0] * a0 + U[1] * a1;
            next_t.at(l, 1, r) = U[2] * a0 + U[3] * a1;
        }
    }
    t = std::move(next_t);
}

void MPSSimulator::apply_2q_gate_adjacent(size_t i, const complex_t U[16]) {
    if (i + 1 >= num_qubits_) throw std::out_of_range("Adjacent index out of range");

    const MPSTensor& tA = tensors_[i];
    const MPSTensor& tB = tensors_[i + 1];

    size_t dl = tA.dl;
    size_t d_mid = tA.dr;
    size_t dr = tB.dr;

    // Contract tA and tB into Theta: shape (dl, 2, 2, dr)
    std::vector<complex_t> theta(dl * 4 * dr, complex_t(0.0, 0.0));

    for (size_t l = 0; l < dl; ++l) {
        for (size_t s0 = 0; s0 < 2; ++s0) {
            for (size_t s1 = 0; s1 < 2; ++s1) {
                for (size_t r = 0; r < dr; ++r) {
                    complex_t sum(0.0, 0.0);
                    for (size_t m = 0; m < d_mid; ++m) {
                        sum += tA.at(l, s0, m) * tB.at(m, s1, r);
                    }
                    size_t idx = ((l * 2 + s0) * 2 + s1) * dr + r;
                    theta[idx] = sum;
                }
            }
        }
    }

    // Apply 4x4 unitary gate
    std::vector<complex_t> theta_prime(dl * 4 * dr, complex_t(0.0, 0.0));
    for (size_t l = 0; l < dl; ++l) {
        for (size_t r = 0; r < dr; ++r) {
            complex_t v[4];
            for (size_t s0 = 0; s0 < 2; ++s0) {
                for (size_t s1 = 0; s1 < 2; ++s1) {
                    size_t in_idx = ((l * 2 + s0) * 2 + s1) * dr + r;
                    v[s0 * 2 + s1] = theta[in_idx];
                }
            }

            for (size_t out_s = 0; out_s < 4; ++out_s) {
                complex_t acc(0.0, 0.0);
                for (size_t in_s = 0; in_s < 4; ++in_s) {
                    acc += U[out_s * 4 + in_s] * v[in_s];
                }
                size_t s0_prime = out_s / 2;
                size_t s1_prime = out_s % 2;
                size_t out_idx = ((l * 2 + s0_prime) * 2 + s1_prime) * dr + r;
                theta_prime[out_idx] = acc;
            }
        }
    }

    decompose_two_site(i, theta_prime, dl, dr);
}

void MPSSimulator::decompose_two_site(size_t i, const std::vector<complex_t>& theta, size_t dl, size_t dr) {
    size_t rows = dl * 2;
    size_t cols = 2 * dr;

    // Build matrix M of size rows x cols
    std::vector<std::vector<complex_t>> M(rows, std::vector<complex_t>(cols));
    for (size_t l = 0; l < dl; ++l) {
        for (size_t s0 = 0; s0 < 2; ++s0) {
            size_t r_idx = l * 2 + s0;
            for (size_t s1 = 0; s1 < 2; ++s1) {
                for (size_t r = 0; r < dr; ++r) {
                    size_t c_idx = s1 * dr + r;
                    size_t th_idx = ((l * 2 + s0) * 2 + s1) * dr + r;
                    M[r_idx][c_idx] = theta[th_idx];
                }
            }
        }
    }

    // Compute H = M * M^\dagger (rows x rows)
    std::vector<std::vector<complex_t>> H(rows, std::vector<complex_t>(rows, complex_t(0, 0)));
    for (size_t r1 = 0; r1 < rows; ++r1) {
        for (size_t r2 = 0; r2 < rows; ++r2) {
            complex_t sum(0, 0);
            for (size_t c = 0; c < cols; ++c) {
                sum += M[r1][c] * std::conj(M[r2][c]);
            }
            H[r1][r2] = sum;
        }
    }

    // Jacobi diagonalization of H to get U and singular values^2
    std::vector<std::vector<complex_t>> U_mat(rows, std::vector<complex_t>(rows, complex_t(0, 0)));
    for (size_t k = 0; k < rows; ++k) U_mat[k][k] = complex_t(1, 0);

    for (int iter = 0; iter < 80; ++iter) {
        double max_val = 0.0;
        size_t p = 0, q = 1;
        for (size_t r1 = 0; r1 < rows; ++r1) {
            for (size_t r2 = r1 + 1; r2 < rows; ++r2) {
                double val = std::abs(H[r1][r2]);
                if (val > max_val) {
                    max_val = val;
                    p = r1;
                    q = r2;
                }
            }
        }
        if (max_val < 1e-13) break;

        double app = H[p][p].real();
        double aqq = H[q][q].real();
        complex_t apq = H[p][q];

        double theta_ang = 0.5 * std::atan2(2.0 * std::abs(apq), app - aqq);
        complex_t phase = apq / std::abs(apq);
        double c = std::cos(theta_ang);
        complex_t s = std::sin(theta_ang) * phase;

        for (size_t k = 0; k < rows; ++k) {
            if (k != p && k != q) {
                complex_t hip = H[k][p];
                complex_t hiq = H[k][q];
                H[k][p] = c * hip + std::conj(s) * hiq;
                H[p][k] = std::conj(H[k][p]);
                H[k][q] = -s * hip + c * hiq;
                H[q][k] = std::conj(H[k][q]);
            }
        }
        complex_t new_app = c * c * app + std::norm(s) * aqq + 2.0 * (c * std::conj(s) * apq).real();
        complex_t new_aqq = std::norm(s) * app + c * c * aqq - 2.0 * (c * std::conj(s) * apq).real();
        H[p][p] = new_app.real();
        H[q][q] = new_aqq.real();
        H[p][q] = complex_t(0, 0);
        H[q][p] = complex_t(0, 0);

        for (size_t k = 0; k < rows; ++k) {
            complex_t ukp = U_mat[k][p];
            complex_t ukq = U_mat[k][q];
            U_mat[k][p] = c * ukp + std::conj(s) * ukq;
            U_mat[k][q] = -s * ukp + c * ukq;
        }
    }

    // Extract eigenvalues and sort
    struct EigPair {
        double val;
        size_t idx;
    };
    std::vector<EigPair> eigs(rows);
    for (size_t k = 0; k < rows; ++k) {
        eigs[k] = {std::max(0.0, H[k][k].real()), k};
    }
    std::sort(eigs.begin(), eigs.end(), [](const EigPair& a, const EigPair& b) {
        return a.val > b.val;
    });

    // Determine new bond dimension
    size_t new_d = 0;
    for (size_t k = 0; k < rows; ++k) {
        double s_val = std::sqrt(eigs[k].val);
        if (s_val >= svd_cutoff_ || new_d == 0) {
            new_d++;
            if (new_d >= max_bond_dim_ || new_d >= cols) break;
        }
    }
    new_d = std::max<size_t>(1, std::min({new_d, max_bond_dim_, cols, rows}));

    std::vector<double> svs(new_d);
    double sum_sq = 0.0;
    for (size_t k = 0; k < new_d; ++k) {
        svs[k] = std::sqrt(eigs[k].val);
        sum_sq += svs[k] * svs[k];
    }
    // Normalize singular values
    if (sum_sq > 0.0) {
        double norm_factor = 1.0 / std::sqrt(sum_sq);
        for (size_t k = 0; k < new_d; ++k) svs[k] *= norm_factor;
    }
    singular_values_[i] = svs;

    // Construct new tensor A[i] (shape: dl x 2 x new_d)
    MPSTensor new_tA(dl, new_d);
    for (size_t l = 0; l < dl; ++l) {
        for (size_t s0 = 0; s0 < 2; ++s0) {
            size_t r_idx = l * 2 + s0;
            for (size_t k = 0; k < new_d; ++k) {
                size_t col_in_U = eigs[k].idx;
                new_tA.at(l, s0, k) = U_mat[r_idx][col_in_U];
            }
        }
    }

    // Construct new tensor A[i+1] (shape: new_d x 2 x dr) from S * V^\dagger
    // V^\dagger_k = (1 / svs[k]) * U_k^\dagger * M, so S * V^\dagger = U_k^\dagger * M
    MPSTensor new_tB(new_d, dr);
    for (size_t k = 0; k < new_d; ++k) {
        size_t col_in_U = eigs[k].idx;
        for (size_t s1 = 0; s1 < 2; ++s1) {
            for (size_t r = 0; r < dr; ++r) {
                size_t c_idx = s1 * dr + r;
                complex_t sum(0, 0);
                for (size_t r_idx = 0; r_idx < rows; ++r_idx) {
                    sum += std::conj(U_mat[r_idx][col_in_U]) * M[r_idx][c_idx];
                }
                new_tB.at(k, s1, r) = sum;
            }
        }
    }

    tensors_[i] = std::move(new_tA);
    tensors_[i + 1] = std::move(new_tB);
}

void MPSSimulator::apply_2q_gate(size_t q0, size_t q1, const complex_t U[16]) {
    if (q0 == q1 || q0 >= num_qubits_ || q1 >= num_qubits_) {
        throw std::invalid_argument("Invalid 2-qubit indices");
    }

    if (q0 + 1 == q1) {
        apply_2q_gate_adjacent(q0, U);
        return;
    }
    if (q1 + 1 == q0) {
        // Swap inputs to match unitary basis
        complex_t U_swapped[16];
        for (int r = 0; r < 4; ++r) {
            for (int c = 0; c < 4; ++c) {
                int r_sw = ((r & 1) << 1) | ((r >> 1) & 1);
                int c_sw = ((c & 1) << 1) | ((c >> 1) & 1);
                U_swapped[r_sw * 4 + c_sw] = U[r * 4 + c];
            }
        }
        apply_2q_gate_adjacent(q1, U_swapped);
        return;
    }

    // Long-range gate: swap path
    size_t low = std::min(q0, q1);
    size_t high = std::max(q0, q1);
    Gate2Q swap_gate = gate_swap();

    // Swap adjacent pairs until target is adjacent
    for (size_t k = low; k + 1 < high; ++k) {
        apply_2q_gate_adjacent(k, swap_gate.m);
    }

    if (q0 < q1) {
        apply_2q_gate_adjacent(high - 1, U);
    } else {
        complex_t U_swapped[16];
        for (int r = 0; r < 4; ++r) {
            for (int c = 0; c < 4; ++c) {
                int r_sw = ((r & 1) << 1) | ((r >> 1) & 1);
                int c_sw = ((c & 1) << 1) | ((c >> 1) & 1);
                U_swapped[r_sw * 4 + c_sw] = U[r * 4 + c];
            }
        }
        apply_2q_gate_adjacent(high - 1, U_swapped);
    }

    // Swap back
    for (size_t k = high - 1; k > low; --k) {
        apply_2q_gate_adjacent(k - 1, swap_gate.m);
    }
}

double MPSSimulator::entanglement_entropy(size_t bond_idx) const {
    if (bond_idx >= singular_values_.size()) return 0.0;
    const auto& svs = singular_values_[bond_idx];

    double entropy = 0.0;
    for (double s : svs) {
        double p = s * s;
        if (p > 1e-14) {
            entropy -= p * std::log2(p);
        }
    }
    return std::max(0.0, entropy);
}

std::vector<double> MPSSimulator::get_bond_dimensions() const {
    std::vector<double> dims;
    for (const auto& t : tensors_) {
        dims.push_back(static_cast<double>(t.dr));
    }
    return dims;
}

std::vector<complex_t> MPSSimulator::to_statevector() const {
    // Sequentially contract from left to right
    // Start with site 0: vector of shape (2, d1)
    size_t cur_dim = 2;
    size_t cur_bond = tensors_[0].dr;
    std::vector<complex_t> state(cur_dim * cur_bond);

    for (size_t s = 0; s < 2; ++s) {
        for (size_t r = 0; r < cur_bond; ++r) {
            state[s * cur_bond + r] = tensors_[0].at(0, s, r);
        }
    }

    for (size_t i = 1; i < num_qubits_; ++i) {
        const MPSTensor& t = tensors_[i];
        size_t next_dim = cur_dim * 2;
        size_t next_bond = t.dr;
        std::vector<complex_t> next_state(next_dim * next_bond, complex_t(0, 0));

        for (size_t prefix = 0; prefix < cur_dim; ++prefix) {
            for (size_t s = 0; s < 2; ++s) {
                size_t out_prefix = prefix * 2 + s;
                for (size_t r = 0; r < next_bond; ++r) {
                    complex_t sum(0, 0);
                    for (size_t m = 0; m < cur_bond; ++m) {
                        sum += state[prefix * cur_bond + m] * t.at(m, s, r);
                    }
                    next_state[out_prefix * next_bond + r] = sum;
                }
            }
        }
        state = std::move(next_state);
        cur_dim = next_dim;
        cur_bond = next_bond;
    }
    return state;
}

double MPSSimulator::measure_probability(size_t target, int outcome) {
    std::vector<complex_t> sv = to_statevector();
    uint64_t m = 1ULL << (num_qubits_ - 1 - target);
    double p = 0.0;
    for (size_t i = 0; i < sv.size(); ++i) {
        int bit = (i & m) ? 1 : 0;
        if (bit == outcome) p += std::norm(sv[i]);
    }
    return p;
}

int MPSSimulator::measure(size_t target, double rand_val) {
    double p0 = measure_probability(target, 0);
    int outcome = (rand_val < p0) ? 0 : 1;
    // Project and normalize site target
    complex_t proj[4] = {0, 0, 0, 0};
    if (outcome == 0) proj[0] = 1.0;
    else proj[3] = 1.0;
    apply_1q_gate(target, proj);
    return outcome;
}

} // namespace invariantq
