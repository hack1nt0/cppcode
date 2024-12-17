import logging, os
import traceback
import sys
from datetime import datetime
import collections
import io

def token_itr(s: str):
    for line in io.StringIO(s):
        for tk in line.split():
            if tk:
                yield tk
        yield "\n"

def formatanswer(s):
    return f"\033[3m{s}\033[0m"

def formatactual(s):
    return f"\033[9m{s}\033[0m"

def formatdiff(answer, actual):
    return f"{answer} ≠ {actual}"

def formatgreen(s):
    return f"\033[32m{s}\033[0m"
    
def formatred(s):
    return f"\033[31m{s}\033[0m"

def headline(s):
    return f"\033[4m{s}\033[0m"

class Logger:

    def __init__(self, testId: int) -> None:
        self.testId = testId

        self.inputHead = headline(f"Test #{testId} input:")
        self.outputHead = headline(f"Test #{testId} Output:")
        self.verdictHead = headline(f"Test #{testId} Verdict:")
        self.concludeHead = headline(f"Conclusion:")

        self.actualToks = collections.deque()
        self.answerToks = collections.deque()
        self.idx = 0

    def _print(self, *xs):
        print(datetime.now().isoformat(), end=" ")
        for x in xs[:-1]:
            print(x.upper().ljust(10), end=" ")
        print("-", xs[-1], flush=True)

    def input(self, content: str):
        if self.inputHead:
            print(self.inputHead)
            self.inputHead = None
        print(content, end=("\n" if not content.endswith("\n") else ""), flush=True)

    def print_token(self):
        answerTok = self.answerToks[0] if len(self.answerToks) else ""
        actualTok = self.actualToks[0] if len(self.actualToks) else ""
        if answerTok and actualTok:
            self.answerToks.popleft()
            self.actualToks.popleft()
            eq = False
            try:
                eq = abs(float(answerTok) - float(actualTok)) < 1e-6
            except ValueError:
                eq = actualTok == answerTok
            if not eq:
                print(f"{formatdiff(answerTok, actualTok)}", end=" ", flush=True)
            else:
                print(diffsame(answerTok), end=" ", flush=True)

    def answer(self, content: str):
        if self.outputHead:
            print(self.outputHead)
            self.outputHead = None

        for tk in token_itr(content):
            if tk == "\n":
                print()
            else:
                self.answerToks.append(tk)
                self.print_token()

    def actual(self, content: str):
        if self.outputHead:
            print(self.outputHead)
            self.outputHead = None
        for tk in token_itr(content):
            if tk == "\n":
                pass
            else:
                self.actualToks.append(tk)
                self.print_token()

    def output(self, content: str):
        if self.outputHead:
            print(self.outputHead)
            self.outputHead = None
        print(content, end="", flush=True)

    def verdict(
            self, 
        cpu: int,
        cpulimit: int,
        mem: int,
        memlimit: int,
        scode: int = 0, gcode: int = 0, ccode: int = 0, 
        answer: io.TextIOBase = None,
        actual: io.TextIOBase = None,
    ) -> bool:
        print(self.verdictHead)
        def print_footer(content: str):
            s = formatgreen(content) if "ok" in content.lower() else formatred(content)
            s += f" in {cpu}s and {mem}mb"
            print(s, flush=True)
        if scode:
            print_footer(f"Solver exit with code {scode}")
            return False
        if gcode:
            print_footer(f"Generator exit with code {scode}")
            return False
        if ccode:
            print_footer(f"Comparator exit with code {scode}")
            return False
        if answer:
            WA = False
            actuals = [tk for line in actual for tk in line.split()]
            # for line in answer:
            #     for answerTk in line.split():
            #         actualTk = next(actuals, None)
            #         if actualTk:
            #             eq = True
            #             try:
            #                 eq = abs(float(answerTk) - float(actualTk)) < 1e-6
            #             except ValueError:
            #                 eq = actualTk == answerTk
            #             if not eq:
            #                 print(f"{formatdiff(answerTk, actualTk)}", end=" ", flush=True)
            #                 WA = True
            #             else:
            #                 print(formatanswer(answerTk), end=" ")
            #         else:
            #             print(formatanswer(answerTk), end=" ")
            #     print()
            # while True:
            #     actualTk = next(actuals, None)
            #     if not actualTk:
            #         break
            #     WA = True
            #     print(formatactual(answerTk), end="")
            answers = [tk for line in answer for tk in line.split()]
            rows = max(len(actuals), len(answers))
            rowW = len(str(rows))
            ACTUAL = "Actual"
            ANSWER = "Answer"
            actualW = max(len(ACTUAL), max(map(len, actuals)))
            answerW = max(len(ANSWER), max(map(len, answers)))
            
            print(f"{' ' * rowW}{ANSWER.rjust(answerW)} {ACTUAL.rjust(actualW)}")
            import itertools
            for row, (actualTk, answerTk) in enumerate(itertools.zip_longest(actuals, answers), start=1):
                print(str(row).ljust(rowW), end="")
                print(answerTk.rjust(answerW), end="")
                print(' ' * (actualW - len(actualTk)), end="")
                eq = True
                try:
                    eq = abs(float(answerTk) - float(actualTk)) < 1e-6
                except ValueError:
                    eq = actualTk == answerTk
                if not eq:
                    actualTk = formatred(actualTk) 
                    WA = True
                else:
                    actualTk = formatgreen(actualTk) 
                print(actualTk)
            if WA:
                print_footer("Wrong Answer")
                return False
        if mem > memlimit:
            print_footer("Memory limit exceeded")
            return False
        if cpu > cpulimit:
            print_footer("Time limit exceeded")
            return False
        print_footer("OK")
        return True


    def conclusion(self, content: str):
        print(self.concludeHead)
        print(formatgreen(content) if "pass" in content.lower() else formatred(content))

    def solver2checker(self, content: str):
        print(formatactual(content), end="", flush=True)
    
    def checker2solver(self, content: str):
        print(formatanswer(content), end="", flush=True)
    
    def error(self, content: str):
        print(formatred(content), end="", flush=True)

    def info(self, content: str):
        print(content, end=("\n" if not content.endswith("\n") else ""), flush=True)


logger = Logger(0)

# def excepthook(exc_type, exc_value, exc_tb):
#     tb = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
#     logger.exception(tb)

# sys.excepthook = excepthook
