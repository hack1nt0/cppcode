```python
%%html
<style>
th {
background-color:#55FF33;
}
td {
background-color:#00AAFF;
}
table, th, td {
    border:1px solid black;
        text-align: center; 
    vertical-align: middle;
}
</style>
```


<style>
th {
background-color:#55FF33;
}
td {
background-color:#00AAFF;
}
table, th, td {
    border:1px solid black;
        text-align: center; 
    vertical-align: middle;
}
</style>



## Task E. No Palindromes
case analysis.

1. S is not palindrome, obvious Yes
2. S consists of same character, then Answer is No
3. Let P = lowest position where $A_P != A_1$, $S_1$ = A[1..P], and $S_2$ = A[P+1...N]. if $S_2$ is not palindrome, then we are done. Else S = AbAb..AbA, where A = $\underbrace{a...a}_{P-1}$.
   1. if S = abab...aba, Answer is No
   2. if S = AbA, Answer is None
   3. Else, Answer is Yes, and $P_1$ = Aba, left is $P_2$
   4. 
<table>
    <tr><th>P: lowest p where $A_p != A_1$</th><th>Second part is palindrome?</th></tr>
    <tr><td>2</td><td>YES</td></tr>
</table>



```python

```

### Ts
sksh


```python

```
