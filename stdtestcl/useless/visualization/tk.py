from tkinter import messagebox
from tkinter import ttk
import tkinter as tk
top = tk.Tk()
C = tk.Canvas(top, bg="blue", height=250, width=300

              )
coord = 10, 50, 240, 210
arc = C.create_arc(coord, start=0, extent=150, fill="red")
line = C.create_line(10,10,200,200,fill='white')

C.pack()

def saveassvg():
    from canvasvg import saveall
    saveall("tk.svg", C)

savebtn = tk.Button(top, text="Save SVG", command=saveassvg)
savebtn.pack()
top.mainloop()

from .painter import Painter
def TKPainter(Painter):
    def __init__(self):
        self.root = tk.Tk()
        self.canvas = tk.Canvas(self.root, )
        
    def newlseg(self, x1,y1,x2,y2):
        id = self.canvas.create_line(10,10,200,200,fill='white')

    def delete(self, idx):
        self.canvas.remo
        
        