import collections
import contextlib
from concurrent.futures import Future
import aiofiles
import collections.abc
import tempfile
import glob
import threading
from .conf import conf
import asyncio
import os, sys, io
import subprocess
from subprocess import Popen, PIPE
import time, psutil
from .combine import combine
import traceback
from typing import List, Tuple
import shutil
import itertools
import argparse
import json
from .logger import Logger, logger
import textwrap
import math

solver = conf.solver
generator = conf.generator
comparator = conf.comparator
checker = conf.checker
ichecker = conf.ichecker
inputs = conf.inputs
answers = conf.answers
cpulimit = conf.cpulimit
memlimit = conf.memlimit
batch = conf.batch

def main():
    try:
        p = argparse.ArgumentParser(
            prog="stdtest",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            description=textwrap.dedent("""
            Test suite for standard io task
            """),
            epilog=textwrap.dedent("""
            Visualization of different test methods (flow left to right):
            1. Default mode:
                            split with blank line(s)
                inputfile ---------------------------> input(+answer)
                                      ^                  |
                                      |                  | solver
                                      |                  v
                                      |                actual
                                      |                  |
                                      |                  | +answer
                                      |                  v
                                      |         token-based-checker
            2. Compare mode:          |
                inputfile -- output --
            3. Interact mode:
                             query
                    solver --------> inputfile
                      ^                 |
                      |_________________|
                             respond
            See also: 
                [stdlist(en): listen part]
                [stdcomb(ine): copy part]
                [sdtnew: New task part]
                [stdconf(ig): configuration part]
            """),
            # usage="hello",
            add_help=True,
        )
        p.add_argument("solver", nargs="?", default="sol.cpp", help="default: sol.cpp")
        # p.add_argument("inputfile", nargs="?", default="tests",help="default: tests")
        group = p.add_argument_group("test method")
        tm = group.add_mutually_exclusive_group()
        tm.add_argument("-R", dest="run", help="Run mode", action="store_true")
        tm.add_argument("-C", dest="compare", help="Compare mode", action="store_true")
        tm.add_argument("-I", dest="interact",help="interact mode", action="store_true")
        tm.add_argument("-B", dest="bruteforce", help="Bruteforce mode", action="store_true")
        tm.add_argument("-b", dest="build_only", help="Build-only mode", action="store_true")
        args = p.parse_args()

        def check_codefile(filename):
            if os.path.exists(filename):
                return
            prefix, suffix = os.path.splitext(filename)
            try:
                lang = conf.language(filename)
                open(filename, "w").write(lang.template)
            except:
                pass
            print(f"File [{filename}] not exists, created as need. please edit it first...")
            exit(1)
        global solver
        solver = os.path.expanduser(args.solver)
        if not os.path.exists(solver):
            solver = conf.solver
        check_codefile(solver)
        global cpulimit, memlimit
        # solver = os.path.abspath(os.path.expanduser(solver))
        try:
            task = json.loads(open("task.json").read())
            cpulimit = task['timeLimit'] / 1000
            memlimit = task['memoryLimit']
        except:
            pass
        if args.build_only:
            return compile(solver)
        if args.run:
            return test_manual()
        if args.compare:
            check_codefile(generator)
            check_codefile(comparator)
            return test_compare()
        if args.interact:
            check_codefile(ichecker)
            return test_interact()
        if args.bruteforce:
            return test_compare(compare=False)
        if not os.path.exists(inputs) or not os.path.exists(answers):
            with (
                open(inputs, 'w') as i,
                open(answers, 'w') as a,
            ):
                try:
                    dat = json.loads(open("task.json").read())
                    for test in dat["tests"]:
                        i.write(test["input"])
                        i.write("\n")
                        a.write(test["output"])
                        a.write("\n")
                except:
                    pass
        return test_file()
    except KeyboardInterrupt:
        return 1


class Verdict:
    cpu: int = 0
    cpudel: int = 0
    mem: int = 0
    solved: bool = True
    pipe: int = 0

stopflag = threading.Event()

verdict: Verdict = Verdict()

def make_process(cmd: str | List[str], desc: str = ""):
    p = Popen(
        cmd,
        # bufsize=0,
        stdin=PIPE,
        stdout=PIPE,
        stderr=subprocess.STDOUT,
        shell=type(cmd) is str,
    )
    p.desc = desc
    return p

from typing import Callable

async def flow(
    source: io.IOBase,
    targets: List[io.IOBase],
    log: Callable,
    verdict: Verdict,
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
                c = await r.read(conf.bps)
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
        if stopflag.is_set():
            # print("Terminated", flush=T)
            pass
        else:
            stopflag.set()
            logger.error(str(e))
            # logger.error(f"Edge[{s.desc} > {t.desc if t else '*'}] ERROR")
            verdict.solved = False


async def poll(
    proc: Popen,
    verdict: Verdict,
    measure: bool,
):
    tic = time.thread_time()
    pp: psutil.Process = None
    try:
        while True:
            if stopflag.is_set():
                proc.terminate()
                return
            ret = proc.poll()
            if ret is not None:
                return
            if measure:
                try:
                    if pp is None:
                        pp = psutil.Process(proc.pid)
                    verdict.mem = round(pp.memory_info().rss / 1024 / 1024)
                except:
                    pass
                verdict.cpu = round((time.thread_time() - tic), 3)
            await asyncio.sleep(0)
    except BaseException as e:
        stopflag.set()
        logger.error(str(e))
        verdict.solved = False


def run_graph(*coros: collections.abc.Coroutine):
    
    async def main(*coros: collections.abc.Coroutine):
        await asyncio.gather(*coros)

    asyncio.run(main(*coros))


def compile(file: str) -> int:
    # os.makedirs(".tmp", exist_ok=True)
    pre_combined = f"{file}.bak"
    if not os.path.exists(pre_combined):
        open(pre_combined, "w").write("")
    cmd = conf.compile_cmd(file)
    if cmd is None:
        print(f"[{file}] has no build command found!")
        return 0
    exe = conf.executable(file)
    file_content = combine(file)
    need_recompile = file_content != open(pre_combined).read() or not os.path.exists(
        exe
    )
    print(" ".join(cmd))
    if not need_recompile:
        print(f"[{file}] is up-to-date, skipped recompile")
        return 0
    try:
        proc = subprocess.run(
            cmd,
            # stdout=sys.stdout,
            # stderr=sys.stderr,
            # capture_output=True,
            # text=True,
        )
        if not proc.returncode:
            open(pre_combined, "w").write(file_content)
        return proc.returncode
    except BaseException as e:
        print("".join(traceback.format_exception(e)))
        return 1


def test_manual():
    logger.clear()
    retcode = compile(solver)
    if retcode:
        return retcode
    logger.clear()
    cmd = conf.execute_cmd(solver)
    # logger.header(f"[{' '.join(cmd)}] Input")
    proc = Popen(
        cmd,
        # bufsize=0,
        stdin=sys.stdin,
        stdout=sys.stdout,
        stderr=sys.stderr,
        shell=type(cmd) is str,
    )
    return proc.wait()

def wait(p: Popen):
    code = p.wait()
    if code:
        print(f"Program exit with code {code}...")
        exit(code)

import textwrap
def print_text(s: io.TextIOBase):
    MAX_LINES = 20
    MAX_COLS = shutil.get_terminal_size().columns
    nrow = 1
    s.seek(0)
    for line in s:
        # print(textwrap.shorten(line, MAX_COLS))
        if len(line) > MAX_COLS:
            print(line[:MAX_COLS-3], '...', sep="")
        else:
            print(line, end="")
        if nrow > MAX_LINES:
            print("...more lines skipped")
            break
        nrow += 1
    s.seek(0)

def test_compare(compare=True):
    logger.clear()
    if compile(solver):
        return 1
    if compile(generator):
        return 1
    if compare and compile(comparator):
        return 1
    testId = 0

    with (
        tempfile.NamedTemporaryFile(mode="w+") as actualstream,
        # tempfile.NamedTemporaryFile(mode="w+") as inputstream,
        open("in", "w+") as inputstream,
        tempfile.NamedTemporaryFile(mode="w+") as answerstream,
    ):
        while True:
            testId += 1
            log = Logger(testId)
            log.clear()
            log.title()
            verdict = Verdict()
            log.header("Generator Output (input)")
            inputstream.seek(0)
            inputstream.truncate(0)
            pgenerator = Popen(
                conf.execute_cmd(generator),
                # bufsize=0,
                # stdin=PIPE,
                stdout=inputstream,
                # stderr=sys.stderr,
            )
            wait(pgenerator)
            print_text(inputstream)
            if compare:
                log.header("Comparator Output (answer)")
                inputstream.seek(0)
                answerstream.seek(0)
                answerstream.truncate(0)
                pcomparator = Popen(
                    conf.execute_cmd(comparator),
                    # bufsize=0,
                    stdin=inputstream,
                    stdout=answerstream,
                    # stderr=subprocess.STDOUT,
                )
                wait(pcomparator)
                print_text(answerstream)
            log.header("solver output (Actual)")
            inputstream.seek(0)
            actualstream.seek(0)
            actualstream.truncate(0)
            tic = time.perf_counter()
            psolver = Popen(
                conf.execute_cmd(solver),
                # bufsize=0,
                stdin=inputstream,
                stdout=actualstream,
                stderr=sys.stderr,
                # shell=False,
            )
            wait(psolver)
            verdict.cpu = round(time.perf_counter() - tic, 3)
            print_text(actualstream)
            actualstream.seek(0)
            answerstream.seek(0)
            passed = log.verdict(
                cpu=verdict.cpu,
                cpulimit=cpulimit,
                mem=verdict.mem,
                memlimit=memlimit,
                scode=psolver.returncode,
                actual=actualstream,
                answer=answerstream if compare else None,
            )
            if not passed or not verdict.solved or stopflag.is_set():
                log.conclusion(f"Found a failed testcase after {testId} tries, saving failed testcase...", )
                inputstream.seek(0)
                with open(inputs, 'a') as w:
                    for line in inputstream:
                        w.write(line)
                    w.write("\n")
                if compare:
                    answerstream.seek(0)
                    with open(answers, 'a') as w:
                        for line in answerstream:
                            w.write(line)
                    w.write("\n")
                return 1
            # print("-" * shutil.get_terminal_size().columns)
            print()
            if (not testId % batch):
                input(f"All test passed after {testId // batch} batchs({batch}), press any key to continue...")

def test_interact():
    logger.clear()
    if compile(solver):
        return 1
    if compile(ichecker):
        return 1
    testId = 0
    totcpu = 0
    maxmem = 0
    while True:
        testId += 1
        log = Logger(testId)
        log.clear()
        log.title()
        verdict = Verdict()
        print(f"Test #{testId} Chat:")
        log.header("Interact Chat")
        pChecker = make_process(
            conf.execute_cmd(inputfile),
            desc="checker",
        )
        pSolver = make_process(
            conf.execute_cmd(solver),
            desc="solver",
        )
        stopflag.clear()
        run_graph(
            poll(pSolver, verdict, measure=True),
            poll(pChecker, verdict, measure=False),
            flow(pChecker.stdout, [pSolver.stdin], log.answer, verdict),
            flow(pSolver.stdout, [pChecker.stdin], log.query, verdict),
        )
        passed = log.verdict(scode=pSolver.returncode, ccode=pChecker.returncode)
        if not passed or not verdict.solved or stopflag.is_set():
            log.conclusion(f"Found a failed testcase after {testId} tries, input should output by checker")
            break
        totcpu += verdict.cpu
        maxmem = max(maxmem, verdict.mem)
        print("")


from typing import List, Tuple
import sys
import matplotlib.pyplot as plt
import matplotlib

class IMGExtractor:
    def __init__(self):
        self.stream = tempfile.NamedTemporaryFile(mode="w+")
    
    def fileno(self): return self.stream.fileno()
    
    # def write(self, cs):
    #     self.segs.append(cs)

    def close(self):
        self.stream.seek(0)
        geo = False
        lsegs = []
        polys = []
        dots = []
        for line in self.stream:
            if line.startswith('<line'):
                geo = True
                x1, y1, x2, y2 = map(float, line.split()[1:-1])
                lsegs.append([(x1, y1), (x2, y2)])
            elif line.startswith('<polygon'):
                geo = True
                points = []
                for xy in line.split()[1:-1]:
                    x, y = map(float, xy.split(","))
                    points.append((x, y))
                polys.append(points)
            elif line.startswith('<circle'):
                geo = True
                cx, cy, r = map(float, line.split()[1:-1])
            elif line.startswith('<rect'):
                geo = True
                pass
            elif line.startswith('graph {') or line.startswith('digraph {'):
                dots.append(line)
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
        self.stream.close()

    def openimage(self, imgfile):
        subprocess.run(
            f"open {imgfile}",
            shell=True,
            stderr=sys.stderr,
            check=True,
        )
        

def test_file():
    logger.clear()
    if compile(solver):
        return 1
    totcpu = 0
    passed = 0
    maxmem = 0
    testId = 0

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
    with (
        tempfile.NamedTemporaryFile(mode="w+") as actualstream,
        tempfile.NamedTemporaryFile(mode="w+") as inputstream,
        tempfile.NamedTemporaryFile(mode="w+") as answerstream,
    ):
        inputsitr = blank_lines_seperated(inputs)
        answersitr = blank_lines_seperated(answers)
        for input in inputsitr:
            try:
                answer = next(answersitr)
            except:
                withanswer = False
            else:
                withanswer = True
            testId += 1
            log = Logger(testId)
            log.title()
            verdict = Verdict()
            log.header("input")
            log.output(input)
            log.header("output")
            imgExtractor = IMGExtractor()
            proc = Popen(
                conf.execute_cmd(solver),
                # bufsize=0,
                stdin=PIPE,
                stdout=PIPE,
                # stderr=subprocess.DEVNULL,
                stderr=imgExtractor,
                shell=False,
            )
            proc2 = Popen(
                conf.execute_cmd(solver),
                # bufsize=0,
                stdin=PIPE,
                stdout=PIPE,
                stderr=subprocess.STDOUT,
                shell=False,
            )
            inputstream.seek(0)
            inputstream.truncate(0)
            inputstream.write(input)
            inputstream.flush()
            inputstream.seek(0)
            actualstream.seek(0)
            actualstream.truncate(0)
            if withanswer:
                # log.answer(answer)
                answerstream.seek(0)
                answerstream.truncate(0)
                answerstream.write(answer)
                answerstream.flush()
            run_graph(
                poll(proc, verdict, True),
                flow(inputstream, [proc.stdin, proc2.stdin], None, verdict),
                flow(proc.stdout, [actualstream], None, verdict),
                flow(proc2.stdout, [], log.output, verdict),
            )
            imgExtractor.close()
            totcpu += verdict.cpu
            maxmem = max(maxmem, verdict.mem)
            actualstream.seek(0)
            answerstream.seek(0)
            passed += log.verdict(
                cpu=verdict.cpu,
                cpulimit=cpulimit,
                mem=verdict.mem,
                memlimit=memlimit,
                scode=proc.returncode,
                answer=answerstream,
                actual=actualstream,
            )
            if not verdict.solved or stopflag.is_set():
                return
            # print("-" * shutil.get_terminal_size().columns)
    logger.conclusion(get_conclusion(testId, passed, totcpu, maxmem))


def compare_tokens(answer: io.TextIOBase, actual: io.TextIOBase) -> bool:
    def tokens(stream):
        for line in stream:
            for tk in line.split():
                if tk:
                    yield tk

    for atoken, btoken in itertools.zip_longest(tokens(answer), tokens(actual)):
        # print(f"{atoken} ~ {btoken}")
        ret = False
        if atoken and btoken:
            try:
                ret = abs(float(atoken) - float(btoken)) < 1e-6
            except ValueError:
                ret = atoken == btoken
        if not ret:
            # print(f"{atoken} != {btoken}", file=sys.stderr)
            return False
    return True


def get_verdict(
    psolver: Popen,
    cpulimit: int,
    memlimit: int,
    verdict: Verdict,
    pchecker: Popen = None,
    answer: io.TextIOBase = None,
    actual: io.TextIOBase = None,
    withanswer: bool = True,
):
    if not verdict.solved:
        ret = ("Inner error")
    elif stopflag.is_set():
        ret = ("Terminated")
        return
    elif psolver.returncode:
        ret = (f"Runtime error")
        verdict.solved = 0
    elif pchecker and pchecker.returncode:
        ret = (f"Runtime error (checker)")
        verdict.solved = 0
    elif withanswer and not compare_tokens(answer, actual):
        verdict.solved = 0
        ret = ("Wrong Answer")
    elif verdict.mem > memlimit:
        verdict.solved = 0
        ret = (f"Memory limit exceeded")
    elif verdict.cpu > cpulimit:
        verdict.solved = 0
        ret = (f"Time limit exceeded")
    else:
        ret = "Answer is unknown" if not answer else "OK"
    ret += f" in {verdict.cpu}s and {verdict.mem}mb"
    return ret


def get_conclusion(total: int, passed: int, totcpu: int, maxmem: int) -> str:
    ret = ""
    if (total == passed):
        ret = f"All tests passed "
    else:
        ret = f"{(total - passed)}/{total} tests failed "
    # print("=" * shutil.get_terminal_size().columns)
    return ret
