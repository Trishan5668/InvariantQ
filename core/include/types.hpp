#pragma once

#include <complex>
#include <vector>
#include <cstdint>
#include <string>
#include <cmath>
#include <iostream>

namespace invariantq {

using complex_t = std::complex<double>;

constexpr double PI = 3.14159265358979323846;

struct Gate1Q {
    complex_t m[4]; // Row-major: m[0]=00, m[1]=01, m[2]=10, m[3]=11
};

struct Gate2Q {
    complex_t m[16]; // Row-major 4x4
};

// Standard Pauli & Single-Qubit Gates
inline Gate1Q gate_identity() {
    return {complex_t(1,0), complex_t(0,0), complex_t(0,0), complex_t(1,0)};
}

inline Gate1Q gate_pauli_x() {
    return {complex_t(0,0), complex_t(1,0), complex_t(1,0), complex_t(0,0)};
}

inline Gate1Q gate_pauli_y() {
    return {complex_t(0,0), complex_t(0,-1), complex_t(0,1), complex_t(0,0)};
}

inline Gate1Q gate_pauli_z() {
    return {complex_t(1,0), complex_t(0,0), complex_t(0,0), complex_t(-1,0)};
}

inline Gate1Q gate_hadamard() {
    double inv = 1.0 / std::sqrt(2.0);
    return {complex_t(inv,0), complex_t(inv,0), complex_t(inv,0), complex_t(-inv,0)};
}

inline Gate1Q gate_s() {
    return {complex_t(1,0), complex_t(0,0), complex_t(0,0), complex_t(0,1)};
}

inline Gate1Q gate_sdg() {
    return {complex_t(1,0), complex_t(0,0), complex_t(0,0), complex_t(0,-1)};
}

inline Gate1Q gate_t() {
    double inv = 1.0 / std::sqrt(2.0);
    return {complex_t(1,0), complex_t(0,0), complex_t(0,0), complex_t(inv, inv)};
}

inline Gate1Q gate_tdg() {
    double inv = 1.0 / std::sqrt(2.0);
    return {complex_t(1,0), complex_t(0,0), complex_t(0,0), complex_t(inv, -inv)};
}

inline Gate1Q gate_rx(double theta) {
    double c = std::cos(theta / 2.0);
    double s = std::sin(theta / 2.0);
    return {complex_t(c, 0), complex_t(0, -s), complex_t(0, -s), complex_t(c, 0)};
}

inline Gate1Q gate_ry(double theta) {
    double c = std::cos(theta / 2.0);
    double s = std::sin(theta / 2.0);
    return {complex_t(c, 0), complex_t(-s, 0), complex_t(s, 0), complex_t(c, 0)};
}

inline Gate1Q gate_rz(double theta) {
    double c = std::cos(theta / 2.0);
    double s = std::sin(theta / 2.0);
    return {complex_t(c, -s), complex_t(0, 0), complex_t(0, 0), complex_t(c, s)};
}

inline Gate1Q gate_u3(double theta, double phi, double lambda) {
    double c = std::cos(theta / 2.0);
    double s = std::sin(theta / 2.0);
    complex_t exp_phi(std::cos(phi), std::sin(phi));
    complex_t exp_lam(std::cos(lambda), std::sin(lambda));
    complex_t exp_phi_lam(std::cos(phi + lambda), std::sin(phi + lambda));

    return {
        complex_t(c, 0),
        -exp_lam * complex_t(s, 0),
        exp_phi * complex_t(s, 0),
        exp_phi_lam * complex_t(c, 0)
    };
}

// 2-Qubit Gates
inline Gate2Q gate_cnot() {
    Gate2Q g;
    std::fill(std::begin(g.m), std::end(g.m), complex_t(0,0));
    g.m[0]  = complex_t(1,0); // 00 -> 00
    g.m[5]  = complex_t(1,0); // 01 -> 01
    g.m[11] = complex_t(1,0); // 10 -> 11
    g.m[14] = complex_t(1,0); // 11 -> 10
    return g;
}

inline Gate2Q gate_cz() {
    Gate2Q g;
    std::fill(std::begin(g.m), std::end(g.m), complex_t(0,0));
    g.m[0]  = complex_t(1,0); // 00 -> 00
    g.m[5]  = complex_t(1,0); // 01 -> 01
    g.m[10] = complex_t(1,0); // 10 -> 10
    g.m[15] = complex_t(-1,0);// 11 -> -11
    return g;
}

inline Gate2Q gate_swap() {
    Gate2Q g;
    std::fill(std::begin(g.m), std::end(g.m), complex_t(0,0));
    g.m[0]  = complex_t(1,0);
    g.m[6]  = complex_t(1,0);
    g.m[9]  = complex_t(1,0);
    g.m[15] = complex_t(1,0);
    return g;
}

} // namespace invariantq
