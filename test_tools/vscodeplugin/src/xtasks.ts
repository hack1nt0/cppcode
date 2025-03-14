import * as vscode from 'vscode';
import * as path from 'path';
import * as fs from 'fs';
import { writeFile, writeFileSync, readFile, readFileSync, statSync, createWriteStream, read } from 'node:fs';
import * as sqlite3 from 'sqlite3'


export function fullpath(filename: string) {
	return path.join(vscode.workspace.workspaceFolders![0].uri.fsPath, filename)
}

class XTemplate {
    fullname : string
    basename : string
    template : string

    constructor(key: string, prefix: string) {
        let dirname = fullpath('')
        let templatebasename = vscode.workspace.getConfiguration(`xtask`).get<string>(key)!
        this.template = readFileSync(path.join(dirname, templatebasename), { encoding: 'utf-8' })
        let suffix = templatebasename.split('.')[1]
        this.basename = `${prefix}.${suffix}`
        this.fullname = path.join(dirname, this.basename)
    }
    
    check(): boolean {
        if (!fs.existsSync(this.fullname)) {
            writeFileSync(this.fullname, this.template)
            open_file(this.fullname)
            return false
        }
        return true
    }
}
class Conf {
    get solver_template() { return new XTemplate('solver_template', 'X') }
    get jurger_template() { return new XTemplate('jurger_template', 'X_jurger') }
    get generator_template() { return new XTemplate('generator_template', 'X_generator') }
    get comparator_template() { return new XTemplate('solver_template', 'X_comparator') }
    get build() { return vscode.workspace.getConfiguration(`xtask`).get<string>('build')! }
    get copy() { return vscode.workspace.getConfiguration(`xtask`).get<string>('copy')! }
    get run_manual() { return vscode.workspace.getConfiguration(`xtask`).get<string>('run_manual')! }
    get run_tests() { return vscode.workspace.getConfiguration(`xtask`).get<string>('run_tests')! }
    get run_compare() { return vscode.workspace.getConfiguration(`xtask`).get<string>('run_compare')! }
    get run_jurger() { return vscode.workspace.getConfiguration(`xtask`).get<string>('run_jurger')! }
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
            [conf.solver_template.basename]: conf.solver_template.template,
        }
        if (!dat.interactive) {
            dat.tests.forEach((e : any, i : number) => {
                files[`X_in${i}`] = e.input + '\n' + e.output
            });
        } else {
            files[conf.jurger_template.basename] = conf.jurger_template.template
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

export function open_file(filename: string) {
    vscode.workspace.openTextDocument(filename).then(doc => { vscode.window.showTextDocument(doc) }).then(undefined, err => { console.log(err) })
}

async function save_current_xtask() {
    const current = await get_current()
    if (current != undefined) {
        let files: any = JSON.parse(current.files.toString())
        let mtime = current.mtime
        for (let uri of await vscode.workspace.findFiles('X*')) {
            let fullname = uri.path
            let basename = path.basename(fullname)
            try {
                let newcontent = readFileSync(fullname, { encoding: 'utf-8' })
                let oldcontent = files[basename]
                if (oldcontent != newcontent) {
                    mtime = Date.now()
                    files[basename] = newcontent
                }
                fs.unlinkSync(fullname)
            } catch (e) {
            }
        }
        await db.run('update xtask set files=?, mtime=?, stash=1 where id=?', [
            Buffer.from(JSON.stringify(files)),
            mtime,
            current.id,
        ])
    }
}
export async function work_xtask(id: number) {
    await vscode.commands.executeCommand('workbench.action.closeAllEditors').then(async () => {
        const current = await get_current()
        if (current != undefined && id == current.id) {
            open_file(conf.solver_template.fullname)
        } else {
            await save_current_xtask()
            const xtask = await db.get('select * from xtask where id=?', [id])
            const files: any = JSON.parse(xtask.files.toString())
            Object.entries(files).reverse().forEach(([filename, content]) => { //todo
                writeFileSync(fullpath(filename), content as string)
            })
            await db.run('update xtask set stash=2 where id=?', [
                id,
            ])
            open_file(conf.solver_template.fullname)
            console.log((await get_current()).name)
        }
    })
}

export async function archive_xtask(id: number) {
    const current = await get_current()
    if (current != undefined && id == current.id) {
        await vscode.commands.executeCommand('workbench.action.closeAllEditors')
        await save_current_xtask()
    }
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


        

