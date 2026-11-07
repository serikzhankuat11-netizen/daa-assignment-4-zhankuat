# Assignment 4 — Analysis (Dynamic Programming and String Processing)

**Student:** Serik Zhankuat, SE-2520  
**Language:** Python 3.12 (`submission.json`: `"language": "Python"`)  
**Source:** `Python/source/a4_solution.py` (all algorithms) — tests in `tests/student/`

> The official template launcher and GitHub Actions still need to be run in the student's own repository. Results below distinguish completed local checks from pending GitHub checks.

## 0. Build, run and test commands

```text
python tools/run.py --language Python --setup                 # compile/startup check
python tools/run.py --language Python --check                 # 44 public cases + repeated batch
python tools/run.py --language Python --input examples/lcs.jsonl
python -m unittest discover -s tests/student -v               # own tests (37 tests)
python tests/student/bench_search.py --runs 5 --seed 20261107 # naive / KMP / RK comparison
```

Status of checks performed for this package:

| Check | Result |
|---|---|
| `tools/run.py --setup` | Not run in the supplied ZIP; run after copying into the official template repository |
| `tools/run.py --check` (44 public cases) | Not run in the supplied ZIP; run after copying into the official template repository |
| `python -m unittest discover -s tests/student -v` | **OK — 37 tests passed** (Python 3.13.5, this review environment) |
| GitHub Actions "Public checks" for the submitted commit | Pending: requires your GitHub repository and pushed commit |

## 1. Common conventions

* Input/output is UTF-8 JSON Lines: one request per line, one result per line, only results on
  stdout. `handle(request)` dispatches on `task`; every algorithm is a pure function that builds
  its own tables, so **no state survives between requests** (checked by a mixed repeated batch).
* All indices (positions, block indices, vertex IDs) are zero-based.
* Python integers are arbitrary precision, so costs, weights and counts never overflow.
* No built-in substring search (`find`, `in`, `index`, `count`, `re`) is used inside naive, KMP,
  Rabin–Karp, suffix array or Aho–Corasick. Sorting (`list.sort`) and `dict` are used as allowed
  standard collections.

## 2. Part 1 — LCS (`lcs`)

**State.** `dp[i][j]` = length of a longest common subsequence of the prefixes `a[:i]` and `b[:j]`.

**Base cases.** `dp[0][j] = dp[i][0] = 0` (an empty prefix has no common character). If either
input is empty the answer is `length = 0`, `sequence = ""`.

**Transition.**
* `a[i-1] == b[j-1]`: `dp[i][j] = dp[i-1][j-1] + 1`.
* otherwise: `dp[i][j] = max(dp[i-1][j], dp[i][j-1])`.

**Order.** Rows `i = 1..|a|`, columns `j = 1..|b|`; every cell depends only on earlier cells.

**Why it is correct.** On a mismatch the last characters cannot both be used, so an optimal
subsequence ignores `a[i-1]` or ignores `b[j-1]`: the better of the two smaller problems is optimal.
On a match there is an optimal solution that pairs the two last characters (exchange argument: if an
optimal solution leaves one of them unused, replacing its last matched pair by this pair keeps the
length), so the match is always safe to take.

**Reconstruction.** Start at `(|a|, |b|)`. If the characters match, emit that character and move
diagonally; otherwise move to the neighbour with the larger `dp` value (up on a tie). Reverse the
emitted characters. Every emitted character is matched in both strings in increasing order, so the
result is a common subsequence, and the number of diagonal steps equals `dp[|a|][|b|]`.

**Complexity.** Time `O((|a|+1)(|b|+1))`, memory `O((|a|+1)(|b|+1))` for the table.

## 3. Part 2 — ordered adjacent block merging (`merge`)

**State.** `dp[l][r]` = minimum total cost to merge the original blocks `l..r` into one block
(`dp[i][i] = 0`).

**Transition.** The *last* merge combines `[l,k]` and `[k+1,r]` for some `l <= k < r`. Its cost is
the size of the whole interval, `S(l,r) = sum(sizes[l..r])`, regardless of `k`, so

`dp[l][r] = min over k of ( dp[l][k] + dp[k+1][r] ) + S(l,r)`.

`S` is computed in O(1) from prefix sums. We store the best `k` in `split[l][r]`.

**Order.** By increasing interval length (2, 3, …, n) so both sub-intervals are already solved.

**Correctness.** Any valid merge sequence is a binary tree over the ordered blocks (merges are only
between adjacent blocks); the last merge fixes the root split, and the two subtrees are independent
subproblems, so optimal substructure holds. Choosing the two smallest *non-adjacent* blocks is not
allowed: for `[1,10,1]` it would cost 14, but the adjacent optimum is 23.

**Plan / reconstruction.** Traverse the split tree from `[0,n-1]` in **post-order** (iteratively):
emit `[l,k,r]` only after the merges that create `[l,k]` and `[k+1,r]`. Thus the plan is
chronological and every merge joins two blocks that exist at that time. `n-1` merges are emitted.
For `n <= 1`: `cost = 0`, `plan = []`.

**Complexity.** Time `O(n^3)` (n(n-1)/2 intervals × up to n-1 splits), memory `O(n^2)`.

## 4. Part 3 — maximum weight independent set on a tree (`tree`)

**State** (for a vertex `v` in the tree rooted at 0):
* `take[v]` = best weight in the subtree of `v` if `v` **is** selected,
* `skip[v]` = best weight in the subtree of `v` if `v` is **not** selected.

**Transition.** `take[v] = w[v] + sum over children c of skip[c]` (children must be unselected);
`skip[v] = sum over children c of max(take[c], skip[c])`. A leaf has `take = w`, `skip = 0`.

**Order.** An iterative DFS records vertices in an order where each parent appears before its
children. Processing that order **in reverse** is a post-order: all children are finished before the
parent, and no recursion is used, so a chain of 100 000 vertices is safe.

**Answer.** `max(take[root], skip[root])`. Because `skip >= 0` the empty set is always possible, so
all-negative inputs give weight 0. The optimum does not depend on the root (the DP is exact for any
root).

**Reconstruction.** Go through the order top-down. If the parent is selected, the child is forced to
be unselected; otherwise the child is selected iff `take[c] > skip[c]`. Selected vertices are
therefore never adjacent and each appears once. For `n = 0`: `weight = 0`, `selected = []`.

**Complexity.** Time `O(n+1)`, auxiliary memory `O(n+1)` (adjacency, parent, order, two DP arrays).

## 5. Part 4 — exact search

Common contract: all zero-based start positions in increasing order, overlaps included; the empty
pattern returns `0..n` (n+1 starts); a pattern longer than the text returns `[]`. All three
functions handle `m = 0` and `m > n` before touching the pattern.

### 5.1 Naive
For every start `s = 0..n-m` compare characters one by one until a mismatch or `m` matches.
The last valid start is `n-m` (not `n-m-1`). Time `O((n-m+1)·m) ⊆ O(n·m)`, auxiliary `O(1)`,
output `O(z)`.

### 5.2 KMP
**Prefix function** `pi[i]` = length of the longest *proper* prefix of `p[0..i]` that is also a suffix
of `p[0..i]`.
**Scan.** Keep `k` = length of the currently matched prefix of the pattern. On a mismatch fall back
`k = pi[k-1]` until the characters agree or `k = 0`; on agreement `k += 1`. When `k = m`, record the
start `i-m+1` and set `k = pi[m-1]` — the fallback after a **full match** keeps overlapping matches
(e.g. `aba` in `abababa` → 0, 2, 4).
**Why linear.** `k` increases by at most 1 per text character and every fallback decreases it, so
the total number of fallbacks is ≤ n; the same argument bounds the prefix-function construction by
`O(m)`. Time `O(n+m+z+1)`, auxiliary `O(m+1)`.

### 5.3 Rabin–Karp (base 31, modulus 101)
**Hash.** `H(w) = (w[0]·31^(m-1) + w[1]·31^(m-2) + … + w[m-1]) mod 101` with ASCII codes; the leftmost
character has the highest power.
**Rolling update.** `H(s+1) = ((H(s) − t[s]·31^(m-1))·31 + t[s+m]) mod 101`; negative remainders are
normalised into `0..100`.
**Verification.** Equal hashes are only candidates: the characters are compared one by one before a
position is reported. With modulus 101 collisions are frequent (`ab` and `dj` both hash to 75:
`97·31+98 = 3105 ≡ 75`, `100·31+106 = 3206 ≡ 75`), so verification is essential.
**Complexity.** With `c` candidate windows: `O(n+m+c·m)`; in the worst case `c ≈ n-m+1` (see the
collision-heavy benchmark case) so the bound over all inputs is `O(n·m+n+m+1)`. We do **not** claim
linear worst-case time. Auxiliary memory is `O(1)` plus the output.

## 6. Part 5 — suffix array (prefix doubling) and Kasai LCP (`suffix`)

**Rank pairs.** After the round with length `k`, `rank[i]` is the rank of suffix `i` by its first `k`
characters (equal prefixes share a rank; suffixes shorter than `k` are compared by the characters they
have). Round `k` sorts the suffixes by the pair `(rank[i], rank[i+k])`, using `0` for the missing
second half (shorter suffix sorts first), then doubles `k`. Initially `rank[i] = ord(s[i])`. We stop
as soon as all ranks are distinct (`rank` of the last suffix = `n-1`). A pair is packed into one
integer `rank[i]·B + (rank[i+k]+1)` with `B > n` and `B > 127`, so Python's `sort` is exact.
No sentinel and no empty suffix are used; suffix strings are never materialised.

**Complexity.** At most `ceil(log2 n)` rounds, each `O(n log n)` (comparison sort) →
`O(n log² n)` time, `O(n)` memory.

**Kasai.** `inv[sa[i]] = i`. Process suffixes in text order `i = 0..n-1`; for `i` with `inv[i] > 0`
let `j = sa[inv[i]-1]` be the previous suffix in sorted order and extend the running value `h` while
`s[i+h] == s[j+h]`; store `lcp[inv[i]] = h`, then `h = max(h-1, 0)`. **Reuse:** if suffix `i` has LCP
`h` with its predecessor, suffix `i+1` has LCP at least `h-1` with *its* predecessor (drop the first
character from both). Hence `h` grows at most `2n` times in total → `O(n)`. `lcp[0] = 0`.

**Longest repeat.** Any substring that occurs at two distinct starts is a common prefix of two
different suffixes, and the LCP of any two suffixes equals the minimum of the adjacent LCPs between
them in sorted order, so the maximum over all pairs is `max(lcp)`. We return
`text[sa[i] : sa[i] + lcp[i]]` for an index `i` with maximal `lcp[i]` (overlapping occurrences are
allowed: `banana` → `ana`). If `max(lcp) = 0` the result is `""`; for the empty text
`sa = lcp = []`.

## 7. Part 6 — Aho–Corasick (`aho`)

1. **Trie.** Insert every pattern; `terminal[i]` is the state of pattern `i`. Duplicate patterns end
   in the same state but keep separate dictionary positions, so they receive equal counts.
2. **Failure links** (BFS). `fail[v]` is the state of the longest proper suffix of `v`'s string that
   is a prefix of some pattern; for a child `v` of `u` via `ch`, follow `fail[u], fail[fail[u]], …`
   until a state with a `ch`-transition exists. Total work is `O(L)` amortised.
3. **Counting per text.** For every text start in state 0, follow transitions (falling back along
   failure links on a missing transition) and add 1 to `cnt[state]` for each visited state. Afterwards
   **propagate visits along failure links in reverse BFS order**: `cnt[fail[v]] += cnt[v]`. A state's
   total then equals the number of text positions where its string ends, which includes occurrences of
   it as a *suffix* of a longer matched pattern (`he` inside `she`). The answer for dictionary
   position `i` is `cnt[terminal[i]]`.
4. **Independence.** `cnt` and the current state are created fresh for each text; an empty text gives a
   row of zeros; no patterns gives an empty row per text; no texts gives `[]`.

No per-match list is built, so dense matches cost nothing extra. We use dictionary children with the
failure-link walk (amortised `O(|text|)`) instead of a full 95-column transition table.

**Complexity.** Build `O(L+p)` time and `O(S+p)` memory (`S` = trie states ≤ L+1); each text
`O(|text|+S+p)`; output `O(q(p+1))`.

## 8. Own tests (input, expected, actual, defect detected)

Implemented in `tests/student/test_a4.py` (37 unit tests). Random tests compare with independent
oracles (brute-force subsets/permutations, slice comparison, sorted suffix strings), not with another
implementation of the same algorithm. A selection of fixed cases (actual = real output of
`Python/source/a4_solution.py`):

| # | Command | Input | Expected | Actual | Defect it detects |
|---|---|---|---|---|---|
| 1 | lcs | `a="tea_time", b="team"` | length 4, `team` | `{"length":4,"sequence":"team"}` | substring instead of subsequence |
| 2 | lcs | `a="", b="abc"` | 0, `""` | `{"length":0,"sequence":""}` | missing empty-input base case |
| 3 | lcs | `a="AB", b="BA"` | length 1 (case-sensitive, alternative witnesses) | `{"length":1,"sequence":"A"}` | wrong mismatch transition |
| 4 | merge | `[2,3,4]` | cost 14 | `{"cost":14,"plan":[[0,0,1],[0,1,2]]}` | wrong merge order / cost |
| 5 | merge | `[1,10,1]` | cost 23 (not 14) | `{"cost":23,"plan":[[1,1,2],[0,0,2]]}` | merging non-adjacent blocks |
| 6 | merge | `[10,1,1,10]` | cost 36, chronological plan | `{"cost":36,"plan":[[1,1,2],[1,2,3],[0,0,3]]}` | parent merge listed before child merges |
| 7 | merge | `[7]`, `[]` | cost 0, `[]` | `{"cost":0,"plan":[]}` | n ≤ 1 base case |
| 8 | tree | path `4-9-6` | weight 10, `{0,2}` | `{"weight":10,"selected":[0,2]}` | selecting adjacent vertices |
| 9 | tree | path, weights `-1,-2,-3` | weight 0, `[]` | `{"weight":0,"selected":[]}` | forcing a non-empty selection |
| 10 | tree | `n=0` | 0, `[]` | `{"weight":0,"selected":[]}` | empty tree crash |
| 11 | tree | star, centre 5, leaves 1,1,1 | weight 5 | `{"weight":5,"selected":[0]}` | wrong take/skip tie handling |
| 12 | tree | chain n=100000 (unit test) | weight 50000, no crash | OK | recursion depth error |
| 13 | naive | `aaaaa`, `aaa` | `[0,1,2]` | `{"positions":[0,1,2]}` | missing overlaps / last start |
| 14 | naive | `abc`, `""` | `[0,1,2,3]` | `{"positions":[0,1,2,3]}` | empty pattern ≠ n+1 starts |
| 15 | naive | `ab`, `abc` | `[]` | `{"positions":[]}` | pattern longer than text |
| 16 | kmp | `abababa`, `aba` | `[0,2,4]` | `{"positions":[0,2,4]}` | no fallback after full match |
| 17 | kmp | `""`, `""` | `[0]` | `{"positions":[0]}` | empty text + empty pattern |
| 18 | rk | `abdj`, `ab` | `[0]` | `{"positions":[0]}` | reporting hash collision `dj` |
| 19 | rk | `djabdj`, `ab` | `[2]` | `{"positions":[2]}` | collision before a real match |
| 20 | suffix | `banana` | sa `[5,3,1,0,4,2]`, lcp `[0,1,3,0,0,2]`, `ana` | identical | wrong order / LCP / repeat |
| 21 | suffix | `""` | `[]`, `[]`, `""` | identical | empty text |
| 22 | suffix | `aaaa` | sa `[3,2,1,0]`, lcp `[0,1,2,3]`, `aaa` | identical | all-equal, overlapping repeat |
| 23 | suffix | `abcd` | sa `[0,1,2,3]`, lcp all 0, `""` | identical | repeated must be empty |
| 24 | aho | `he,she,he` × `sheshe,sheshe,""` | `[[2,2,2],[2,2,2],[0,0,0]]` | identical | missing suffix patterns / duplicates / state reuse |
| 25 | aho | `[]` × `ab,""` | `[[],[]]` | `{"counts":[[],[]]}` | empty dictionary |
| 26 | aho | `ab` × `a,b,ab,a,b` | `[[0],[0],[1],[0],[0]]` | identical | automaton state leaking between texts |
| 27 | aho | `aa,a` × `aaaa` | `[[3,4]]` | `{"counts":[[3,4]]}` | overlaps and nested patterns |

Further automated checks: random LCS/merge/tree/search/suffix/Aho cases against oracles
(hundreds each); `rk` with long periodic text to exercise negative remainders; a mixed batch of all
eight commands run twice in one process (no stale state); scale tests (`lcs` 1000×1000, `merge` n=200
with values 10⁹, `tree` chain/star n=10⁵ with sums > 2³¹, `kmp` 2·10⁵, `suffix` 5·10⁴ for `a^n`,
random and `(ab)^k`, `aho` with 10 000 patterns / 100 texts / dense nested patterns).

## 9. Comparison naive / KMP / exact RK

Reproducible with `python tests/student/bench_search.py --runs 5 --seed 20261107`.

**Method.** Three increasing sizes `(n, m) = (500, 25), (1500, 75), (3000, 150)`, all inside the common
domain of the three algorithms (both lengths ≤ 3000). Four text/pattern distributions, each at all
three sizes: *random* (uniform on `{a,b,c,d}`, the pattern is a real substring), *repetitive*
(`a^n` with pattern `a^(m-1)b`, no match), *repetitive-match* (`a^n` with `a^m`, every window
matches) and *collision-heavy* (`a^n` with `a^(m-2)bB`: `31·98+66 ≡ 31·97+97 (mod 101)`, so the
pattern has the same hash as every window but matches nowhere). Generator: `random.Random(seed)`,
default seed `20261107`. **Before timing**, each method's output is compared with an independent
oracle and the script aborts on any difference. Timer: `time.perf_counter_ns()` around exactly one
call of the search function (parsing, generation and process start-up excluded; no compilation in
Python). Warm-up: one untimed call per method and case (CPython has no JIT). Measured runs: 5 per
method and case; the **median** is reported.

**Environment and results** (paste the script output here after running it on your machine):

```text
Recorded in the ChatGPT review execution environment (not the student's personal computer):

- Python: 3.13.5 (CPython)
- OS: Linux 6.18.57 x86_64 (glibc 2.41)
- CPU: Intel Xeon Platinum 8573C; 3 logical CPUs exposed to the process
- Seed: 20261107; five measured runs per method; one untimed warm-up

| case | n | m | matches z | naive ms | KMP ms | RK ms | RK candidate windows c |
|---|---:|---:|---:|---:|---:|---:|---:|
| random | 500 | 25 | 1 | 0.037 | 0.033 | 0.065 | 4 |
| random | 1500 | 75 | 1 | 0.109 | 0.098 | 0.195 | 13 |
| random | 3000 | 150 | 1 | 0.203 | 0.198 | 0.400 | 27 |
| repetitive a^n / a^(m-1)b | 500 | 25 | 0 | 0.554 | 0.051 | 0.064 | 0 |
| repetitive a^n / a^(m-1)b | 1500 | 75 | 0 | 4.663 | 0.156 | 0.196 | 0 |
| repetitive a^n / a^(m-1)b | 3000 | 150 | 0 | 20.283 | 0.374 | 0.375 | 0 |
| repetitive-match a^n / a^m | 500 | 25 | 476 | 0.550 | 0.045 | 0.635 | 476 |
| repetitive-match a^n / a^m | 1500 | 75 | 1426 | 4.751 | 0.136 | 5.072 | 1426 |
| repetitive-match a^n / a^m | 3000 | 150 | 2851 | 20.308 | 0.295 | 19.053 | 2851 |
| collision-heavy a^n / a^(m-2)bB | 500 | 25 | 0 | 0.556 | 0.052 | 0.650 | 476 |
| collision-heavy a^n / a^(m-2)bB | 1500 | 75 | 0 | 5.029 | 0.171 | 5.678 | 1426 |
| collision-heavy a^n / a^(m-2)bB | 3000 | 150 | 0 | 18.982 | 0.308 | 20.386 | 2851 |

All three outputs matched the independent oracle before timing. These figures describe this review container only; rerun the benchmark on your own machine before submission if your instructor expects your own hardware details.
```

**What to expect and why** (check it against your own table):
* *Random text:* few matches and few hash collisions (about n/101 candidate windows); naive exits
  after ~1 comparison per window, so naive and KMP are close and RK pays for its hash arithmetic.
* *Repetitive `a^n / a^(m-1)b`:* naive compares ~m characters at every window → `Θ(n·m)`; KMP stays
  linear; RK has no candidates because the hashes differ, so it is also fast.
* *Repetitive-match and collision-heavy:* every window is a candidate, RK verifies ~m characters per
  window and becomes `Θ(n·m)` like naive (plus the hashing overhead); KMP is unaffected.
* Medians from a few runs on one machine are illustrations only; they do not prove asymptotic
  complexity. A collision laboratory with base 31 and modulus 101 does not represent real hashing: a
  production implementation uses a much larger (or random) modulus/base, 64-bit or double hashing,
  so false positives are rare and the candidate cost is negligible in practice. Here the tiny
  modulus is deliberate, to make collisions easy to test.

## 10. Acknowledgements and AI assistance

* **Sources:** the assignment specification and `docs/guide/CONTRACTS.md` of the template; lecture
  8–10 material on LCS/interval/tree DP, KMP and rolling hashes, suffix arrays/Kasai and Aho–Corasick.
* **AI assistance:** The original archive credits Claude (Anthropic) with producing the initial
  implementation (`Python/source/a4_solution.py`), unit tests, benchmark script and draft analysis.
  ChatGPT was subsequently used to compare the archive with the published specification, review
  the project layout, execute the 37 supplied unit tests and run the benchmark in a separate
  review environment. Neither AI assistant ran the official Moodle grader or submitted the work.
* **Student contribution and verification:** Serik Zhankuat supplied the project archive for review.
  Before submission, the student must personally inspect and understand all eight algorithms,
  run `tools/run.py --setup` and `tools/run.py --check` in the official template repository, run
  the student tests and benchmark, inspect the GitHub Actions result, and edit this paragraph to
  describe only work personally completed. The student should submit only if able to explain the
  implementation independently during the individual defence.
