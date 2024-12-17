import random as R

# n = 576460752303423487 
# q = 1
# u = 435255549744527627
# s = R.choices('LRU', k=int(1e5))
# print(n, q)
# print(u)
# print(''.join(s))xxx

n=int(2e5)
print(n)
for _ in range(n):
    print(R.randint(-int(1e9), int(1e9)))
for _ in range(n):
    print(R.randint(-int(1e9), int(1e9)))
k=int(2e5)
print(k)
for _ in range(k):
    l = R.randint(1, n - 1)
    r = R.randint(l, n)
    print(3, l, r)
