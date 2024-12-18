import collections
import contextlib
from concurrent.futures import Future
import aiofiles
import collections.abc
import tempfile
import glob
import threading
import asyncio
import os, sys, io
import subprocess
from subprocess import Popen, PIPE
import matplotlib.collections
import time, psutil
import traceback
from typing import List, Tuple
import shutil
import itertools
import argparse
import json
from .logger import *
import textwrap
import math
from .taskcrud2 import getlocaltaskmeta, db, getfiles

SOL_CMD = "make runsol"
GEN_CMD = "make rungen"
CMP_CMD = "make runcmp"
CHK_CMD = "make runchk"

def comptokens(actuals: list[str], answers: list[str]):
    import itertools
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
        return wrongs == 0

def testmanually():
    # logger.clear()
    proc = Popen(
        SOL_CMD,
        shell=True,
        # bufsize=0,
        stdin=sys.stdin,
        stdout=sys.stdout,
        stderr=sys.stderr,
    )
    return proc.wait()

def runmanually(cmd: str):
    # logger.clear()
    proc = Popen(
        cmd,
        shell=True,
        # bufsize=0,
        stdin=sys.stdin,
        stdout=sys.stdout,
        stderr=sys.stderr,
    )
    return proc.wait()

def wait(p: Popen):
    code = p.wait()
    if code:
        print(f"Program exit with code {code}...")
        exit(code)


def test_compare(compare=True):
    # logger.clear()
    # if compare:
    #     logger.info("compare mode...".upper())
    # else:
    #     logger.info("brutefoce-test mode...".upper())
    dat = getlocaltaskmeta()
    # sol = dat['sol']
    # assert sol and os.path.exists(sol), "Solver not exists!"
    # gen = dat['gen']
    # assert gen and os.path.exists(gen), "Generator not exists!"
    # if compare: 
    #     cmp = dat['cmp']
    #     assert cmp and os.path.exists(cmp), "Comparator not exists!"
    cpulimit = dat['timeLimit']
    memlimit = dat['memoryLimit']
    # solruncmd = f"/usr/bin/time -al {compilefile(sol)}"
    # genruncmd = compilefile(gen)
    # if compare: cmpruncmd = compilefile(cmp)
    
    TESTID = len(glob.glob('in-*'))+1
    FAILED = f"in-{TESTID}"
    GENOUT = "out-gen"
    SOLOUT = "out-sol"
    CMPOUT = "out-cmp"
    for testId in range(1, 101):
        logger.settestid(testId)
        passed = True
        with open(GENOUT, 'w+') as w:
            pgen = Popen(
                GEN_CMD,
                shell=True,
                stdout=w,
                stderr=sys.stderr,
            )
            if pgen.wait(): return 1
        logger.header("input")
        logger.abbrfile(GENOUT)
        logger.header("log/stderr")
        with (
            open(GENOUT) as r,
            open(SOLOUT, 'w') as w,
        ):
            psol = Popen(
                SOL_CMD,
                shell=True,
                stdin=r,
                stdout=w,
                stderr=subprocess.PIPE,
                text=True,
            )
        if compare:
            with (
                open(GENOUT) as r,
                open(CMPOUT, 'w') as w,
            ):
                pcmp = Popen(
                    CMP_CMD,
                    shell=True,
                    stdin=r,
                    stdout=w,
                    stderr=sys.stderr,
                )
        infoExtractor = InfoExtractor().run(psol.stderr)
        scode = psol.wait()
        if compare:
            ccode = pcmp.wait()
            passed = logger.verdict(
                actual=SOLOUT,
                answer=CMPOUT,
                scode=scode,
                ccode=ccode,
                cpu=infoExtractor.cpu,
                mem=infoExtractor.mem,
                cpulimit=cpulimit,
                memlimit=memlimit,
            )
            if not passed:
                # os.remove(FAILED)
                # newtest(FAILED)
                with open(FAILED, 'w+') as w:
                    w.write(open(GENOUT).read())
                    w.write(open(CMPOUT).read())
                logger.conclusion(f"Failed test #{testId} have been saved as `{FAILED}`.")
                return 1
        else:
            passed = logger.verdict(
                actual=SOLOUT,
                answer=None,
                scode=scode,
                cpu=infoExtractor.cpu,
                mem=infoExtractor.mem,
                cpulimit=cpulimit,
                memlimit=memlimit,
            )
            if not passed:
                # newtest(GENOUT)
                with open(FAILED, 'w+') as w:
                    w.write(open(GENOUT).read())
                logger.conclusion(f"Failed test #{testId} have been saved as `{FAILED}`.")
                c = input("Continue? [Y|n]: ")
                if c != 'n':
                    continue
                else:
                    return 1
    print()
    logger.conclusion("All 100 tests passed.")
    return 0


def test_interact():
    # logger.clear()
    dat = getlocaltaskmeta()
    cpulimit = dat['timeLimit']
    memlimit = dat['memoryLimit']
    BPS = 1024
    from typing import Callable
    async def flow(
        source: io.IOBase,
        targets: List[io.IOBase],
        log: Callable,
    ):
        t = None
        try:
            async with contextlib.AsyncExitStack() as stack:
                r = await stack.enter_async_context(
                    aiofiles.open(source.fileno(), "rb", buffering=0, closefd=False)
                )
                ws = [
                    await stack.enter_async_context(
                        aiofiles.open(target.fileno(), "ab", buffering=0, closefd=False) # buffering=0)
                    )
                    for target in targets
                ]
                while True:
                    c = await r.read(BPS)
                    # c = await r.read(3)
                    if not c:
                        break
                    if log:
                        log(c.decode())
                    # print(c)
                    for w in ws:
                        await w.write(c)
                        await w.flush()
            # # deal with less input
            # if s.desc == "input":
            #     for t in ts:
            #         t.close()
        except BaseException as e:
            raise e
    def run_graph(*coros: collections.abc.Coroutine):
        
        async def main(*coros: collections.abc.Coroutine):
            await asyncio.gather(*coros)

        asyncio.run(main(*coros))
    testId = 0
    while True:
        testId += 1
        logger.settestid(testId)
        logger.header("Chat")
        psol = Popen(
            SOL_CMD,
            shell=True,
            stdin=PIPE,
            stdout=PIPE,
            stderr=PIPE,
            text=True,
        )
        pchk = Popen(
            CHK_CMD,
            shell=True,
            stdin=PIPE,
            stdout=PIPE,
            stderr=sys.stderr,
        )
        def sol2chk(cs):
            print("SOL --> CHK:", cs, end='')
        def chk2sol(cs):
            print("SOL <-- CHK:", cs, end='')
        run_graph(
            flow(psol.stdout, [pchk.stdin], sol2chk),
            flow(pchk.stdout, [psol.stdin], chk2sol),
        )
        infoExtractor = InfoExtractor().run(psol.stderr)
        passed = logger.verdict(
            interactive=True,
            scode=psol.wait(),
            ccode=pchk.wait(),
            cpu=infoExtractor.cpu,
            mem=infoExtractor.mem,
            cpulimit=cpulimit,
            memlimit=memlimit,
        )
        if not passed: return 1


from typing import List, Tuple
import sys
import matplotlib.pyplot as plt
import matplotlib

class MetricExtractor:
    def __init__(self):
        self.cpu = 0
        self.mem = 0
        self.stream = tempfile.NamedTemporaryFile(mode="w+")
    
    def fileno(self): return self.stream.fileno()
    
    def close(self):
        self.stream.seek(0)
        for line in self.stream:
            if 'real' in line and 'user' in line and 'sys' in line:
                self.cpu = float(line.split()[0])
            elif 'maximum resident set size' in line:
                self.mem = round(int(line.split()[0]) / 1024 / 1024, 2)
                break

class InfoExtractor:
    def __init__(self):
        self.cpu = 0
        self.mem = 0
        # self.stdout = []
    
    # def fileno(self): return self.stream.fileno()
    
    # def write(self, cs):
    #     self.segs.append(cs)

    def run(self, stream):
        geo = False
        lsegs = []
        polys = []
        dots = []
        for line in stream:
            if line.startswith('<svg'):
                
                pass
            if line.startswith('<line'):
                geo = True
                x1, y1, x2, y2 = map(float, line.split()[1:-1])
                lsegs.append([(x1, y1), (x2, y2)])
            elif line.startswith('<polygon'):
                # print(line)
                geo = True
                points = []
                for xy in line.split()[1:-1]:
                    x, y = map(float, xy.split(","))
                    points.append((x, y))
                polys.append(points)

                colors = plt.rcParams['axes.prop_cycle'].by_key()['color']
                fig, ax = plt.subplots()
                col = matplotlib.collections.PolyCollection([points], )
                ax.add_collection(col, autolim=True)
                col.set_color('k')
                ax.autoscale_view()  # See comment above, after ax1.add_collection.
                plt.show()

            elif line.startswith('<circle'):
                geo = True
                cx, cy, r = map(float, line.split()[1:-1])
                matplotlib.collections.path
            elif line.startswith('<rect'):
                geo = True
                pass
            elif line.startswith('graph {') or line.startswith('digraph {'):
                dots.append(line)
            elif 'real' in line and 'user' in line and 'sys' in line:
                self.cpu = int(float(line.split()[0]) * 1000)
            elif 'maximum resident set size' in line:
                self.mem = round(int(line.split()[0]) / 1024 / 1024, 2)
                break
            else:
                print(formatred(line), end='', flush=True)
            # elif line.startswith('['):
            #     from .logger import formatred
            #     print(formatred(line), end='')
            # else:
                # self.stdout.append(line)
                # print(line, end='')
            
        # self.stdout = ''.join(self.stdout)
        if geo:
            colors = plt.rcParams['axes.prop_cycle'].by_key()['color']
            fig, ax = plt.subplots()
            
        if lsegs:
            col = matplotlib.collections.LineCollection(lsegs,)
            ax.add_collection(col, autolim=True)
            col.set_color('b')
        if polys:
            col = matplotlib.collections.PolyCollection(polys, )
            ax.add_collection(col, autolim=True)
            col.set_color('k')
        if geo:
            ax.autoscale_view()  # See comment above, after ax1.add_collection.
            # imagefile = f"{int(time.time())}.pdf"
            # fig.savefig(imagefile)
            # plt.close(fig)
            # self.openimage(imagefile)
            plt.show()
        if dots:
            for idx, dot in enumerate(dots):
                dotfile = f"{int(time.time())}-{idx}.dot"
                open(dotfile, 'w+').write(dot)
                imgfile = f"{os.path.splitext(dotfile)[0]}.png"
                dotcmd = f"dot -Tpng -Kdot -o {imgfile} {dotfile}"
                ret = subprocess.run(
                    dotcmd,
                    shell=True,
                    stderr=sys.stderr,
                )
                if not ret.returncode: self.openimage(imgfile)
        return self

    def openimage(self, imgfile):
        subprocess.run(
            f"open {imgfile}",
            shell=True,
            stderr=sys.stderr,
            check=True,
        )
        

def runtests():
    # logger.clear()
    logger.info("Running Build-in testcases")
    
    # sol = dat['sol']
    # runcmd = compilefile(sol)
    # runcmd = f"/usr/bin/time -al {runcmd}"

    dat = getlocaltaskmeta()
    testfiles = [x for x in getfiles(dat) if x.startswith('in-')]
    cpulimit = dat['timeLimit']
    memlimit = dat['memoryLimit']
    totcpu = 0
    passed = 0
    maxmem = 0
    testId = 0

    ACTUAL = "actual"
    for testfile in testfiles:
        testId += 1
        logger.settestid(testId)
        logger.header('testcase (input + answer)')
        logger.info(open(testfile).read())
        logger.header('log/stderr')
        inputstream = open(testfile)
        with (
            open(ACTUAL, 'w+') as w,
        ):
            proc = Popen(
                SOL_CMD,
                shell=True,
                text=True,
                # bufsize=0,
                stdin=inputstream,
                stdout=w,
                stderr=subprocess.PIPE,
            )
        infoExtractor = InfoExtractor().run(proc.stderr)
        scode = proc.wait()
        totcpu += infoExtractor.cpu
        maxmem = max(maxmem, infoExtractor.mem)
        passed += logger.verdict(
            cpu=infoExtractor.cpu,
            cpulimit=cpulimit,
            mem=infoExtractor.mem,
            memlimit=memlimit,
            scode=scode,
            answer=inputstream,
            actual=ACTUAL,
        )
        os.remove(ACTUAL)
        # print("-" * shutil.get_terminal_size().columns)
    def get_conclusion(total: int, passed: int, totcpu: int, maxmem: int) -> str:
        ret = ""
        if (total == passed):
            ret = f"All {total} tests passed "
        else:
            ret = f"{(total - passed)}/{total} tests failed "
        return ret
    logger.conclusion(get_conclusion(testId, passed, totcpu, maxmem))


