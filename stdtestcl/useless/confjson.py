import dataclasses
from typing import List, Tuple, Dict, Any
import datetime
import os, sys, json
import argparse
import json
from .logger import Logger, logger
from subprocess import Popen

CONFFILE = os.path.expanduser("~/stdtest.json")

def main():
    try:
        p = argparse.ArgumentParser(
            prog="StdConfig",
        )
        args = p.parse_args()
        cmd = f"vi {CONFFILE}"
        logger.info(cmd)
        proc = Popen(
            cmd,
            # bufsize=0,
            stdin=sys.stdin,
            stdout=sys.stdout,
            stderr=sys.stderr,
            shell=type(cmd) is str,
        )
        proc.wait()
        # validate
        
    except KeyboardInterrupt:
        return 1

_WIN = sys.platform == "win32"

@dataclasses.dataclass
class Language:
    name: str = ""
    filename: str = ""
    template: str = None
    interpreted: bool = False
    debug: str = ""
    release: str = ""
    run: str = ""

class Configuration:
    def __init__(self) -> None:
        self.langsuffix = ".cpp"
        self.languages = {
            ".cpp": {
                "name": "C++",
                "filename": "solver.cpp",
                "interpreted": False,
                "debug": "c++ -I/Users/dy/cc/include -std=c++17 -g -Wall -DDEBUG -fsanitize=address -fsanitize=undefined -o {output} {input}",
                "release": "c++ -I/Users/dy/cc/include -std=c++17 -O2 -o {output} {input}",
                "template": 
                    r"""#include "debug.h"

void solve(int it) {
}

int main() {
    ios_base::sync_with_stdio(false);
    cin.tie(&cout);
    int nt; cin >> nt;
    for (int it = 0; it < n; ++it) solve(it);
    return 0;
}
""",
            },
            ".py": {
                "name": "Python",
                "filename": "solver.py",
                "interpreted": True,
                "run": "python3 -Xfrozen_modules=off {}",
                "template": 
                    r"""import random
n = int(1e6)
print(n)
for _ in range(n):
    x = random.randint(0, 10)
    y = random.randint(0, 10)
    print(x, y)
""",
            },
        }

        self.bytes_per_read = 1024
        self.rows_per_page = 100
        self.log_level = "DEBUG"
        self.exe_dump_delay = 1
        self.exe_warm_delay = 2
        self.parallel = 1
        self.build_debug = True

    def language(self, file: str) -> Language:
        prefix, suffix = os.path.splitext(file)
        return Language(**self.languages[suffix]) if suffix in self.languages else None

    def compile_cmd(self, file: str) -> str:
        # TODO -it : ERR the input device is not a TTY
        # ret = f"docker exec dev bash compile{self.suffix}.sh /code/tasks/{self.taskname} {self.path} {self.executable} {1 if conf.build_debug else 0}"
        lang = self.language(file)
        if not lang:
            return None
        ret = None
        prefix, suffix = os.path.splitext(file)
        ret = lang.debug if conf.build_debug else lang.release
        ret = ret.format(input=file, output=f"{prefix}.exe")
        if _WIN:
            ret = f"wsl {ret}"
        return self.format_cmd(ret)
    
    def executable(self, file) -> str:
        prefix, suffix = os.path.splitext(file)
        return f"{suffix}.exe"

    def execute_cmd(self, file) -> str:
        lang = self.language(file)
        if not lang:
            return None
        ret = None
        prefix, suffix = os.path.splitext(file)
        if suffix not in conf.languages:
            return
        ret = lang.run.format(file) if lang.interpreted else f"./{prefix}.exe"
        if _WIN:
            ret = f"wsl {ret}"
        return self.format_cmd(ret)

    def format_cmd(self, cmd: str):
        if not cmd:
            return
        import shlex

        return shlex.split(cmd)  # TODO

    def save(self):
        open(CONFFILE, "w").write(json.dumps(self, indent=4, cls=JsonEncoder))

class JsonEncoder(json.JSONEncoder):
    def default(self, o: Any) -> Any:
        return o.__dict__

conf = Configuration()
if os.path.exists(CONFFILE):
    jsondat = json.loads(open(CONFFILE).read())
    for k, v in jsondat.items():
        if hasattr(conf, k):
            setattr(conf, k, v)
else:
    conf.save()
