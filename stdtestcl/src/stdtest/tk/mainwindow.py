import tkinter as tk
from tkinter import ttk

class MainWindow(tk.Frame):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs);
        self.grid()
        tk.Label(self, text="Hello World!").grid(column=0, row=0)
        tk.Button(self, text="Quit",).grid(column=1, row=0)
        ttk.Combobox(self, values=[
            'Visualization',
            'Edit Task',
            'Configuration',
        ], ).grid(column=0, row=1)
        

