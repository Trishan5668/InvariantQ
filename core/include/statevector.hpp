#pragma once

#include "types.hpp"
#include <vector>
#include <random>
#include <numeric>
#include <stdexcept>
#include <cmath>

namespace invariantq {

class StateVector {
public:
    explicit StateVector(size_t num_qubits);
    ~StateVector() = default;

    size_t num_qubits() const { return num_qubits_; }
    size_t dim() const { return dim_; }

    void reset();
    void set_amplitudes(const complex_t* data, size_t size);
    const complex_t* data() const { return amplitudes_.data(); }
    complex_t* data() { return amplitudes_.data(); }

    void apply_1q_gate(size_t target, const complex_t U[4]);
    void apply_2q_gate(size_t q0, size_t q1, const complex_t U[16]);
    void apply_fused_gate(const std::vector<size_t>& qubits, const complex_t* U, size_t k);

    int measure(size_t target, double rand_val);
    double measure_probability(size_t target, int outcome) const;
    void collapse(size_t target, int outcome);

    double norm_squared() const;
    void normalize();

    std::vector<double> probabilities() const;
    std::vector<uint64_t> sample(size_t num_shots, uint64_t seed) const;

    complex_t expectation_value_pauli(const std::string& pauli_str, const std::vector<size_t>& qubits) const;
    std::vector<complex_t> partial_trace(const std::vector<size_t>& keep_qubits) const;
    double von_neumann_entropy(const std::vector<size_t>& subsystem_qubits) const;

private:
    size_t num_qubits_;
    size_t dim_;
    std::vector<complex_t> amplitudes_;
};

} // namespace invariantq
