#ifndef INCLUDED_SEGTREE_H
#define INCLUDED_SEGTREE_H

#include "debug.h"

/*
Pointer based range tree, slow but agile.
*/
template <
    typename V 
> struct SegTree {
    struct Node {
        V v;
        int l, r;
        Node *lchd, *rchd;
    };
    Node* root;
    int n;
    function<void(V&,const V&,const V&)> maintain;
    function<void(const V&,V&,V&)> pushdown;
    
    SegTree(
            int n,
            function<void(V&,int)> init,
            function<void(V&,const V&,const V&)> maintain,
            function<void(const V&,V&,V&)> pushdown=[](const V& v, V& l, V& r) {}
            ): n(n), maintain(maintain), pushdown(pushdown) {
        assert(n);
        function<Node*(int,int)> F = [&](int l, int r) -> Node* {
            assert(l < r);
            Node* x = new Node;
            x->l = l;
            x->r = r;
            if (l + 1 == r) {
                x->lchd = nullptr;
                x->rchd = nullptr;
                init(x->v, l);
            } else {
                int mid = l + ((r - l) >> 1);
                x->lchd = F(l, mid);
                x->rchd = F(mid, r);
                maintain(x->v, x->lchd->v, x->rchd->v);
            }
            return x; 
        };
        root = F(0, n);
    }

    int size() { return n; }

    bool overlay(int aL, int aR, int bL, int bR) {
        return !(aR <= bL || bR <= aL);
    }

    bool contains(int aL, int aR, int bL, int bR) {
        return aL <= bL && bR <= aR;
    }

    template <class Vis>
    void visit(int l, int r, Vis vis) {
        function<void(int,int,Node*)> F = [&](int l, int r, Node* x) {
            if (!overlay(l, r, x->l, x->r))
                return;
            if (contains(l, r, x->l, x->r)) {
                vis(x->v);
            } else {
                pushdown(x->v, x->lchd->v, x->rchd->v);
                F(l, r, x->lchd);
                F(l, r, x->rchd);
                maintain(x->v, x->lchd->v, x->rchd->v);
            }
        };
        F(l, r, root);
    }
};

#ifdef DEBUG
template <typename V>
void __print(SegTree<V> &tree) {
    assert(tree.root != nullptr);
    cerr << "\ndigraph {\n";
    vector<int> leafs;
    using N = typename SegTree<V>::Node;
    function<void(N*,int)> F = [&](N* x, int idx) {
        cerr << "\t" << idx << " [label=<" << x->v;
        cerr << "<BR/>[" << x->l+1 << "," << x->r << "]";
        cerr << "<BR/>>]\n";
        if (x->lchd == nullptr && x->rchd == nullptr) {
            leafs.push_back(idx);
        } else {
            F(x->lchd, idx * 2 + 1);
            F(x->rchd, idx * 2 + 2);
            cerr << "\t" << idx << " -> " << idx * 2 + 1 << "\n";
            cerr << "\t" << idx << " -> " << idx * 2 + 2 << "\n";
        }
    };
    F(tree.root, 0);
    cerr << "\t{rank=source;" << 0 << "}\n";
    cerr << "\t{rank=sink;";
    for (auto x : leafs) if (x) cerr << x << ";";
    cerr << "}\n";
    cerr << "}\n";
}
#endif

#endif

