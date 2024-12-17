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
from .testsync import compile

def main():
    try:
        p = argparse.ArgumentParser(
            prog="StdRun",
            description="Run part",
        )
        p.add_argument("solver")
        args = p.parse_args()

        retcode = compile(args.solver, logger.info)
        if retcode:
            return retcode
        cmd = conf.execute_cmd(args.solver)
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
    except KeyboardInterrupt:
        return 1