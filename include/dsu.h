#ifndef INCLUDED_DSU_H
#define INCLUDED_DSU_H

#include "debug.h"

//Disjoint Set Union
struct DSU {
    vector<int> root;
    vector<int> rank;
    vector<int> rootsize;
    int S;
    DSU(int n): root(n), rank(n, 0), rootsize(n, 1), S(n) {
        assert(n);
        iota(root.begin(), root.end(), 0);
    }

    void join(int x, int y) {
        assert(0 <= x && x < root.size());
        assert(0 <= y && y < root.size());
        int fx = find(x);
        int fy = find(y);
        if (fx != fy) {
            S--;
            if (rank[fx] > rank[fy]) swap(fx, fy);
            root[fx] = fy;
            rank[fy] = max(rank[fx] + 1, rank[fy]);
            rootsize[fy] += rootsize[fx];
            rootsize[fx] = 0;
        }
    }

    int find(int x) {
        assert(0 <= x && x < root.size());
        if (root[x] == x) return x;
        else return root[x] = find(root[x]);
    }

    int size() { return S; }
    int size(int root) { return rootsize[root]; }
    
};

#endif
