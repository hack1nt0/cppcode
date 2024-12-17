import json
from http.server import HTTPServer, BaseHTTPRequestHandler
import os
from .conf import conf
import argparse
import sys
from datetime import datetime

verbose = True

def main():
    try:
        p = argparse.ArgumentParser(prog="StdListen", description="StdTest's listen part")
        p.add_argument("-p", dest="port", type=int, default=27121)
        p.add_argument("-v", dest="verbose", action="store_true",) 
        args = p.parse_args()
        global verbose
        verbose = args.verbose
        print(f"Listen for [+ Competitive Companion] on {args.port}...")
        server = HTTPServer(("localhost", args.port), Listener)
        server.serve_forever()
        server.shutdown()
            
    except KeyboardInterrupt:
        sys.exit(0)
    except BaseException as e:
        print(str(e), file=sys.stderr)
        sys.exit(1)

def printv(s):
    if verbose:
        print(s)

def create_task(name, solvername, url=""):
    taskdir = "".join(filter(lambda c: c.isalnum(), name)).lower()
    os.makedirs(taskdir, exist_ok=True)
    lang = conf.language(solvername)
    if not lang:
        solver = os.path.join(taskdir, solvername)
        open(solver, "w").write("")
        printv(f"solver...C")
        printv(f"Writing solver file...No config found for {solvername}")
    else:
        solver = os.path.join(taskdir, conf.solver)
        if not os.path.exists(solver) or not os.path.getsize(solver):
            printv(f"solver...C")
            open(solver, "w").write(conf.language(solver).template)
        else:
            printv(f"solver...S")
    readmefile = os.path.join(taskdir, "readme.md")
    if not os.path.exists(readmefile):
        printv(f"readme...C")
        open(readmefile, "w").write(f"""
<h2 align="center"><a href="{url}">{name}</a></h2>
<p align="center">{datetime.now().isoformat()}</p>
        """)
    # indexfile = "index.html"
    # if not os.path.exists(indexfile):
    #     printv(f"index...C")
    #     pass
    # from bs4 import BeautifulSoup
    # soup = BeautifulSoup(open(indexfile).read(), 'html.parser')
    # tr = soup.find_all('tr', attrs={"id": name})
    # if not tr:
    #     printv(f"index...U")
    #     tr = soup.new_tag("tr", attrs={"id": name})
    #     td = soup.new_tag("td")
    #     td.append(name)
    #     tr.append(td)
    #     soup.body.table.append(tr)
    #     open(indexfile, "w").write(soup.prettify())
        
    return taskdir

class Listener(BaseHTTPRequestHandler):
    def do_POST(self):
        dat = self.rfile.read(int(self.headers["content-length"]))
        dat = json.loads(dat)
        printv(dat)
        taskname = dat["name"]
        taskdir = create_task(taskname, conf.solver, url=dat["url"])
        open(os.path.join(taskdir, "task.json"), "w").write(json.dumps(dat, indent=4))
        printv("meta...U")
        print(f"Task {taskname} created in {taskdir}.")
