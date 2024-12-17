#ifndef INCLUDED_SEGTREEX_H
#define INCLUDED_SEGTREEX_H

#include "debug.h"

/*
Array based segtree, faster
init: function<void(V&,int)> init,
maintain: function<void(V&,V&,V&)> maintain, 
pushdown: function<void(V&,V&,V&)> pushdown=[](V& v, V& l, V& r) {}
*/
template <
    typename V
> struct SegTreeX {
    vector<V> vs;
    int n;
    function<void(V&,const V&,const V&)> maintain;
    function<void(const V&,V&,V&)> pushdown;
    
    SegTreeX(
            int n,
            function<void(V&,int)> init,
            function<void(V&,const V&,const V&)> maintain,
            function<void(const V&,V&,V&)> pushdown=[](const V& v, V& l, V& r) {}
    ): vs(), maintain(maintain), pushdown(pushdown) {
        this->n = 1;
        while (this->n < n) this->n <<= 1;
        vs.resize(this->n * 2);
        assert(n);
        function<void(int,int,int)> F = [&](int l, int r, int id) -> void {
            if (l + 1 == r) {
                // if (l >= n) vs[id] = V();
                // else init(vs[id], l);
                init(vs[id], l);
            } else {
                int mid = l + ((r - l) >> 1);
                F(l, mid, L(id));
                F(mid, r, R(id));
                maintain(vs[id], vs[L(id)], vs[R(id)]);
            }
        };
        F(0, this->n, 0);
    }

    inline int L(int x) { return (x << 1) + 1; }
    inline int R(int x) { return (x << 1) + 2; }
    inline bool overlay(int aL, int aR, int bL, int bR) { return !(aR <= bL || bR <= aL); }
    inline bool contains(int aL, int aR, int bL, int bR) { return aL <= bL && bR <= aR; }

    template <class Vis>
    void visit(int l, int r, Vis vis) {
        function<void(int,int,int,int,int)> F = [&](int ql, int qr, int l, int r, int id) {
            if (!overlay(ql, qr, l, r))
                return;
            if (contains(ql, qr, l, r)) {
                vis(vs[id]);
            } else {
                pushdown(vs[id], vs[L(id)], vs[R(id)]);
                int mid = l + ((r - l) >> 1);
                F(ql, qr, l, mid, L(id));
                F(ql, qr, mid, r, R(id));
                maintain(vs[id], vs[L(id)], vs[R(id)]);
            }
        };
        F(l, r, 0, n, 0);
    }
};

#ifdef DEBUG
template <typename V>
void __print(SegTreeX<V> &tree) {
    cerr << "\ndigraph {\n";
    vector<int> leafs;
    function<void(int,int,int)> F = [&](int l, int r, int id) {
        cerr << "\t" << id << " [label=<" << tree.vs[id];
        cerr << "<BR/>[" << l+1 << "," << r << "]";
        cerr << "<BR/>>]\n";
        if (l + 1 <= r) {
            leafs.push_back(id);
        } else {
            cerr << "\t" << id << " -> " << tree.L(id) << "\n";
            cerr << "\t" << id << " -> " << tree.R(id) << "\n";
            int mid = l + ((r - l) >> 1);
            F(l, mid, tree.L(id));
            F(mid, r, tree.R(id));
        }
    };
    F(0, tree.n, 0);
    cerr << "\t{rank=source;" << 0 << "}\n";
    cerr << "\t{rank=sink;";
    for (auto x : leafs) if (x) cerr << x << ";";
    cerr << "}\n";
    cerr << "}\n";
}
#endif

#endif

