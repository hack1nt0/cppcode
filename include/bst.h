#ifndef INCLUDED_BST_H
#define INCLUDED_BST_H
#include "debug.h"

/*
    0 is null node
    erase is lazy: just set count = 0
*/
template <typename T> struct Bst {
    vector<T> val;
    vector<int> l;
    vector<int> r;
    vector<int> h;
    vector<int> s; //size of subtree
    vector<int> c; //count of element
    int root = 0;

    Bst() : val(1), l(1), r(1), h(1), s(1), c(1) {}

    int size() const { return s[root]; }

    void maintain(int x) {
        s[x] = c[x] + s[l[x]] + s[r[x]];
        h[x] = max(h[l[x]], h[r[x]]) + 1;
    }

    T* end() { return &val[0]; }

    T* find(const T& v) {
        function<int(int)> F = [&](int x) {
            if (!x) return x;
            int cmp = _cmp(v, val[x]);
            if (cmp == 0) return c[x] ? x : 0;
            if (cmp <  0) return F(l[x]);
            return F(r[x]);
        };
        return &val[F(root)];
    }

    // @unfinished
    T* lower_bound(const T& v) {
        auto find_smallest = [&](int x) -> int {
            int res = x;
            while (l[x]) x = l[x], res = x;
            return res;
        };
        auto dfs = [&](auto& self, int x) -> int {
            if (!x) return x;
            int cmp = _cmp(v, val[x]);
            if (cmp == 0) return c[x] ? x : find_smallest(r[x]);
            if (cmp <  0) {
                int res = self(self, l[x]);
                return !res && c[x] ? x : res;
            }
            return self(self, r[x]);
        };
        return &val[dfs(dfs, root)];
    }

    T* upper_bound(const T& v) {

    }

    int order_of_key(const T& v) {
        int ord = 0;
        function<int(int)> F = [&](int x) {
            if (!x) return ord;
            int cmp = _cmp(v, val[x]);
            if (cmp < 0) return F(l[x]);
            ord += s[l[x]];
            if (cmp == 0) return ord;
            ord += c[x];
            return F(r[x]);
        };
        return F(root);
    }

    const T* find_by_order(int ord) const {
        assert(ord >= 0);
        function<int(int)> F = [&](int x) {
            if (!x) return x;
            if (s[l[x]] > ord) return F(l[x]);
            ord -= s[l[x]];
            if (c[x] > ord) return x;
            ord -= c[x];
            return F(r[x]);
        };
        return &val[F(root)];
    }

    void insert(const T& v) {
        function<int(int)> F = [&](int x) {
            if (!x) {
                val.push_back(v);
                l.push_back(0);
                r.push_back(0);
                s.push_back(1);
                h.push_back(0);
                c.push_back(1);
                return int(val.size() - 1);
            }
            int cmp = _cmp(v, val[x]);
            if (cmp == 0) {
                ++c[x];
            } else if (cmp < 0) {
                l[x] = F(l[x]);
            } else {
                r[x] = F(r[x]);
            }
            maintain(x);
            return rotate(x);
        };
        root = F(root);
    }

    void erase(const T &v) {
        function<int(int)> F = [&](int x) {
            // LOG(x, c[x], v);
            if (!x) return x;
            int cmp = _cmp(v, val[x]);
            if (cmp == 0) {
                c[x] = max(0, c[x] - 1);
            } else if (cmp < 0) {
                l[x] = F(l[x]);
            } else if (cmp > 0) {
                r[x] = F(r[x]);
            }
            maintain(x);
            return x;
        };
        root = F(root);
    }

    int rotate(int x) {
        assert(x);
        int hl = h[l[x]], hr = h[r[x]];
        if (abs(hl - hr) <= 1) return x;
        int y; //pivot
        int z; //split
        if (hl < hr) {
            y = r[x];
            z = l[y];
            l[y] = x;
            r[x] = z;
        } else {
            y = l[x];
            z = r[y];
            r[y] = x;
            l[x] = z;
        }
        maintain(x);
        maintain(y);
        return y;
    }

    int _cmp(const T& a, const T& b) {
        return a < b ? -1 : (b < a ? 1 : 0);
    }

    void dfs(
        function<void(int)> before,
        function<void(int)> middle,
        function<void(int)> after
    ) const {
        function<void(int)> F = [&](int x) {
            if (!x) return;
            if (c[x]) before(x);
            F(l[x]);
            if (c[x]) middle(x);
            F(r[x]);
            if (c[x]) after(x);
        };
        F(root);
    }

    template <class S>
    bool operator==(const S& o) {
        if (size() != o.size()) return false;
        vector<int> idx;
        dfs([](int x) {}, [&](int x) { idx.push_back(x); }, [](int x) {});
        auto it2 = o.begin();
        for (auto i: idx) {
            if (val[i] != *it2) return false;
            ++it2;
        }
        return true;
    }

};
#ifdef DEBUG
template <typename T> void __print(const Bst<T>& o) {
    cerr << "(";
    for (int i = 0; i < o.size(); ++i) cerr << *o.find_by_order(i) << ",";
    cerr << ")";
}
#endif

#endif
