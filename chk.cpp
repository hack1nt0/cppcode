#include "include/libs"
int main() {
    ios_base::sync_with_stdio(false);
    cin.tie(&cout);
    Random R;
    int x = R.randint(0, 10);
    int y = R.randint(0, 10);
    cout << x << y << endl;
    int z; cin >> z;
    assert(z == x + y);
    return 0;
}
