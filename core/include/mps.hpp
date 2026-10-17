#pragma once

#include "types.hpp"
#include <vector>
#include <memory>
#include <string>

namespace invariantq {

// Tensor representation for MPS site
struct MPSTensor {
    size_t dl; // left bond dim
    size_t dr; // right bond dim
    // shape: dl x 2 x dr. Flat index: (l * 2 + s) * dr + r
    std::vector<complex_t> data;

    MPSTensor(size_t l, size_t r) : dl(l), dr(r), data(l * 2 * r, complex_t(0, 0)) {}

    complex_t& at(size_t l, size_t s, size_t r) {
        return data[(l * 2 + s) * dr + r];
    }
    const complex_t& at(size_t l, size_t s, size_t r) const {
        return data[(l * 2 + s) * dr + r];
    }
};

class MPSSimulator {
public:
    MPSSimulator(size_t num_qubits, size_t max_bond_dim = 64, double svd_cutoff = 1e-12);
    ~MPSSimulator() = default;

    size_t num_qubits() const { return num_qubits_; }
    size_t max_bond_dim() const { return max_bond_dim_; }

    void reset();

    void apply_1q_gate(size_t target, const complex_t U[4]);
    void apply_2q_gate_adjacent(size_t i, const complex_t U[16]);
    void apply_2q_gate(size_t q0, size_t q1, const complex_t U[16]);

    double entanglement_entropy(size_t bond_idx) const;
    std::vector<double> get_bond_dimensions() const;

    // Measurement & sampling
    double measure_probability(size_t target, int outcome);
    int measure(size_t target, double rand_val);

    // Reconstruct full state vector (for differential verification on small circuits)
    std::vector<complex_t> to_statevector() const;

private:
    size_t num_qubits_;
    size_t max_bond_dim_;
    double svd_cutoff_;
    std::vector<MPSTensor> tensors_;
    std::vector<std::vector<double>> singular_values_; // singular values at each bond [0 .. n-2]

    void decompose_two_site(size_t i, const std::vector<complex_t>& theta, size_t dl, size_t dr);
};

} // namespace invariantq
