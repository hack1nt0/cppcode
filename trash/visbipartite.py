import graphviz as G

g = G.Graph("Bipartite")
a, b, m = map(int, input().split())
for x in range(1, a+b+1):
    g.node(str(x), str(x if x <= a else x - a))
for e in range(m):
    x, y = map(int, input().split())
    g.edge(str(x), str(y+a), label=str(e+1))
g.render(directory="gv", view=True)


