#ifndef INCLUDED_SEGTREEX_H
#define INCLUDED_SEGTREEX_H

#include "debug.h"

#define L(x) ((x << 1) + 1)
#define R(x) ((x << 1) + 2)
#define M(l, r) (l + ((r - l) >> 1))

#define DISJOIN(aL,aR,bL,bR) (aR <= bL || bR <= aL)
#define CONTAIN(aL,aR,bL,bR) (aL <= bL && bR <= aR)

/*
Array based segtree, faster
init: function<void(V&,int)> init,
maintain: function<void(V&,V&,V&)> maintain, 
pushdown: function<void(V&,V&,V&)> pushdown=[](V& v, V& l, V& r) {}
*/

template <typename V> 
struct SegTreeX {
    vector<V> val;
    int n, nn;

    SegTreeX(int n) {
        assert(n);
        this->n = n;
        nn = 1;
        while (nn < n) nn <<= 1;
        nn *= 2;
        val.resize(nn);
    }

    template <class Vis>
    void visit(int l, int r, Vis vis) {
        auto F = [&](auto& self, int ql, int qr, int l, int r, int id) -> void {
            if (DISJOIN(ql, qr, l, r))
                return;
            if (CONTAIN(ql, qr, l, r)) {
                vis(val[id]);
            } else {
                // pushdown(val[id], val[L(id)], val[R(id)]);
                int mid = l + ((r - l) >> 1);
                self(self, ql, qr, l, mid, L(id));
                self(self, ql, qr, mid, r, R(id));
                val[id] = val[L(id)] + val[R(id)];
                // maintain(val[id], val[L(id)], val[R(id)]);
            }
        };
        F(F, l, r, 0, n, 0);
    }

    virtual V query(int l, int r) {
        V res;
        visit(l, r, [&](V& x) { res = res + x; });
        return res;
    }
    V query(int i) { return query(i, i + 1); }
    V query() { return query(0, n); }

    virtual void update(int i, const V& v) { 
        visit(i, i + 1, [&](V& x) { x = v; });
    }

};

template <typename V, typename ACC> 
struct LazySegTreeX {
    vector<V> val;
    vector<ACC> acc;
    int n, nn;

    LazySegTreeX(int n) {
        assert(n);
        this->n = n;
        nn = 1;
        while (nn < n) nn <<= 1;
        nn *= 2;
        val.resize(nn);
        acc.resize(nn);
    }
    
    template <class Vis>
    void visit(int l, int r, Vis vis) {
        auto FF = [&](auto& self, int ql, int qr, int l, int r, int id) -> void {
            if (DISJOIN(ql, qr, l, r))
                return;
            if (CONTAIN(ql, qr, l, r)) {
                vis(id);
            } else {
                //pushdown
                acc[L(id)] = acc[L(id)] + acc[id];
                acc[R(id)] = acc[R(id)] + acc[id];
                acc[id] = ACC();
                //recursive
                int mid = l + ((r - l) >> 1);
                self(self, ql, qr, l, mid, L(id));
                self(self, ql, qr, mid, r, R(id));
                //maintain
                val[id] = (val[L(id)] + acc[L(id)]) + (val[R(id)] + acc[R(id)]);
            }
        };
        FF(FF, l, r, 0, n, 0);
    }

    V query(int l, int r) {
        V res;
        visit(l, r, [&](int i) { res = res + (val[i] + acc[i]); });
        return res;
    }

    void update(int l, int r, const ACC& v) { 
        visit(l, r, [&](int i) { acc[i] = acc[i] + v; });
    }
};

#ifdef DEBUG
template <class T, class Vis>
void print_segtree(const T& tree, Vis vis) {
    cerr << "\ndigraph { ";
    vector<int> leafs;
    function<void(int,int,int)> F = [&](int l, int r, int id) {
        cerr << "\t" << id << " [label=<";
        vis(id);
        cerr << "<BR/>[" << l+1 << "," << r << "]";
        cerr << "<BR/>>]; ";
        if (l + 1 == r) {
            leafs.push_back(id);
        } else {
            cerr << "\t" << id << " -> " << L(id) << "; ";
            cerr << "\t" << id << " -> " << R(id) << "; ";
            int mid = M(l, r);
            F(l, mid, L(id));
            F(mid, r, R(id));
        }
    };
    F(0, tree.n, 0);
    cerr << "\t{rank=source;" << 0 << "}; ";
    cerr << "\t{rank=sink;";
    for (auto x : leafs) if (x) cerr << x << ";";
    cerr << "}; ";
    cerr << "}\n";
}

template <typename V> 
void __print(const SegTreeX<V>& tree) { print_segtree(tree, [&](int i) { cerr << tree.val[i]; }); }

template <typename V, typename ACC> 
void __print(const LazySegTreeX<V, ACC>& tree) { 
    print_segtree(tree, [&](int i) { cerr << "val: " << tree.val[i] << "<BR/>acc: " << tree.acc[i]; }); 
}
#endif

#endif

