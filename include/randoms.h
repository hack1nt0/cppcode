#ifndef INCLUDED_RANDVAL_H
#define INCLUDED_RANDVAL_H

#include "debug.h"

struct Random {
    mt19937 gen;
    uniform_real_distribution<double> dist;
    Random(unsigned int seed): gen(seed), dist(0, 1) {}
    Random(): gen(random_device()()), dist(0, 1) {}

    using pii = pair<int, int>;
    using vvi = vector<vector<int>>;

    double random() {
        return dist(gen);
    }

    template <typename T> T randint(T left_close, T right_open) {
        assert(left_close < right_open);
        T x = T(left_close + T((right_open - left_close) * random()));
        // assert(s <= x && x < t);
        return x;
    }

    vector<int> randtree(int n) {
        vector<int> ord(n);
        for (int i = 0; i < n; ++i) ord[i] = i;
        std::shuffle(ord.begin(), ord.end(), gen);
        vector<int> fa(n);
        fa[ord[0]] = -1;
        for (int i = 1; i < n; ++i) {
            fa[ord[i]] = ord[randint(0, i)];
        }
        return fa;
    }

    /* reservoir sample with replacement */
    template <typename T> vector<T> choices(T left_close, T right_open, int k) {
        assert(left_close < right_open);
        assert(k > 0);
        vector<T> ret;
        ret.reserve(k);
        for (T x = left_close; x < right_open; ++x) {
            for (int test = 1, n = 1; test <= k; ++test, ++n) {
                if (random() < 1. / n) {
                    if (ret.size() < test) {
                        ret.push_back(x);
                    } else {
                        ret[test - 1] = x;
                    }
                }
            }
        }
        return ret;
    }
    
    /* reservoir sample without replacement */
    template <typename T> vector<T> sample(T left_close, T right_open, int k) {
        assert(left_close < right_open);
        assert(k > 0);
        vector<T> ret;
        ret.reserve(k);
        int n = 1;
        for (T x = left_close; x < right_open; ++x, ++n) {
            if (n <= k) {
                ret.push_back(x);
            } else if (random() < k / n) {
                ret[randint(0, k)] = x;
            }
        }
        return ret;
    }

    /* directed acycle graph without duplcated edges (not forest) */
    set<pii> randDAG(int n, int m) {
        assert(n > 0);
        assert(n <= m && m <= n * (n - 1) / 2);
        vector<int> ord(n);
        for (int i = 0; i < n; ++i) ord[i] = i;
        shuffle(ord.begin(), ord.end(), gen);
        vector<int> fa(n);
        fa[ord[0]] = -1;
        for (int i = 1; i < n; ++i) {
            fa[ord[i]] = ord[randint(0, i)];
        }
        set<pii> edges;
        for (int i = 0; i < n; ++i) if (fa[i] > 0) 
            edges.insert({fa[i], i});
        m -= n - 1;
        vector<pii> pops;
        for (int i = 0; i < n; ++i)
            for (int j = i + 1; j < n; ++j) {
                pii edge = {ord[i], ord[j]};
                if (!edges.count(edge)) pops.push_back(edge);
            }
        for (auto idx: sample<int>(0, pops.size(), m))
            edges.insert(pops[idx]);
        assert(edges.size() == m);
        return edges;

    }

    /* undirected graph without self-loop and duplcated edges (not forest)
    */
    vvi randG(int n, int m) {
        vvi adj(n);
        for (auto [x, y]: randDAG(n, m)) {
            adj[x].push_back(y);
            adj[y].push_back(x);
        }
        return adj;
    }


    // /* Random Polygon (maybe not convex, i.e., concave/\*-sharpe */
    // template<typename T> vector<PT> randpoly(int n, T xl, T xr, T yl, T yr) {
    //     assert(n >= 3);
    //     vector<PT> pts(n);
    //     vector<int> ord(n+1);
    //     bool collinear = true;
    //     bool intersect = true;

    //     int its = 0;
    //     while (collinear || intersect) {
    //         LOG(its++, collinear, intersect);
    //         if (!collinear && n == 3) break;
    //         if (collinear) {
    //             collinear = false;
    //             for (int i = 0; i < n; ++i) pts[i] = {randint(xl,xr), randint(yl,yr)};
    //             iota(ord.begin(), ord.begin() + n, 0);
    //             shuffle(ord.begin(), ord.begin() + n, this->gen); ord[n] = ord[0];
    //         }
            
    //         vector<PT> pts2(n);
    //         for (int i = 0; i < n; ++i) pts2[i] = pts[ord[i]];
    //         PLT(pts2);
    //         intersect = false;
    //         for (int i = 0; i < n; ++i) {
    //             LSEG li(pts[ord[i]], pts[ord[i + 1]]);
    //             for (int j = i + 2; j < n; ++j) {
    //                 LSEG lj(pts[ord[j]], pts[ord[j + 1]]);
    //                 auto ints = li & lj;
    //                 if (!ints.size()) continue;
    //                 if (ints.size() == 2) {
    //                     collinear = true;
    //                     break;
    //                 }
    //                 else {
    //                     reverse(ord.begin() + i + 1, ord.begin() + j + 1);
    //                     ord[n] = ord[0];
    //                     intersect = true;
    //                     break;
    //                 }
    //             }
    //             if (collinear || intersect) break;
    //         }
    //     }
    //     LOG(its);
    //     assert(ord[0] == ord[n]);
    //     vector<PT> res(n);
    //     for (int i = 0; i < n; ++i) res[i] = pts[ord[i]];
    //     return res;
    // }
    
    
};

#endif
