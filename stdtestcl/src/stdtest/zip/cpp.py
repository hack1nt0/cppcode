import json, shlex, sys, subprocess, argparse, os, tempfile, re
import datetime, collections
from ..logger import logger

def main():
    p = argparse.ArgumentParser(prog="StdCopy", description="StdTest's copy part")
    p.add_argument("solver", help="File to zip")
    p.add_argument("-E", dest="preprocess", help="Preprocess, i.e., includes combine/macro substition/del comments...", action="store_true")
    p.add_argument("-S", dest="ast", help="Generate AST", action="store_true")
    p.add_argument("-O", dest="prune", help="Pruning", action="store_true")
    p.add_argument("-v", dest="verbose", help="Verbose", action="store_true")
    args = p.parse_args()
    global verbose
    verbose = args.verbose
    cppfile = args.solver
    zipcpp(cppfile)

def zipcpp(cppfile):
    cppfile = os.path.abspath(cppfile)
    prefix = os.path.splitext(cppfile)[0]
    prepfile = prefix + ".tmp.prep.cpp"
    astfile = prefix + ".tmp.ast.json"
    prunfile = prefix + ".zip.cpp"
    preprocess(cppfile, prepfile)
    astdump(prepfile, astfile)
    prune(astfile, prepfile, prunfile)
    os.remove(prepfile)
    os.remove(astfile)
    return prunfile

    
CUSTOM_NAMESPACE = "__stdtest__"
CUSTOM_NAMESPACE_BEGIN_LINE = f"namespace {CUSTOM_NAMESPACE} {{\n"
CUSTOM_NAMESPACE_END_LINE = "}; int main() { return 0; }\n"

stdheaders = set()
def preprocess(cppfile: str, prepfile: str):
    cppfile = os.path.abspath(cppfile)
    with (
        open(prepfile, 'w+') as prepstream,
        tempfile.NamedTemporaryFile(mode="w+") as tempstream,
    ):
        logger.debug(">Preprocess...".title())
        logger.debug(">>include no-standard headers + format...".title())
        pat_header = re.compile(r'[ \t]*#include[ \t]*["<]([\w\\/\._]+)[>"]')
        vis = set()
        def concat(x: str):
            with open(x, "r") as f:
                for line in f.readlines():
                    m = pat_header.match(line)
                    iscustomheader = False
                    isstdheader = False
                    if m:
                        header = m.group(1)
                        y = os.path.normpath(os.path.join(os.path.dirname(x), header))
                        if os.path.exists(y) and os.path.isfile(y):
                            iscustomheader = True
                            if y not in vis:
                                vis.add(y)
                                concat(y)
                        else:
                            isstdheader = True
                            stdheaders.add(line)
                    if not iscustomheader and not isstdheader:
                        line = line.replace('\t', ' '*4)
                        tempstream.write(line)
                        # Last line of file may not ends with newline
                        if not line.endswith("\n"):
                            tempstream.write('\n')
        concat(cppfile)
        tempstream.seek(0)
        logger.debug(">>macro substitution + del comments...".title())
        ret = subprocess.run(
            "clang++ -E -xc++ -".split(),
            stdin=tempstream,
            stdout=prepstream,
            stderr=sys.stderr,
        )
        if ret.returncode:
            exit(ret.returncode)
        logger.debug(">>Remove # lines...".title())
        lines = open(prepfile).readlines()
        with open(prepfile, 'w') as w:
            for line in stdheaders:
                w.write(line)
            w.write(CUSTOM_NAMESPACE_BEGIN_LINE)
            for line in lines:
                if not line.startswith("#"):
                    w.write(line)
            w.write(CUSTOM_NAMESPACE_END_LINE)
        logger.debug(f">Preprocess...done:".title(), prepfile, "\n")

def astdump(prepfile: str, astfile: str):
    with (
        open(astfile, 'w+') as w,
    ):
        logger.debug(">Generate AST...".title())
        ret = subprocess.run(
            f"clang++ -std=c++20 -Xclang -ast-dump=json -Xclang -ast-dump-filter={CUSTOM_NAMESPACE} {prepfile}".split(), 
            stdout=w, 
            stderr=subprocess.DEVNULL, #todo always have errors...
        )
        # if ret.returncode:
        #     exit(ret.returncode)
        logger.debug(f">Generate AST...done:".title(), astfile, "\n")

def prune(astfile: str, prepfile: str, prunfile: str):
    lines = open(prepfile).readlines()
    tree = json.loads(open(astfile).read())

    def getkind(d): return d.get('kind', '')
    def getname(d): return d.get('name', '')
    # def gettype(d): return d['type']['qualType']
    def gettype(d):
        try:
            return d['type']['desugaredQualType']
        except:
            try:
                return d['type']['qualType']
            except:
                pass
        return ''
    def getid(d): return d.get('id', '')

    def isfundecl(d): return getkind(d) == 'FunctionDecl'
    def istemplatefundecl(d): return getkind(d) == 'FunctionTemplateDecl'
    def isclsdecl(d): return getkind(d) == 'CXXRecordDecl'
    def istemplateclsdecl(d): return getkind(d) == 'ClassTemplateDecl'
    def istemplateclspartialdecl(d): return getkind(d) == 'ClassTemplatePartialSpecializationDecl'
    # def isaliasdecl(d): return getkind(d) == 'TypeAliasDecl'


    # overrided funcs invocations from template class
    def getunsolvedfunrefs(d): return d['lookups'] if getkind(d) == 'UnresolvedLookupExpr' else []
    def getfunref(d): return d.get('referencedDecl', '')
    def gettemplatefunref(d): return d.get('foundReferencedDecl', '')
    def isclsref(d): return getkind(d) == 'CXXConstructExpr'
    def istemplateclsref(d): return getkind(d) == 'CXXConstructExpr'

    def getrefids(d): 
        if not d: return []
        refs = getunsolvedfunrefs(d)
        if refs:
            return [x['id'] for x in refs]
        ref = gettemplatefunref(d) or getfunref(d) # order matter!
        if ref:
            return [ref['id']]
        if istemplateclsref(d) or isclsref(d):
            x = gettype(d)
            # std::vector<__stdtest__::E___________>
            x = map(lambda c: c[len(CUSTOM_NAMESPACE)+2:] if c.startswith(CUSTOM_NAMESPACE) else c, re.split('[<>, ]', x))
            x = list(filter(lambda c: c, x))
            return x
        return []

    def getdeclid(x):
        if not x: return ''
        return getid(x) if istemplatefundecl(x) or isfundecl(x) else getname(x)


    def getseg(d, lines: list[str]):
        start = d['loc']['line']-1
        if istemplateclsdecl(d) or istemplatefundecl(d):
            start = d['inner'][0]['loc']['line']-1
            while not lines[start].startswith("template"):
                start -= 1
            assert lines[start].startswith("template")
        try:
            stop = d['range']['end']['line']
        except:
            stop = start + 1
        return slice(start, stop)


    def dfs(x, visit):
        if not visit(x):
            return
        if 'inner' not in x:
            return
        for y in x['inner']:
            dfs(y, visit)

    logger.debug(">Pruning...".title())
    logger.debug(">>founding declarations...".title())
    decls = {}
    def visit_decls(x):
        if istemplatefundecl(x):
            xseg = getseg(x, lines)
            for y in x['inner']:
                if isfundecl(y):
                    decls[getid(y)] = (xseg, getname(y), gettype(y), y)
            return 0
        elif istemplateclspartialdecl(x):
            xid = getdeclid(x)
            assert xid in decls, f"{xid} not in decls!!!!!!!!!!!!!"
            old = decls[xid]
            oldseg = old[0]
            newseg = getseg(x, lines)
            # print("~~~~~~~~~~~~~~~~~~newseg:", newseg, oldseg)
            decls[xid] = (slice(oldseg.start, newseg.stop), *old[1:])
            return 0
        elif istemplateclsdecl(x) \
            or isclsdecl(x) \
            or isfundecl(x): 
            # order matter!
            xid = getdeclid(x)
            assert xid not in decls
            decls[xid] = (getseg(x, lines), getname(x), gettype(x), x)
            return 0
        return 1
    dfs(tree, visit_decls)
    for x in decls:
        logger.debug('>>>', x.rjust(20), ':', decls[x][:-1])

    logger.debug(">>founding references...".title())
    adj = {}
    for declid, decljdat in decls.items():
        refs = set()
        def visit_refs(x):
            for refid in getrefids(x):
                if refid in decls:
                    refs.add(refid)
            return 1
        dfs(decljdat[-1], visit_refs)
        adj[declid] = refs
        
    for x, ys in adj.items():
        logger.debug('>>>', x.rjust(20), ":", ys)

    logger.debug(">>removing useless declarations...".title())
    usefuldecls = set()
    que = collections.deque()
    main = next(filter(lambda x: decls[x][1] == 'main', decls))
    que.append(main)
    while len(que):
        x = que.popleft()
        if x not in adj or x in usefuldecls:
            continue
        usefuldecls.add(x)
        for y in adj[x]:
            que.append(y)
    logger.debug(">>>", usefuldecls)

    logger.debug(">>removing blank lines...".title())
    def shrink_consecutive_newlines(lines: list[str]):
        preisnewline = False
        for line in lines:
            if not line.strip():
                if preisnewline:
                    continue
                else:
                    preisnewline = True
                    yield line
            else:
                preisnewline = False
                yield line
    usefullines = []
    curline = 0
    preblank = False
    alldecls = sorted(list(decls.keys()), key=lambda x: decls[x])
    for declid in alldecls:
        seg, declname, decltype, decljdat = decls[declid]
        if curline >= seg.stop: 
            # sometimes desls are overlapped...
            # e.g., default template param in template class decl
            # 
            continue 
        while curline < seg.start:
            line = lines[curline]
            if line == CUSTOM_NAMESPACE_BEGIN_LINE:
                curline += 1
                continue
            if line.strip() or not preblank:
                usefullines.append(line)
            curline += 1
            preblank = not line.strip()
        curline = seg.start
        if declid in usefuldecls:
            while curline < seg.stop:
                line = lines[curline]
                if line.strip():
                    usefullines.append(line)
                curline += 1
        curline = seg.stop
    logger.debug(">>validate final result...".title())
    with open(prunfile, 'w+') as w:
        for line in usefullines:
            w.write(line)
    ret = subprocess.run(
        f"clang++ -std=c++20 -Wfatal-errors -o {os.path.splitext(prunfile)[0]} {prunfile} ".split(),
        stderr=sys.stderr
    )
    if ret.returncode:
        print(f"Validate failed, see {prunfile} for details.")
        sys.exit(ret.returncode)
    with open(prunfile, 'w') as writer:
        usefullines = [line for line in usefullines if line not in stdheaders]
        writer.write(f"/* By dy@stdtest @ {datetime.datetime.now().isoformat()} */\n")
        writer.write("#include <bits/stdc++.h>\n")
        writer.writelines(shrink_consecutive_newlines(usefullines))
        # writer.write(''.join(lines[curline:]))
    logger.debug(f">Pruning...done:".title(), prunfile, "\n")


def shrink_inner(lines: list[str]):
    # todo when there are literal string contains newline...
    pass

if __name__ == '__main__':
    main()