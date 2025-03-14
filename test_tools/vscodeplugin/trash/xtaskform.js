"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.getxtaskform = getxtaskform;
function getxtaskform(xtaskid) {
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
//# sourceMappingURL=xtaskform.js.map