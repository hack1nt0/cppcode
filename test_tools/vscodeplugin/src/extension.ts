// The module 'vscode' contains the VS Code extensibility API
// Import the module and reference it with the alias vscode in your code below
import * as vscode from 'vscode';
import { window, commands, ExtensionContext } from 'vscode';
import * as http from 'node:http';
import * as xtasks from './xtasks';
import * as subprocess from 'node:child_process';


// 创建http server，并传入回调函数:
const server = http.createServer((request, response) => {
	if (request.method == 'POST') {
		var body = ''
		request.on('data', function(data) {
			body += data
		})
		request.on('end', async () => {
			const result = await xtasks.create_xtask(JSON.parse(body))
			if (!result) return
			var msg = ''
			if (result.code == 0) msg = `New Task: ${result.name}`
			if (result.code == 1) msg = `Duplicated Task: ${result.name}`
			window.showInformationMessage(msg);
			response.writeHead(200, { 'Content-Type': 'text/html' })
			response.end('post received')
		})
	}
});

// 出错时返回400:
server.on('clientError', (err, socket) => {
  socket.end('HTTP/1.1 400 Bad Request\r\n\r\n');
});

const port = 12345
server.listen(port);
window.showInformationMessage(`xtask Server is running at http://127.0.0.1:${port}/`);


const taskData = new WeakMap<vscode.QuickPickItem, number>();

// This method is called when your extension is activated
// Your extension is activated the very first time the command is executed
export async function activate(context: vscode.ExtensionContext) {

	// Use the console to output diagnostic information (console.log) and errors (console.error)
	// This line of code will only be executed once when your extension is activated
	console.log('Congratulations, your extension "xtask" is now active!');

	class XTaskButton implements vscode.QuickInputButton {
		iconPath: vscode.IconPath;
		tooltip?: string | undefined;
		constructor(label: string) {
			switch (label) {
				case 'Check':
					this.iconPath = new vscode.ThemeIcon('check')
					break;
				case 'Archive':
					this.iconPath = new vscode.ThemeIcon('arrow-down')
					break;
				case 'Stash':
					this.iconPath = new vscode.ThemeIcon('arrow-up')
					break;
				case 'Delete':
					this.iconPath = new vscode.ThemeIcon('trash')
					break;
				case 'New':
					this.iconPath = new vscode.ThemeIcon('new-file')
					break;
				case 'Load':
					this.iconPath = new vscode.ThemeIcon('database')
					break;
				default:
					this.iconPath = new vscode.ThemeIcon('?')
					break;
			}
			this.tooltip = label
		}
	}
	class XTaskItem implements vscode.QuickPickItem {
		label: string;
		iconPath?: vscode.IconPath | undefined;
		buttons?: readonly vscode.QuickInputButton[] | undefined;
		detail?: string | undefined;
		constructor(task: any) {
			this.label = task.name
			switch (task.result) {
				case 1:
					this.iconPath = new vscode.ThemeIcon('check', new vscode.ThemeColor('successIcon.foreground'))
					break;
				case 2:
					this.iconPath = new vscode.ThemeIcon('close', new vscode.ThemeColor('errorIcon.foreground'))
					break;
				case 3:
					this.iconPath = new vscode.ThemeIcon('star', new vscode.ThemeColor('starIcon.foreground'))
					break;
				default:
					this.iconPath = undefined
					break;
			}
			this.detail = `Group: ${task.description}, CTime: ${new Date(task.ctime).toLocaleString()}`
			switch (task.stash) {
				case 0:
					this.buttons = [new XTaskButton('Check'), new XTaskButton('Stash'), new XTaskButton('Delete')]
					break
				default:
					this.buttons = [new XTaskButton('Check'), new XTaskButton('Archive'), new XTaskButton('Delete')]
					break
			}
		}
	};

	context.subscriptions.push(vscode.commands.registerCommand('xtask.list', async () => {
		const quickPick = window.createQuickPick();
		quickPick.title = `XTasks`;
		quickPick.placeholder = `Select or change working task`;
		quickPick.ignoreFocusOut = true;
		async function get_current_task() : Promise<any | undefined>{
			let task = await xtasks.get_current()
			if (task == undefined) return undefined
			else {
				let item = new XTaskItem(task)
				taskData.set(item, task.id);
				return item
			}
		}
		async function get_stash_tasks() : Promise<[any]>{
			return (await xtasks.db.all('SELECT * FROM xtask WHERE stash == 1 order by name')).map((task: { id: number; }) => {
				let item = new XTaskItem(task)
				taskData.set(item, task.id);
				return item
			})
		}
		async function get_archive_tasks(): Promise<[any]> {
			return (await xtasks.db.all('SELECT * FROM xtask WHERE stash == 0 order by name')).map((task: { id: number; }) => {
				let item = new XTaskItem(task)
				taskData.set(item, task.id);
				return item
			})
		}
		let load_archive = false
		async function get_items() {
				// let ret = [{label: 'Working XTask', kind: vscode.QuickPickItemKind.Separator}]
				let ret = []
				let current = await get_current_task()
				if (current != undefined) ret.push(current)
				ret.push({ label: 'Stashed XTasks', kind: vscode.QuickPickItemKind.Separator })
				ret = ret.concat(await get_stash_tasks())
				ret.push({ label: 'Archived XTasks', kind: vscode.QuickPickItemKind.Separator })
				if (load_archive) ret = ret.concat(await get_archive_tasks())
				return ret
		}
		quickPick.items = await get_items()
		quickPick.buttons = [
			new XTaskButton('New'),
			new XTaskButton('Load'),
		]
		quickPick.onDidTriggerButton(async e => {
			switch (e.tooltip) {
				case 'New':
					let newtaskname = quickPick.value
					if (newtaskname == '') {
						quickPick.placeholder = 'Please input task name here ...'
						return
					}
					await xtasks.create_xtask({
						name: newtaskname,
						group: '',
						timeLimit: 1000,
						memoryLimit: 256,
						interactive: false,
						tests: [],
					})
					break
				case 'Load':
					load_archive = !load_archive
					break
			}
			quickPick.items = await get_items()
		})
		quickPick.onDidTriggerItemButton(async e => {
			const task = taskData.get(e.item)!
			switch (e.button.tooltip) {
				case 'Check':
					await xtasks.change_xtask_result(task)
					break;
				case 'Archive':
					await xtasks.archive_xtask(task)
					break;
				case 'Delete':
					const result = await vscode.window.showWarningMessage('Are you sure to delete the selected tasks?', { modal: true }, 'Yes', 'No')
					if (result === 'Yes') {
						await xtasks.delete_xtask(task)
					}
					break;
				case 'Stash':
					await xtasks.stash_xtask(task)
					break;
			}
			quickPick.items = await get_items()
		})
		// quickPick.onDidChangeSelection((selection) => {
		// 	console.log('change selection: ', selection)
		// })
		quickPick.onDidAccept(async () => {
			if (quickPick.selectedItems.length == 0) return
			const selection = quickPick.selectedItems[0]
			let id = taskData.get(selection)
			if (id == undefined) return
			await xtasks.work_xtask(id)
			quickPick.dispose()
		});
		quickPick.onDidHide(() => quickPick.dispose());
		// quickPick.selectedItems = quickPick.items.filter(async item => taskData.get(item) == (await xtasks.get_current()).id)
		quickPick.show();
	}));

	
	context.subscriptions.push(vscode.commands.registerCommand('xtask.test', async () => {
		let current = await xtasks.get_current()
		if (current == undefined) {
			return vscode.commands.executeCommand('xtask.list')
		}
		let terminal = vscode.window.terminals.filter(e => e.name == 'XTest')[0]
		if (terminal == undefined) {
			terminal = vscode.window.createTerminal('XTest')
		}
		terminal.show()
		if (current.interactive) {
			terminal.sendText(`${xtasks.conf.build} && ${xtasks.conf.run_manual}`)
		} else {
			terminal.sendText(`${xtasks.conf.build} && ${xtasks.conf.run_tests}`)
		}
	}))

	context.subscriptions.push(vscode.commands.registerCommand('xtask.testpanel', async () => {
		let current = await xtasks.get_current()
		if (current == undefined) {
			return vscode.commands.executeCommand('xtask.list')
		}
		let terminal = vscode.window.terminals.filter(e => e.name == 'XTest')[0]
		if (terminal == undefined) {
			terminal = vscode.window.createTerminal('XTest')
		}
		terminal.show()
		let quickPick = vscode.window.createQuickPick()
		if (!current.interactive) {
			quickPick.items = [
				{label: 'Manual'},
				{label: 'Tests', description: 'Run X_in* test files'},
				{label: 'Bruteforce/Compare', description: 'generator --> (input + answer) <-- comparator', detail: 'you need a custom generator and a custom comparator, and comparator == solver when no X_compare.* found !'},
				{label: 'Interactive Jurge', description: 'generator --> answer --> jurger <-> solver', detail: 'you need a custom jurger !'},
			]
		} else {
			quickPick.items = [
				{label: 'Manual'},
				{label: 'Interactive Jurge', description: 'generator --> answer --> jurger <-> solver', detail: 'you need a custom jurger !'}
			]
		}
		quickPick.onDidAccept(async () => {
			if (quickPick.selectedItems.length == 0) return
			const selection = quickPick.selectedItems[0]
			switch (selection.label) {
				case 'Manual':
					terminal.sendText(`${xtasks.conf.build} && ${xtasks.conf.run_manual}`)
					break
				case 'Tests':
					terminal.sendText(`${xtasks.conf.build} && ${xtasks.conf.run_tests}`)
					break
				case 'Bruteforce/Compare':
					if (!xtasks.conf.generator_template.check()) break
					if (!xtasks.conf.comparator_template.check()) break
					terminal.sendText(`${xtasks.conf.build} && ${xtasks.conf.run_compare}`)
					break
				default:
					if (!xtasks.conf.jurger_template.check()) break
					terminal.sendText(`${xtasks.conf.build} && ${xtasks.conf.run_jurger}`)
			}
			quickPick.dispose()
		});
		quickPick.onDidHide(() => quickPick.dispose());
		quickPick.show()
	}))
	

	context.subscriptions.push(vscode.commands.registerCommand('xtask.copy', async () => {
		let current = await xtasks.get_current()
		if (current == undefined) {
			return vscode.commands.executeCommand('xtask.list')
		}
		return new Promise(((resolve, reject) => {
			subprocess.exec(`${xtasks.conf.copy}`, { cwd: vscode.workspace.workspaceFolders![0].uri.fsPath }, (err, stdout, stderr) => {
				if (err) {
					vscode.window.showInformationMessage(`${err.message}`)
					reject(err)
				} else {
					vscode.env.clipboard.writeText(stdout).then(() => {
						vscode.window.showInformationMessage(`${stderr}\nCopied =_=`);
					})
					resolve(0)
				}
			})
		}))
	}))
	
};
	
	
// This method is called when your extension is deactivated
export function deactivate() { }
