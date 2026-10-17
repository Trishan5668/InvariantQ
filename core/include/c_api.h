#pragma once

#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

// StateVector API
void* iq_statevector_create(size_t num_qubits);
void  iq_statevector_free(void* sv);
void  iq_statevector_reset(void* sv);
void  iq_statevector_apply_1q(void* sv, size_t target, const double* u_real, const double* u_imag);
void  iq_statevector_apply_2q(void* sv, size_t q0, size_t q1, const double* u_real, const double* u_imag);
void  iq_statevector_apply_fused(void* sv, const size_t* qubits, size_t k, const double* u_real, const double* u_imag);
int   iq_statevector_measure(void* sv, size_t target, double rand_val);
void  iq_statevector_reset_qubit(void* sv, size_t target, double rand_val);
double iq_statevector_measure_prob(void* sv, size_t target, int outcome);
void  iq_statevector_get_amplitudes(void* sv, double* real_out, double* imag_out);
void  iq_statevector_get_probabilities(void* sv, double* probs_out);
void  iq_statevector_sample(void* sv, size_t num_shots, uint64_t seed, uint64_t* results_out);
double iq_statevector_entropy(void* sv, const size_t* qubits, size_t num_subsys_qubits);
void  iq_statevector_expval_pauli(void* sv, const char* pauli_str, const size_t* qubits, size_t len, double* val_real, double* val_imag);

// DensityMatrix API
void* iq_density_matrix_create(size_t num_qubits);
void  iq_density_matrix_free(void* dm);
void  iq_density_matrix_reset(void* dm);
void  iq_density_matrix_apply_1q_unitary(void* dm, size_t target, const double* u_real, const double* u_imag);
void  iq_density_matrix_apply_2q_unitary(void* dm, size_t q0, size_t q1, const double* u_real, const double* u_imag);
void  iq_density_matrix_apply_kraus_1q(void* dm, size_t target, size_t num_kraus, const double* k_real, const double* k_imag);
void  iq_density_matrix_get_elements(void* dm, double* real_out, double* imag_out);
double iq_density_matrix_trace(void* dm);
double iq_density_matrix_purity(void* dm);
double iq_density_matrix_entropy(void* dm);
int   iq_density_matrix_measure(void* dm, size_t target, double rand_val);
void  iq_density_matrix_reset_qubit(void* dm, size_t target);

// Stabilizer API
void* iq_stabilizer_create(size_t num_qubits);
void  iq_stabilizer_free(void* stab);
void  iq_stabilizer_reset(void* stab);
void  iq_stabilizer_reset_qubit(void* stab, size_t a, double rand_val);
void  iq_stabilizer_apply_h(void* stab, size_t a);
void  iq_stabilizer_apply_s(void* stab, size_t a);
void  iq_stabilizer_apply_sdg(void* stab, size_t a);
void  iq_stabilizer_apply_cnot(void* stab, size_t a, size_t b);
void  iq_stabilizer_apply_cz(void* stab, size_t a, size_t b);
void  iq_stabilizer_apply_swap(void* stab, size_t a, size_t b);
void  iq_stabilizer_apply_x(void* stab, size_t a);
void  iq_stabilizer_apply_y(void* stab, size_t a);
void  iq_stabilizer_apply_z(void* stab, size_t a);
int   iq_stabilizer_measure(void* stab, size_t a, double rand_val);
void  iq_stabilizer_to_string(void* stab, char* buffer, size_t max_len);

// MPS API
void* iq_mps_create(size_t num_qubits, size_t max_bond_dim, double cutoff);
void  iq_mps_free(void* mps);
void  iq_mps_reset(void* mps);
void  iq_mps_apply_1q(void* mps, size_t target, const double* u_real, const double* u_imag);
void  iq_mps_apply_2q(void* mps, size_t q0, size_t q1, const double* u_real, const double* u_imag);
double iq_mps_entropy(void* mps, size_t bond_idx);
void  iq_mps_to_statevector(void* mps, double* real_out, double* imag_out);
int   iq_mps_measure(void* mps, size_t target, double rand_val);

#ifdef __cplusplus
}
#endif
