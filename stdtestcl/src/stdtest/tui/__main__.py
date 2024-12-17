#!/usr/bin/env python
import sys
import sqlite3

from prompt_toolkit import PromptSession
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.lexers import PygmentsLexer
from prompt_toolkit.styles import Style
from pygments.lexers.sql import SqlLexer

commands = {
    'list': 'list most recent tasks',
    'work': 'work specified task: work [id]',
    'config': 'config task',
    'delete': 'delete task',
    'current': 'current',
    'run': 'run built-in testcases',
    'bruteforce': 'bruteforce test mode, need generator',
    'compare': 'compare test mode, need generator and comparator',
    'check': 'check test mode, need checker',
    'query': 'query tasks from db with sql',
}

task_completer = WordCompleter(commands.keys(), ignore_case=True)

style = Style.from_dict({
    'completion-menu.completion': 'bg:#008888 #ffffff',
    'completion-menu.completion.current': 'bg:#00aaaa #000000',
    'scrollbar.background': 'bg:#88aaaa',
    'scrollbar.button': 'bg:#222222',
})

from ..taskcrud import *

def main():
    session = PromptSession(
        lexer=PygmentsLexer(SqlLexer), completer=task_completer, style=style)

    def printtable(dats, headers, ):
        rows = len(dats)
        cols = len(headers)
        colwidths = [max(len(r[c]) for r in dats) for c in range(cols)]
        FORMATSTR = ' '.join([f'%-{w}s' for w in colwidths])
        print(FORMATSTR)
        print(FORMATSTR % headers)
        for dat in dats:
            print(FORMATSTR % dat)

    while True:
        try:
            text = session.prompt('STDTEST> ')
        except KeyboardInterrupt:
            continue  # Control-C pressed. Try again.
        except EOFError:
            break  # Control-D pressed.

        if text == 'list':
            from .tasksdialog import tasksdialog
            # printtask(db.select(f"select id from task order by ctime desc limit 10"))
            condition = "limit 10"
            sql = "select id, name from task order by ctime desc " + condition;
            task = tasksdialog(db.select(sql), condition=sql).run()
            print(task)
        elif text == '?':
            printtable(dats=commands.items(), headers=('command'.upper(), 'desc'.upper()))
        elif text == 'config':
            from .confdialog import confdialog
            confdialog().run()
        elif text == 'run':
            from .rundialog import confdialog
            confdialog().run()
            

    print('GoodBye!')

if __name__ == '__main__':
    if len(sys.argv) < 2:
        db = ':memory:'
    else:
        db = sys.argv[1]

    main(db)