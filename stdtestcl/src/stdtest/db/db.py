import sqlite3
import os, time, shutil, json

SQL = os.path.join(os.path.dirname(__file__), "db.sql")
DB = "task.db"

class Database:
    def __init__(self):
        # os.remove(DB)
        self.con = sqlite3.connect(DB)
        self.ptr = self.con.cursor()
        self.ptr.executescript(open(SQL).read())
        self.ptr.executemany(
            "insert or replace into task2(id,fullname,dat,ctime,mtime,`status`) values (?,?,?,?,?,?)",
            [
                (
                    0,
                    "('TEST', '')",
                    json.dumps({
                        "id": 0,
                        "name": "test",
                        "group": "",
                        "url": "",
                        "interactive": False,
                        "memoryLimit": 256,
                        "timeLimit": 500,
                        "files": {
                            "in-1": "1 2",
                            "sol.cpp": r"""#include "include/libs"
int main() {
    int x, y; cin >> x >> y;
    cout << (x + y) << endl;
    return 0;
}
""",
                            "gen.py": r"""import random as R
x = R.randint(0, 10)
y = R.randint(0, 10)
print(x, y)
""",
                            "cmp.cpp": r"""#include "include/libs"

int main() {
    int x, y; cin >> x >> y;
    cout << (x + y) << endl;
    return 0;
}
""",
                            "chk.cpp": r"""#include "include/libs"
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
"""
                    }}).encode(),
                    int(time.time()),
                    int(time.time()),
                    0,
                ),
            ]
        )
        self.con.commit()
    
    
    def select(self, sql, params=()):
        if type(params) is tuple:
            self.ptr.execute(sql, params)
        else:
            print(type(params))
            assert type(params) is list
            self.ptr.executemany(sql, params)
        return self.ptr.fetchall()
    
    def execute(self, sql, params=()):
        self.ptr.execute(sql, params)
        self.con.commit()