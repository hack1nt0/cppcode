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
import time, psutil
import traceback
from typing import List, Tuple
import shutil
import itertools
import argparse
import json
import textwrap
import math
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
import os
import argparse
import sys
from datetime import datetime
import sqlite3
from .db.db import Database
from .logger import logger

TBL = 'task2'
META = "task.json"
db = Database()

def getlocaltaskmeta() -> dict:
    if not os.path.exists(META):
        return None
    dat = json.loads(open(META).read())
    return dat

def getfiles(dat) -> list:
    filewildcards = dat['files']
    return (x for fkey in filewildcards for x in glob.glob(fkey) if os.path.isfile(x))

def getfullname(dat) -> str:
    return str((dat['name'], dat['group']))

# def savelocaltaskmeta(dat) -> dict:
#     with open(META, 'w') as w:
#         json.dump(dat, w, indent=4)

def printtask(taskids):
    tasks = [db.select(f"select `status`, id, fullname, ctime from {TBL} where id=?", id)[0] for id in taskids]
    W = shutil.get_terminal_size().columns - 24 - 3
    FORMATSTR = f"%4s %-{W}s %20s"
    headers = ("ID", "Name", "CTime")
    print(FORMATSTR % headers)
    for status, ID, fullname, ctime in tasks:
        if status == 1: #solved
            print(f'\033[48;5;{46}m', end='')
        elif status == 2: #unsolved
            print(f'\033[48;5;{196}m', end='')
        print(FORMATSTR % (
            str(ID),
            textwrap.shorten(fullname, W, tabsize=4),
            datetime.fromtimestamp(ctime).isoformat(),
        ), end='')
        print(f"\033[0m")

def listtasks(sql=f'select id from {TBL} order by ctime desc limit 11'):
    print(f"{sql}\n\nHI")
    printtask(db.select(sql))
    # id = int(input("Work task by specify an id:"))
    # print(id)

def createtask(dat):
    # dat from competition companion plugin
    old = db.select(f"select id from {TBL} where fullname=?", (getfullname(dat),))
    if old:
        printtask(old)
        return
    newid = db.select('select count(*) from task')[0][0]
    files = {}
    for idx, test in enumerate(dat['tests']):
        i, o = test['input'], test['output']
        files[f'in-{idx}'] = '\n'.join([i, o])
    del dat['tests']
    templatedir = 'template/standard' if not dat['interactive'] else 'template/interactive'
    for f in glob.glob(f'{templatedir}/*'):
        files[os.path.basename(f)] = open(f).read()
    ctime = int(time.time())
    mtime = ctime
    db.execute(f"insert into {TBL}(id,fullname,dat,ctime,mtime) values(?,?,?,?,?)", (newid, getfullname(dat), json.dumps(dat, indent=4).encode(), ctime,mtime))
    printtask([(newid,)])


def listentask():
    class Listener(BaseHTTPRequestHandler):
        def do_POST(self):
            dat = self.rfile.read(int(self.headers["content-length"]))
            dat = json.loads(dat)
            createtask(dat)
    port = 27121
    print(f"Listen for [+ Competitive Companion] on {port}...")
    server = HTTPServer(("localhost", port), Listener)
    server.serve_forever()
    server.shutdown()


def worktask(id):
    archivetask()
    try:
        dat = db.select(f"select dat from {TBL} where id=?", (id,))[0][0]
    except:
        logger.error("No task found in db...".upper())
        return
    dat = json.loads(dat)
    for fname, ftext in dat['files'].items():
        open(fname, 'w+').write(ftext)
    dat['files'] = list(dat['files'].keys())
    if 'tests' in dat: del dat['tests']
    open(META, 'w+').write(json.dumps(dat, indent=4))
    print(f"Switch to task '{getfullname(dat)}'!".upper())
    # printtask([(id,)])
    
def archivetask():
    dat = getlocaltaskmeta()
    if not dat:
        logger.error("No working task to arxiv...".upper())
        return
    id = dat['id']
    if id == 0:
        logger.error("task of id ZERO cannot be archived...".upper())
        return
    filesmap = {}
    for filekeeped in getfiles(dat):
        filesmap[filekeeped] = open(filekeeped).read()
    dat['files'] = filesmap
    mtime = int(time.time())
    db.execute(f"update task2 set fullname=?, dat=?, mtime=? where id=?",
               (getfullname(dat), json.dumps(dat, indent=4).encode(), mtime, id)
    )
    print(f"Sucessfully uploaded task '{getfullname(dat)}' to arxiv, congrats!".upper())
    try:
        for f in getfiles(dat):
            os.remove(f)
        os.remove(META)
    except:
        pass
    
def deletetask():
    dat = getlocaltaskmeta()
    if not dat:
        logger.error("No working task to delete...".upper())
        return
    id = dat['id']
    if id == 0:
        logger.error("task of id ZERO cannot be deleted...".upper())
        return
    db.execute(f"delete from {TBL} where id=?", (id,))
    #delete all local files
    for f in getfiles(dat):
        os.remove(f)
    print(f"Sucessfully removed task '{getfullname(dat)}' from arxiv.")


def task2task2():
    tasks = db.select(f"select id,`group`,name,dat,sol,gen,cmp,chk,ctime,mtime,solved from task where id != 0")
    for id, group, name, dat, sol, gen, cmp, chk, ctime, mtime, solved in tasks:
        files = {}
        dat = json.loads(dat)
        if dat['sol']: files[dat['sol']] = sol
        if dat['gen']: files[dat['gen']] = gen
        if dat['cmp']: files[dat['cmp']] = cmp
        if dat['chk']: files[dat['chk']] = chk
        del dat['sol']
        del dat['gen']
        del dat['cmp']
        del dat['chk']
        for idx, test in enumerate(dat['tests']):
            i, o = test['input'], test['output']
            files[f'in-{idx}'] = '\n'.join([i, o])
        del dat['tests']
        dat['files'] = files
        db.execute(f"insert or replace into {TBL}(id,fullname,dat,ctime,mtime,`status`) values(?,?,?,?,?,?)", (id, getfullname(dat), json.dumps(dat, indent=4).encode(),ctime,mtime,solved))
    
# def clean():
#     dat = getlocaltaskmeta()
#     for fd in os.listdir():
#         if usefull(fd): continue
#         if os.path.isdir(fd):
#             shutil.rmtree(fd)
#         else:
#             os.remove(fd)