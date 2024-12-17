
class Painter:
    def zoom(self, delta):
        pass

    def pan(self, xdelta, ydelta):
        pass

    def newlseg(self, x1,y1,x2,y2):
        pass
    def newpoly(self, *pts):
        pass
    def newpath(self, *pts):
        pass

    def select(self, idx: int, reversed: bool):
        pass

    def delete(self, idx):
        pass

    def sort(self, ord: list[int]):
        pass

    def saveassvg(self):
        pass