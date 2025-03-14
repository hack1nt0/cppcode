
#ifndef INCLUDED_CONVOLUTION_H
#define INCLUDED_CONVOLUTION_H

#include "modint.h"
#include <valarray>

/*
 * The Cooley-Tukey algorithm
 * https://www.cs.cmu.edu/afs/andrew/scs/cs/15-463/2001/pub/www/notes/fourier/fourier.pdf
 * ~ 2s when N = 1e6
 * */
vector<double> operator*(const vector<double>& lhs, const vector<double>& rhs) {
    using T = double;
    using C = complex<T>;
    using V = valarray<C>;
    int n = lhs.size();
    int m = rhs.size();
    assert(n > 1 && m > 1);
    int N = 1;
    while (N < n + m - 1) N <<= 1;
    V A(N);
    V B(N);
    for (int i = 0; i < n; ++i) A[i] = C(lhs[i]);
    for (int i = 0; i < m; ++i) B[i] = C(rhs[i]);
    T PI = acos(-1.0);
    bool inverse = false;
    auto fft = [&](V& p) -> V {
        // Bit-reversed addressing permutation
        for (size_t i = 1, j = 0; i < N; ++i) {
            size_t bit = N >> 1;
            while (j & bit) {
                j ^= bit;
                bit >>= 1;
            }
            j ^= bit;
            if (i < j) {
                swap(p[i], p[j]);
            }
        }
        // Iterative FFT
        for (size_t len = 2; len <= N; len <<= 1) {
            T angle = -2 * PI / len;
            if (inverse) angle = -angle;
            C wlen(cos(angle), sin(angle));
            for (size_t i = 0; i < N; i += len) {
                C w(1);
                for (size_t j = 0; j < len / 2; ++j) {
                    C u = p[i + j];
                    C v = p[i + j + len / 2] * w;
                    p[i + j] = u + v;
                    p[i + j + len / 2] = u - v;
                    w *= wlen;
                }
            }
        }
        if (inverse) p /= N;
    };
    fft(A);
    fft(B);
    V Z = A * B;
    inverse = true;
    fft(Z);
    vector<double> res(n + m - 1);
    for (int i = 0; i < res.size(); ++i) {
        res[i] = Z[i].real();
    }
    return res;
}

/**
 * ntt, todo
 */
// template <auto MOD>
// vector<ModInt<MOD>> operator*(const vector<ModInt<MOD>>& lhs, const vector<ModInt<MOD>>& rhs) {
//     using T = ModInt<MOD>;
//     using V = valarray<T>;
//     int n = lhs.size();
//     int m = rhs.size();
//     assert(n > 1 && m > 1);
//     int N = 1;
//     while (N < n + m - 1) N <<= 1;
//     V A = lhs; A.resize(N);
//     V B = rhs; B.resize(N);
//     T root_1, root, root_pw;
//     bool inverse = false;
//     auto ntt = [&](V& p) -> V {
//         // Bit-reversed addressing permutation
//         for (size_t i = 1, j = 0; i < N; ++i) {
//             size_t bit = N >> 1;
//             while (j & bit) {
//                 j ^= bit;
//                 bit >>= 1;
//             }
//             j ^= bit;
//             if (i < j) {
//                 swap(p[i], p[j]);
//             }
//         }
//         // Iterative FFT
//         for (size_t len = 2; len <= N; len <<= 1) {
//             T wlen = inverse ? root_1 : root;
//             for (int i = len; i < root_pw; i <<= 1)
//                 wlen = wlen * wlen;
//             for (size_t i = 0; i < N; i += len) {
//                 T w = 1;
//                 for (size_t j = 0; j < len / 2; ++j) {
//                     T u = p[i + j];
//                     T v = p[i + j + len / 2] * w;
//                     p[i + j] = u + v;
//                     p[i + j + len / 2] = u - v;
//                     w *= wlen;
//                 }
//             }
//         }
//         if (inverse) p /= N;
//     };
//     fft(A);
//     fft(B);
//     V Z = A * B;
//     inverse = true;
//     fft(Z);
//     Z.resize(n + m - 1);
//     return Z;
// }
#endif

