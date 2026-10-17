#pragma once

#include "types.hpp"
#include <vector>
#include <stdexcept>

namespace invariantq {

class DensityMatrix {
public:
    explicit DensityMatrix(size_t num_qubits);
    ~DensityMatrix() = default;

    size_t num_qubits() const { return num_qubits_; }
    size_t dim() const { return dim_; }

    void reset();
    const complex_t* data() const { return rho_.data(); }
    complex_t* data() { return rho_.data(); }

    void apply_1q_unitary(size_t target, const complex_t U[4]);
    void apply_2q_unitary(size_t q0, size_t q1, const complex_t U[16]);
    void apply_1q_kraus(size_t target, const std::vector<Gate1Q>& kraus_ops);
    void apply_kraus(const std::vector<size_t>& qubits, const std::vector<std::vector<complex_t>>& kraus_ops, size_t k);

    double trace() const;
    double purity() const;
    std::vector<double> diagonal_probabilities() const;

    int measure(size_t target, double rand_val);
    double measure_probability(size_t target, int outcome) const;
    void collapse(size_t target, int outcome);

    std::vector<complex_t> partial_trace(const std::vector<size_t>& keep_qubits) const;
    double von_neumann_entropy() const;

private:
    size_t num_qubits_;
    size_t dim_;
    std::vector<complex_t> rho_; // Size dim_ * dim_
};

} // namespace invariantq
