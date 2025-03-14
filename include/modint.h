#ifndef INCLUDED_MODINT_H
#define INCLUDED_MODINT_H

#include "debug.h"

template <typename T>
array<T, 3> euclid(T a, T b) {
    if (b == 0) {
        return {1, 0, a};
    } else {
        auto [xx, yy, g] = euclid(b, a % b);
        T x = yy;
        T y = xx - a / b * yy;
        return {x, y, g};
    }
}

template <class ll>
ll modlog(ll a, ll b, ll m) {
    ll n = (ll) sqrt(m) + 1, e = 1, f = 1, j = 1;
    unordered_map<ll, ll> A;
    while(j<=n && (e = f = e*a %m)!=b%m) A[e*b%m]=j++;
    if (e == b % m) return j;
    if (__gcd(m, e) == __gcd(m, b))
    for(int i = 2; i < n + 2; ++i) if (A.count(e = e * f % m)) return n * i - A[e];
    return -1;
}

/*
Description: Chinese Remainder Theorem.
crt(a, m, b, n) computes x such that x≡a (mod m),x≡b (mod n).
If |a|< m and |b|<n, x will obey 0≤x<lcm(m,n). Assumes mn<2^62.
Time: log(n)
*/
template <class ll>
ll crt(ll a, ll m, ll b, ll n) {
    if (n > m) swap(a, b), swap(m, n);
    auto [x, y, g] = euclid(m, n);
    assert((a - b) % g == 0); // else no solution
    x = (b - a) % n * x % n / g * m + a;
    return x < 0 ? x + m*n/g : x;
}
template <class ll, class Arr>
pair<ll, ll> crt(const Arr& rems, const Arr& mods) {

}


template <auto MOD> struct ModInt {
    using T = decltype(MOD);
    T v;
    using val = ModInt<MOD>;
    using ref = const val&;

    T norm(T vv) { return (vv % MOD + MOD) % MOD; }
    ModInt(T vv = 0) { v = norm(vv); }
    // ModInt(ref o) : v(o.v) {}
    // val operator=(ref o) { v = o.v; return *this; }
    val operator=(T vv) { v = norm(vv); return *this; }

    val inverse() const {
        using arr3 = array<T, 3>;
        auto extgcd = [&](const auto& F, T a, T b) {
            if (b == 0) {
                return arr3{1, 0, a};
            } else {
                auto [xx, yy, g] = F(F, b, a % b);
                T x = yy;
                T y = xx - a / b * yy;
                return arr3{x, y, g};
            }
        };
        auto [xinv, _, d] = extgcd(extgcd, v, MOD);
        assert(d == 1);
        return xinv;
    }
    val operator+(ref x) { return v + x.v; }
    val operator+=(ref x) { return *this = *this + x; }
    val operator-(ref x) { return v - x.v; }
    val operator-=(ref x) { return *this = *this - x; }
    val operator*(ref x) { return v * x.v; }
    // val operator*(T x) { return x * v; }
    val operator*=(ref x) { return *this = *this * x; }
    val operator/(ref x) { return *this * x.inverse(); }
    val operator/=(ref x) { return *this = *this / x; }
};
// template <auto MOD>
// ModInt<MOD> operator+(const ModInt<MOD>& x, const ModInt<MOD>& y) { return x.v + y.v; }
// template <auto MOD>
// ModInt<MOD> operator+=(ModInt<MOD>& x, const ModInt<MOD>& y) { return x = x + y; }
// template <auto MOD>
// ModInt<MOD> operator-(const ModInt<MOD>& x, const ModInt<MOD>& y) { return x.v - y.v; }
// template <auto MOD>
// ModInt<MOD> operator-=(ModInt<MOD>& x, const ModInt<MOD>& y) { return x = x - y; }
// template <auto MOD>
// ModInt<MOD> operator*(const ModInt<MOD>& x, const ModInt<MOD>& y) { return x.v * y.v; }
// template <auto MOD>
// ModInt<MOD> operator*=(ModInt<MOD>& x, const ModInt<MOD>& y) { return x = x * y; }

// template <auto MOD>
// ModInt<MOD> inverse(const ModInt<MOD>& x) {
//     auto [xinv, _, d] = extgcd(x.v, MOD);
//     assert(d == 1);
//     return xinv;
// }

// template <auto MOD>
// ModInt<MOD> operator/(const ModInt<MOD>& x, const ModInt<MOD>& y) { return x * y.inverse(); }
// template <auto MOD>
// ModInt<MOD> operator/=(ModInt<MOD>& x, const ModInt<MOD>& y) { return x = x / y; }

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
        result = result.inverse();
    return result;
}

template <auto MOD>
typename ModInt<MOD>::T log(const ModInt<MOD>& x, const ModInt<MOD>& y) {
}

template <auto MOD>
ostream &operator<<(ostream &os, const ModInt<MOD>& c) { return os << c.v; }

template <auto MOD>
istream &operator>>(istream &is, ModInt<MOD>& c) { typename ModInt<MOD>::T v; is >> v; c.v = v; return is; }

template <auto MOD>
bool operator==(ModInt<MOD>& x, const ModInt<MOD>& y) { return x.v == y.v; }

template <auto MOD>
bool operator==(ModInt<MOD>& x, int y) { return x.v == y; }

#ifdef DEBUG
template <auto MOD> void __print(const ModInt<MOD> &x) { cerr << x.v; }
#endif

#endif
