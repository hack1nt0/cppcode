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


def main():
    try:
        p = argparse.ArgumentParser(
            prog="StdTest",
            description="Test suite for standard io task",
            epilog="""Related: 
                [StdList(en): listen part]
                [StdComb(ine): copy part]
                [StdRun: Run part]
            """,
        )
        p.add_argument("solver")
        p.add_argument("-F", dest="testsfile", )
        p.add_argument("-G", dest="generator", )
        p.add_argument("-C", dest="comparator", )
        p.add_argument("-I", dest="checker", help="interactive?")
        p.add_argument(
            "-cpu", dest="cpulimit", type=int, default="1", help="<= (cpu) seconds"
        )
        p.add_argument(
            "-mem", dest="memlimit", type=int, default="256", help="<= (mem) megabytes"
        )
        args = p.parse_args()

        task = None
        cpu = args.cpulimit
        mem = args.memlimit
        try:
            task = json.loads(open("task.json").read())
            cpu = task['timeLimit'] / 1000
            mem = task['memoryLimit']
        except:
            pass
        if args.checker:
            return test_interact(args.solver, args.checker, cpu, mem)
        elif args.generator:
            return test_bruteforce(args.solver, args.generator, cpu, mem)
            pass
        elif args.comparator:
            return test_compare(args.solver, args.comparator, cpu, mem)
        elif args.testsfile:
            return test_file(args.solver, args.testsfile, cpu, mem)
        else:
            return test_manual(args.solver)
            
    except KeyboardInterrupt:
        return 1

class Verdict:
    cpu: int = 0
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
        stderr=PIPE,
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
    tic = time.perf_counter()
    pp: psutil.Process = None
    try:
        while True:
            if stopflag.is_set():
                proc.terminate()
                return
            if measure:
                verdict.cpu = round((time.perf_counter() - tic), 3)
                try:
                    if pp is None:
                        pp = psutil.Process(proc.pid)
                    verdict.mem = round(pp.memory_info().rss / 1024 / 1024)
                except:
                    pass
            ret = proc.poll()
            if ret is not None:
                return
            await asyncio.sleep(0)
    except BaseException as e:
        stopflag.set()
        logger.error(str(e))
        verdict.solved = False


def run_graph(*coros: collections.abc.Coroutine):
    async def main(*coros: collections.abc.Coroutine):
        await asyncio.gather(*coros)

    asyncio.run(main(*coros))


def compile(file: str, log: Callable) -> int:
    os.makedirs(".tmp", exist_ok=True)
    pre_combined = os.path.join(".tmp", file)
    if not os.path.exists(pre_combined):
        open(pre_combined, "w").write("")
    if conf.language(file).interpreted:
        return 0
    cmd = conf.compile_cmd(file)
    if cmd is None:
        log(f"{file} has no compilation command!")
        return 1
    exe = conf.executable(file)
    file_content = combine(file)
    need_recompile = file_content != open(pre_combined).read() or not os.path.exists(
        exe
    )
    if not need_recompile:
        log(f"{file} is up-to-date, skipped recompile")
        return 0
    try:
        log(" ".join(cmd))
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
        )
        if not proc.returncode:
            open(pre_combined, "w").write(file_content)
            return 0
        else:
            log(proc.stderr)
            try:
                os.remove(exe)
            except:
                pass
            return proc.returncode
    except BaseException as e:
        log("".join(traceback.format_exception(e)))
        return 1


def test_manual(solver: str):
    retcode = compile(solver, logger.info)
    if retcode:
        return retcode
    cmd = conf.execute_cmd(solver)
    logger.info(cmd)
    proc = Popen(
        cmd,
        # bufsize=0,
        stdin=sys.stdin,
        stdout=sys.stdout,
        stderr=sys.stderr,
        shell=type(cmd) is str,
    )
    return proc.wait()

def test_bruteforce(solver: str, generator: str, cpulimit: int, memlimit: int):
    if compile(solver, logger.info):
        return 1
    if compile(generator, logger.info):
        return 1
    testId = 0
    while True:
        testId += 1
        log = Logger(testId)
        verdict = Verdict()
        psolver = make_process(
            conf.execute_cmd(solver),
        )
        pgenerator = make_process(
            conf.execute_cmd(generator),
        )
        run_graph(
            poll(psolver, verdict, True),
            poll(pgenerator, verdict, False),
            flow(pgenerator.stdout, [psolver.stdin], log.input, verdict),
            flow(psolver.stdout, [], log.output, verdict),
            flow(psolver.stderr, [], log.error, verdict),
            flow(pgenerator.stderr, [], log.error, verdict),
        )
        log.verdict(
        get_verdict(
            psolver=psolver,
            cpulimit=cpulimit,
            memlimit=memlimit,
            verdict=verdict,
            answer=None,
            actual=None,
        )
        )
        if not verdict.solved or stopflag.is_set():
            return
        print("-" * shutil.get_terminal_size().columns)

def test_compare(solver: str, comparator: str, cpulimit: int, memlimit: int):
    if compile(solver, logger.info):
        return 1
    if compile(comparator, logger.info):
        return 1
    testId = 0

    with (
        tempfile.NamedTemporaryFile(mode="w+") as actualstream,
        tempfile.NamedTemporaryFile(mode="w+") as inputstream,
        tempfile.NamedTemporaryFile(mode="w+") as answerstream,
    ):
        while True:
            testId += 1
            log = Logger(testId)
            verdict = Verdict()
            psolver = make_process(
                conf.execute_cmd(solver),
            )
            pcomparator = make_process(
                conf.execute_cmd(comparator),
            )
            part = 0
            inputstream.seek(0)
            inputstream.truncate(0)
            answerstream.seek(0)
            answerstream.truncate(0)
            withanswer = False
            for line in pcomparator.stdout:
                line = line.decode()
                if part:
                    withanswer = True
                    answerstream.write(line)
                else:
                    if line == "\n":
                        part = 1
                        continue
                    log.input(line)
                    inputstream.write(line)
            inputstream.seek(0)
            actualstream.seek(0)
            actualstream.truncate(0)
            run_graph(
                poll(psolver, verdict, True),
                flow(inputstream, [psolver.stdin], None, verdict),
                flow(psolver.stdout, [actualstream], log.actual, verdict),
                flow(psolver.stderr, [], log.error, verdict),
            )
            actualstream.seek(0)
            answerstream.seek(0)
            log.answer(answerstream.read())
            answerstream.seek(0)
            log.verdict(
            get_verdict(
                psolver=psolver,
                cpulimit=cpulimit,
                memlimit=memlimit,
                verdict=verdict,
                answer=answerstream,
                actual=actualstream,
                withanswer=withanswer,
            )
            )
            if not verdict.solved or stopflag.is_set():
                return
            print("-" * shutil.get_terminal_size().columns)


def test_interact(solver: str, checker: str, cpulimit: int, memlimit: int):
    if compile(solver, logger.info):
        return 1
    if compile(checker, logger.info):
        return 1
    
    testId = 0
    totcpu = 0
    maxmem = 0
    while True:
        testId += 1
        log = Logger(testId)
        verdict = Verdict()
        print(f"Test #{testId} Chat:")
        pChecker = make_process(
            conf.execute_cmd(checker),
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
            flow(pChecker.stderr, [], log.error, verdict),
            flow(pSolver.stderr, [], log.error, verdict),
        )
        ret = None
        if not verdict.solved:
            ret = ("Inner error")
        elif stopflag.is_set():
            ret = ("Terminated")
        if pSolver.returncode:
            ret = (
                "A solution finishing with exit code other than 0 (without exceeding time \n"
                "or memory limits) would be interpreted as a Runtime Error in the system."
            )
            verdict.solved = 0
        elif pChecker.returncode:
            ret = (
                "Fails: "
                "A solution finishing with exit code 0 (without exceeding time \n"
                "or memory limits) and a judge finishing with exit code other \n"
                "than 0 would be interpreted as a Wrong Answer (or query limit exceeded) \n"
                "in the system.\n"
            )
            verdict.solved = 0
        elif verdict.mem > memlimit:
            ret = (f"Memory limit exceeded ({verdict.mem} > {memlimit})")
            verdict.solved = 0
        elif verdict.cpu > cpulimit:
            ret = (
                f"Time limit exceeded ({verdict.cpu} > {cpulimit})"
            )
            verdict.solved = 1
        else:
            ret = (f"OK in {verdict.cpu}s & {verdict.mem}mB")
        log.verdict(ret)
        if not verdict.solved or stopflag.is_set():
            break
        totcpu += verdict.cpu
        maxmem = max(maxmem, verdict.mem)
        print("")


from typing import List, Tuple
import sys

def test_file(solver: str, testsfile: str, withanswer: bool, cpulimit: int, memlimit: int):
    if compile(solver, logger.info):
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
        itr = blank_lines_seperated(testsfile)
        while itr:
            input = next(itr)
            if withanswer:
                answer = next(itr)
            testId += 1
            log = Logger(testId)
            verdict = Verdict()
            proc = make_process(
                conf.execute_cmd(solver),
                desc="solver",
            )
            inputstream.seek(0)
            inputstream.truncate(0)
            inputstream.write(input)
            inputstream.flush()
            inputstream.seek(0)
            actualstream.seek(0)
            actualstream.truncate(0)
            run_graph(
                poll(proc, verdict, True),
                flow(inputstream, [proc.stdin], log.input, verdict),
                flow(proc.stdout, [actualstream], log.actual, verdict),
                flow(proc.stderr, [], log.error, verdict),
            )
            totcpu += verdict.cpu
            maxmem = max(maxmem, verdict.mem)
            if withanswer:
                log.answer(answer)
                actualstream.seek(0)
                answerstream.seek(0)
                answerstream.truncate(0)
                answerstream.write(answer)
                answerstream.flush()
                answerstream.seek(0)
            log.verdict(
            get_verdict(
                psolver=proc,
                cpulimit=cpulimit,
                memlimit=memlimit,
                verdict=verdict,
                answer=answerstream,
                actual=actualstream,
                withanswer=withanswer,
            )
            )
            passed += verdict.solved
            if stopflag.is_set():
                print("terminated")
                return
            # print("-" * shutil.get_terminal_size().columns)
    log.conclusion(get_conclusion(testId, passed, totcpu, maxmem))


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

