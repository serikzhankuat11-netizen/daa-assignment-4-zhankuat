"""Assignment 4 -- Dynamic Programming and String Processing (Python 3.12).

Eight commands: lcs, merge, tree, naive, kmp, rk, suffix, aho.

Every algorithm is a pure function (no global state), so consecutive requests
with different tasks cannot influence each other.  ``handle`` dispatches one
parsed JSON request, ``main`` implements the UTF-8 JSON Lines interface
(one request per input line -> one result per output line, stdout only).

No built-in substring search (str.find / in / index / count / re) is used in
any search algorithm.
"""

import json
import sys


# --------------------------------------------------------------------------
# Part 1: LCS  (prefix DP)
# --------------------------------------------------------------------------
def lcs(a: str, b: str):
    """dp[i][j] = LCS length of a[:i] and b[:j].  O(|a||b|) time and memory."""
    n, m = len(a), len(b)
    if n == 0 or m == 0:
        return 0, ""
    dp = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        ai = a[i - 1]
        row, prev = dp[i], dp[i - 1]
        for j in range(1, m + 1):
            if ai == b[j - 1]:
                row[j] = prev[j - 1] + 1
            else:
                up, left = prev[j], row[j - 1]
                row[j] = up if up >= left else left
    # reconstruction: walk back from dp[n][m]
    out = []
    i, j = n, m
    while i > 0 and j > 0:
        if a[i - 1] == b[j - 1]:
            out.append(a[i - 1])
            i -= 1
            j -= 1
        elif dp[i - 1][j] >= dp[i][j - 1]:
            i -= 1
        else:
            j -= 1
    out.reverse()
    return dp[n][m], "".join(out)


# --------------------------------------------------------------------------
# Part 2: ordered adjacent block merging (interval DP)
# --------------------------------------------------------------------------
def merge(sizes):
    """dp[l][r] = min cost to merge blocks l..r into one block.

    dp[l][r] = min_{l<=k<r} dp[l][k] + dp[k+1][r] + sum(l..r),  dp[i][i] = 0.
    The plan lists merges [l, k, r] with children before their parent.
    """
    n = len(sizes)
    if n <= 1:
        return 0, []
    pre = [0] * (n + 1)
    for i in range(n):
        pre[i + 1] = pre[i] + sizes[i]
    INF = float("inf")
    dp = [[0] * n for _ in range(n)]
    split = [[-1] * n for _ in range(n)]
    for length in range(2, n + 1):
        for l in range(0, n - length + 1):
            r = l + length - 1
            best, best_k = INF, -1
            dl = dp[l]
            for k in range(l, r):
                c = dl[k] + dp[k + 1][r]
                if c < best:
                    best, best_k = c, k
            dp[l][r] = best + pre[r + 1] - pre[l]
            split[l][r] = best_k
    # iterative post-order over the split tree (children before parent)
    plan = []
    stack = [(0, n - 1, False)]
    while stack:
        l, r, done = stack.pop()
        if l == r:
            continue
        k = split[l][r]
        if done:
            plan.append([l, k, r])
        else:
            stack.append((l, r, True))
            stack.append((k + 1, r, False))
            stack.append((l, k, False))
    return dp[0][n - 1], plan


# --------------------------------------------------------------------------
# Part 3: maximum weight independent set on a tree (take / skip DP)
# --------------------------------------------------------------------------
def tree(n, weights, edges):
    """take[v] = w[v] + sum skip[c];  skip[v] = sum max(take[c], skip[c]).

    Iterative DFS (no recursion -> deep chains are safe).  The empty set is
    allowed, so the answer is max(take[root], skip[root]) >= 0.
    """
    if n == 0:
        return 0, []
    adj = [[] for _ in range(n)]
    for u, v in edges:
        adj[u].append(v)
        adj[v].append(u)
    parent = [-1] * n
    order = []
    stack = [0]
    seen = [False] * n
    seen[0] = True
    while stack:
        v = stack.pop()
        order.append(v)  # parent always appears before its children
        for c in adj[v]:
            if not seen[c]:
                seen[c] = True
                parent[c] = v
                stack.append(c)
    take = [0] * n
    skip = [0] * n
    for v in reversed(order):  # children are processed before parents
        take[v] += weights[v]
        p = parent[v]
        if p != -1:
            take[p] += skip[v]
            skip[p] += take[v] if take[v] > skip[v] else skip[v]
    # reconstruction top-down: the parent's decision restricts the child
    taken = [False] * n
    for v in order:
        p = parent[v]
        if p != -1 and taken[p]:
            taken[v] = False
        else:
            taken[v] = take[v] > skip[v]
    total = take[0] if take[0] > skip[0] else skip[0]
    return total, [v for v in range(n) if taken[v]]


# --------------------------------------------------------------------------
# Part 4: exact search -- naive, KMP, Rabin-Karp
# --------------------------------------------------------------------------
def naive(text: str, pattern: str):
    n, m = len(text), len(pattern)
    if m == 0:
        return list(range(n + 1))
    if m > n:
        return []
    res = []
    for s in range(n - m + 1):
        j = 0
        while j < m and text[s + j] == pattern[j]:
            j += 1
        if j == m:
            res.append(s)
    return res


def prefix_function(p: str):
    """pi[i] = length of the longest proper prefix of p[:i+1] that is also a suffix."""
    m = len(p)
    pi = [0] * m
    k = 0
    for i in range(1, m):
        while k > 0 and p[i] != p[k]:
            k = pi[k - 1]
        if p[i] == p[k]:
            k += 1
        pi[i] = k
    return pi


def kmp(text: str, pattern: str):
    n, m = len(text), len(pattern)
    if m == 0:  # handled before any pattern indexing
        return list(range(n + 1))
    if m > n:
        return []
    pi = prefix_function(pattern)
    res = []
    k = 0
    for i in range(n):
        c = text[i]
        while k > 0 and c != pattern[k]:
            k = pi[k - 1]
        if c == pattern[k]:
            k += 1
        if k == m:
            res.append(i - m + 1)
            k = pi[k - 1]  # fallback keeps overlapping matches
    return res


RK_BASE = 31
RK_MOD = 101


def rk(text: str, pattern: str):
    n, m = len(text), len(pattern)
    if m == 0:
        return list(range(n + 1))
    if m > n:
        return []
    high = 1  # BASE^(m-1) mod MOD : weight of the leftmost character
    for _ in range(m - 1):
        high = (high * RK_BASE) % RK_MOD
    hp = 0
    hw = 0
    for i in range(m):
        hp = (hp * RK_BASE + ord(pattern[i])) % RK_MOD
        hw = (hw * RK_BASE + ord(text[i])) % RK_MOD
    res = []
    for s in range(n - m + 1):
        if hp == hw:  # candidate only -> verify every character
            j = 0
            while j < m and text[s + j] == pattern[j]:
                j += 1
            if j == m:
                res.append(s)
        if s + m < n:
            hw = (hw - ord(text[s]) * high) % RK_MOD
            if hw < 0:  # normalise (Python's % is already >= 0, kept explicit)
                hw += RK_MOD
            hw = (hw * RK_BASE + ord(text[s + m])) % RK_MOD
    return res


# --------------------------------------------------------------------------
# Part 5: suffix array (prefix doubling) + Kasai LCP
# --------------------------------------------------------------------------
def suffix_array(s: str):
    """Prefix doubling: sort suffixes by (rank[i], rank[i+k]), k = 1, 2, 4, ..."""
    n = len(s)
    if n == 0:
        return []
    sa = list(range(n))
    rank = [ord(c) for c in s]
    base = max(n, 127) + 2
    k = 1
    while True:
        key = [
            rank[i] * base + (rank[i + k] + 1 if i + k < n else 0)
            for i in range(n)
        ]
        sa.sort(key=key.__getitem__)
        new_rank = [0] * n
        r = 0
        for idx in range(1, n):
            if key[sa[idx]] != key[sa[idx - 1]]:
                r += 1
            new_rank[sa[idx]] = r
        rank = new_rank
        if r == n - 1:
            break
        k <<= 1
    return sa


def kasai(s: str, sa):
    """lcp[i] = LCP(suffix sa[i-1], suffix sa[i]); lcp[0] = 0.  O(n)."""
    n = len(s)
    lcp = [0] * n
    if n == 0:
        return lcp
    inv = [0] * n
    for i, p in enumerate(sa):
        inv[p] = i
    h = 0
    for i in range(n):
        r = inv[i]
        if r > 0:
            j = sa[r - 1]
            while i + h < n and j + h < n and s[i + h] == s[j + h]:
                h += 1
            lcp[r] = h
            if h > 0:
                h -= 1
        else:
            h = 0
    return lcp


def suffix(text: str):
    n = len(text)
    if n == 0:
        return [], [], ""
    sa = suffix_array(text)
    lcp = kasai(text, sa)
    best, at = 0, -1
    for i in range(1, n):
        if lcp[i] > best:
            best, at = lcp[i], i
    repeated = text[sa[at]: sa[at] + best] if best > 0 else ""
    return sa, lcp, repeated


# --------------------------------------------------------------------------
# Part 6: Aho-Corasick (counts per dictionary position)
# --------------------------------------------------------------------------
def aho(patterns, texts):
    q = len(texts)
    p = len(patterns)
    if q == 0:
        return []
    if p == 0:
        return [[] for _ in range(q)]
    # trie
    children = [{}]
    terminal = [0] * p
    for idx, pat in enumerate(patterns):
        node = 0
        for ch in pat:
            nxt = children[node].get(ch)
            if nxt is None:
                nxt = len(children)
                children[node][ch] = nxt
                children.append({})
            node = nxt
        terminal[idx] = node  # duplicates share one terminal state
    S = len(children)
    # failure links by BFS (also gives the BFS order)
    fail = [0] * S
    order = [0]
    head = 0
    while head < len(order):
        u = order[head]
        head += 1
        for ch, v in children[u].items():
            if u == 0:
                fail[v] = 0
            else:
                f = fail[u]
                while f and ch not in children[f]:
                    f = fail[f]
                fv = children[f].get(ch, 0)
                fail[v] = fv if fv != v else 0
            order.append(v)
    rev = order[:0:-1]  # reverse BFS order without the root
    rows = []
    for text in texts:
        cnt = [0] * S
        state = 0
        for ch in text:
            while state and ch not in children[state]:
                state = fail[state]
            state = children[state].get(ch, 0)
            cnt[state] += 1
        # visit propagation along failure links, deepest states first
        for v in rev:
            c = cnt[v]
            if c:
                cnt[fail[v]] += c
        rows.append([cnt[t] for t in terminal])
    return rows


# --------------------------------------------------------------------------
# JSON Lines interface
# --------------------------------------------------------------------------
def handle(req):
    task = req["task"]
    if task == "lcs":
        length, seq = lcs(req["a"], req["b"])
        return {"length": length, "sequence": seq}
    if task == "merge":
        cost, plan = merge(req["sizes"])
        return {"cost": cost, "plan": plan}
    if task == "tree":
        w, sel = tree(req["n"], req["weights"], req["edges"])
        return {"weight": w, "selected": sel}
    if task == "naive":
        return {"positions": naive(req["text"], req["pattern"])}
    if task == "kmp":
        return {"positions": kmp(req["text"], req["pattern"])}
    if task == "rk":
        return {"positions": rk(req["text"], req["pattern"])}
    if task == "suffix":
        sa, lcp, rep = suffix(req["text"])
        return {"sa": sa, "lcp": lcp, "repeated": rep}
    if task == "aho":
        return {"counts": aho(req["patterns"], req["texts"])}
    raise ValueError("unknown task: %r" % (task,))


def main():
    out = sys.stdout
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        out.write(json.dumps(handle(json.loads(line)), separators=(",", ":")))
        out.write("\n")
    out.flush()


if __name__ == "__main__":
    if hasattr(sys.stdin, "reconfigure"):
        sys.stdin.reconfigure(encoding="utf-8")
        sys.stdout.reconfigure(encoding="utf-8")
    main()
