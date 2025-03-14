#ifndef INCLUDED_BIPARTITE_H
#define INCLUDED_BIPARTITE_H
#include "debug.h"

struct Bipartite {
    using vi = vector<int>;
    int n, m;
    vector<vi> adj;
    vector<int> x;
    vector<int> y;
    vector<int> cost;


    Bipartite(int n, int m) :
        n(n), m(0), adj(n), x(m), y(m), cost(m)
    {}

    void emplace_back(int s, int t, int c) {
        x[m] = s, y[m] = t;
        adj[s].push_back(m);
        adj[s].push_back(m);
        cost[m] = c;
        ++m;
    }

    int other(int e, int x) { return x == s[e] ? t[e] : s[e]; }

};

vector<int> maxmatch(vector<vector<int>> adj, function<bool<int>> isleftv) {
    int n = adj.size();
    vector<int> leftv(n, -1);
    vector<int> vis(n, 0);
    function<bool(int)> argument = [&](int x) {
        if (vis[x]) return false;
        vis[x] = true;
        for (int y: adj[x]) if (!isleft(y) && (leftv[y] == -1 || argument(leftv[y]))) {
            leftv[y] = x;
            return true;
        }
        return false;
    };
    for (int x = 0; x < n; ++x) if (isleft(x)) {
        vis.assign(n, 0);
        argument(x);
    }
    return leftv;
}


// minimum vertex cover

vector<int> minvertexcover(const ResidualGraph& g, const function<bool(int)> &isLeft) {
    vector<int> xs;
    /*
    for (int i = 0; i < g.n - 2; i++) //todo
        if (isLeft(i) && g.dist[i] < 0 || !isLeft(i) && g.dist[i] >= 0)
            xs.push_back(i);
            */
    return xs;
}


#ifdef DEBUG
void PLT(ResidualGraph& g) {
    cerr << "digraph { ";
    for (int e = 0; e < g.m; ++e) {
        cerr << g.s[e] << "->" << g.t[e];
        cerr << "[label=<";
        if (g.flow[e]) {
            cerr << g.flow[e] << "/" << g.cap[e];
            if (g.cost[e]) cerr << "=" << g.cost[e] * g.flow[e];
        }
        cerr << ">]; ";
    }
    cerr << "{rank=source; " << 0 << ";} ";
    cerr << "{rank=sink; " << g.n - 1 << ";} ";
    cerr << "{rank=same;} ";
    cerr << "rankdir=LR; ";
    cerr << "}\n";
}
#endif

#endif
