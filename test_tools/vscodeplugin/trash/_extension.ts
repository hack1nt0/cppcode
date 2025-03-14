// The module 'vscode' contains the VS Code extensibility API
// Import the module and reference it with the alias vscode in your code below
import * as vscode from 'vscode';
import { window, commands, ExtensionContext } from 'vscode';
import * as http from 'node:http';
import * as xtasks from './xtasks';
import * as path from 'node:path';
import * as subprocess from 'node:child_process';
import { writeFileSync } from 'node:fs';


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
let xtaskStatusBarItem : vscode.StatusBarItem
let xtestStatusBarItem : vscode.StatusBarItem
async function updateStatusBarItems() {
	const current = await xtasks.get_current()
	if (current == undefined) {
		xtaskStatusBarItem.text = `[No XTask Woking]`
	} else {
		xtaskStatusBarItem.text = `[${current.name}]`
	}
	xtaskStatusBarItem.show()
}
// This method is called when your extension is activated
// Your extension is activated the very first time the command is executed
export async function activate(context: vscode.ExtensionContext) {

	// Use the console to output diagnostic information (console.log) and errors (console.error)
	// This line of code will only be executed once when your extension is activated
	console.log('Congratulations, your extension "xtask" is now active!');

	xtaskStatusBarItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Right, 1)
	xtestStatusBarItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Right, 0)
	xtaskStatusBarItem.tooltip = 'Current XTask'
	xtestStatusBarItem.tooltip = 'Run XTask'
	xtaskStatusBarItem.command = 'xtask.liststash'
	xtestStatusBarItem.command = 'xtask.testx'
	xtestStatusBarItem.text = '$(notebook-execute)'
	context.subscriptions.push(xtaskStatusBarItem)
	context.subscriptions.push(xtestStatusBarItem)
	await updateStatusBarItems()
	xtestStatusBarItem.show()

	class XTaskButton implements vscode.QuickInputButton {
		iconPath: vscode.IconPath;
		tooltip?: string | undefined;
		constructor(label: string) {
			switch (label) {
				case 'Check':
					this.iconPath = new vscode.ThemeIcon('check')
					break;
				case 'Archive':
					this.iconPath = new vscode.ThemeIcon('archive')
					break;
				case 'Stash':
					this.iconPath = new vscode.ThemeIcon('cloud-download')
					break;
				case 'Delete':
					this.iconPath = new vscode.ThemeIcon('trash')
					break;
				case 'New':
					this.iconPath = new vscode.ThemeIcon('new-file')
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
		constructor(task: any, db: boolean) {
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
			if (db) {
				this.detail = `Group: ${task.description}, CTime: ${new Date(task.ctime).toLocaleString()}`
				this.buttons = [new XTaskButton('Stash'), new XTaskButton('Delete')]
			} else {
				this.buttons = [new XTaskButton('Check'), new XTaskButton('Archive')]
			}
		}
	};

	context.subscriptions.push(vscode.commands.registerCommand('xtask.liststash', async () => {
		const quickPick = window.createQuickPick();
		quickPick.title = `[Xtask Stash]`;
		quickPick.placeholder = `Select and work by enter`;
		quickPick.ignoreFocusOut = true;
		async function get_items() {
			return (await xtasks.db.all('SELECT id, name, result FROM xtask WHERE stash != 0 order by name')).map((task: { id: number; }) => {
				let item = new XTaskItem(task, false)
				taskData.set(item, task.id);
				return item
			})
		}
		quickPick.items = await get_items()
		quickPick.buttons = [new XTaskButton('New')]
		quickPick.onDidTriggerButton(async e => {
			switch (e.tooltip) {
				case 'New':
					let newtaskname = quickPick.value
					await xtasks.create_xtask({
						name: newtaskname,
						group: '',
						timeLimit: 1000,
						memoryLimit: 256,
						interactive: false,
						tests: [],
					})
					break;
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
					await xtasks.delete_xtask(task)
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
			await xtasks.work_xtask(taskData.get(selection)!).then(updateStatusBarItems)
			quickPick.dispose()
		});
		quickPick.onDidHide(() => quickPick.dispose());
		// quickPick.selectedItems = quickPick.items.filter(async item => taskData.get(item) == (await xtasks.get_current()).id)
		quickPick.show();
	}));

	context.subscriptions.push(vscode.commands.registerCommand('xtask.listdb', async () => {
		const quickPick = window.createQuickPick()
		quickPick.title = `[XTask DB]`;
		quickPick.placeholder = 'Select and stash by enter, or delete by button';
		quickPick.canSelectMany = true
		async function get_xtasks() {
			return (await xtasks.db.all('SELECT id, name, description, result, ctime FROM xtask order by mtime desc')).map((task: { id: number; }) => {
				let item = new XTaskItem(task, true)
				taskData.set(item, task.id);
				return item
			})
		}
		quickPick.items = await get_xtasks()
		quickPick.buttons = [new XTaskButton('Stash'), new XTaskButton('Delete')]
		quickPick.onDidTriggerButton(async e => {
			switch (e.tooltip) {
				case 'Delete':
					const result = await vscode.window.showWarningMessage('Are you sure to delete the selected tasks?', { modal: true }, 'Yes', 'No')
					if (result === 'Yes') {
						await Promise.all(
							quickPick.selectedItems.map(item => xtasks.delete_xtask(taskData.get(item)!))
						).then(updateStatusBarItems)
					}
					break;
				case 'Stash':
					stash_xtasks()
					break;
				default:
					break;
				quickPick.items = await get_xtasks()
			}
			//todo refresh
		})
		function stash_xtasks() {
			quickPick.selectedItems.forEach(async item => {
				await xtasks.stash_xtask(taskData.get(item)!)
			})
		}
		quickPick.onDidAccept(async () => {
			stash_xtasks()
			quickPick.dispose()
		});
		quickPick.onDidHide(() => quickPick.dispose());
		quickPick.show();
	}));

	// context.subscriptions.push(vscode.commands.registerCommand('xtask.test', async () => {
	// 	const quickPick = window.createQuickPick();
	// 	quickPick.placeholder = 'Select test mode';
	// 	if (!conf.current.interactive) {
	// 		quickPick.items = [
	// 			{ label: 'Testcases', description: 'feed Builtin and/or custom testcases' },
	// 			{ label: 'Manual', description: '' },
	// 			{ label: 'Bruteforce', description: 'with Generator' },
	// 			{ label: 'Compare', description: 'with Generator and Comparator' },
	// 			{ label: 'Visualize', description: '' },
	// 		]
	// 	} else {
	// 		quickPick.items = [
	// 			{ label: 'Manual', description: '' },
	// 			{ label: 'Checke', description: 'with Interactive Checker' },
	// 		]
	// 	}
	// 	// quickPick.onDidChangeSelection(async (selection) => {
	// 	// });
	// 	quickPick.onDidAccept(async () => {
	// 		const cmd = vscode.workspace.getConfiguration('xtask.Commands').get<string>(quickPick.selectedItems[0].label)!
	// 		const execution = await vscode.tasks.executeTask(new vscode.Task(
	// 			{ type: 'xtask', name: 'test' },
	// 			vscode.TaskScope.Workspace,
	// 			'test',
	// 			'xtask',
	// 			new vscode.ShellExecution(cmd, {})
	// 		));
	// 		quickPick.dispose()
	// 		await new Promise<void>(resolve => {
	// 			let disposable = vscode.tasks.onDidEndTask(e => {
	// 				if (e.execution === execution) {
	// 					execution.task.definition.
	// 					disposable.dispose();
	// 					resolve();
	// 				}
	// 			});
	// 		});
	// 	});
	// 	quickPick.onDidHide(() => quickPick.dispose());
	// 	quickPick.show();
	// }));
	
	context.subscriptions.push(vscode.commands.registerCommand('xtask.testx', async () => {
		const quickPick = window.createQuickPick();
		quickPick.placeholder = 'Select test mode';
		const current = await xtasks.get_current()
		if (current == undefined) {
			vscode.window.showErrorMessage('No xtask working now ...')
			return 1
		}
		if (current.interactive) {
			quickPick.items = [
				{ label: 'Manual', description: '' },
				{ label: 'Random Inputs * Custom Jurger', description: 'Rand ins -> jurger <-> solver' },
				{ label: 'TestKs Inputs * Custom Jurger', description: 'Test ins -> jurger <-> solver' },
			]
		} else {
			quickPick.items = [
				{ label: 'Test Cases', description: 'Test ins -> solver -> token cmp <- Test outs' },
				{ label: 'Random Inputs', description: 'Rand ins -> solver' },
				{ label: 'Random Inputs * Comparator', description: 'Rand ins -> solver -> token cmp <- comparator <- Rand ins' },
				{ label: 'Random Inputs * Custom Jurger', description: 'Rand ins -> jurger <-> solver' },
				{ label: 'TestKs Inputs * Custom Jurger', description: 'Test ins -> jurger <-> solver' },
				{ label: 'Manual', description: '' },
			]
		}
		quickPick.onDidAccept(async () => {
			const option = quickPick.selectedItems[0].label
    		quickPick.dispose()
			switch (option) {
				case 'Test Cases': {
					await xtasks.run_testcases()
					break;
				}
				case 'Random Inputs': {
					await xtasks.run_randominputs()
					break;
				}
				case 'Random Inputs * Comparator': {
					await xtasks.run_comparator_with_randominputs()
					break;
				}
				case 'TestKs Inputs * Custom Jurger': {
					await xtasks.run_customjurger_with_testcaseinputs()
					break;
				}
				case 'Random Inputs * Custom Jurger': {
					await xtasks.run_customjurger_with_randominputs()
					break;
				}
				case 'Manual': {
					await xtasks.run_manually()
					break;
				}
				default: {
					break;
				}
			}
		});
		quickPick.onDidHide(() => quickPick.dispose());
		quickPick.show();
	}));

	const INPUT_SUFFIX = 'INPUT'
	const EXPECT_SUFFIX = 'EXPECT'
	const ACTUAL_SUFFIX = 'ACTUAL'
	context.subscriptions.push(vscode.commands.registerCommand('xtask.listtestcases', async () => {
		class XTestButton implements vscode.QuickInputButton {
			iconPath: vscode.IconPath;
			tooltip?: string | undefined;
			constructor(label: string) {
				switch (label) {
					case 'New':
						this.iconPath = new vscode.ThemeIcon('new-file')
						break;
					case 'Show Diff':
						this.iconPath = new vscode.ThemeIcon('diff')
						break;
					case 'Edit Input':
						this.iconPath = new vscode.ThemeIcon('notebook-edit')
						break;
					case 'Edit Expect':
						this.iconPath = new vscode.ThemeIcon('notebook-state-success')
						break;
					case 'Close':
						this.iconPath = new vscode.ThemeIcon('panel-close')
						break;
					default: {
						this.iconPath = new vscode.ThemeIcon('')
						break;
					}
				}
				this.tooltip = label
			}
		}
		class XTestItem implements vscode.QuickPickItem {
			label: string;
			detail?: string | undefined;
			buttons?: readonly vscode.QuickInputButton[] | undefined;
			test: any;
			index: number;
			
			constructor(i: number, test: any) {
				this.index = i + 1
				this.test = test
				this.label = `#${i + 1}`
				this.detail = `Result: ${test.result}, Cpu: ${test.cpu} ms, Memory: ${test.mem} mb, source: ${test.source}`
				this.buttons = [
					new XTestButton('Edit Input'),
					new XTestButton('Edit Expect'),
					new XTestButton('Show Diff'),
				]
			}
		};
		const quickPick = window.createQuickPick<XTestItem>();
		quickPick.title = 'Test Cases'
		quickPick.ignoreFocusOut = true;
		quickPick.canSelectMany = true
		quickPick.placeholder = '';
		const items = xtasks.get_tests().map((test, i) => new XTestItem(i, test))
		quickPick.items = items
		quickPick.selectedItems = items
		quickPick.buttons = [new XTestButton('New'), new XTestButton('Close')]
		quickPick.onDidAccept(async () => {
			let tests = xtasks.get_tests()
			tests.forEach(e => e.selected = false)
			quickPick.selectedItems.forEach(e => {
				tests[e.index - 1].selected = true;
			})
			xtasks.set_tests(tests)
    		await vscode.window.showInformationMessage('Test Cases saved sucessfully')
			quickPick.dispose()
		})
		// quickPick.onDidChangeSelection(() => {
		// 	console.log("change selection")
		// })
		quickPick.onDidTriggerButton(async e => {
			switch (e.tooltip) {
				case 'New':
					let id = xtasks.get_tests().length + 1
					let INPUT_TEMPFILE = xtasks.fullpath(`${id}.${INPUT_SUFFIX}`)
					writeFileSync(INPUT_TEMPFILE, '')
	                await vscode.workspace.openTextDocument(INPUT_TEMPFILE).then(doc => { vscode.window.showTextDocument(doc) })
					break;
				case 'Close':
					quickPick.dispose()
					break;
				default:
					break;
			}
			quickPick.dispose()
		})
		quickPick.onDidTriggerItemButton(async e => {
			let id = e.item.index
			let INPUT_TEMPFILE = xtasks.fullpath(`${id}.${INPUT_SUFFIX}`)
			let EXPECT_TEMPFILE = xtasks.fullpath(`${id}.${EXPECT_SUFFIX}`)
			let ACTUAL_TEMPFILE = xtasks.fullpath(`${id}.${ACTUAL_SUFFIX}`)
			switch (e.button.tooltip) {
				case 'Show Diff':
					writeFileSync(EXPECT_TEMPFILE, e.item.test.expect)
					writeFileSync(ACTUAL_TEMPFILE, e.item.test.actual)
            		await vscode.commands.executeCommand("vscode.diff", vscode.Uri.file(EXPECT_TEMPFILE), vscode.Uri.file(ACTUAL_TEMPFILE), `Test Case #${e.item.index}`).then()
					break
				case 'Edit Input':
					writeFileSync(INPUT_TEMPFILE, e.item.test.input)
	                await vscode.workspace.openTextDocument(INPUT_TEMPFILE).then(doc => { vscode.window.showTextDocument(doc) })
					break
				case 'Edit Expect':
					writeFileSync(EXPECT_TEMPFILE, e.item.test.expect)
	                await vscode.workspace.openTextDocument(EXPECT_TEMPFILE).then(doc => { vscode.window.showTextDocument(doc) })
					break
				default:
					break;
			}
		})
		quickPick.onDidHide(() => quickPick.dispose());
		quickPick.show();
	}))

	/**
	 * listener for testcase edit
	 */
	context.subscriptions.push(vscode.workspace.onDidSaveTextDocument(async (doc) => {
		if (doc.uri.path.endsWith(INPUT_SUFFIX) || doc.uri.path.endsWith(EXPECT_SUFFIX)) {
			const testid = Number(path.basename(doc.uri.path).split('.')[0]) - 1
			const suffix = path.extname(doc.uri.path).toLowerCase()
			const tests = xtasks.get_tests()
			tests[testid][suffix] = doc.getText()
			xtasks.set_tests(tests)
		}
	}))
	context.subscriptions.push(vscode.workspace.onDidCloseTextDocument(async (doc) => {
		if (doc.uri.path.endsWith(INPUT_SUFFIX) || doc.uri.path.endsWith(EXPECT_SUFFIX)|| doc.uri.path.endsWith(ACTUAL_SUFFIX)) {
			vscode.workspace.fs.delete(doc.uri)
		}
	}))

	context.subscriptions.push(vscode.commands.registerCommand('xtask.copy', async () => {
		const outputChannel = vscode.window.createOutputChannel('XTask', 'log')
		outputChannel.show()
		outputChannel.clear()
		let file = xtasks.conf.solver.fullname
		return new Promise(((resolve, reject) => {
			subprocess.exec(`${xtasks.conf.copy} ${file}`, { cwd: vscode.workspace.workspaceFolders![0].uri.fsPath }, (err, stdout, stderr) => {
				outputChannel.appendLine('Copying file ...')
				if (err) {
					outputChannel.appendLine(err.message)
					reject(err)
				} else {
					outputChannel.appendLine(stderr)
					outputChannel.appendLine('')
					outputChannel.appendLine(stdout)
					vscode.env.clipboard.writeText(stdout).then(() => {
						vscode.window.showInformationMessage('Copied');
					})
					resolve(0)
				}
			})
		}))
	}));
	// context.subscriptions.push(
	// 	vscode.commands.registerCommand('xtask.form', () => {
	// 	  const panel = vscode.window.createWebviewPanel(
	// 		'catCoding',
	// 		'Cat Coding',
	// 		vscode.ViewColumn.One,
	// 		{
	// 		  enableScripts: true
	// 		}
	// 	  );
	
	// 	  panel.webview.html = getxtaskform(1);
	
	// 	  // Handle messages from the webview
	// 	  panel.webview.onDidReceiveMessage(
	// 		message => {
	// 		  switch (message.command) {
	// 			default:
	// 			  vscode.window.showErrorMessage(message.text);
	// 			  return;
	// 		  }
	// 		},
	// 		undefined,
	// 		context.subscriptions
	// 	  );
	// 	})
	//   );

	// const ctrl = vscode.tests.createTestController('xTestController', 'Standard IO Testcases');
	// context.subscriptions.push(ctrl);
	// async function runHandler(
	// 	request: vscode.TestRunRequest,
	// 	token: vscode.CancellationToken
	// ) {
	// 	const run = ctrl.createTestRun(request);
	// 	const queue: vscode.TestItem[] = [];

	// 	// Loop through all included tests, or all known tests, and add them to our queue
	// 	if (request.include) {
	// 		request.include.forEach(item => queue.push(item));
	// 	} else {
	// 		ctrl.items.forEach(item => queue.push(item));
	// 	}
	// 	// For every test that was queued, try to run it. Call run.passed() or run.failed().
	// 	// The `TestMessage` can contain extra information, like a failing location or
	// 	// a diff output. But here we'll just give it a textual message.
	// 	while (queue.length > 0 && !token.isCancellationRequested) {
	// 		const item = queue.pop()!;
	// 		// Skip tests the user asked to exclude
	// 		if (request.exclude?.includes(item)) {
	// 			continue;
	// 		}
	// 		await xtask.testData.get(item)!.run(item, run)
	// 		// test.children.forEach(test => queue.push(test));
	// 	}
	// 	// Make sure to end the run after all tests have been executed:
	// 	run.end();
	// }
	// ctrl.createRunProfile('XTask Test', vscode.TestRunProfileKind.Run, runHandler, true, undefined, true);
	
	// async function parseTests(e: vscode.TextDocument) {
	// 	if (e.uri.path.endsWith(xtask.test_file())) 
	// 		await xtask.parseTests(ctrl);
	// }
	// context.subscriptions.push(
	// 	vscode.workspace.onDidOpenTextDocument(parseTests),
	// 	vscode.workspace.onDidChangeTextDocument(e => parseTests(e.document))
	// );
	// ctrl.resolveHandler = async (item) => {
	// 	await xtask.parseTests(ctrl);
	// }
	
};
	
	
// This method is called when your extension is deactivated
export function deactivate() { }
