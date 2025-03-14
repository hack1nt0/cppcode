#ifndef INCLUDED_TWOSAT_H
#define INCLUDED_TWOSAT_H

#include "scc.h"

/*
 * n: count of variables, despite +/-
 */
struct TwoSat: private Scc {
    
    TwoSat(int n): Scc(n * 2 + 1), n(n), _truth(n) {}

    int encode(int u) const {
        return u < 0 ? (-u - 1) * 2 + 1 : (u - 1) * 2;
    }

    void add_clause(int x, int y) {
        assert(-n <= x && x <= n && x);
        assert(-n <= y && y <= n && y);
        addEdge(encode(-x), encode(y));
        addEdge(encode(-y), encode(x));
    }

    bool sat() {
        decompose();
        for (int x = 1; x <= n; ++x) {
            int cmp = scc[encode(x)] - scc[encode(-x)]; 
            if (cmp == 0) return false;
            else _truth[x - 1] = cmp < 0;
        }
        return true;
    }

    bool truth(int x) {
        assert(-n <= x && x <= n && x);
        return x > 0 ? _truth[x - 1] : -_truth[-x - 1];
    }

private:
    int n;
    vector<int> _truth;
};

#endif
