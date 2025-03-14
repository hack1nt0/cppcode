#ifndef INCLUDED_MATRIX_H
#define INCLUDED_MATRIX_H

#include "debug.h"

template <typename T>
struct Matrix {
    
};



template <typename T>
struct Tensor {
    using val = Tensor<T>;
    using ref = const Tensor<T>&;
    int N, D;
    int *dim, *stride;
    //vector<int> dim, stride;
    T* dat;

    Tensor(initializer_list<int> list, T v=0) {
        D = list.size();
        dim = (int*) malloc(D * sizeof(int));
        D = 0;
        for (auto d: list) dim[D++] = d;
        stride = (int*) malloc(D * sizeof(int));
        N = 1;
        for (int i = D - 1; i >= 0; --i) {
            stride[i] = N;
            N *= dim[i];
        }
        dat = (T*) malloc(N * sizeof(T));
        *this = v;
    }

    Tensor(int N, int D, int *dim, int *stride, T *dat): N(N), D(D), dim(dim), stride(stride), dat(dat) {
    }

    int size() const { return N; }
    int dims() const { return D; }

    void operator=(T v) {
        fill(dat, dat + size(), v);
    }
    
    val operator[](int idx) const {
        assert(D);
        return Tensor(stride[0], D - 1, dim + 1, stride + 1, dat + idx * stride[0]);
    }

    T operator[](initializer_list<int> list) const {
        assert(list.size() == dims());
        int idx = 0, ord = 0;
        for (auto i: list) idx += i * stride[ord++];
        return dat[idx];
    }

    val operator*(ref y) {
    }

    T permaniant() {
    }

    friend ostream& operator<<(ostream& s, ref o) {
        if (o.dims() == 1) {
            for (int i = 0; i < o.dim[0]; ++i) 
                s << o.dat[i] << " ";
        } else {
            for (int i = 0; i < o.dim[0]; ++i) {
                if (i) s << "\n";
                s << o[i];
            }
        }
        return s;
    }
};

#endif
