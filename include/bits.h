#ifndef INCLUDED_BITS_H
#define INCLUDED_BITS_H

#include "debug.h"
#include <bit>




template <typename T>
int bitat(T x, int b) {
    return x >> b & 1;
}

template <typename T>
int bitcnt(T x) {
    return popcount(x);
}


#endif
