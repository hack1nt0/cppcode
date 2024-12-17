from .taskcrud2 import *
# from .logger import logger
from .runtests import *
from .zip import zipx

def main():
    import argparse, textwrap
    try:
        p = argparse.ArgumentParser(
            prog="task",
            description=textwrap.dedent("""
            """),
        )
        
        p.add_argument("--new", help="new task(s)", action="store_true")
        p.add_argument("--list", help="list tasks", action="store_true")
        p.add_argument("--work", help="work task by specify id", type=int, default=-1)
        # p.add_argument("-nl", dest="listen", help="listen", action="store_true")
        # p.add_argument("-n", dest="create", help="new task: group/name, default group: test", type=str)
        # p.add_argument("-nt", dest="newtest", help="add new test from file, seperate input/answer by blank line(s)", type=str)
        p.add_argument("--save", help="save current task to db", action="store_true")
        # p.add_argument("-r", dest="retrieve", help="search task by name")
        p.add_argument("--delete", help="delete/remove", action="store_true")
        # p.add_argument("-w", dest="work", help="download/work specified task(id), meantime archive pre-task", type=int, default=-1)
        # p.add_argument("-q", dest="query", help="query task table given sql")
        # p.add_argument("-l", dest="list", help="query 10 tasks of most recently", action="store_true")
        # p.add_argument("--show", dest="show", help="show task")
        
        # subp = p.add_subparsers(dest='subcommand', help="Sub commands")
        # bruteforce_parser = subp.add_parser('bruteforce', 'brute', )
        # test_parser = subp.add_parser('test')
        # compare_parser = subp.add_parser('compare')
        # check_parser = subp.add_parser('check')

        # p.add_argument("--test", help="test task".upper(), action="store_true")
        p.add_argument("--runtests", help="test task with in-* files".upper(), action="store_true")
        p.add_argument("--bruteforce", help="brutefoce-test mode, need generator", action="store_true")
        p.add_argument("--compare", help="compare-test mode, need generator and comparator", action="store_true")
        p.add_argument("--check", help="interactive-test mode, need comparator(ichecker)", action="store_true")

        p.add_argument("--submit", help="combine into single file to submit", action="store_true")
        p.add_argument("-v", dest="verbose", help="verbose", action="store_true")
        
        p.add_argument("--transfer", help="db transfer".upper(), action="store_true")

        args = p.parse_args()
        logger.verbose = args.verbose
        if args.transfer:
            return task2task2()
        elif args.new:
            print("Creating tasks...")
            opts = ["Listen from Competition Companion", "Manually"]
            for idx, opt in enumerate(opts, start=1):
                print(idx, ":", opt)
            while True:
                opt = input('choose how to create task(s), default is [1]: ')
                if not opt:
                    opt = 1
                else:
                    try:
                        opt = int(opt)
                    except:
                        continue
                if opt == 2:
                    gname = input('input `group/name`[default group is test]: '.upper())
                    p = gname.find('/')
                    if p < 0:
                        name, group = 'test', ''
                    else:
                        name, group = args.create[p:], args.create[:p]
                    return createtask({
                        "name": name,
                        "group": group,
                    })
                elif opt == 1:
                    return listentask()
                else: continue
        elif args.list:
            DEFAULTSQL = "select id from task order by ctime desc limit 11"
            sql = input(f"input sql to query task table, [{DEFAULTSQL}]: ".upper())
            if not sql:
                sql = DEFAULTSQL
            printtask(db.select(sql))
            while True:
                id = input('work task of id: ')
                try:
                    return worktask(int(id))
                except Exception as e:
                    print(e)
                    continue
        elif args.work >= 0:
            return worktask(int(args.work))
        # elif args.test:
        #     opts = [
        #         "run builtin tests",
        #         "brutefoce-test mode, need generator",
        #         "compare-test mode, need generator and comparator",
        #         "interactive-test mode, need comparator(ichecker)",
        #         "Manually"
        #     ]
        #     ret = subprocess.run(
        #         "make compile",
        #         shell=True,
        #         # bufsize=0,
        #         stdin=sys.stdin,
        #         stdout=sys.stdout,
        #         stderr=sys.stderr,
        #     )
        #     if ret.returncode:
        #         sys.exit(ret.returncode)
        #     for idx, opt in enumerate(opts, start=1):
        #         print(idx, ":", opt.capitalize())
        #     while True:
        #         opt = input('choose how to test task, default is [1]: ')
        #         if not opt:
        #             opt = 1
        #         else:
        #             try:
        #                 opt = int(opt)
        #             except:
        #                 continue
        #         if opt == 1:
        #             return runtests()
        #         elif opt == 2:
        #             return test_compare(compare=False)
        #         elif opt == 3:
        #             return test_compare(compare=True)
        #         elif opt == 4:
        #             return test_interact()
        #         else:
        #             return testmanually()
        #             # cmd = input(">")
        #             # ret = subprocess.run(cmd, shell=True, stdin=sys.stdin, stdout=sys.stdout, stderr=sys.stderr)
        #             # print(f"Exit with code {ret.returncode}")
        elif args.runtests:
            return runtests()
        elif args.bruteforce:
            return test_compare(compare=False)
        elif args.compare:
            return test_compare(compare=True)
        elif args.check:
            return test_interact()
        # elif args.retrieve:
        #     return retrievetask(args.retrieve)
        elif args.save:
            return archivetask()
        elif args.delete:
            opt = input(f"Are you sure to delete task `{getlocaltaskmeta()['name']}`, [y]/n: ")
            if not opt or opt == 'y':
                return deletetask()
            else: return
        elif args.submit:
            ret = zipx(getlocaltaskmeta()['sol'])
            if ret:
                print(ret)
                return 0
            else:
                return 1
        else:
            import textwrap
            if args.query:
                print(db.select(args.query))
            elif args.list:
                # printtask(db.select(f"select id from task order by ctime desc limit 10"))
                listtasks()
            else:
                task = getlocaltaskmeta()
                if task: 
                    if args.show:
                        print(task[args.show])
                    else:
                        printtask([(task['id'],)])
                else: print("No task yet...".upper())

    except KeyboardInterrupt:
        return 1

def main2():
    import argparse, textwrap
    try:
        p = argparse.ArgumentParser(
            prog="run",
            description=textwrap.dedent("""
            """),
        )
        p.add_argument("file", help="file to run")
        args = p.parse_args()
        return runmanually(args.file)
    except KeyboardInterrupt:
        return 1

if __name__ == "__main__":
    main()