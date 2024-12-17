from subprocess import run, Popen, PIPE
import shlex
import sys
import os
from .conf import conf
import argparse
from .logger import logger

def main():
    try:
        p = argparse.ArgumentParser(prog="StdComb", description="StdTest's copy part")
        args = p.parse_args()
        print(combine(conf.solver))
    except KeyboardInterrupt:
        sys.exit(0)
    except BaseException as e:
        print(str(e), file=sys.stderr)
        sys.exit(1)

def combine_cpp(
    file: str,
):
    def extract_includes(cmd: str):
        cmd = shlex.split(cmd)
        I = []
        for i in range(len(cmd)):
            c = cmd[i]
            if c.startswith("-I"):
                if c == "-I":
                    I.append(c[i + 1])
                else:
                    I.append(c[2:])
        return I
    
    lang = conf.language(file)
    
    includes = extract_includes(lang.build)

    def preprocess_cmd() -> str:
        ret = ["c++"]
        for idir in includes:
            ret.append(f"-I{idir}")
        ret += "-E -x c++ -".split()
        if sys.platform == "win32":
            ret.insert(0, "wsl")
        return ret
    lines = []
    std_headers = {'bits/stdc++.h'}
    import re

    pat_header = re.compile(r'[ \t]*#include[ \t]*["<]([\w\\/\._]+)[>"]')

    def concat(fn: str):
        with open(fn, "r") as f:
            for line in f.readlines():
                m = pat_header.match(line)
                if m:
                    header = m.group(1)
                    for include_dir in includes:
                        nfn = os.path.join(include_dir, header)
                        if os.path.exists(nfn) and os.path.isfile(nfn):
                            concat(nfn)
                            break
                else:
                    line = line.replace('\t', ' '*4)
                    lines.append(line)
                    # Last line of file may not ends with newline
                    if not line.endswith("\n"):
                        lines.append("\n")

    concat(file)

    # macro substitution (aka. after preprocessing)
    p = Popen(preprocess_cmd(), stdin=PIPE, stdout=PIPE, stderr=PIPE, text=True)
    p.stdin.writelines(lines)
    p.stdin.close()
    if p.wait():
        logger.error(p.stderr.read())
        return
    raw = p.stdout.readlines()

    lines = []
    lines += map(lambda h: f"#include <{h}>\n", std_headers)
    i = 0
    n = len(raw)
    while i < n:
        if raw[i].strip() == "":
            while i < n:
                if raw[i].lstrip() == "":
                    i += 1
                    continue
                if raw[i].lstrip().startswith("//"):
                    i += 1
                    continue
                if raw[i].lstrip().startswith("#"):
                    i += 1
                    continue
                if raw[i].lstrip().startswith("/*"):
                    while i < n and raw[i].strip() != "*/":
                        i += 1
                    i += 1
                    continue
                break
            lines.append("\n")
            continue
        if raw[i].lstrip().startswith("//"):
            i += 1
            continue
        if raw[i].lstrip().startswith("#"):
            i += 1
            continue
        if raw[i].lstrip().startswith("/*"):
            while i < n and raw[i].strip() != "*/":
                i += 1
            i += 1
            continue
        lines.append(raw[i])
        i += 1
    return "".join(lines)

def combine(file: str) -> str:
    prefix, suffix = os.path.splitext(file)
    match suffix:
        case '.cpp':
            return combine_cpp(file)
        case _:
            return open(file).read()