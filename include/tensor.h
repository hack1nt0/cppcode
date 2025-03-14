#ifndef INCLUDED_TENSOR_H
#define INCLUDED_TENSOR_H

#include "./debug.h"

template <typename T, int D>
struct Tensor: public vector<Tensor<T, D-1>> {
    static_assert(D >= 2, "Dimension must be >= 2");
    array<int, D> dims;
    template <typename... Args>
    Tensor(int n, Args... args) : vector<Tensor<T, D-1>>(n, Tensor<T, D-1>(args...)), dims{n, args...} { assert(n); }
    void operator=(T v) { for (auto& x: *this) x = v; }
};


template <typename T>
struct Tensor<T, 1> : public vector<T> {
    array<int, 1> dims;
    Tensor(int n) : std::vector<T>(n), dims{n} { assert(n); }
    void operator=(T v) { for (auto& x: *this) x = v; }
};


template <class T, int D1, int D2>
using arr2d = array<array<T, D2>, D1>;

template <class T, int D1, int D2, int D3>
using arr3d = array<array<array<T, D3>, D2>, D1>;


#ifdef DEBUG
    template<typename T>
    T get_tensor(const Tensor<T, 1>& o, vector<int> idx) {
        return o[idx[0]];
    }
    template <typename T, int D>
    T get_tensor(const Tensor<T, D>& o, vector<int> idx) {
        return get_tensor(o[idx[0]], vector<int>(idx.begin() + 1, idx.end()));
    }
    template <typename T, int D>
    void __print(const Tensor<T, D>& o) {
        vector<int> idx(D);
        cerr << "\n";
        function<void(int)> F = [&](int d) {
            if (d >= D) {
                cerr << "["; for (int i = 0; i < D; ++i) cerr << idx[i] << ",]"[i == D - 1];
                cerr << ":\t" << get_tensor(o, idx) << "\n";
                return;
            }
            for (int i = 0; i < o.dims[d]; ++i) {
                idx[d] = i;
                F(d + 1);
            }
        };
        F(0);
    }
#endif

#endif
