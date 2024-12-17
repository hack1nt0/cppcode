#ifndef INCLUDED_MAXFLOW_H
#define INCLUDED_MAXFLOW_H
#include "debug.h"

struct ResidualGraph {
    using vi = vector<int>;
    vector<vi> adj;
    vi s, t, cap, rev, flow, cost;
    int n, m;
    
    ResidualGraph(int n) : 
        adj(n), s(), t(), cap(), rev(), flow(), cost(), n(n), m(0)
    {}
    
    void emplace_back(int S, int T, int CAP, int COST=0) {
        auto addedge = [&](int S, int T, int E, int REV, int CAP, int COST) {
            adj[S].push_back(E);
            s.push_back(S);
            t.push_back(T);
            rev.push_back(REV);
            flow.push_back(0);
            cap.push_back(CAP);
            cost.push_back(COST);
        };
        addedge(S, T, m, m + 1, CAP, COST);
        addedge(T, S, m + 1, m, 0, 0);
        m += 2;
    }

    int other(int e, int x) { return x == s[e] ? t[e] : s[e]; }
    
};

int maxflow(ResidualGraph& g, int S, int T) {
    using vi = vector<int>;
    const int INF = 2e9;
    int ret = 0;
    while (1) {
        vi dist(g.n, INF);
        queue<int> que;
        que.push(S);
        dist[S] = 0;
        while (que.size()) {
            int x = que.front();
            que.pop();
            for (int e : g.adj[x]) {
                int y = g.t[e];
                if (g.cap[e] - g.flow[e] > 0 && dist[y] == INF) {
                    dist[y] = dist[x] + 1;
                    que.push(y);
                }
            }
        }
        if (dist[T] == INF) break;
        vi ptr(g.n);
        function<int(int,int)> dfs = [&](int x, int acc) {
            if (x == T) return acc;
            while (ptr[x] < g.adj[x].size()) {
                int e = g.adj[x][ptr[x]];
                int y = g.t[e];
                if (dist[S] < dist[y] && g.cap[e] - g.flow[e] > 0) {
                    int res = dfs(y, min(acc, g.cap[e] - g.flow[e]));
                    if (0 < res && res < INF) {
                        g.flow[e] += res;
                        g.cap[g.rev[e]] += res;
                        return res;
                    }
                }
                ptr[x]++;
            }
            return 0;
        };
        while (1) {
            int acc = dfs(S, INF);
            if (0 < acc && acc < INF) ret += acc;
            else break;
        }
    }
    return ret;
}

int mincostflow(ResidualGraph& g, int S, int T, int FLOW) {
    using pii = pair<int, int>;
    using vi = vector<int>;
    const int INF = 2e9;
    int ret = 0;
    while (FLOW > 0) {
        vector<pii> dist(g.n, {INF, INF});
        set<int> upds{S};
        dist[S] = {0, -INF};
        vi pre(g.n);
        while (upds.size()) {
            int updsize = upds.size();
            int minupd = *upds.begin();
            int maxupd = *upds.rbegin();
            int x = *upds.begin();
            for (int e: g.adj[x]) {
                int y = g.other(e, x);
                if (!(g.cap[e] - g.flow[e] > 0)) continue;
                pii disty{dist[x].first + g.cost[e], -min(-dist[x].second, g.cap[e])};
                if (disty < dist[y]) {
                    dist[y] = disty;
                    pre[y] = e;
                    upds.insert(y);
                }
            }
            if (upds.size() == updsize && *upds.begin() == minupd && *upds.rbegin() == maxupd) break;
        }
        if (dist[T].first == INF) break;
        int flowdel = min(FLOW, -dist[T].second);
        ret += dist[T].first * flowdel;
        FLOW -= flowdel;
        int V = T;
        while (V != S) {
            int e = pre[V];
            g.flow[e] += flowdel;
            g.cap[g.rev[e]] += flowdel;
            V = g.other(e, V);
        }
    }
    return ret;
}

// minimum vertex cover

vector<int> minvc(const ResidualGraph& g, const function<bool(int)> &isLeft) {
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
