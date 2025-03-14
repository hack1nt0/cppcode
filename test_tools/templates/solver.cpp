
#include "include/debug.h"

#define ALL(x) x.begin(), x.end()
#define UMAX(x, y) (x = max(x, y))
#define UMIN(x, y) (x = min(x, y))

void solve(int it) {}

int main() {
    ios_base::sync_with_stdio(false);
    cin.tie(nullptr);
    cout.tie(nullptr);
    int T; cin >> T;
    for (int i = 1; i <= T; ++i) solve(i);
    return 0;
}

/*
1. order matters!
2. certains on fixed uncertains
3. decompose into subtasks
4. tansfer to another task

*/
