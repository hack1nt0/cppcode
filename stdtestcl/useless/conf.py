import dataclasses
from typing import List, Tuple, Dict, Any
import datetime
import os, sys, json
import argparse
import json
from .logger import Logger, logger
from subprocess import Popen
import tomllib

# CONFFILE = os.path.expanduser("~/stdtest.json")
CONFFILE = os.path.join(os.path.dirname(__file__), ".stdtest")

def main():
    try:
        p = argparse.ArgumentParser(
            prog="StdConfig",
        )
        args = p.parse_args()
        cmd = f"vi {CONFFILE}"
        logger.info(cmd)
        proc = Popen(
            cmd,
            # bufsize=0,
            stdin=sys.stdin,
            stdout=sys.stdout,
            stderr=sys.stderr,
            shell=type(cmd) is str,
        )
        proc.wait()
        # validate
        
    except KeyboardInterrupt:
        return 1

@dataclasses.dataclass
class Language:
    name: str = ""
    template: str = None
    build: str = ""
    run: str = ""
    includepath: str = ""

class Configuration:
    def __init__(self) -> None:
        self.dat = tomllib.loads(open(CONFFILE).read())
        self.languages = self.dat["lang"]
        self.bps = self.dat["prefer"]["bps"]
        self.solver = self.dat["prefer"]["solver"]
        self.generator = self.dat["prefer"]["generator"]
        self.comparator = self.dat["prefer"]["comparator"]
        self.checker = self.dat["prefer"]["checker"]
        self.ichecker = self.dat["prefer"]["ichecker"]
        # self.inputs = self.dat["prefer"]["inputs"]
        # self.answers = self.dat["prefer"]["answers"]
        self.testfiles = self.dat["prefer"]["in*"]
        self.batch = int(self.dat["prefer"]["batch"])
        self.bps = int(self.dat["prefer"]["bps"])
        self.cpulimit = int(self.dat["prefer"]["cpulimit"])
        self.memlimit = int(self.dat["prefer"]["memlimit"])

    def language(self, file: str) -> Language:
        prefix, suffix = os.path.splitext(file)
        suffix = suffix[1:]
        if suffix in self.languages: 
            return Language(**self.languages[suffix])
        else:
            print(f"Please add config for [lang{suffix}].")
            exit(1)

    def compile_cmd(self, file: str) -> str:
        # TODO -it : ERR the input device is not a TTY
        # ret = f"docker exec dev bash compile{self.suffix}.sh /code/tasks/{self.taskname} {self.path} {self.executable} {1 if conf.build_debug else 0}"
        lang = self.language(file)
        if lang.build:
            prefix, suffix = os.path.splitext(file)
            try:
                ret = lang.build.format(includepath=lang.includepath, input=file, output=f"{prefix}.exe")
            except:
                print(f"Build command should include 3 placeholders: `{{includepath}}, {{input}}`, `{{output}}`!")
                exit(1)
            return self.format_cmd(ret)
        else:
            return ''
    
    def executable(self, file) -> str:
        prefix, suffix = os.path.splitext(file)
        suffix = suffix[1:]
        return f"{suffix}.exe"

    def execute_cmd(self, file) -> str:
        file = os.path.abspath(file)
        lang = self.language(file)
        prefix, suffix = os.path.splitext(file)
        try:
            ret = lang.run.format(file) if lang.run else f"{prefix}.exe"
        except:
            print(f"Run command should include a placeholder: `{{}}`!")
            exit(1)
        return self.format_cmd(ret)

    def format_cmd(self, cmd: str):
        if not cmd:
            return
        import shlex
        return shlex.split(cmd)  # TODO

conf = Configuration()
