"""Own tests for Assignment 4 (run:  python -m unittest discover -s tests/student -v).

Each algorithm is compared with an independently written oracle (brute force
or a different formulation), not with another implementation that could share
the same bug.  Every test documents the defect it is meant to detect.
"""

import itertools
import json
import os
import random
import sys
import time
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
for rel in (".", "..", "../../Python/source", "../../source"):
    sys.path.insert(0, os.path.normpath(os.path.join(HERE, rel)))

import a4_solution as A  # noqa: E402

ALPHA = "ab"
PRINTABLE = [chr(c) for c in range(32, 127)]


def rnd_str(rng, n, alpha=ALPHA):
    return "".join(rng.choice(alpha) for _ in range(n))


def is_subsequence(s, t):
    it = iter(t)
    return all(ch in it for ch in s)


# ------------------------------------------------------------------ LCS
def lcs_oracle_len(a, b):
    """Brute force: longest common element over all subsequences of a (tiny)."""
    best = 0
    for mask in range(1 << len(a)):
        sub = "".join(a[i] for i in range(len(a)) if mask >> i & 1)
        if len(sub) > best and is_subsequence(sub, b):
            best = len(sub)
    return best


class TestLCS(unittest.TestCase):
    def test_example(self):  # subsequence, not substring
        self.assertEqual(A.lcs("tea_time", "team"), (4, "team"))

    def test_empty(self):  # base cases
        self.assertEqual(A.lcs("", ""), (0, ""))
        self.assertEqual(A.lcs("abc", ""), (0, ""))
        self.assertEqual(A.lcs("", "abc"), (0, ""))

    def test_random_vs_bruteforce(self):  # wrong mismatch transition
        rng = random.Random(1)
        for _ in range(400):
            a = rnd_str(rng, rng.randint(0, 9), "abc")
            b = rnd_str(rng, rng.randint(0, 9), "abc")
            length, seq = A.lcs(a, b)
            self.assertEqual(length, lcs_oracle_len(a, b), (a, b))
            self.assertEqual(len(seq), length)
            self.assertTrue(is_subsequence(seq, a) and is_subsequence(seq, b))

    def test_repeated_and_punctuation(self):
        length, seq = A.lcs("a a,A!", " A,a! a")
        self.assertEqual(length, lcs_oracle_len("a a,A!", " A,a! a"))
        self.assertTrue(is_subsequence(seq, "a a,A!"))

    def test_max_domain(self):  # |a|*|b| = 10^6
        rng = random.Random(2)
        a, b = rnd_str(rng, 1000, "abcd"), rnd_str(rng, 1000, "abcd")
        length, seq = A.lcs(a, b)
        self.assertEqual(len(seq), length)
        self.assertTrue(is_subsequence(seq, a) and is_subsequence(seq, b))


# ---------------------------------------------------------------- merge
def merge_oracle(sizes):
    """Try every order of adjacent merges (tiny n)."""
    best = [None]

    def rec(blocks, cost):
        if len(blocks) == 1:
            if best[0] is None or cost < best[0]:
                best[0] = cost
            return
        for i in range(len(blocks) - 1):
            nb = blocks[:i] + [blocks[i] + blocks[i + 1]] + blocks[i + 2:]
            rec(nb, cost + blocks[i] + blocks[i + 1])

    if len(sizes) <= 1:
        return 0
    rec(list(sizes), 0)
    return best[0]


def check_plan(sizes, cost, plan):
    """Simulate the plan: adjacency, chronological order, total cost."""
    n = len(sizes)
    if n <= 1:
        return cost == 0 and plan == []
    if len(plan) != n - 1:
        return False
    blocks = [(i, i) for i in range(n)]
    total = 0
    for l, k, r in plan:
        if (l, k) not in blocks or (k + 1, r) not in blocks:
            return False
        i = blocks.index((l, k))
        if i + 1 >= len(blocks) or blocks[i + 1] != (k + 1, r):
            return False  # blocks must be adjacent
        blocks[i:i + 2] = [(l, r)]
        total += sum(sizes[l:r + 1])
    return blocks == [(0, n - 1)] and total == cost


class TestMerge(unittest.TestCase):
    def test_example(self):
        cost, plan = A.merge([2, 3, 4])
        self.assertEqual(cost, 14)
        self.assertTrue(check_plan([2, 3, 4], cost, plan))

    def test_small(self):  # 0/1 blocks
        self.assertEqual(A.merge([]), (0, []))
        self.assertEqual(A.merge([5]), (0, []))
        self.assertEqual(A.merge([0, 0]), (0, [[0, 0, 1]]))

    def test_random_vs_bruteforce(self):  # greedy / non-adjacent merging bug
        rng = random.Random(3)
        for _ in range(300):
            n = rng.randint(0, 7)
            sizes = [rng.choice([0, 1, 2, 5, 9, 100]) for _ in range(n)]
            cost, plan = A.merge(sizes)
            self.assertEqual(cost, merge_oracle(sizes), sizes)
            self.assertTrue(check_plan(sizes, cost, plan), (sizes, plan))

    def test_adjacency_vs_arbitrary_merge(self):
        # Merging the two smallest NON-adjacent blocks (1 and 1) would cost 2+12=14.
        # Only adjacent blocks may be merged, so the optimum is 11+12=23.
        cost, plan = A.merge([1, 10, 1])
        self.assertEqual(cost, 23)
        self.assertEqual(cost, merge_oracle([1, 10, 1]))
        self.assertTrue(check_plan([1, 10, 1], cost, plan))

    def test_interior_merge_first(self):  # plan must be chronological
        sizes = [10, 1, 1, 10]
        cost, plan = A.merge(sizes)
        self.assertEqual(cost, 36)
        self.assertTrue(check_plan(sizes, cost, plan))

    def test_large_values_and_n200(self):  # large totals, full domain
        sizes = [10 ** 9] * 200
        cost, plan = A.merge(sizes)
        self.assertTrue(cost > 2 ** 31)
        self.assertTrue(check_plan(sizes, cost, plan))
        rng = random.Random(4)
        sizes = [rng.randint(0, 10 ** 9) for _ in range(200)]
        cost, plan = A.merge(sizes)
        self.assertTrue(check_plan(sizes, cost, plan))


# ----------------------------------------------------------------- tree
def tree_oracle(n, weights, edges):
    best = 0
    for mask in range(1 << n):
        if any((mask >> u & 1) and (mask >> v & 1) for u, v in edges):
            continue
        best = max(best, sum(weights[i] for i in range(n) if mask >> i & 1))
    return best


def random_tree(rng, n):
    edges = []
    for v in range(1, n):
        u = rng.randrange(v)
        edges.append([u, v] if rng.random() < 0.5 else [v, u])
    perm = list(range(n))
    rng.shuffle(perm)  # relabel so that the root is not special
    return [[perm[u], perm[v]] for u, v in edges]


def check_tree(n, weights, edges, w, sel):
    if len(set(sel)) != len(sel) or any(not 0 <= v < n for v in sel):
        return False
    s = set(sel)
    if any(u in s and v in s for u, v in edges):
        return False
    return sum(weights[v] for v in sel) == w


class TestTree(unittest.TestCase):
    def test_example(self):
        w, sel = A.tree(3, [4, 9, 6], [[0, 1], [1, 2]])
        self.assertEqual(w, 10)
        self.assertTrue(check_tree(3, [4, 9, 6], [[0, 1], [1, 2]], w, sel))

    def test_empty_and_single(self):
        self.assertEqual(A.tree(0, [], []), (0, []))
        self.assertEqual(A.tree(1, [5], []), (5, [0]))
        self.assertEqual(A.tree(1, [-5], []), (0, []))
        self.assertEqual(A.tree(1, [0], [])[0], 0)

    def test_all_negative(self):  # empty set is allowed
        w, sel = A.tree(3, [-1, -2, -3], [[0, 1], [1, 2]])
        self.assertEqual((w, sel), (0, []))

    def test_random_vs_bruteforce(self):  # wrong take/skip, wrong reconstruction
        rng = random.Random(5)
        for _ in range(500):
            n = rng.randint(1, 11)
            weights = [rng.randint(-6, 9) for _ in range(n)]
            edges = random_tree(rng, n)
            w, sel = A.tree(n, weights, edges)
            self.assertEqual(w, tree_oracle(n, weights, edges), (n, weights, edges))
            self.assertTrue(check_tree(n, weights, edges, w, sel))

    def test_deep_chain_no_recursion_error(self):
        n = 100000
        weights = [1] * n
        edges = [[i, i + 1] for i in range(n - 1)]
        w, sel = A.tree(n, weights, edges)
        self.assertEqual(w, 50000)
        self.assertTrue(check_tree(n, weights, edges, w, sel))

    def test_large_sum(self):  # exceeds one entry's bound / 32-bit range
        n = 100000
        weights = [10 ** 9] * n
        edges = [[0, i] for i in range(1, n)]  # star: take all leaves
        w, sel = A.tree(n, weights, edges)
        self.assertEqual(w, (n - 1) * 10 ** 9)
        self.assertTrue(check_tree(n, weights, edges, w, sel))


# --------------------------------------------------------------- search
def search_oracle(text, pattern):
    n, m = len(text), len(pattern)
    return [i for i in range(n - m + 1) if text[i:i + m] == pattern]


class TestSearch(unittest.TestCase):
    ALL = (A.naive, A.kmp, A.rk)

    def test_examples(self):
        self.assertEqual(A.naive("aaaaa", "aaa"), [0, 1, 2])
        self.assertEqual(A.kmp("abababa", "aba"), [0, 2, 4])
        self.assertEqual(A.rk("abdj", "ab"), [0])

    def test_collision_pair(self):  # equal hash is only a candidate
        h = lambda s: (ord(s[0]) * 31 + ord(s[1])) % 101  # noqa: E731
        self.assertEqual(h("ab"), 75)
        self.assertEqual(h("dj"), 75)
        self.assertEqual(A.rk("dj", "ab"), [])
        self.assertEqual(A.rk("djabdj", "ab"), [2])

    def test_empty_pattern_and_text(self):  # n+1 boundaries
        for f in self.ALL:
            self.assertEqual(f("abc", ""), [0, 1, 2, 3])
            self.assertEqual(f("", ""), [0])
            self.assertEqual(f("", "a"), [])
            self.assertEqual(f("ab", "abc"), [])

    def test_case_and_punctuation(self):
        for f in self.ALL:
            self.assertEqual(f("Aa aA, a!", "a"), [1, 3, 7])
            self.assertEqual(f("x, y, z", ", "), [1, 4])

    def test_overlaps_last_start(self):
        for f in self.ALL:
            self.assertEqual(f("aaaa", "aa"), [0, 1, 2])
            self.assertEqual(f("abcab", "ab"), [0, 3])  # last valid start
            self.assertEqual(f("ab", "ab"), [0])

    def test_random_all_agree_with_oracle(self):
        rng = random.Random(6)
        for _ in range(1500):
            alpha = rng.choice(["a", "ab", "abc", PRINTABLE])
            text = rnd_str(rng, rng.randint(0, 25), alpha)
            pattern = rnd_str(rng, rng.randint(0, 5), alpha)
            exp = search_oracle(text, pattern)
            for f in self.ALL:
                self.assertEqual(f(text, pattern), exp, (f.__name__, text, pattern))

    def test_negative_remainder_normalisation(self):
        # long periodic text forces many window updates where (h - c*high) < 0
        text = "zaz" * 400 + "~ " * 100
        for pattern in ("zaz", "az", "~ ~", " ~"):
            self.assertEqual(A.rk(text, pattern), search_oracle(text, pattern))

    def test_scale(self):
        rng = random.Random(7)
        text = rnd_str(rng, 200000, "ab")
        pat = rnd_str(rng, 1000, "ab")
        t0 = time.time()
        self.assertEqual(A.kmp(text, pat), search_oracle(text, pat))
        self.assertEqual(A.kmp("a" * 200000, "a" * 100000)[:3], [0, 1, 2])
        self.assertLess(time.time() - t0, 10)
        # rk worst case: every window is a candidate AND a true match
        t0 = time.time()
        r = A.rk("a" * 10000, "a" * 2000)
        self.assertEqual(len(r), 8001)
        self.assertLess(time.time() - t0, 10)


# --------------------------------------------------------------- suffix
def suffix_oracle(text):
    n = len(text)
    sa = sorted(range(n), key=lambda i: text[i:])
    lcp = [0] * n
    for i in range(1, n):
        a, b = text[sa[i - 1]:], text[sa[i]:]
        k = 0
        while k < min(len(a), len(b)) and a[k] == b[k]:
            k += 1
        lcp[i] = k
    best = 0
    for L in range(1, n):  # brute-force longest repeated substring length
        seen, hit = set(), False
        for i in range(n - L + 1):
            sub = text[i:i + L]
            if sub in seen:
                hit = True
                break
            seen.add(sub)
        if hit:
            best = L
    return sa, lcp, best


class TestSuffix(unittest.TestCase):
    def test_example(self):
        self.assertEqual(
            A.suffix("banana"),
            ([5, 3, 1, 0, 4, 2], [0, 1, 3, 0, 0, 2], "ana"),
        )

    def test_empty_one_equal_distinct(self):
        self.assertEqual(A.suffix(""), ([], [], ""))
        self.assertEqual(A.suffix("x"), ([0], [0], ""))
        self.assertEqual(A.suffix("aaaa"), ([3, 2, 1, 0], [0, 1, 2, 3], "aaa"))
        self.assertEqual(A.suffix("abcd"), ([0, 1, 2, 3], [0, 0, 0, 0], ""))

    def test_random_vs_oracle(self):  # permutation, order, LCP, longest repeat
        rng = random.Random(8)
        for _ in range(600):
            alpha = rng.choice(["a", "ab", "abc", PRINTABLE])
            text = rnd_str(rng, rng.randint(0, 22), alpha)
            sa, lcp, rep = A.suffix(text)
            esa, elcp, best = suffix_oracle(text)
            self.assertEqual(sa, esa, text)
            self.assertEqual(lcp, elcp, text)
            self.assertEqual(len(rep), best, text)
            if rep:  # witness occurs at two distinct starts (overlap allowed)
                occ = search_oracle(text, rep)
                self.assertGreaterEqual(len(occ), 2)

    def test_scale(self):
        rng = random.Random(9)
        for text in ("a" * 50000, rnd_str(rng, 50000, "ab"), "ab" * 25000):
            t0 = time.time()
            sa, lcp, rep = A.suffix(text)
            self.assertLess(time.time() - t0, 10)
            self.assertEqual(sorted(sa), list(range(len(text))))
            self.assertEqual(len(lcp), len(text))
            self.assertEqual(len(rep), max(lcp))


# ------------------------------------------------------------------ aho
def aho_oracle(patterns, texts):
    return [[len(search_oracle(t, p)) for p in patterns] for t in texts]


class TestAho(unittest.TestCase):
    def test_example(self):
        self.assertEqual(
            A.aho(["he", "she", "he"], ["sheshe", "sheshe", ""]),
            [[2, 2, 2], [2, 2, 2], [0, 0, 0]],
        )

    def test_empty_dictionary_and_texts(self):
        self.assertEqual(A.aho([], ["ab", ""]), [[], []])
        self.assertEqual(A.aho(["a"], []), [])
        self.assertEqual(A.aho([], []), [])

    def test_random_vs_oracle(self):  # suffix patterns, duplicates, overlaps
        rng = random.Random(10)
        for _ in range(600):
            alpha = rng.choice(["a", "ab", "abc"])
            patterns = [rnd_str(rng, rng.randint(1, 4), alpha)
                        for _ in range(rng.randint(0, 6))]
            texts = [rnd_str(rng, rng.randint(0, 15), alpha)
                     for _ in range(rng.randint(0, 4))]
            self.assertEqual(A.aho(patterns, texts), aho_oracle(patterns, texts),
                             (patterns, texts))

    def test_independent_texts_state_reset(self):
        r = A.aho(["ab"], ["a", "b", "ab", "a", "b"])
        self.assertEqual(r, [[0], [0], [1], [0], [0]])

    def test_scale_dense(self):  # dense matches, many failure links
        pats = ["a" * k for k in range(1, 400)]  # 399 nested patterns
        texts = ["a" * 2000] * 100
        t0 = time.time()
        res = A.aho(pats, texts)
        self.assertLess(time.time() - t0, 15)
        self.assertEqual(res[0][0], 2000)
        self.assertEqual(res[0][398], 2000 - 399 + 1)

    def test_scale_many_patterns(self):
        rng = random.Random(11)
        pats = [rnd_str(rng, 10, "abcdefgh") for _ in range(10000)]
        texts = [rnd_str(rng, 2000, "abcdefgh") for _ in range(100)]
        t0 = time.time()
        res = A.aho(pats, texts)
        self.assertLess(time.time() - t0, 15)
        self.assertEqual(res[3][5], len(search_oracle(texts[3], pats[5])))


# ------------------------------------------------- JSON Lines interface
class TestInterface(unittest.TestCase):
    def test_mixed_batch_no_stale_state(self):
        reqs = [
            {"task": "lcs", "a": "tea_time", "b": "team"},
            {"task": "aho", "patterns": ["he", "she", "he"], "texts": ["sheshe", ""]},
            {"task": "tree", "n": 3, "weights": [4, 9, 6], "edges": [[0, 1], [1, 2]]},
            {"task": "kmp", "text": "abababa", "pattern": "aba"},
            {"task": "suffix", "text": "banana"},
            {"task": "merge", "sizes": [2, 3, 4]},
            {"task": "rk", "text": "abdj", "pattern": "ab"},
            {"task": "naive", "text": "aaaaa", "pattern": "aaa"},
        ] * 2
        out = [A.handle(json.loads(json.dumps(r))) for r in reqs]
        half = len(reqs) // 2
        self.assertEqual(out[:half], out[half:])
        self.assertEqual(out[0], {"length": 4, "sequence": "team"})
        self.assertEqual(out[4]["repeated"], "ana")

    def test_integer_types_and_stdio(self):
        import subprocess
        inp = "\n".join(json.dumps(r) for r in [
            {"task": "merge", "sizes": [2, 3, 4]},
            {"task": "tree", "n": 0, "weights": [], "edges": []},
            {"task": "naive", "text": "", "pattern": ""},
        ]) + "\n"
        p = subprocess.run(
            [sys.executable, os.path.join(os.path.dirname(A.__file__), "a4_solution.py")],
            input=inp, capture_output=True, text=True, check=True,
        )
        lines = [json.loads(x) for x in p.stdout.splitlines()]
        self.assertEqual(lines[0], {"cost": 14, "plan": [[0, 0, 1], [0, 1, 2]]})
        self.assertEqual(lines[1], {"weight": 0, "selected": []})
        self.assertEqual(lines[2], {"positions": [0]})
        self.assertIs(type(lines[0]["cost"]), int)


if __name__ == "__main__":
    unittest.main()
