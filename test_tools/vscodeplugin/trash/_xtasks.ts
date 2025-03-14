import * as vscode from 'vscode';
import * as subprocess from 'node:child_process';
import * as path from 'path';
import * as fs from 'fs';
import { writeFile, writeFileSync, readFile, readFileSync, statSync, createWriteStream, read } from 'node:fs';
import * as sqlite3 from 'sqlite3'
import * as pidusage from 'pidusage'
// import * as pidusageTree from 'pidusage-tree'
// var pidusageTree = require('pidusage-tree')
import { assert, log } from 'node:console';
import { resolve } from 'node:path';


export function fullpath(filename: string) {
	return path.join(vscode.workspace.workspaceFolders![0].uri.fsPath, filename)
}

export function get_tests() : any[] {
    let s = readFileSync(conf.tests.fullname, { encoding: 'utf-8'})
    return JSON.parse(s)
}

export function set_tests(tests: any[]) {
    writeFileSync(conf.tests.fullname, JSON.stringify(tests, null, 4))
}

class XFile {
    role: string
    fullname : string
    basename : string
    template : string
    command : string

    constructor(role: string) {
        this.role = role
        let dirname = fullpath('')
        switch (role) {
            case 'tests':
                this.basename = 'X_tests.json'
                this.fullname = path.join(dirname, this.basename)
                this.template = '[]'
                this.command = ''
                break
            case 'debuginput':
                this.basename = 'X_debug.in'
                this.fullname = path.join(dirname, this.basename)
                this.template = ''
                this.command = ''
                break
            default:
                let templatebasename = vscode.workspace.getConfiguration(`xtask`).get<string>(role)!
                this.template = readFileSync(path.join(dirname, templatebasename), { encoding: 'utf-8' })
                let suffix = templatebasename.split('.')[1]
                let prefix = `X_${role}`
                this.basename = `${prefix}.${suffix}`
                this.fullname = path.join(dirname, this.basename)
                switch (suffix) {
                    case 'py':
                        this.command = `python3 ${this.fullname}`
                        break
                    default:
                        this.command = `${dirname}/bin/${prefix}`
                        break
                }
                break
        }
    }

    check() : boolean {
        switch (this.role) {
            case 'tests':
                if (!fs.existsSync(this.fullname)) {
                    writeFileSync(this.fullname, this.template)
                    vscode.window.showErrorMessage(`No testcases found !`, 'Edit testcases').then(selection => {
                        switch (selection) {
                            case 'Edit testcases':
                                vscode.commands.executeCommand('xtask.listtestcases')
                                break
                        }
                    })
                }
                return true
            default:
                if (!fs.existsSync(this.fullname)) {
                    vscode.window.showErrorMessage(`No ${this.role} (${this.basename}) exists!`, 'Create File').then(selection => {
                        switch (selection) {
                            case 'Create File':
                                writeFileSync(this.fullname, this.template)
                                vscode.workspace.openTextDocument(this.fullname).then(doc => vscode.window.showTextDocument(doc))
                                break;
                        }
                    })
                    return false
                } else {
                    return true
                }
        }
    }
}
class Conf {
    get solver() { return new XFile('solver') }
    get generator() { return new XFile('generator') }
    get comparator() { return new XFile('comparator') }
    get jurger() { return new XFile('jurger') }
    get visualizer() { return new XFile('visualizer') }
    get tests() { return new XFile('tests') }
    get debuginput() { return new XFile('debuginput') }
    get build() { return vscode.workspace.getConfiguration(`xtask`).get<string>('build')! }
    get copy() { return vscode.workspace.getConfiguration(`xtask`).get<string>('copy')! }
}
export const conf = new Conf()
class DB {
    db: sqlite3.Database
    constructor() {
        const DB_FILE = 'xtask.db'
        writeFileSync(fullpath(DB_FILE), '', { flag: 'a+' }) //todo
        this.db = new sqlite3.Database(fullpath(DB_FILE))
        this.db.exec(`
            create table if not exists xtask (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                timeLimit INT NOT NULL,
                memoryLimit INT NOT NULL,
                interactive BOOLEAN NOT NULL,
                files BLOB NOT NULL,
                url TEXT,
                ctime INT NOT NULL,
                mtime INT NOT NULL,
                stash INT NOT NULL, -- 0: db, 1: stash, 2: current
                result INT NOT NULL -- 0: untried, 1: passed, 2: failed, 3: star
            );
	    `)
    }
    async get(sql: string, params?: any) {
        return new Promise<any>((resolve, reject) => {
            this.db.get(sql, params, (err, row) => {
                if (err) reject(err);
                resolve(row)
            })
        })
    }
    async all(sql: string, params?: any) {
        return new Promise<any>((resolve, reject) => {
            this.db.all(sql, params, (err, rows) => {
                if (err) reject(err);
                resolve(rows)
                // resolve(Array.isArray(rows) ? rows : [rows])
            })
        })
    }
    async run(sql: string, params?: any) {
        return new Promise<void>((resolve, reject) => {
            this.db.run(sql, params == undefined ? [] : params, (err) => {
                if (err) reject(err)
                resolve()
            })
        })
    }
}
export const db = new DB();

export async function get_current() {
    return await db.get('select * from xtask where stash=2 LIMIT 1')
}

export async function create_xtask(dat: any) {
	const exist = await db.get('select id from xtask where name=? and description=?', [dat.name, dat.group])
	let code = 0
    if (!exist) {
        let files = {
            [conf.solver.basename]: conf.solver.template,
            [conf.tests.basename]: JSON.stringify(
                (dat.tests as any[]).map(e => ({
                    input: e.input,
                    expect: e.output,
                    actual: '',
                    selected: true,
                    cpu: -1,
                    mem: -1,
                    result: 'N/A',
                    source: '',
                })),
                null,
                4
            )
        }
        db.run(`insert into xtask (name,description,files,timeLimit,memoryLimit,interactive,ctime,mtime,stash,result) values (?,?,?,?,?,?,?,?,?,?)`, [
            dat.name,
            dat.group,
            Buffer.from(JSON.stringify(files)),
            dat.timeLimit,
            dat.memoryLimit,
            dat.interactive,
            Date.now(),
            Date.now(),
            1,
            0,
        ])
    } else {
        code = 1
    }
	return {code: code, name: dat.name}
}

function open_file(filename: string) {
    vscode.workspace.openTextDocument(filename).then(doc => { vscode.window.showTextDocument(doc) }).then(undefined, err => { console.log(err) })
}
export async function work_xtask(id: number) {
    await vscode.commands.executeCommand('workbench.action.closeAllEditors').then(async () => {
        const current = await get_current()
        if (current != undefined && id == current.id) {
            open_file(conf.solver.fullname)
        } else {
            if (current != undefined) {
                let files: any = JSON.parse(current.files.toString())
                let mtime = current.mtime
                for (let file of [conf.solver, conf.tests, conf.generator, conf.comparator, conf.jurger]) 
                    try {
                        let newcontent = readFileSync(file.fullname, { encoding: 'utf-8' })
                        let oldcontent = files[file.basename]
                        if (oldcontent != newcontent) {
                            mtime = Date.now()
                            files[file.basename] = newcontent
                        }
                        fs.unlinkSync(file.fullname)
                    } catch (e) {
                    }
                await db.run('update xtask set files=?, mtime=?, stash=1 where id=?', [
                    Buffer.from(JSON.stringify(files)),
                    mtime,
                    current.id,
                ])
            }
            const xtask = await db.get('select * from xtask where id=?', [id])
            const files: any = JSON.parse(xtask.files.toString())
            Object.entries(files).reverse().forEach(([filename, content]) => { //todo
                writeFileSync(fullpath(filename), content as string)
            })
            await db.run('update xtask set stash=2 where id=?', [
                id,
            ])
            open_file(conf.solver.fullname)
            console.log((await get_current()).name)
        }
    })
}

export async function archive_xtask(id: number) {
    await db.run('update xtask set stash=0 where id=?', [id])
}
export async function stash_xtask(id: number) {
    await db.run('update xtask set stash=1 where id=?', [id])
}
export async function change_xtask_result(id: number) {
    const xtask = await db.get('select id, result from xtask where id=?', [id])
    console.log(xtask, (xtask.result + 1) % 4)
    await db.run('update xtask set result=? where id=?', [(xtask.result + 1) % 4, id]) //todo
}

export async function delete_xtask(id: number) {
    const current = await get_current()
	if (current != undefined && id == current.id) {
        await vscode.commands.executeCommand('workbench.action.closeAllEditors').then(() => {
            let files = JSON.parse(current.files.toString())
            Object.keys(files).forEach(filename => {
                fs.unlinkSync(fullpath(filename))
            })
        })
	}
	return await db.run('delete from xtask where id=?', [id])
}


export async function build_xtask() : Promise<number | undefined> {
    let current = await get_current()
    const execution = await vscode.tasks.executeTask(new vscode.Task(
        { type: 'shell'},
        vscode.TaskScope.Workspace,
        current.name,
        'XTask',
        new vscode.ShellExecution(conf.build)
    ));
    return new Promise<number | undefined>(resolve => {
        let disposable = vscode.tasks.onDidEndTaskProcess(e => {
            if (e.execution === execution) {
                disposable.dispose();
                resolve(e.exitCode);
            }
        });
    });
    // return await runxtaskcmd(build_cmd, 'Build XTask')
}

// export async function run_manually() {
//     const build_retcode = await build_xtask()
//     if (build_retcode) return
//     let current = await get_current()
//     const execution = await vscode.tasks.executeTask(new vscode.Task(
//         { type: 'shell'},
//         vscode.TaskScope.Workspace,
//         current.name,
//         'XTask',
//         new vscode.ShellExecution(conf.solver.command)
//     ));
//     return new Promise<number | undefined>(resolve => {
//         let disposable = vscode.tasks.onDidEndTaskProcess(e => {
//             if (e.execution === execution) {
//                 disposable.dispose();
//                 resolve(e.exitCode);
//             }
//         });
//     });
// }
export async function run_manually() {
    const build_retcode = await build_xtask()
    if (build_retcode) return
    let current = await get_current()
    const solcmd = conf.solver.command
    let cpu = 0
    let mem = 0
    let logger = new Logger(solcmd)
    logger.show()
    logger.clear()
    const sol = subprocess.spawn(solcmd, { shell: true, cwd: vscode.workspace.workspaceFolders![0].uri.fsPath });
    let canceled = false
    sol.stdout.on('data', (dat) => {
        logger.info('ACTUAL', dat)
        pidusage(sol.pid!, (err: any, stats: any) => {
            console.log(stats)
            cpu = stats.elapsed
            mem = Math.max(mem, stats.memory / 1024 / 1024)
        })
    })
    sol.stderr.on('data', (dat) => {
        logger.info('STDERR', dat)
    });
    try {
    } catch (e) { }
    let quickinput = vscode.window.createInputBox()
    quickinput.busy = true
    quickinput.ignoreFocusOut = true
    quickinput.placeholder = 'Stdin'
    // quickinput.buttons = [
    //     {iconPath: new vscode.ThemeIcon('debug-stop'), tooltip: 'Stop'},
    //     // {iconPath: new vscode.ThemeIcon('debug-restart'), tooltip: 'Restart'},
    // ]
    // quickinput.onDidTriggerButton(async e => {
    //     switch (e.tooltip) {
    //         case 'Stop':
    //             canceled = true
    //             sol.kill()
    //             quickinput.dispose()
    //             break
    //         // case 'Restart':
    //         //     await vscode.commands.executeCommand('xtask.testx.manually')
    //         //     break
    //     }
    // })
    quickinput.onDidAccept(() => {
        let stdin = quickinput.value
        logger.info('INPUT', stdin)
        sol.stdin.write(stdin)
        sol.stdin.write(' ')
        quickinput.value = ''
    })
    quickinput.onDidHide(() => {
        canceled = true
        if (!sol.killed) sol.kill()
        quickinput.dispose()
    })
    quickinput.show()
    return new Promise<any>(resolve => {
        sol.on('close', code => {
            if (canceled) {
                logger.info('VERDICT', `Cancelled in ${cpu} ms and ${mem} mb !`)
            } else if (code! > 0) {
                logger.info('VERDICT', `Solver exited with code ${code} != 0 !`)
            // } else if (cpu > current.timeLimit) {
            //     logger.info('VERDICT', `TLE: ${cpu} > ${current.timeLimit} ms !`)
            } else if (mem > current.memoryLimit) {
                logger.info('VERDICT', `MLE: ${mem} > ${current.memoryLimit} ms !`)
            } else {
                logger.info('VERDICT', `Passed in ${cpu} ms and ${mem} mb !`)
            }
            quickinput.hide()
            resolve(code)
        })
    })
}

const outputChannel = vscode.window.createOutputChannel('XTask', 'log')

class Logger {
    testid: any
    counter: Map<string, number>

    constructor(testid: any) {
        this.testid = testid
        this.counter = new Map()
    }

    show() { outputChannel.show() }

    clear() { outputChannel.replace('') }

    private getcnt(key: string) {
        this.counter.set(key, this.counter.has(key) ? this.counter.get(key)! + 1 : 1)
        return this.counter.get(key)
    }

    info(edge: string | null, dat? : any) {
        if (edge == null) {
            if (dat != undefined && dat.length > 0) outputChannel.appendLine(dat)
        } else {
            outputChannel.appendLine(`--- Test #${this.testid} - ${edge} - #${this.getcnt(edge)} ---`)
            if (dat != undefined && dat.length > 0) outputChannel.appendLine(dat.toString())
        }
    }

    
}

function visualize(input: string) {
    const viz = subprocess.spawn(conf.visualizer.command, { shell: true, cwd: vscode.workspace.workspaceFolders![0].uri.fsPath });
    viz.stdin.write(input)
    let path = ''
    viz.stdout.on('data', (dat) => path += dat)
    return new Promise<string>(resolve => {
        viz.on('close', code => resolve(path))
    })
}

function compare_tokens(expect: string, actual: string) : number {
    let s1 = expect.split(/\s/).filter(c => c != '')
    let s2 = actual.split(/\s/).filter(c => c != '')
    if (s1.length != s2.length) return -1
    let res = 0
    s1.forEach((c1, i) => {
        let c2 = s2[i]
        res += c1 == c2 ? 0 : 1
    })
    return res
}
export async function run_testcases() {
    const build_retcode = await build_xtask()
    if (build_retcode) return
    if (!conf.tests.check()) return
    let current = await get_current()
    const solcmd = conf.solver.command
    await vscode.window.withProgress({ //todo await a then ?
        location: vscode.ProgressLocation.Notification,
        title: `${current.name} - Test Cases`,
        cancellable: true
    }, (progress, token) => {
        progress.report({ increment: 0});
        let cancelled = false
        let fails = 0
        writeFileSync(conf.debuginput.fullname, '')
        return Promise.all(get_tests().map(async (test, i) => {
            let logger = new Logger(i + 1)
            if (i == 0) logger.clear()
            logger.show()
            if (!test.selected) {
                logger.info('SKIPPED')
                return test
            }
            if (cancelled) {
                logger.info("Cancelled")
                return test
            }
            test.actual = ''
            test.cpu = 0
            test.mem = 0
            const sol = subprocess.spawn(solcmd, { shell: true, cwd: vscode.workspace.workspaceFolders![0].uri.fsPath });
            token.onCancellationRequested(e => {
                cancelled = true
                sol.kill()
            })
            sol.stdout.on('data', (dat) => {
                test.actual += dat //todo
                logger.info('ACTUAL', dat)
                pidusage(sol.pid!, (err: any, stats: any) => {
                    console.log(stats)
                    test.cpu = stats.elapsed
                    test.mem = Math.max(test.mem, stats.memory / 1024 / 1024)
                })
            })
            sol.stderr.on('data', (dat) => {
                logger.info('STDERR', dat)
            });
            try {
            } catch (e) {}
            await new Promise<any>(resolve => {
                pidusage(sol.pid!, (err, stats) => {
                    test.cpu = stats.elapsed
                    test.mem = stats.memory / 1024 / 1024
                })
                sol.on('close', async (code) => {
                    progress.report({ increment: i });
                    if (cancelled) {
                        logger.info('VERDICT', `Cancelled in ${test.cpu} ms and ${test.mem} mb !`)
                    } else if (code != 0) {
                        test.result = 'RE'
                        logger.info('VERDICT', `Solver exited with code ${code} != 0 !`)
                    } else {
                        let res = compare_tokens(test.expect, test.actual)
                        if (res < 0) {
                            test.result = 'WA'
                            logger.info('VERDICT', `WA: length mismatched !`)
                        } else if (res > 0) {
                            test.result = 'WA'
                            logger.info('VERDICT', `WA: ${res} tokens mismatched !`)
                        } else if (test.cpu > current.timeLimit) {
                            test.result = 'TLE'
                            logger.info('VERDICT', `TLE: ${test.cpu} > ${current.timeLimit} ms !`)
                        } else if (test.mem > current.memoryLimit) {
                            test.result = 'MLE'
                            logger.info('VERDICT', `MLE: ${test.mem} > ${current.memoryLimit} ms !`)
                        } else {
                            test.result = 'AC'
                            logger.info('VERDICT', `Passed in ${test.cpu} ms and ${test.mem} mb !`)
                        }
                        if (test.result != 'AC') {
                            fails++
                            if (fails == 1) {
                                writeFileSync(conf.debuginput.fullname, test.input)
                            }
                            logger.info(null, await visualize(test.input))
                        }
                    }
                    resolve(test)
                });
                sol.stdin.write(test.input)
                logger.info('INPUT', test.input)
            })
            return test
        })).then(async tests => {
            set_tests(tests)
            new Logger('').info(null, fails > 0 ? 'Some testscases Failed !' : 'All testcases Passed !')
            progress.report({increment: 100})
            await vscode.commands.executeCommand("xtask.listtestcases")
        })
    })
}

export async function run_customjurger_with_testcaseinputs() {
    const build_retcode = await build_xtask()
    if (build_retcode) return
    if (!conf.tests.check()) return
    if (!conf.jurger.check()) return
    const current = await get_current()
    const solcmd = conf.solver.command
    const jrgcmd = conf.jurger.command
    const outputChannel = vscode.window.createOutputChannel('XTask', 'log')
    outputChannel.show()
    outputChannel.replace('')
    await vscode.window.withProgress({ //todo await a then ?
        location: vscode.ProgressLocation.Notification,
        title: `${current.name} - TestKs Inputs (${conf.generator.basename}) + Custom Jurger (${conf.jurger.basename})`,
        cancellable: true
    }, (progress, token) => {
        progress.report({ increment: 0});
        let cancelled = false
        return Promise.all(get_tests().map(async (test, i) => {
            let logger = new Logger(i)
            logger.show()
            if (!test.selected) {
                logger.info('SKIPPED')
                return test
            }
            if (cancelled) {
                logger.info("Cancelled")
                return test
            }
            let sol = subprocess.spawn(solcmd, { shell: true, cwd: vscode.workspace.workspaceFolders![0].uri.fsPath });
            let jrg = subprocess.spawn(jrgcmd, { shell: true, cwd: vscode.workspace.workspaceFolders![0].uri.fsPath });
            token.onCancellationRequested(e => {
                cancelled = true
                jrg.kill()
                sol.kill()
            })
            logger.info('Tests Input -> JRG', test.input)
            sol.stdout.on('data', (dat) => {
                jrg.stdin.write(dat)
                logger.info('SOL -> JRG', dat)
            })
            sol.stderr.on('data', (dat) => {
                logger.info('SOL STDERR', dat)
            });
            jrg.stdout.on('data', (dat) => {
                sol.stdin.write(dat)
                logger.info('JRG -> SOL', dat)
            })
            jrg.stderr.on('data', (dat) => {
                logger.info('JRG STDERR', dat)
            });
            let jrgpromise = new Promise<any>(resolve => {
                jrg.on('close', (code) => {
                    resolve(code)
                });
                jrg.stdin.write(test.input)
            })
            let solpromise = new Promise<any>(resolve => {
                sol.on('close', (code) => {
                    resolve(code)
                });
            })
            try {
                pidusage(sol.pid!, (err, stats) => {
                    test.cpu = stats.elapsed
                    test.mem = stats.memory / 1024 / 1024
                })
            } catch (e) { }
            await Promise.all([solpromise, jrgpromise]).then(codes => {
                progress.report({ increment: i });
                if (cancelled) {
                    logger.info("Cancelled")
                } else if (codes[0] != 0) {
                    test.result = 'RE'
                    logger.info('VERDICT', 'RE: Generator exited with code ${codes[2]} != 0 !')
                } else if (test.cpu > current.timeLimit) {
                    test.result = 'TLE'
                    logger.info('VERDICT', `TLE: ${test.cpu} > ${current.timeLimit} ms !`)
                } else if (test.mem > current.memoryLimit) {
                    test.result = 'MLE'
                    logger.info('VERDICT', `MLE: ${test.mem} > ${current.memoryLimit} ms !`)
                } else if (codes[1] != 0) {
                    test.result = 'WA'
                    logger.info('VERDICT', `WA: solution finishing with exit code 0 (without exceeding time or memory limits) and a judge finishing with exit code other than 0 (${codes[1]}) would be interpreted as a Wrong Answer (or query limit exceeded) in the system !`)
                } else {
                    logger.info("AC")
                    test.result = 'AC'
                }
            })
            return test
        })).then(tests => {
            set_tests(tests)
            progress.report({ increment: 100, message: `${tests.filter(test => test.result != 'AC').length > 0 ? 'All testcases passed !' : 'Some testcase(s) failed !'}` });
        })
    })
}

export async function run_randominputs() {
    const build_retcode = await build_xtask()
    if (build_retcode) return
    if (!conf.generator.check()) return
    const current = await get_current()
    const solcmd = conf.solver.command
    const gencmd = conf.generator.command
    const outputChannel = vscode.window.createOutputChannel('XTask', 'log')
    outputChannel.show()
    await vscode.window.withProgress({ //todo await a then ?
        location: vscode.ProgressLocation.Notification,
        title: "Running Bruteforce ...",
        cancellable: true
    }, (progress, token) => {
        progress.report({ increment: 0});
        return new Promise<void>(async resolve => {
            let test: any = {
                input: '',
                actual: '',
                expect: '',
                selected: true,
                cpu: -1,
                mem: -1,
                source: 'C',
                result: 'N/A',
            }
            let i = 0
            while (true) {
                outputChannel.replace('')
                i++
                test.input = ''
                test.actual = ''
                let sol = subprocess.spawn(solcmd, { shell: true, cwd: vscode.workspace.workspaceFolders![0].uri.fsPath });
                let gen = subprocess.spawn(gencmd, { shell: true, cwd: vscode.workspace.workspaceFolders![0].uri.fsPath });
                let cancelled = false
                token.onCancellationRequested(e => {
                    cancelled = true
                    gen.kill()
                    sol.kill()
                })
                gen.stdout.on('data', (dat) => {
                    test.input += dat
                    sol.stdin.write(dat)
                    outputChannel.appendLine('Generated Input Chunk:')
                    outputChannel.appendLine(dat)
                })
                gen.stderr.on('data', (dat) => {
                    outputChannel.appendLine('Generated Stderr:')
                    outputChannel.append(dat.toString())
                });
                sol.stdout.on('data', (dat) => {
                    test.actual += dat
                    outputChannel.appendLine('Solver Output Chunk:')
                    outputChannel.appendLine(dat)
                })
                sol.stderr.on('data', (dat) => {
                    outputChannel.appendLine('Solver Stderr:')
                    outputChannel.append(dat.toString())
                    console.log(dat)
                    console.log(dat.toString())
                });
                try {
                    pidusage(sol.pid!, (err, stats) => {
                        test.cpu = stats.elapsed
                        test.mem = stats.memory / 1024 / 1024
                    })
                } catch (e) { }
                let lastOk = await Promise.all([
                    new Promise<number | null>(resolve => { gen.on('close', code => resolve(code) )}),
                    new Promise<number | null>(resolve => { sol.on('close', code => resolve(code) )}),
                ]).then((codes: any[]) => {
                    progress.report({ increment: i, message: `${i}`});
                    if (codes.filter(code => code != 0).length > 0) {
                        test.result = 'RE'
                    } else if (test.cpu > current.timeLimit) {
                        test.result = 'TLE'
                    } else if (test.mem > current.memoryLimit) {
                        test.result = 'MLE'
                    } else {
                        test.result = 'AC'
                    }
                    return test.result == 'AC'
                })
                if (cancelled) {
                    outputChannel.appendLine("Cancelled !")
                    resolve()
                    break
                }
                if (!lastOk) {
                    outputChannel.appendLine('')
                    outputChannel.append(`Testcase #${i} ERROR : `)
                    switch (test.result) {
                        case 'TLE':
                            outputChannel.appendLine(`TLE ${test.cpu} > ${current.timeLimit} ms.`)
                            break;
                        case 'MLE':
                            outputChannel.appendLine(`MLE ${test.mem} > ${current.memoryLimit} ms.`)
                            break;
                        case 'RE':
                            outputChannel.appendLine(`Runtime Error.`)
                            break;
                    }
                    outputChannel.appendLine('Input:')
                    outputChannel.appendLine(test.input)
                    vscode.window.showErrorMessage(`Found a ${test.result} counter sample !`, 'Add to test cases').then(selection => {
                        switch (selection) {
                            case 'Add to test cases':
                                let tests = get_tests()
                                tests.push(test)
                                set_tests(tests)
                                break;
                        }
                    })
                    resolve();
                    break
                }
            }
        })
    })
}

export async function run_comparator_with_randominputs() {
    const build_retcode = await build_xtask()
    if (build_retcode) return
    if (!conf.generator.check()) return
    if (!conf.comparator.check()) return
    const current = await get_current()
    const solcmd = conf.solver.command
    const gencmd = conf.generator.command
    const cmpcmd = conf.comparator.command
    const outputChannel = vscode.window.createOutputChannel('XTask', 'log')
    outputChannel.show()
    await vscode.window.withProgress({ //todo await a then ?
        location: vscode.ProgressLocation.Notification,
        title: "Running Bruteforce ...",
        cancellable: true
    }, (progress, token) => {
        progress.report({ increment: 0});
        return new Promise<void>(async resolve => {
            let test: any = {
                input: '',
                actual: '',
                expect: '',
                selected: true,
                cpu: -1,
                mem: -1,
                source: 'C',
                result: 'N/A',
            }
            let i = 0
            while (true) {
                let logger = new Logger(i)
                logger.clear()
                i++
                test.input = ''
                test.actual = ''
                let gen = subprocess.spawn(gencmd, { shell: true, cwd: vscode.workspace.workspaceFolders![0].uri.fsPath });
                let sol = subprocess.spawn(solcmd, { shell: true, cwd: vscode.workspace.workspaceFolders![0].uri.fsPath });
                let cmp = subprocess.spawn(cmpcmd, { shell: true, cwd: vscode.workspace.workspaceFolders![0].uri.fsPath });
                let cancelled = false
                token.onCancellationRequested(e => {
                    cancelled = true
                    gen.kill()
                    sol.kill()
                    cmp.kill()
                })
                gen.stdout.on('data', (dat) => {
                    test.input += dat
                    sol.stdin.write(dat)
                    cmp.stdin.write(dat)
                    logger.info('GEN INPUT', dat)
                })
                gen.stderr.on('data', (dat) => {
                    logger.info('GEN STDERR', dat)
                });
                sol.stdout.on('data', (dat) => {
                    test.actual += dat
                    logger.info('ACTUAL', dat)
                })
                sol.stderr.on('data', (dat) => {
                    logger.info('SOL STDERR', dat)
                });
                cmp.stdout.on('data', (dat) => {
                    test.expect += dat
                    logger.info('EXPECT', dat)
                })
                cmp.stderr.on('data', (dat) => {
                    logger.info('SOL STDERR', dat)
                });
                try {
                    pidusage(sol.pid!, (err, stats) => {
                        test.cpu = stats.elapsed
                        test.mem = stats.memory / 1024 / 1024
                    })
                } catch (e) { }
                let lastOk = await Promise.all([
                    new Promise<number | null>(resolve => { gen.on('close', code => resolve(code) )}),
                    new Promise<number | null>(resolve => { sol.on('close', code => resolve(code) )}),
                    new Promise<number | null>(resolve => { cmp.on('close', code => resolve(code) )}),
                ]).then((codes: any[]) => {
                    progress.report({ increment: i, message: `${i}`});
                    if (cancelled) {
                        logger.info("Cancelled")
                    } else if (codes[0] != 0) {
                        test.result = 'RE'
                        logger.info('VERDICT', `RE: Generator exit with ${codes[0]} !`)
                    } else if (codes[1] != 0) {
                        test.result = 'RE'
                        logger.info('VERDICT', `RE: Solver exit with ${codes[1]} !`)
                    } else if (codes[2] != 0) {
                        test.result = 'RE'
                        logger.info('VERDICT', `RE: Comparator exit with ${codes[2]} !`)
                    } else if (test.cpu > current.timeLimit) {
                        test.result = 'TLE'
                        logger.info('VERDICT', `TLE ${test.cpu} > ${current.timeLimit} ms.`)
                    } else if (test.mem > current.memoryLimit) {
                        test.result = 'MLE'
                        logger.info('VERDICT', `MLE ${test.mem} > ${current.memoryLimit} ms.`)
                    } else {
                        let res = compare_tokens(test.expect, test.actual)
                        if (res == 0) {
                            test.result = 'AC'
                            logger.info('AC')
                        } else if (res < 0) {
                            test.result = 'WA'
                            logger.info('VERDICT', `WA: length mismatched !`)
                        } else {
                            test.result = 'WA'
                            logger.info('VERDICT', `WA: ${res} tokens mismatched !`)
                        }
                    }
                    return test.result == 'AC'
                })
                if (cancelled) {
                    resolve()
                    break
                }
                if (!lastOk) {
                    vscode.window.showErrorMessage(`Found a ${test.result} counter sample !`, 'Add to test cases').then(selection => {
                        switch (selection) {
                            case 'Add to test cases':
                                let tests = get_tests()
                                tests.push(test)
                                set_tests(tests)
                                break;
                        }
                    })
                    resolve();
                    break
                }
            }
        })
    })
}

export async function run_customjurger_with_randominputs() {
    const build_retcode = await build_xtask()
    if (build_retcode) return
    if (!conf.generator.check()) return
    if (!conf.jurger.check()) return
    const current = await get_current()
    const solcmd = conf.solver.command
    const gencmd = conf.generator.command
    const jrgcmd = conf.jurger.command
    const outputChannel = vscode.window.createOutputChannel('XTask', 'log')
    outputChannel.show()
    function log_solstdout(dat: any) {
        outputChannel.appendLine(`Query: ${dat}`)
    }
    await vscode.window.withProgress({ //todo await a then ?
        location: vscode.ProgressLocation.Notification,
        title: `${current.name} - Random Inputs (${conf.generator.basename}) + Custom Jurger (${conf.jurger.basename})`,
        cancellable: true
    }, (progress, token) => {
        progress.report({ increment: 0});
        return new Promise<void>(async resolve => {
            let test: any = {
                input: '',
                actual: '',
                expect: '',
                selected: true,
                cpu: -1,
                mem: -1,
                source: 'C',
                result: 'N/A',
            }
            let i = 0
            while (true) {
                outputChannel.replace('')
                i++
                test.input = ''
                test.actual = ''
                let gen = subprocess.spawn(gencmd, { shell: true, cwd: vscode.workspace.workspaceFolders![0].uri.fsPath });
                let sol = subprocess.spawn(solcmd, { shell: true, cwd: vscode.workspace.workspaceFolders![0].uri.fsPath });
                let jrg = subprocess.spawn(jrgcmd, { shell: true, cwd: vscode.workspace.workspaceFolders![0].uri.fsPath });
                let cancelled = false
                token.onCancellationRequested(e => {
                    cancelled = true
                    gen.kill()
                    jrg.kill()
                    sol.kill()
                })
                gen.stdout.on('data', (dat) => {
                    jrg.stdin.write(dat)
                    test.input += dat
                    outputChannel.appendLine(`Query: ${dat}`)
                })
                gen.stderr.on('data', (dat) => {
                    outputChannel.appendLine(`Generator Stderr: ${dat}`)
                });
                sol.stdout.on('data', (dat) => {
                    jrg.stdin.write(dat)
                    outputChannel.appendLine(`Query: ${dat}`)
                })
                sol.stderr.on('data', (dat) => {
                    outputChannel.appendLine(`Solver Stderr: ${dat}`)
                });
                jrg.stdout.on('data', (dat) => {
                    sol.stdin.write(dat)
                    outputChannel.appendLine(`Reply: ${dat}`)
                })
                jrg.stderr.on('data', (dat) => {
                    outputChannel.appendLine(`Verdict: ${dat}`)
                });
                try {
                    pidusage(sol.pid!, (err, stats) => {
                        test.cpu = stats.elapsed
                        test.mem = stats.memory / 1024 / 1024
                    })
                } catch (e) { }
                let lastOk = await Promise.all([
                    new Promise<number | null>(resolve => { gen.on('close', code => resolve(code) )}),
                    new Promise<number | null>(resolve => { jrg.on('close', code => resolve(code) )}),
                    new Promise<number | null>(resolve => { sol.on('close', code => resolve(code) )}),
                ]).then((codes: any[]) => {
                    outputChannel.appendLine('')
                    outputChannel.append(`Testcase #${i} Verdict : `)
                    progress.report({ increment: i, message: `${i}`});
                    if (cancelled) {
                        outputChannel.appendLine("Cancelled !")
                    } else if (codes[0] != 0) {
                        test.result = 'RE'
                        outputChannel.appendLine(`RE: Generator exited with code ${codes[0]} != 0 !`)
                    } else if (codes[1] != 0) {
                        test.result = 'RE'
                        outputChannel.appendLine(`RE: Solver exited with code ${codes[1]} != 0 !`)
                    } else if (test.cpu > current.timeLimit) {
                        test.result = 'TLE'
                        outputChannel.appendLine(`TLE: ${test.cpu} > ${current.timeLimit} ms !`)
                    } else if (test.mem > current.memoryLimit) {
                        test.result = 'MLE'
                        outputChannel.appendLine(`MLE: ${test.mem} > ${current.memoryLimit} ms !`)
                    } else if (codes[1] != 0) {
                        test.result = 'WA'
                        outputChannel.appendLine(`WA: solution finishing with exit code 0 (without exceeding time or memory limits) and a judge finishing with exit code other than 0 (${codes[2]}) would be interpreted as a Wrong Answer (or query limit exceeded) in the system !`)
                    } else {
                        outputChannel.appendLine("AC !")
                        test.result = 'AC'
                    }
                    return test.result == 'AC'
                })
                if (cancelled) {
                    outputChannel.appendLine("Cancelled !")
                    resolve()
                    break
                }
                if (!lastOk) {
                    vscode.window.showErrorMessage(`Found a ${test.result} counter sample !`, 'Add to test cases').then(selection => {
                        switch (selection) {
                            case 'Add to test cases':
                                let tests = get_tests()
                                tests.push(test)
                                set_tests(tests)
                                break;
                        }
                    })
                    resolve();
                    break
                }
            }
        })
    })
}

        

