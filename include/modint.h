#ifndef INCLUDED_MODINT_H
#define INCLUDED_MODINT_H

#include "debug.h"

template <typename T>
array<T, 3> extgcd(T a, T b) {
    if (b == 0) {
        return {1, 0, a};
    } else {
        auto [xx, yy, g] = extgcd(b, a % b);
        T x = yy;
        T y = xx - a / b * yy;
        return {x, y, g};
    }
}

template <auto MOD> struct ModInt {
    using T = decltype(MOD);
    T v;
    using val = ModInt<MOD>;
    using ref = const val&;

    ModInt(T v=0) { 
        if (v >= MOD) {
            v = v % MOD;
        } else if (v <= 0) {
            v = (v % MOD + MOD) % MOD;
        }
        this->v = v;
    }
    ModInt(ref o) { this->v = o.v; }
    val operator=(ref o) { v = o.v; return *this; }
    //val operator=(T v) { *this = val(v); return *this; }
};
template <auto MOD>
ModInt<MOD> operator+(const ModInt<MOD>& x, const ModInt<MOD>& y) { return x.v + y.v; }
template <auto MOD>
ModInt<MOD> operator+=(ModInt<MOD>& x, const ModInt<MOD>& y) { return x = x + y; }
template <auto MOD>
ModInt<MOD> operator-(const ModInt<MOD>& x, const ModInt<MOD>& y) { return x.v - y.v; }
template <auto MOD>
ModInt<MOD> operator-=(ModInt<MOD>& x, const ModInt<MOD>& y) { return x = x - y; }
template <auto MOD>
ModInt<MOD> operator*(const ModInt<MOD>& x, const ModInt<MOD>& y) { return x.v * y.v; }
template <auto MOD>
ModInt<MOD> operator*=(ModInt<MOD>& x, const ModInt<MOD>& y) { return x = x * y; }

template <auto MOD>
ModInt<MOD> inverse(const ModInt<MOD>& x) {
    auto [xinv, _, d] = extgcd(x.v, MOD);
    assert(d == 1);
    return xinv;
}

template <auto MOD>
ModInt<MOD> operator/(const ModInt<MOD>& x, const ModInt<MOD>& y) { return x * inverse(y); }
template <auto MOD>
ModInt<MOD> operator/=(ModInt<MOD>& x, const ModInt<MOD>& y) { return x = x / y; }

template <auto MOD>
ModInt<MOD> pow(const ModInt<MOD>& x, typename ModInt<MOD>::T n) {
    int pw = abs(n);
    ModInt<MOD> result{1}, acc = x;
    while (pw > 0) {
        if ((pw & 1) == 1) {
            result *= acc;
        }
        acc *= acc;
        pw >>= 1;
    }
    if (n < 0)
        result = inverse(result);
    return result;
}

template <auto MOD>
typename ModInt<MOD>::T log(const ModInt<MOD>& x, const ModInt<MOD>& y) {
}

template <auto MOD>
ostream &operator<<(ostream &os, const ModInt<MOD>& c) { return os << c.v; }

template <auto MOD>
istream &operator>>(istream &is, ModInt<MOD>& c) { typename ModInt<MOD>::T v; is >> v; c.v = v; return is; }


#ifdef DEBUG
template <auto MOD> void __print(const ModInt<MOD> &x) { cerr << x.v; }
#endif

#endif
