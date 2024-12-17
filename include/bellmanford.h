#ifndef INCLUDED_SHORTESTPATH_H
#define INCLUDED_SHORTESTPATH_H

#include "graph.h"

/*
    Return: false if negative cycle(s) exists.
*/
template <typename G, typename W=typename G::W>
bool bellmanford(G& g, int s, vector<W>& dist, vector<int>& pre) {
    fill(dist.begin(), dist.end(), numeric_limits<W>::max());
    dist[s] = 0;
    int nv = g.nv();
    vector<int> upds(nv, 0);
    queue<tuple<int, typename G::W>> que;
    que.push({s, 0});
    while (que.size()) {
        auto [u, d] = que.front();
        que.pop();
        if (dist[u] < d) continue;
        for (auto& e : g.adj(u)) if ((d + e.w) < dist[e.t]) {
            dist[e.t] = d + e.w;
            pre[e.t] = u;
            upds[e.t]++;
            if (upds[e.t] >= nv) return false;
            que.push({e.t, dist[e.t]});
        }
    }
    return true;
}

#endif