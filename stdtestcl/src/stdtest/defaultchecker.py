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
from .taskcrud import getlocaltaskmeta, savelocaltaskmeta, db


def getlocaltestfiles():
    for infile in glob.glob('in*'):
        if os.path.isdir(infile): continue
        outfile = f"ou{infile[2:]}"
        if os.path.exists(outfile):
            yield infile, outfile
        else:
            yield infile, None

def defaultchecker():
    def blank_lines_seperated(file: str):
        with open(file) as r:
            cached = []
            for line in r:
                line = line.strip()
                if not line:
                    if cached:
                        yield "\n".join(cached) + "\n"
                        cached.clear()
                else:
                    cached.append(line)
            if cached:
                yield "\n".join(cached) + "\n"
                cached.clear()
    for fd in glob.glob('in*'):
        if os.path.isdir(fd): continue
        for input, answer in blank_lines_seperated(fd):
            logger.header("input")
            logger.info(input)
            print(input)
            actual = []
            for line in sys.stdin:
                actual.append(line)
            actual = ''.join(actual)
            if comptokens(actual, answer):
                exit(0)
            else:
                printdiff(actual, answer)
                exit(1)

    # logger.clear()
    dat = getlocaltaskmeta()
    sol = dat['sol']
    chk = dat['chk']
    cpulimit = dat['timeLimit']
    memlimit = dat['memoryLimit']
    solruncmd = f"/usr/bin/time -al {compilefile(sol)}"
    chkruncmd = compilefile(chk)
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
        infoExtractor = MetricExtractor()
        psol = Popen(
            solruncmd,
            shell=True,
            stdin=PIPE,
            stdout=PIPE,
            stderr=infoExtractor,
        )
        pchk = Popen(
            chkruncmd,
            shell=True,
            stdin=PIPE,
            stdout=PIPE,
            stderr=sys.stderr,
        )
        def sol2chk(cs):
            print("SOL --> CHK:", cs)
        def chk2sol(cs):
            print("SOL <-- CHK:", cs)
        run_graph(
            flow(psol.stdout, [pchk.stdin], sol2chk),
            flow(pchk.stdout, [psol.stdin], chk2sol),
        )
        infoExtractor.close()
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

class InfoExtractor:
    def __init__(self):
        self.cpu = 0
        self.mem = 0
        self.stdout = []
    
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
                self.cpu = float(line.split()[0])
            elif 'maximum resident set size' in line:
                self.mem = round(int(line.split()[0]) / 1024 / 1024, 2)
                break
            elif line.startswith('['):
                from .logger import formatred
                print(formatred(line), end='')
            else:
                self.stdout.append(line)
                print(line, end='')
        self.stdout = ''.join(self.stdout)
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


