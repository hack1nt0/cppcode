#ifndef INCLUDED_SCC_H
#define INCLUDED_SCC_H

#include "debug.h"

struct Scc {
    int n;
    vector<vector<int>> adj;
    vector<int> scc;
    vector<int> lowest;
    vector<int> preorder;

    Scc(int n): n(n), adj(n), scc(n, -1), lowest(n, -1), preorder(n, -1) {} 
    
    void addEdge(int u, int v) {
        adj[u].push_back(v);
    }

    void decompose() {
        int nodeN = 0;
        int sccN = 0;
        stack<int> stk;
        function<void(int)> dfs = [&](int u) -> void {
            preorder[u] = lowest[u] = nodeN++;
            stk.push(u);
            for (auto v: adj[u])
                if (preorder[v] == -1) {
                    dfs(v);
                    lowest[u] = min(lowest[u], lowest[v]);
                } else if (scc[v] == -1) {
                    lowest[u] = min(lowest[u], preorder[v]);
                }
            if (preorder[u] == lowest[u]) {
                while (stk.size()) {
                    auto v = stk.top();
                    stk.pop();
                    scc[v] = sccN;
                    if (v == u) break;
                }
                sccN++;
            }
        };
        for (int i = 0; i < n; ++i) if (preorder[i] == -1) {
            dfs(i);
        }
        for (int i = 0; i < n; ++i) assert(scc[i] >= 0 && scc[i] < n);
    }

};


#endif
