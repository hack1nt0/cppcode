#ifndef INCLUDED_BINSEARCH_H
#define INCLUDED_BINSEARCH_H

#include "debug.h"

int findclose(int x, const vector<int> &xs, int dir, int null=-1) {
    if (dir < 0) {
        auto ptr = lower_bound(xs.begin(), xs.end(), x);
        return (ptr != xs.begin()) ? *--ptr : null;
    } else {
        auto ptr = upper_bound(xs.begin(), xs.end(), x);
        return (ptr != xs.end()) ? *ptr : null;
    }
};

#endif
