#ifndef INCLUDED_SEGMENT_H
#define INCLUDED_SEGMENT_H

#include "debug.h"

/*
 * left close - right close segment
 */
template <typename T, T L=0, T R=T(2e9)>
struct Segment {
    using val = Segment<T, L, R>;
    using ref = const Segment<T, L, R>&;
    T l = L;
    T r = R;

    int size() { return l <= r ? r - l + 1: 0; }
    
    val operator+(ref y) {
        return {min(l, y.l), max(r, y.r)};
    }
    val operator+=(ref y) {
        return *this = *this + y;
    }
    val operator*(ref y) {
        return {max(l, y.l), min(r, y.r)};
    }
    val operator*=(ref y) {
        return *this = *this * y;
    }

    bool operator==(ref o) const { return l == o.l && r == o.r; }
    bool operator<(ref o) const { return (l == o.l) ? (r < o.r) : (l < o.l); }
};

#ifdef DEBUG
template <typename T, T L, T R>
void __print(const Segment<T, L, R>& o) {
    cerr << "[" << o.l << "," << o.r << "]";
}
#endif

/*
template <typename T>
pair<T, T> operator+(const pair<T, T> &x, const pair<T, T> &y) {
    return {min(x.first, y.first), max(x.second, y.second)};
}

void operator+=(pair<T, T> &x, const pair<T, T> &y) {
    x.first = min(x.first, y.first);
    x.second = max(x.second, y.second);
}

template <typename T>
pair<T, T> operator*(const pair<T, T> &x, const pair<T, T> &y) {
    return {max(x.first, y.first), min(x.second, y.second)};
}

void operator*=(pair<T, T> &x, const pair<T, T> &y) {
    x.first = max(x.first, y.first);
    x.second = min(x.second, y.second);
}
*/


#endif
