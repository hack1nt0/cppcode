import collections
import contextlib
from concurrent.futures import Future
import collections.abc
import tempfile
import glob
import threading
import asyncio
import os, sys, io
import subprocess
from subprocess import Popen, PIPE
import shutil
import itertools
import argparse
import json
import textwrap
import math
from run_tests import compare_tokens, InfoExtractor, print_diff

def run(sol_cmd, gen_cmd, cmp_cmd):
    print(f'Solver: {sol_cmd}')
    print(f'Generator: {gen_cmd}')
    print(f'Comparator: {cmp_cmd}')
    maxcpu = 0
    maxmem = 0
    testid = 0
    try:
        while True:
            testid += 1
            print('.', flush=True, end=('\n' if testid % 10 == 0 else ''))
            with open('X_in', 'w+') as w:
                pgen = Popen(
                    gen_cmd,
                    shell=True,
                    stdout=w,
                    stderr=sys.stderr,
                )
                gcode = pgen.wait()
                if gcode: 
                    print(f'Runtime Error : generator finished with code {gcode} !')
                    return 1
            with (
                open('X_in') as reader,
                open('X_in') as reader2,
                open('X_in', 'a') as answerstream,
                tempfile.NamedTemporaryFile(mode="w+") as actualstream,
                tempfile.NamedTemporaryFile(mode="w+") as stderrstream,
            ):
                psol = Popen(
                    f'/usr/bin/time -al {sol_cmd}',
                    shell=True,
                    stdin=reader,
                    stdout=actualstream,
                    stderr=stderrstream,
                    text=True,
                )
                answerstream.write('\n\n')
                pcmp = Popen(
                    cmp_cmd,
                    shell=True,
                    stdin=reader2,
                    stdout=answerstream,
                    stderr=stderrstream,
                )
                scode = psol.wait()
                ccode = pcmp.wait()
                if scode:
                    print()
                    stderrstream.seek(0)
                    print(stderrstream.read())
                    print(f'Runtime Error : solver finished with code {scode}!')
                    return 1
                if ccode:
                    print()
                    print(stderrstream.read())
                    print(f'Runtime Error : comparator finished with code {ccode} !')
                    return 1
                actualstream.seek(0)
                wrongtokens, actuals, answers = compare_tokens(actualstream, reader)
                if wrongtokens > 0:
                    print()
                    print(f'Wrong Answer:')
                    print_diff(actuals, answers)
                    print(f'Failed test case saved in X_in .')
                    return 1
                stderrstream.seek(0)
                infoExtractor = InfoExtractor().run(stderrstream, prt=False)
                maxcpu = max(maxcpu, infoExtractor.cpu)
                maxmem = max(maxmem, infoExtractor.mem)
    except KeyboardInterrupt:
        print(f'\nAll {testid} tests passed with maximum {maxcpu} ms and {maxmem} mb')
        return 2

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('sol_cmd')
    p.add_argument('gen_cmd')
    p.add_argument('cmp_cmd', nargs='?')
    args = p.parse_args()
    run(args.sol_cmd, args.gen_cmd, args.cmp_cmd if args.cmp_cmd else args.sol_cmd)
        