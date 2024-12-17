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
from .listener import create_task

def main():
    try:
        p = argparse.ArgumentParser(
            prog="StdNew",
            description="New task part",
        )
        p.add_argument("taskname")
        p.add_argument("-S", "--solver", dest="langsuffix", default=conf.solver)
        # p.add_argument("-T", "--testsfile", dest="testsfile", default="tests", help="test file, blank line seperated test cases, input & answer interleaves")
        p.add_argument("-v", dest="verbose", action="store_true",) 
        args = p.parse_args()

        taskdir = create_task(args.taskname, args.solver, args.verbose)
        print(f"Task {args.taskname} created in {taskdir}.")
    except KeyboardInterrupt:
        return 1
