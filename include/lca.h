#ifndef INCLUDED_LCA_H
#define INCLUDED_LCA_H

#include "debug.h"

struct Lca {
    using G = vector<vector<int>>;
    int n, l;
    int timer;
    vector<int> tin, tout;
    vector<vector<int>> up;

    Lca(const G& adj, int root): n(adj.size()), tin(n), tout(n), timer(0) {
        l = ceil(log2(n));
        up.assign(n, vector<int>(l + 1));
        function<void(int,int)> dfs = [&](int v, int p) {
            tin[v] = ++timer;
            up[v][0] = p;
            for (int i = 1; i <= l; ++i)
                up[v][i] = up[up[v][i-1]][i-1];
            for (int u : adj[v]) if (u != p) dfs(u, v);
            tout[v] = ++timer;
        };
        dfs(root, root);
    }

    bool is_ancestor(int u, int v) {
        return tin[u] <= tin[v] && tout[u] >= tout[v];
    }

    int lca(int u, int v) {
        if (is_ancestor(u, v))
            return u;
        if (is_ancestor(v, u))
            return v;
        for (int i = l; i >= 0; --i) {
            if (!is_ancestor(up[u][i], v))
                u = up[u][i];
        }
        return up[u][0]; //move top one
    }

};

#ifdef DEBUG
#endif

#endif
