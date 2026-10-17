#pragma once

#include <vector>
#include <string>
#include <cstdint>
#include <stdexcept>

namespace invariantq {

class StabilizerSimulator {
public:
    explicit StabilizerSimulator(size_t num_qubits);
    ~StabilizerSimulator() = default;

    size_t num_qubits() const { return num_qubits_; }

    void reset();

    // Clifford Gates
    void apply_h(size_t a);
    void apply_s(size_t a);
    void apply_sdg(size_t a);
    void apply_cnot(size_t a, size_t b);
    void apply_cz(size_t a, size_t b);
    void apply_swap(size_t a, size_t b);
    void apply_x(size_t a);
    void apply_y(size_t a);
    void apply_z(size_t a);

    // Measurement
    int measure(size_t a, double rand_val);

    // Diagnostics & extraction
    std::string to_string() const;
    bool is_stabilizer_row(size_t row_idx) const;
    std::string get_pauli_row(size_t row_idx) const;

private:
    size_t num_qubits_;
    size_t rows_; // 2 * num_qubits_
    // Tableau data: rows_ x num_qubits_ for X, rows_ x num_qubits_ for Z, and rows_ for r
    std::vector<uint8_t> x_;
    std::vector<uint8_t> z_;
    std::vector<uint8_t> r_; // phase: 0 for +1, 1 for -1

    int g_func(uint8_t x1, uint8_t z1, uint8_t x2, uint8_t z2) const;
    void row_mult(size_t target_row, size_t source_row);
};

} // namespace invariantq
