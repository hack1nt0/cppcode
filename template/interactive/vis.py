import graphviz as G

g = G.Graph("Tree")
n = int(input())
a = input().split()
for v in range(n * 2):
    g.node(str(v+1), f"{v+1}({a[v]})")
for _ in range(n * 2 - 1):
    x, y = map(int, input().split())
    g.edge(str(x), str(y))
g.render(directory="gv", view=True)


