#include "stabilizer.hpp"
#include <sstream>
#include <iostream>

namespace invariantq {

StabilizerSimulator::StabilizerSimulator(size_t num_qubits)
    : num_qubits_(num_qubits),
      rows_(2 * num_qubits),
      x_(rows_ * num_qubits, 0),
      z_(rows_ * num_qubits, 0),
      r_(rows_, 0) {
    reset();
}

void StabilizerSimulator::reset() {
    std::fill(x_.begin(), x_.end(), 0);
    std::fill(z_.begin(), z_.end(), 0);
    std::fill(r_.begin(), r_.end(), 0);

    // Initial state |0...0>
    // Destabilizers: R_i = X_i
    for (size_t i = 0; i < num_qubits_; ++i) {
        x_[i * num_qubits_ + i] = 1;
    }
    // Stabilizers: R_{n+i} = Z_i
    for (size_t i = 0; i < num_qubits_; ++i) {
        z_[(num_qubits_ + i) * num_qubits_ + i] = 1;
    }
}

int StabilizerSimulator::g_func(uint8_t x1, uint8_t z1, uint8_t x2, uint8_t z2) const {
    if (x1 == 0 && z1 == 0) return 0;
    if (x1 == 1 && z1 == 1) {
        // Y * P
        if (x2 == 1 && z2 == 0) return 1;  // Y * X = -i Z
        if (x2 == 0 && z2 == 1) return -1; // Y * Z = i X
        return 0;
    }
    if (x1 == 1 && z1 == 0) {
        // X * P
        if (x2 == 0 && z2 == 1) return 1;  // X * Z = -i Y
        if (x2 == 1 && z2 == 1) return -1; // X * Y = i Z
        return 0;
    }
    if (x1 == 0 && z1 == 1) {
        // Z * P
        if (x2 == 1 && z2 == 1) return 1;  // Z * Y = -i X
        if (x2 == 1 && z2 == 0) return -1; // Z * X = i Y
        return 0;
    }
    return 0;
}

void StabilizerSimulator::row_mult(size_t target_row, size_t source_row) {
    int sum_g = 0;
    for (size_t j = 0; j < num_qubits_; ++j) {
        uint8_t x1 = x_[target_row * num_qubits_ + j];
        uint8_t z1 = z_[target_row * num_qubits_ + j];
        uint8_t x2 = x_[source_row * num_qubits_ + j];
        uint8_t z2 = z_[source_row * num_qubits_ + j];
        sum_g += g_func(x1, z1, x2, z2);
    }

    int total = 2 * r_[target_row] + 2 * r_[source_row] + sum_g;
    total = ((total % 4) + 4) % 4;

    if (total == 0) {
        r_[target_row] = 0;
    } else if (total == 2) {
        r_[target_row] = 1;
    } else {
        // Total should always be 0 or 2 for valid Pauli products
        r_[target_row] = 0;
    }

    for (size_t j = 0; j < num_qubits_; ++j) {
        x_[target_row * num_qubits_ + j] ^= x_[source_row * num_qubits_ + j];
        z_[target_row * num_qubits_ + j] ^= z_[source_row * num_qubits_ + j];
    }
}

void StabilizerSimulator::apply_h(size_t a) {
    if (a >= num_qubits_) throw std::out_of_range("Qubit out of range");
    for (size_t i = 0; i < rows_; ++i) {
        uint8_t x_ia = x_[i * num_qubits_ + a];
        uint8_t z_ia = z_[i * num_qubits_ + a];
        r_[i] ^= (x_ia & z_ia);
        x_[i * num_qubits_ + a] = z_ia;
        z_[i * num_qubits_ + a] = x_ia;
    }
}

void StabilizerSimulator::apply_s(size_t a) {
    if (a >= num_qubits_) throw std::out_of_range("Qubit out of range");
    for (size_t i = 0; i < rows_; ++i) {
        uint8_t x_ia = x_[i * num_qubits_ + a];
        uint8_t z_ia = z_[i * num_qubits_ + a];
        r_[i] ^= (x_ia & z_ia);
        z_[i * num_qubits_ + a] ^= x_ia;
    }
}

void StabilizerSimulator::apply_sdg(size_t a) {
    // S^\dagger = S * S * S
    apply_s(a);
    apply_s(a);
    apply_s(a);
}

void StabilizerSimulator::apply_cnot(size_t a, size_t b) {
    if (a >= num_qubits_ || b >= num_qubits_ || a == b) {
        throw std::invalid_argument("Invalid CNOT indices");
    }
    for (size_t i = 0; i < rows_; ++i) {
        uint8_t x_ia = x_[i * num_qubits_ + a];
        uint8_t z_ia = z_[i * num_qubits_ + a];
        uint8_t x_ib = x_[i * num_qubits_ + b];
        uint8_t z_ib = z_[i * num_qubits_ + b];

        r_[i] ^= (x_ia & z_ib & (x_ib ^ z_ia ^ 1));
        x_[i * num_qubits_ + b] ^= x_ia;
        z_[i * num_qubits_ + a] ^= z_ib;
    }
}

void StabilizerSimulator::apply_cz(size_t a, size_t b) {
    apply_h(b);
    apply_cnot(a, b);
    apply_h(b);
}

void StabilizerSimulator::apply_swap(size_t a, size_t b) {
    apply_cnot(a, b);
    apply_cnot(b, a);
    apply_cnot(a, b);
}

void StabilizerSimulator::apply_x(size_t a) {
    apply_h(a);
    apply_z(a);
    apply_h(a);
}

void StabilizerSimulator::apply_z(size_t a) {
    if (a >= num_qubits_) throw std::out_of_range("Qubit out of range");
    for (size_t i = 0; i < rows_; ++i) {
        r_[i] ^= x_[i * num_qubits_ + a];
    }
}

void StabilizerSimulator::apply_y(size_t a) {
    apply_z(a);
    apply_x(a);
}

int StabilizerSimulator::measure(size_t a, double rand_val) {
    if (a >= num_qubits_) throw std::out_of_range("Qubit out of range");

    // Check if there is p in [n, 2n) such that x_[p * n + a] == 1
    size_t p = 2 * num_qubits_;
    for (size_t i = num_qubits_; i < rows_; ++i) {
        if (x_[i * num_qubits_ + a] == 1) {
            p = i;
            break;
        }
    }

    if (p < rows_) {
        // Case 1: Random outcome
        for (size_t i = 0; i < rows_; ++i) {
            if (i != p && x_[i * num_qubits_ + a] == 1) {
                row_mult(i, p);
            }
        }

        // Copy row p to row p - num_qubits_
        size_t p_destab = p - num_qubits_;
        for (size_t j = 0; j < num_qubits_; ++j) {
            x_[p_destab * num_qubits_ + j] = x_[p * num_qubits_ + j];
            z_[p_destab * num_qubits_ + j] = z_[p * num_qubits_ + j];
        }
        r_[p_destab] = r_[p];

        // Set row p to Z_a
        for (size_t j = 0; j < num_qubits_; ++j) {
            x_[p * num_qubits_ + j] = 0;
            z_[p * num_qubits_ + j] = 0;
        }
        z_[p * num_qubits_ + a] = 1;

        int outcome = (rand_val < 0.5) ? 0 : 1;
        r_[p] = outcome;
        return outcome;
    } else {
        // Case 2: Deterministic outcome
        // Create scratch row: starts with identity (all 0, phase 0)
        std::vector<uint8_t> acc_x(num_qubits_, 0);
        std::vector<uint8_t> acc_z(num_qubits_, 0);
        uint8_t acc_r = 0;

        for (size_t i = 0; i < num_qubits_; ++i) {
            if (x_[i * num_qubits_ + a] == 1) {
                size_t src = num_qubits_ + i;
                int sum_g = 0;
                for (size_t j = 0; j < num_qubits_; ++j) {
                    sum_g += g_func(acc_x[j], acc_z[j], x_[src * num_qubits_ + j], z_[src * num_qubits_ + j]);
                }
                int total = 2 * acc_r + 2 * r_[src] + sum_g;
                total = ((total % 4) + 4) % 4;
                acc_r = (total == 2) ? 1 : 0;

                for (size_t j = 0; j < num_qubits_; ++j) {
                    acc_x[j] ^= x_[src * num_qubits_ + j];
                    acc_z[j] ^= z_[src * num_qubits_ + j];
                }
            }
        }
        return acc_r;
    }
}

void StabilizerSimulator::reset_qubit(size_t a, double rand_val) {
    int outcome = measure(a, rand_val);
    if (outcome == 1) {
        apply_x(a);
    }
}

std::string StabilizerSimulator::get_pauli_row(size_t row_idx) const {
    std::string s = (r_[row_idx] == 1) ? "-" : "+";
    for (size_t j = 0; j < num_qubits_; ++j) {
        uint8_t xj = x_[row_idx * num_qubits_ + j];
        uint8_t zj = z_[row_idx * num_qubits_ + j];
        if (xj == 0 && zj == 0) s += "I";
        else if (xj == 1 && zj == 0) s += "X";
        else if (xj == 1 && zj == 1) s += "Y";
        else s += "Z";
    }
    return s;
}

std::string StabilizerSimulator::to_string() const {
    std::ostringstream oss;
    oss << "Stabilizers:\n";
    for (size_t i = num_qubits_; i < rows_; ++i) {
        oss << "  " << get_pauli_row(i) << "\n";
    }
    return oss.str();
}

} // namespace invariantq
