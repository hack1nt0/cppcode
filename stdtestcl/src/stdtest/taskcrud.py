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


META = "task.json"
db = Database()

def getlocaltaskmeta() -> dict:
    if not os.path.exists(META):
        return None
    dat = json.loads(open(META).read())
    return dat

def savelocaltaskmeta(dat) -> dict:
    with open(META, 'w') as w:
        json.dump(dat, w, indent=4)

def printtask(taskids):
    tasks = [db.select(f"select solved, id, name, ctime, `group` from task where id=?", x)[0] for x in taskids]
    FORMATSTR = "%4s %20s %20s %s"
    headers = ("ID", "Name", "CTime", "DESC")
    print(FORMATSTR % headers)
    for solved, ID, name, ctime, desc in tasks:
        if solved == 1: #solved
            print(f'\033[48;5;{46}m', end='')
        elif solved == 2: #unsolved
            print(f'\033[48;5;{196}m', end='')
        print(FORMATSTR % (
            str(ID),
            textwrap.shorten(name, 20, tabsize=4),
            datetime.fromtimestamp(ctime).isoformat(),
            desc,
        ), end='')
        print(f"\033[0m")

def listtasks(sql='select id from task order by ctime desc limit 11'):
    print(f"{sql}\n\nHI")
    printtask(db.select(sql))
    # id = int(input("Work task by specify an id:"))
    # print(id)

def createtask(dat):
    olds = db.select(f"select id from task where name=? and `group`=? limit 10", (dat['name'], dat['group']))
    if olds:
        printtask(olds)
        return
    newid = db.select('select count(*) from task')[0][0]
    newdat = db.select("select template from lang where suffix='.json'")[0][0]
    newdat = json.loads(newdat)
    newdat['id'] = newid
    for key in newdat.keys():
        if key in dat:
            newdat[key] = dat[key]
    name = newdat['name']
    group = newdat['group']
    solfile = newdat['sol']
    soltmpl = db.select(f"select template from lang where suffix='{os.path.splitext(solfile)[-1]}'")[0][0]
    ctime = int(time.time())
    db.execute(f"insert into task(id,`group`,name,dat,sol,gen,cmp,chk,ctime,mtime) values(?,?,?,?,?,?,?,?,?,?)", (newid, group, name, json.dumps(newdat, indent=4), soltmpl, None, None, None, ctime,ctime))
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
    task = db.select(f"select dat,sol,gen,cmp,chk from task where id=?", (id,))[0]
    if not task:
        logger.error("No task found in db...")
        return
    dat, sol, gen, cmp, chk = task
    if dat: open(META, 'w+').write(dat)
    dat = json.loads(dat)
    if sol: open(dat['sol'], 'w+').write(sol)
    if gen: open(dat['gen'], 'w+').write(gen)
    if cmp: open(dat['cmp'], 'w+').write(cmp)
    if chk: open(dat['chk'], 'w+').write(chk)
    printtask([(id,)])


def worktask(id):
    archivetask()
    task = db.select(f"select dat,sol,gen,cmp,chk from task where id=?", (id,))[0]
    if not task:
        logger.error("No task found in db...")
        return
    dat, sol, gen, cmp, chk = task
    if dat: open(META, 'w+').write(dat)
    dat = json.loads(dat)
    if sol: open(dat['sol'], 'w+').write(sol)
    if gen: open(dat['gen'], 'w+').write(gen)
    if cmp: open(dat['cmp'], 'w+').write(cmp)
    if chk: open(dat['chk'], 'w+').write(chk)
    printtask([(id,)])
    
def archivetask():
    dat = getlocaltaskmeta()
    if not dat:
        logger.error("No working task to arxiv...")
        return
    id = dat['id']
    fullname = f"{dat['name']} - {dat['group']}"
    filewildcards = dat['files']
    filesmap = {}
    for filekeeped in (x for fkey in filewildcards for x in glob.glob(fkey) if os.path.isfile(x)):
        filesmap[filekeeped] = open(dat[filekeeped]).read()
    dat['files'] = filesmap
    mtime = int(time.time())
    db.execute(f"update task2 set fullname=?, dat=?, mtime=? where id=?",
               (fullname, json.dumps(dat, indent=4), mtime, id)
    )
    print(f"Sucessfully uploaded task '{fullname}' to arxiv, congrats!".upper())
    try:
        for f in filesmap:
            os.remove(f)
        os.remove(META)
    except:
        pass
    
def deletetask():
    dat = getlocaltaskmeta()
    if not dat:
        logger.debug("No working task to delete...")
        return
    id = dat['id']
    name = dat['name']
    db.execute(f"delete from task where id=?", (id,))
    #delete all local files
    files = {
        'sol': None,
        'gen': None,
        'cmp': None,
        'chk': None,
    }
    for fkey in files:
        if dat[fkey]:
            os.remove(dat[fkey])
    print(f"Sucessfully removed task '{name}' from arxiv.")

def task2task2():
    tasks = db.select(f"select id,grdat,sol,gen,cmp,chk from task")
    
    pwd = os.getcwd()
    glob.glob()
    
# def clean():
#     dat = getlocaltaskmeta()
#     for fd in os.listdir():
#         if usefull(fd): continue
#         if os.path.isdir(fd):
#             shutil.rmtree(fd)
#         else:
#             os.remove(fd)