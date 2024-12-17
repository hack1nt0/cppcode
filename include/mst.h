#ifndef INCLUDED_MST_H
#define INCLUDED_MST_H

#include "graph.h"

template <typename G>
bool find_cycle(G& g, int u, vector<int>& father, vector<int>& color) {
    if (color[u] == -1) {
        int fa = u;
        while (1) {
            fa = father[fa];
            color[fa] = 2;
            if (fa == u) break;
        }
        return true;
    }
    if (color[u] >= 1) return false;
    color[u] = -1;
    for (auto [s, t, w, _] : g.adj(u)) {
        father[t] = u;
        if (find_cycle(g, t, father, color)) return true;
    }
    color[u] = 1;
    return false;
}
/*
    https://en.wikipedia.org/wiki/Edmonds%27_algorithm
*/
template <typename G, typename E=typename G::E>
vector<E*> directed_mst(G& g, int s, vector<int>& father, vector<int>& color) {
    vector<E*> P(g.nv()); // Potentials
    for (int u = 0; u < g.nv(); u++) {
        auto& es = g.adj(u);
        for (auto p = es.begin(); p != es.end();) {
            auto q = next(p);
            auto& e = *p;
            if (p->t == s) {
                es.erase(p);
            } else {
                if (!P[e.t] || e.w < P[e.t]->w) P[e.t] = &e;
            }
            p = q;
        }
    }
    fill(begin(color), end(color), 0);
    bool has_cycle = false;
    for (int u = 0; u < g.nv(); ++u) if (color[u] == 0) {
        if (find_cycle(g, u, father, color)) {
            has_cycle = true;
            break;
        }
    }
    if (!has_cycle) {
        return P;
    }
    G ng(g.nv() + 1);
    for (int u = 0; u < g.nv(); u++) {
        for (auto& e : g.adj(u)) {
            bool sC = color[e.s] == 2;
            bool tC = color[e.t] == 2;
            if (sC && tC) {
                ;
            } else if (!sC && tC) {
                ng.adde({e.s, g.nv(), e.w - P[e.t]->w, &e});
            } else if (sC && !tC) {
                ng.adde({g.nv(), e.t, e.w, &e});
            } else {
                ng.adde({e.s, e.t, e.w, &e});
            }
        }
    }
    vector<E*> A = directed_mst(ng, s, father, color);
    for (auto e : A) if (e) P[e->pre->t] = e->pre;
    return P;
}

#endif