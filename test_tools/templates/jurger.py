import os, sys, io
import subprocess
from subprocess import Popen, PIPE
import argparse

class Jurger:
    def __init__(self, testid):
        pass

    def respond_init(self, out: io.TextIOBase) -> str:
        pass

    # throw runtime error with info when wrong answer
    def respond(self, query, out: io.TextIOBase) -> str:
        pass

    def print_input(self) -> str:
        print('-' * 3, 'input', '-' * 3)
        pass
    
    def run(self, sol_cmd):
        psol = Popen(
            f'/usr/bin/time -al {sol_cmd}',
            shell=True,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=sys.stderr,
            text=True,
        )
        try:
            print(self.respond_init(psol.stdout))
            for line in psol.stdout:
                print(line)
                print(self.respond(line, psol.stdin))
        except BrokenPipeError:
            print(f'\nRuntime Error: Error when sending response to team program - possibly exited')
            self.print_input()
            exit(1)
        except RuntimeError as e:
            print(f'\nWrong Answer:\n {e}')
            self.print_input()
            exit(1)

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('sol_cmd')
    args = p.parse_args()
    testid = 0
    while True:
        testid += 1
        print('-' * 3, testid, '-' * 3)
        Jurger(testid).run(args.sol_cmd)
