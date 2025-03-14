
#include "debug.h"
/* adaptive simpson's rule */
template <class F>
double intergrate(F, double l, double r, double eps=1e-5) {
    auto simpson = [&](double a, double b) {
        return (F(a) + 4 * F(a + (b - a) / 2) + F(b)) * (b - a) / 6;
    };
    auto asr = [&](auto& self, double a, double b, double eps) -> double {
        double c = a + (b - a) / 2;
        double L = simpson(a, c), R = simpson(c, b), A = simpson(a, b);
        if (abs(L + R - A) <= 15 * eps) return L + R + (L + R - A) / 15;
        return self(self, a, c, eps / 2) + self(self, c, b, eps / 2);
    };
    return asr(asr, l, r, eps);
}

