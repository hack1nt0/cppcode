#ifndef INCLUDED_GEOMETRY_H
#define INCLUDED_GEOMETRY_H

#include "debug.h"

using D = long double;
#define EPS 1e-9

//using PT = complex<D>;
//#define X real()
//#define Y imag()
#define U(p) ((p) / abs(p))
#define Z(x) (abs(x) < EPS)
#define SIGN(x) (((x) > -EPS) - ((x) < EPS))
#define DCMP(x, y) SIGN((x) - (y))

struct PT {
    using val = PT;
    using ref = const val&;
    D x, y;
    PT(D x=0, D y=0): x(x), y(y) {}
    PT(ref o): x(o.x), y(o.y) {}
    PT(const complex<D>& o): x(o.real()), y(o.imag()) {}
    val operator=(ref o) { x = o.x, y = o.y; return *this; }
    bool operator==(const PT& b) const { ref a = *this; return Z(a.x - b.x) && Z(a.y - b.y); }
    auto operator<=>(const PT& b) const { ref a = *this; return a == b ? (0<=>0) : (Z(a.x - b.x) ? a.y <=> b.y : a.x <=> b.x); }
};
PT operator+(const PT& a, const PT& b) { return {a.x + b.x, a.y + b.y}; }
PT operator+(const PT& a, D b) { return {a.x + b, a.y + b}; }
PT operator-(const PT& a, const PT& b) { return {a.x - b.x, a.y - b.y}; }
PT operator-(const PT& a, D b) { return {a.x - b, a.y - b}; }
PT operator*(const PT& a, D b) { return {a.x * b, a.y * b}; }
PT operator*(const PT& a, const PT& b) { return {a.x * b.x, a.y * b.y}; }
PT operator/(const PT& a, D b) { return {a.x / b, a.y / b}; }
D cross(const PT& a, const PT& b) { return a.x * b.y - b.x * a.y; }
D dot(const PT& a, const PT& b) { return a.x * b.x + a.y * b.y; }
D abs(const PT& a) { return hypot(a.x, a.y); }
D arg(const PT& a) { return atan2(a.y, a.x); }
istream& operator>>(istream& s, PT& pt) { D x, y; s >> x >> y; pt = {x, y}; return s; }
ostream& operator<<(ostream& s, PT& pt) { s << pt.x << " " << pt.y; return s; }
#ifdef DEBUG
void __print(const PT& a) { cerr << "(" << a.x << "," << a.y << ")"; }
#endif


struct LSEG {
    using val = PT;
    using ref = const PT&;
    val s, d;
    // Two points
    LSEG(ref a, ref b) : s(a), d(b-a) {}
    // Point and angle
    LSEG(ref a, D theta) : s(a), d(polar(1.l, theta)) {}
    PT t() const { return s + d; }
};

struct LINE {
    using val = PT;
    using ref = const PT&;
    val s, d;
    // Two points
    LINE(ref a, ref b) : s(a), d(b-a) {}
    // Point and angle
    LINE(ref a, D theta) : s(a), d(polar(1.l, theta)) {}
    PT t() const { return s + d; }
    LINE(const LSEG& o): s(o.s), d(o.d) {}
};

//using LINE = Line<0>;
//using LSEG = Line<1>;

//point logical ops
//namespace std {
    //auto operator<=>(const D& a, const D& b) { return Z(a - b) ? 0 : (a < b ? -1 : 1); }
    //auto operator<=>(const PT& a, const PT& b) { return Z(a.X - b.X) ? a.Y <=> b.Y : a.X <=> b.X; }
//};
// helper functions
//D cross(const PT& a, const PT& b) { return (conj(a) * b).Y; }
//D dot(const PT& a, const PT& b) { return (conj(a) * b).X; }
//bool parallel(const PT& d1, const PT& d2) { return Z(abs(arg(d1)) - abs(arg(d2))); }
bool parallel(const PT& d1, const PT& d2) { return Z(cross(d1, d2)); }
PT interact(const LINE& l1, const LINE& l2) {
    return l1.s + l1.d * cross(l2.d, l2.s - l1.s) / cross(l2.d, l1.d);
}
// helper functions end

vector<PT> operator&(const PT& pt, const LINE& line) {
    if (parallel(pt - line.s, line.d)) return {pt}; else return {};
}
vector<PT> operator&(const PT& pt, const LSEG& line) {
    if ((pt & LINE(line)).size() && min(line.s, line.t()) <= pt && pt <= max(line.s, line.t())) return {pt}; else return {};
}
bool operator==(const LINE& l1, const LINE& l2) { return parallel(l1.d, l2.d) && (l1.s & l2).size(); }
bool operator!=(const LINE& l1, const LINE& l2) { return !(l1 == l2); }
vector<PT> operator&(const LINE& l1, const LINE& l2) {
    if (l1 == l2) return {l1.s, l1.t()};
    if (parallel(l1.d, l2.d)) return {};
    return {interact(l1, l2)};
}
vector<PT> operator&(const LSEG& l1, const LINE& l2) {
    if (LINE(l1) == l2) return {l1.s, l1.t()};
    if (parallel(l1.d, l2.d)) return {};
    PT p = interact(LINE(l1), l2);
    LOG(l1.s, l1.t(), p);
    if ((p & l1).size()) return {p}; else return {};
}
vector<PT> operator&(const LSEG& l1, const LSEG& l2) {
    if (l1 == l2) return {l1.s, l1.t()};
    if (parallel(l1.d, l2.d)) {
        PT pts[2][2] = {
            {l1.s, l1.t()},
            {l2.s, l2.t()},
        };
        for (int i = 0; i < 2; ++i) {
            if (pts[i][1] < pts[i][0]) swap(pts[i][1], pts[i][0]);
        }
        if (pts[0][1] < pts[1][0] || pts[1][1] < pts[0][0]) return {};
        PT lp = max(pts[0][0], pts[1][0]);
        PT rp = min(pts[0][1], pts[1][1]);
        if (lp == rp) return {lp}; else return {lp, rp};
    }
    PT p = interact(LINE(l1), LINE(l2));
    if ((p & l1).size() && (p & l2).size()) return {p}; else return {};
}

/* POLYGON */
vector<PT> convexhull(vector<PT>& ply) {
    int n = ply.size();
    if (n <= 2) return ply;
    sort(ply.begin(), ply.end());
    vector<PT> hull(n + 2);
    int m = 0;
    auto half = [&]() {
        for (auto z: ply) {
            while(m >= 2 && SIGN(cross(hull[m - 1] - hull[m - 2], z - hull[m - 1])) <= 0) --m;
            assert(m < n+2);
            hull[m++] = z;
        }
    };
    half();
    m--;
    reverse(ply.begin(), ply.end());
    half();
    m--;
    return {hull.begin(), hull.begin() + m};
}
/*
vector<PT> concavehull(const vector<PT>& ply, int k = 3) {
    if (ply.size() <= 3) return ply;
    int n = ply.size();
    using vd = vector<D>;
    vector<vd> B(n, vd(n));
    for (int i = 0; i < n; ++i) {
        vd D(n);
        for (int j = 0; j < n; ++j) D[j] = abs(ply[i] - ply[j]);
        iota(B[i].begin(), B[i].end());
        sort(B[i].begin(), B[i].end(), [&](int x, int y) -> bool { return D[x] < D[y]; });
    }

    for (int i = 0; i < n; ++i) swap(ply[i].x, ply[i].y);
    int start = 0;
    for (int i = 1; i < n; ++i) if (ply[i] < ply[start]) start = i;
    for (int i = 0; i < n; ++i) swap(ply[i].x, ply[i].y);
    for (int i = 0; 
}*/

//#ifdef DEBUG
void PLT(PT pt) { 
    cerr << "<circle " << pt.x << " " << pt.y << " " << 0.1 << " />\n";
}
void PLT(LINE l) { 
    cerr << "<line " << l.s.x << " " << l.s.y << " " << l.t().x << " " << l.t().y << " />\n";
}
void PLT(LSEG l) { 
    cerr << "<line " << l.s.x << " " << l.s.y << " " << l.t().x << " " << l.t().y << " />\n";
}
void PLT(const vector<PT>& poly) { 
    cerr << "<polygon ";
    for (auto pt: poly) cerr << pt.x << "," << pt.y << " ";
    cerr << "/>\n";
}
//#endif

#endif
