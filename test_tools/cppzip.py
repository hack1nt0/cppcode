import json, shlex, sys, subprocess, argparse, os, tempfile, re, os
import datetime, collections

def main():
    p = argparse.ArgumentParser(prog="cppzip", description="Zip cpp files to single")
    p.add_argument("solver", help="File to zip")
    args = p.parse_args()
    cppfile : str = args.solver
    if (os.path.exists(cppfile) and os.path.isfile(cppfile) and cppfile.split('.')[1] == 'cpp'):
        go(cppfile)
    else:
        print(f"{cppfile} not supported yet ...", file=sys.stderr)

def go(cppfile: str):
    cppfile = os.path.abspath(cppfile)
    with (
        tempfile.NamedTemporaryFile(mode="w+") as stdinstream,
        tempfile.NamedTemporaryFile(mode="w+") as stdoutstream,
        tempfile.NamedTemporaryFile(mode="w+") as validstream,
    ):
        stdheaders = set()
        pat_header = re.compile(r'[ \t]*#include[ \t]*["<]([\w\\/\._]+)[>"]')
        vis = set()
        def concat(x: str):
            with open(x, "r") as f:
                for line in f.readlines():
                    m = pat_header.match(line)
                    iscustomheader = False
                    isstdheader = False
                    if m:
                        header = m.group(1)
                        y = os.path.normpath(os.path.join(os.path.dirname(x), header))
                        if os.path.exists(y) and os.path.isfile(y):
                            iscustomheader = True
                            if y not in vis:
                                vis.add(y)
                                concat(y)
                        else:
                            isstdheader = True
                            stdheaders.add(line)
                    if not iscustomheader and not isstdheader:
                        line = line.replace('\t', ' '*4)
                        stdinstream.write(line)
                        # Last line of file may not ends with newline
                        if not line.endswith("\n"):
                            stdinstream.write('\n')
        concat(cppfile)
        stdinstream.seek(0)
        print("Macro substitution + del comments...".title(), file=sys.stderr)
        ret = subprocess.run(
            "g++ -E -xc++ -".split(),
            stdin=stdinstream,
            stdout=stdoutstream,
            stderr=sys.stderr,
        )
        if ret.returncode:
            exit(ret.returncode)
        
        print('Validating...', file=sys.stderr)
        for header in stdheaders:
            validstream.write(header)
        stdoutstream.seek(0)
        for line in stdoutstream:
            if (not line.startswith('#')):
                validstream.write(line)
        validstream.seek(0)
        ret = subprocess.run(
            f"g++ -xc++ -std=c++2b -o {validstream.file.name}.exe - ",
            shell=True,
            stdin=validstream,
            stderr=sys.stderr,
        )
        if ret.returncode:
            exit(ret.returncode)
        
        print('Generating Final result...', file=sys.stderr)
        print('#include <bits/stdc++.h>')
        stdoutstream.seek(0)
        for line in stdoutstream:
            if (not line.startswith('#')):
                print(line, end='')
        

if __name__ == '__main__':
    main()