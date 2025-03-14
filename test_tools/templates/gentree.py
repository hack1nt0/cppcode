from cyaron import *

def oper(x):
    return "%d %d" % (x.start, x.end)

n = int(2e5)
print(1, n)
graph = Graph.tree(n, 0.3, 0.3)
print(graph.to_str(output=oper, shuffle=True))