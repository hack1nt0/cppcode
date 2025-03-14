#ifndef INCLUDED_DEBUG_H
#define INCLUDED_DEBUG_H

#include <algorithm>
#include <cassert>
#include <complex>
#include <cstring>
#include <forward_list>
#include <functional>
#include <iomanip>
#include <iostream>
#include <limits>
#include <list>
#include <map>
#include <queue>
#include <random>
#include <set>
#include <stack>
#include <string>
#include <unordered_map>
#include <unordered_set>
#include <vector>
#include <bitset>
#include <bit>


using namespace std;


#ifdef DEBUG
void __print(int x) { cerr << x; }
void __print(long x) { cerr << x; }
void __print(long long x) { cerr << x; }
void __print(unsigned x) { cerr << x; }
void __print(unsigned long x) { cerr << x; }
void __print(unsigned long long x) { cerr << x; }
void __print(float x) { cerr << x; }
void __print(double x) { cerr << x; }
void __print(long double x) { cerr << x; }
void __print(char x) { cerr << '\'' << x << '\''; }
void __print(const char *x) { cerr << '\"' << x << '\"'; }
void __print(const string &x) { cerr << '\"' << x << '\"'; }
void __print(bool x) { cerr << (x ? "true" : "false"); }
template <typename T> void __print(const complex<T> &x) {
    cerr << x;
}
template <typename T, typename V> void __print(const pair<T, V> &x) {
    cerr << '(';
    __print(x.first);
    cerr << ',';
    __print(x.second);
    cerr << ')';
}
template <typename T1, typename T2> void __print(const tuple<T1, T2> &v) {
    auto [x, y] = v;
    cerr << '(' << x << ',' << y << ")";
}
template <typename T1, typename T2, typename T3> void __print(const tuple<T1, T2, T3> &v) {
    auto [x, y, z] = v;
    cerr << '(' << x << ',' << y << "," << z << ")";
}
template <typename T1, typename T2, typename T3, typename T4> void __print(const tuple<T1, T2, T3, T4> &v) {
    auto [x, y, z, zz] = v;
    cerr << '(' << x << ',' << y << "," << z << "," << zz << ")";
}
template <typename T, unsigned long N> void __print(const array<T, N> &xs) {
    int f = 0;
    cerr << '[';
    for (const auto &x : xs)
        cerr << (f++ ? "," : ""), __print(x);
    cerr << ']';
}
template <typename T> void __print(const vector<T> &xs) {
    int f = 0;
    cerr << '[';
    for (const auto &x : xs)
        cerr << (f++ ? "," : ""), __print(x);
    cerr << ']';
}
template <typename T> void __print(const deque<T> &xs) {
    int f = 0;
    cerr << '[';
    for (const auto &x : xs)
        cerr << (f++ ? "," : ""), __print(x);
    cerr << ']';
}
template <typename T> void __print(const set<T> &xs) {
    int f = 0;
    cerr << '{';
    for (const auto &x : xs)
        cerr << (f++ ? "," : ""), __print(x);
    cerr << '}';
}
template <typename T> void __print(const multiset<T> &xs) {
    int f = 0;
    cerr << '{';
    for (const auto &x : xs)
        cerr << (f++ ? "," : ""), __print(x);
    cerr << '}';
}
template <typename K, typename V> void __print(const map<K, V> &xs) {
    cerr << "{";
    for (const auto &x : xs) {
        __print(x.first);
        cerr << ": ";
        __print(x.second);
        cerr << ", ";
    }
    cerr << "}";
}
template< std::size_t N >
void __print(const bitset<N> &xs) {
    cerr << xs;
}
// template <typename T> void __print(T &o) { o.dot(); }
void _print() { cerr << "]" << endl; }
template <typename T, typename... V> void _print(T t, V... v) {
    __print(t);
    if (sizeof...(v))
        cerr << ", ";
    _print(v...);
}
#define LOG(x...)                                                            \
    cerr << "[" << #x << "] = [";                                              \
    _print(x);
#else
#define LOG(x...)
#endif



#endif
