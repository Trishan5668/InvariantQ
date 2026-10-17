#include "c_api.h"
#include "statevector.hpp"
#include "density_matrix.hpp"
#include "stabilizer.hpp"
#include "mps.hpp"
#include <cstring>

using namespace invariantq;

extern "C" {

// ==================== StateVector ====================

void* iq_statevector_create(size_t num_qubits) {
    try {
        return new StateVector(num_qubits);
    } catch (...) {
        return nullptr;
    }
}

void iq_statevector_free(void* sv) {
    if (sv) delete static_cast<StateVector*>(sv);
}

void iq_statevector_reset(void* sv) {
    if (sv) static_cast<StateVector*>(sv)->reset();
}

void iq_statevector_apply_1q(void* sv, size_t target, const double* u_real, const double* u_imag) {
    if (!sv || !u_real || !u_imag) return;
    complex_t U[4];
    for (int i = 0; i < 4; ++i) {
        U[i] = complex_t(u_real[i], u_imag[i]);
    }
    static_cast<StateVector*>(sv)->apply_1q_gate(target, U);
}

void iq_statevector_apply_2q(void* sv, size_t q0, size_t q1, const double* u_real, const double* u_imag) {
    if (!sv || !u_real || !u_imag) return;
    complex_t U[16];
    for (int i = 0; i < 16; ++i) {
        U[i] = complex_t(u_real[i], u_imag[i]);
    }
    static_cast<StateVector*>(sv)->apply_2q_gate(q0, q1, U);
}

void iq_statevector_apply_fused(void* sv, const size_t* qubits, size_t k, const double* u_real, const double* u_imag) {
    if (!sv || !qubits || !u_real || !u_imag) return;
    size_t dim = 1ULL << k;
    std::vector<complex_t> U(dim * dim);
    for (size_t i = 0; i < dim * dim; ++i) {
        U[i] = complex_t(u_real[i], u_imag[i]);
    }
    std::vector<size_t> q_vec(qubits, qubits + k);
    static_cast<StateVector*>(sv)->apply_fused_gate(q_vec, U.data(), k);
}

int iq_statevector_measure(void* sv, size_t target, double rand_val) {
    if (!sv) return 0;
    return static_cast<StateVector*>(sv)->measure(target, rand_val);
}

void iq_statevector_reset_qubit(void* sv, size_t target, double rand_val) {
    if (!sv) return;
    static_cast<StateVector*>(sv)->reset_qubit(target, rand_val);
}

double iq_statevector_measure_prob(void* sv, size_t target, int outcome) {
    if (!sv) return 0.0;
    return static_cast<StateVector*>(sv)->measure_probability(target, outcome);
}

void iq_statevector_get_amplitudes(void* sv, double* real_out, double* imag_out) {
    if (!sv || !real_out || !imag_out) return;
    auto* s = static_cast<StateVector*>(sv);
    const complex_t* data = s->data();
    size_t dim = s->dim();
    for (size_t i = 0; i < dim; ++i) {
        real_out[i] = data[i].real();
        imag_out[i] = data[i].imag();
    }
}

void iq_statevector_get_probabilities(void* sv, double* probs_out) {
    if (!sv || !probs_out) return;
    auto* s = static_cast<StateVector*>(sv);
    std::vector<double> probs = s->probabilities();
    std::memcpy(probs_out, probs.data(), probs.size() * sizeof(double));
}

void iq_statevector_sample(void* sv, size_t num_shots, uint64_t seed, uint64_t* results_out) {
    if (!sv || !results_out) return;
    auto* s = static_cast<StateVector*>(sv);
    std::vector<uint64_t> shots = s->sample(num_shots, seed);
    std::memcpy(results_out, shots.data(), shots.size() * sizeof(uint64_t));
}

double iq_statevector_entropy(void* sv, const size_t* qubits, size_t num_subsys_qubits) {
    if (!sv || !qubits) return 0.0;
    std::vector<size_t> sub_q(qubits, qubits + num_subsys_qubits);
    return static_cast<StateVector*>(sv)->von_neumann_entropy(sub_q);
}

void iq_statevector_expval_pauli(void* sv, const char* pauli_str, const size_t* qubits, size_t len, double* val_real, double* val_imag) {
    if (!sv || !pauli_str || !qubits || !val_real || !val_imag) return;
    std::string p_str(pauli_str, len);
    std::vector<size_t> q_vec(qubits, qubits + len);
    complex_t res = static_cast<StateVector*>(sv)->expectation_value_pauli(p_str, q_vec);
    *val_real = res.real();
    *val_imag = res.imag();
}

// ==================== DensityMatrix ====================

void* iq_density_matrix_create(size_t num_qubits) {
    try {
        return new DensityMatrix(num_qubits);
    } catch (...) {
        return nullptr;
    }
}

void iq_density_matrix_free(void* dm) {
    if (dm) delete static_cast<DensityMatrix*>(dm);
}

void iq_density_matrix_reset(void* dm) {
    if (dm) static_cast<DensityMatrix*>(dm)->reset();
}

void iq_density_matrix_apply_1q_unitary(void* dm, size_t target, const double* u_real, const double* u_imag) {
    if (!dm || !u_real || !u_imag) return;
    complex_t U[4];
    for (int i = 0; i < 4; ++i) U[i] = complex_t(u_real[i], u_imag[i]);
    static_cast<DensityMatrix*>(dm)->apply_1q_unitary(target, U);
}

void iq_density_matrix_apply_2q_unitary(void* dm, size_t q0, size_t q1, const double* u_real, const double* u_imag) {
    if (!dm || !u_real || !u_imag) return;
    complex_t U[16];
    for (int i = 0; i < 16; ++i) U[i] = complex_t(u_real[i], u_imag[i]);
    static_cast<DensityMatrix*>(dm)->apply_2q_unitary(q0, q1, U);
}

void iq_density_matrix_apply_kraus_1q(void* dm, size_t target, size_t num_kraus, const double* k_real, const double* k_imag) {
    if (!dm || !k_real || !k_imag) return;
    std::vector<Gate1Q> ops(num_kraus);
    for (size_t k = 0; k < num_kraus; ++k) {
        for (int i = 0; i < 4; ++i) {
            ops[k].m[i] = complex_t(k_real[k * 4 + i], k_imag[k * 4 + i]);
        }
    }
    static_cast<DensityMatrix*>(dm)->apply_1q_kraus(target, ops);
}

void iq_density_matrix_get_elements(void* dm, double* real_out, double* imag_out) {
    if (!dm || !real_out || !imag_out) return;
    auto* d = static_cast<DensityMatrix*>(dm);
    const complex_t* data = d->data();
    size_t dim = d->dim();
    size_t total = dim * dim;
    for (size_t i = 0; i < total; ++i) {
        real_out[i] = data[i].real();
        imag_out[i] = data[i].imag();
    }
}

double iq_density_matrix_trace(void* dm) {
    if (!dm) return 0.0;
    return static_cast<DensityMatrix*>(dm)->trace();
}

double iq_density_matrix_purity(void* dm) {
    if (!dm) return 0.0;
    return static_cast<DensityMatrix*>(dm)->purity();
}

double iq_density_matrix_entropy(void* dm) {
    if (!dm) return 0.0;
    return static_cast<DensityMatrix*>(dm)->von_neumann_entropy();
}

int iq_density_matrix_measure(void* dm, size_t target, double rand_val) {
    if (!dm) return 0;
    return static_cast<DensityMatrix*>(dm)->measure(target, rand_val);
}

void iq_density_matrix_reset_qubit(void* dm, size_t target) {
    if (!dm) return;
    static_cast<DensityMatrix*>(dm)->reset_qubit(target);
}

// ==================== Stabilizer ====================

void* iq_stabilizer_create(size_t num_qubits) {
    try {
        return new StabilizerSimulator(num_qubits);
    } catch (...) {
        return nullptr;
    }
}

void iq_stabilizer_free(void* stab) {
    if (stab) delete static_cast<StabilizerSimulator*>(stab);
}

void iq_stabilizer_reset(void* stab) {
    if (stab) static_cast<StabilizerSimulator*>(stab)->reset();
}

void iq_stabilizer_reset_qubit(void* stab, size_t a, double rand_val) {
    if (!stab) return;
    static_cast<StabilizerSimulator*>(stab)->reset_qubit(a, rand_val);
}

void iq_stabilizer_apply_h(void* stab, size_t a) {
    if (stab) static_cast<StabilizerSimulator*>(stab)->apply_h(a);
}

void iq_stabilizer_apply_s(void* stab, size_t a) {
    if (stab) static_cast<StabilizerSimulator*>(stab)->apply_s(a);
}

void iq_stabilizer_apply_sdg(void* stab, size_t a) {
    if (stab) static_cast<StabilizerSimulator*>(stab)->apply_sdg(a);
}

void iq_stabilizer_apply_cnot(void* stab, size_t a, size_t b) {
    if (stab) static_cast<StabilizerSimulator*>(stab)->apply_cnot(a, b);
}

void iq_stabilizer_apply_cz(void* stab, size_t a, size_t b) {
    if (stab) static_cast<StabilizerSimulator*>(stab)->apply_cz(a, b);
}

void iq_stabilizer_apply_swap(void* stab, size_t a, size_t b) {
    if (stab) static_cast<StabilizerSimulator*>(stab)->apply_swap(a, b);
}

void iq_stabilizer_apply_x(void* stab, size_t a) {
    if (stab) static_cast<StabilizerSimulator*>(stab)->apply_x(a);
}

void iq_stabilizer_apply_y(void* stab, size_t a) {
    if (stab) static_cast<StabilizerSimulator*>(stab)->apply_y(a);
}

void iq_stabilizer_apply_z(void* stab, size_t a) {
    if (stab) static_cast<StabilizerSimulator*>(stab)->apply_z(a);
}

int iq_stabilizer_measure(void* stab, size_t a, double rand_val) {
    if (!stab) return 0;
    return static_cast<StabilizerSimulator*>(stab)->measure(a, rand_val);
}

void iq_stabilizer_to_string(void* stab, char* buffer, size_t max_len) {
    if (!stab || !buffer || max_len == 0) return;
    std::string s = static_cast<StabilizerSimulator*>(stab)->to_string();
    std::strncpy(buffer, s.c_str(), max_len - 1);
    buffer[max_len - 1] = '\0';
}

// ==================== MPS ====================

void* iq_mps_create(size_t num_qubits, size_t max_bond_dim, double cutoff) {
    try {
        return new MPSSimulator(num_qubits, max_bond_dim, cutoff);
    } catch (...) {
        return nullptr;
    }
}

void iq_mps_free(void* mps) {
    if (mps) delete static_cast<MPSSimulator*>(mps);
}

void iq_mps_reset(void* mps) {
    if (mps) static_cast<MPSSimulator*>(mps)->reset();
}

void iq_mps_apply_1q(void* mps, size_t target, const double* u_real, const double* u_imag) {
    if (!mps || !u_real || !u_imag) return;
    complex_t U[4];
    for (int i = 0; i < 4; ++i) U[i] = complex_t(u_real[i], u_imag[i]);
    static_cast<MPSSimulator*>(mps)->apply_1q_gate(target, U);
}

void iq_mps_apply_2q(void* mps, size_t q0, size_t q1, const double* u_real, const double* u_imag) {
    if (!mps || !u_real || !u_imag) return;
    complex_t U[16];
    for (int i = 0; i < 16; ++i) U[i] = complex_t(u_real[i], u_imag[i]);
    static_cast<MPSSimulator*>(mps)->apply_2q_gate(q0, q1, U);
}

double iq_mps_entropy(void* mps, size_t bond_idx) {
    if (!mps) return 0.0;
    return static_cast<MPSSimulator*>(mps)->entanglement_entropy(bond_idx);
}

void iq_mps_to_statevector(void* mps, double* real_out, double* imag_out) {
    if (!mps || !real_out || !imag_out) return;
    auto sv = static_cast<MPSSimulator*>(mps)->to_statevector();
    for (size_t i = 0; i < sv.size(); ++i) {
        real_out[i] = sv[i].real();
        imag_out[i] = sv[i].imag();
    }
}

int iq_mps_measure(void* mps, size_t target, double rand_val) {
    if (!mps) return 0;
    return static_cast<MPSSimulator*>(mps)->measure(target, rand_val);
}

} // extern "C"
