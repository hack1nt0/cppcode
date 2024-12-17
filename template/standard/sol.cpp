
#include "include/libs"


int main() {
    ios_base::sync_with_stdio(false);
    cin.tie(&cout);
    using val = long long;
    const val INF = 1e17 + 4;
    const int S = 5;
    int n; cin >> n;
    vector<val> a(n), b(n);
    for (auto& x: a) cin >> x;
    for (auto& x: b) cin >> x;
    using V = array<array<val, S>, S>;
    auto init = [&](V& x, int i) {
        for (int i = 0; i < S; ++i) x[i].fill(-INF);
        if (i >= n) {
            return;
        }
        x[0][0] = 0;
        x[0][1] = a[i] + b[i];
        x[0][2] = a[i] + b[i] * 2;
        x[1][1] = a[i];
        x[1][2] = a[i] + b[i];
        x[2][2] = 0;
        x[2][3] = a[i] + b[i];
        x[2][4] = a[i] + b[i] * 2;
        x[3][3] = a[i];
        x[3][4] = a[i] + b[i];
        x[4][4] = 0;
    };
    auto combine = [](const V& y, const V& z) -> V {
        V x;
        for (int i = 0; i < S; ++i) {
            x[i].fill(-INF);
        for (int j = i; j < S; ++j)
        for (int k = i; k <= j; ++k) if (y[i][k] != -INF and z[k][j] != -INF)
            x[i][j] = max(x[i][j], y[i][k] + z[k][j]);
        }
        return x;
    };
    SegTreeX<V> tree(n, init, [&](V& x, const V& y, const V& z) { x = combine(y, z); });
    int q; cin >> q;
    while (q--) {
        int type; cin >> type;
        if (type == 1) {
            int p, x; cin >> p >> x; --p;
            a[p] = x;
            tree.visit(p, p + 1, [&](V& x) { init(x, p); });
        }
        if (type == 2) {
            int p, x; cin >> p >> x; --p;
            b[p] = x;
            tree.visit(p, p + 1, [&](V& x) { init(x, p); });
        } else if (type == 3) {
            int l, r; cin >> l >> r; --l, --r;
            V res;
            for (int i = 0; i < S; ++i) res[i].fill(-INF);
            res[0][0] = 0;
            tree.visit(l, r + 1, [&](V& x) { res = combine(res, x); });
            cout << res[0][4] << "\n";
        }
    }
    return 0;
}
