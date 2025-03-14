import tempfile
import glob
import os, sys, io
import subprocess
from subprocess import Popen, PIPE
import time
from typing import List, Tuple
import itertools
import argparse
from typing import List, Tuple
import sys, glob

__TESTS__ = glob.glob('X_in*')

def print_diff(actuals: list[str], answers: list[str]):
    answerW = max(map(len, answers), default=0)
    for row, (actualTk, answerTk) in enumerate(itertools.zip_longest(actuals, answers), start=1):
        if not actualTk:
            actualTk = ''
        if not answerTk:
            answerTk = ''
        eq = True
        try:
            eq = abs(float(answerTk) - float(actualTk)) < 1e-6
        except ValueError:
            eq = actualTk == answerTk
        if not eq:
            actualTk = formatred(actualTk) 
        else:
            actualTk = formatgreen(actualTk) 
        print('\t', answerTk.rjust(answerW), '\t', actualTk,)
    
def compare_tokens(actualstream: io.TextIOBase, answersteam: io.TextIOBase):
    actuals = actualstream.read().strip().splitlines()
    answers = answersteam.read().strip().splitlines()
    wrongs = 0
    total = 0
    for row, (actualTk, answerTk) in enumerate(itertools.zip_longest(actuals, answers), start=1):
        if not actualTk:
            actualTk = ''
        if not answerTk:
            answerTk = ''
        eq = True
        try:
            eq = abs(float(answerTk) - float(actualTk)) < 1e-6
        except ValueError:
            eq = actualTk == answerTk
        wrongs += not eq
        total += 1
    return wrongs, actuals, answers

def formatgreen(s): return f"\033[32m{s}\033[0m"
def formatred(s): return f"\033[31m{s}\033[0m"
class InfoExtractor:
    def __init__(self):
        self.cpu = 0
        self.mem = 0
        # self.stdout = []
    
    # def fileno(self): return self.stream.fileno()
    
    # def write(self, cs):
    #     self.segs.append(cs)

    def run(self, stream, prt=True):
        geo = False
        lsegs = []
        polys = []
        dots = []
        for line in stream:
            if line.startswith('<svg'):
                pass
            elif line.startswith('graph {') or line.startswith('digraph {'):
                try:
                    import graphviz as G
                    g = G.Source(line, filename=f"{time.perf_counter_ns()}")
                    img = g.render(directory="gv", view=True).replace('\\', '/')
                    print(formatred(img), end='', flush=True)
                except:
                    print(line)
                    print("Need graphviz package to visiualize...")
            elif 'real' in line and 'user' in line and 'sys' in line:
                self.cpu = int(float(line.split()[0]) * 1000)
            elif 'maximum resident set size' in line:
                self.mem = round(int(line.split()[0]) / 1024 / 1024, 2)
                break
            else:
                if (prt): print(formatred(line), end='', flush=True)
        return self
        

def run(sol_cmd, test_id):
    print("Running Build-in testcases")
    total = 0
    wrongs = 0
    totcpu = 0
    maxmem = 0
    testId = 0
    for testfile in __TESTS__:
        if (not os.path.exists(testfile)): continue
        total += 1
        testId += 1
        print('-' * 3 + f'#{testId}' + '-' * 3)
        if (test_id and test_id != testId): 
            print('skipped...')
            continue
        with (
            open(testfile) as reader,
            tempfile.NamedTemporaryFile(mode="w+") as actualstream,
        ):
            proc = Popen(
                f'/usr/bin/time -al {sol_cmd}',
                shell=True,
                text=True,
                # bufsize=0,
                stdin=reader,
                stdout=actualstream,
                stderr=subprocess.PIPE,
            )
            infoExtractor = InfoExtractor().run(proc.stderr)
            scode = proc.wait()
            totcpu += infoExtractor.cpu
            maxmem = max(maxmem, infoExtractor.mem)
            print('-' * 3 + 'verdict' + '-' * 3)
            if (scode != 0):
                wrongs += 1
                print('Runtime Error')
                continue
            actualstream.seek(0)
            wrongtokens, actuals, answers = compare_tokens(actualstream, reader)
            if wrongtokens > 0:
                wrongs += 1
                print(f'Wrong Answer:')
                print_diff(actuals, answers)
            else:
                print(f'AC in {infoExtractor.cpu} ms and {infoExtractor.mem} mb')
            print(f'Input file is {testfile}, cmd + click to see detail (input + newline + answer).')
    print('=' * 3 + 'conclusion' + '=' * 3)
    if (wrongs == 0):
        print(f"All {total} tests passed")
    else:
        print(f"{(wrongs)}/{total} tests failed")


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('sol_cmd')
    p.add_argument('test_id', nargs='?', type=int)
    args = p.parse_args()
    run(args.sol_cmd, args.test_id)