// The module 'vscode' contains the VS Code extensibility API
// Import the module and reference it with the alias vscode in your code below
import * as vscode from 'vscode';
import { window, commands, ExtensionContext } from 'vscode'; 


export function getxtaskform(xtaskid: number) {
	return `<!DOCTYPE html>
  <html lang="en">
  <head>
	  <meta charset="UTF-8">
	  <meta name="viewport" content="width=device-width, initial-scale=1.0">
	  <title>XTask - Form</title>
  </head>
  <body>
	  <div id="xtasktable"></div>
	  <div id="xtaskform" >
	  	<form onsubmit="submitform(this)">
		  <label for="name">Name:</label><br>
		  <input type="text" id="name" name="name"><br>
		  <label for="group">Group:</label><br>
		  <input type="text" id="group" name="group"><br>
		  <label for="description">Description:</label><br>
		  <textarea id="description" name="description"></textarea><br>
		  <button type="submit">Submit</button>
		</form>
	  </div>
	  <button onclick="refreshCat()">Refresh</button>
	<script>
		const vscode = acquireVsCodeApi();
		const main = document.getElementById('main');
		
		function refreshCat() {
			vscode.postMessage({
				command: 'alert',
				text: '🐛  on line ' + count
			})
		};
		function submitform(dat) {
			vscode.postMessage({
				command: 'submit',
				text: dat
			})
		};
    </script>
  </body>
  </html>`;
}