#ifndef INCLUDED_PRIMES_H
#define INCLUDED_PRIMES_H

#include "debug.h"

template <typename T>
map<int,int> decompose_primes(T n) {
    map<int,int> mp;
    for (int p = 2; p <= T(sqrt(n)); p++) {
        if (n % p == 0) {
            mp[p] = 0;
            while (n % p == 0) mp[p]++, n /= p;
        }
    }
    if (n > 1) mp[n] = 1;
    return mp;
}

template <typename T>
vector<T> filter_range_primes(T l, T r) {
    auto maxd = (T) sqrt(r);
    vector<int> ok(r - l, 1);
    for (T d = 2; d <= maxd; ++d) if (ok[d]) {
        for (T m = max(d * 2, (l + d - 1) / d * d); m < r; m += d) 
            ok[m - l] = 0;
    }
    vector<T> ret;
    for (int i = 0; i < r - l; ++i) if (ok[i])
        ret.push_back(l + i);
    return ret;
}

#ifdef DEBUG
template <typename T>
string decompose_primes_str(T n) {
    auto mp = decompose_primes(n);
    stringstream str;
    for (auto [k, v]: mp) {
        if (str.tellp()) cerr << "*";
        str << k;
        if (v > 1) str << "^" << v;
    }
    return str.str();
}
#endif

#endif
