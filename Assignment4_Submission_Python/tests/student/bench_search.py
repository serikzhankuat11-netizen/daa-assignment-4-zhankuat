"""Reproducible comparison of naive / KMP / exact Rabin-Karp (modulus 101).

Run from the repository root (any of these works):
    python tests/student/bench_search.py
    python tests/student/bench_search.py --runs 5 --seed 12345

What is measured
  * the three pure search functions only (a4_solution.naive / kmp / rk);
  * input generation, JSON parsing and process start-up are NOT inside the timer;
  * the same boundary for every method: time.perf_counter_ns() around one call;
  * CPython has no JIT, so "warm-up" is 1 untimed call per method and case
    (fills caches / specialises the bytecode);
  * correctness first: every method must return exactly the same positions as an
    independent oracle (slice comparison) before it is timed.

Sizes stay inside the common domain of all three methods (n, m <= 3000).
Cases:  random (uniform over a 4-letter alphabet)   -> few hash candidates
        repetitive (text a^n, pattern a^(m-1) b)     -> naive worst case, RK has no candidates
        repetitive-match (text a^n, pattern a^m)    -> every window matches
        collision-heavy (text a^n, pattern a^(m-2) b B) -> hash(pattern) == hash(a^m) mod 101,
                                    so EVERY window is an RK candidate but none matches
"""

import argparse
import os
import platform
import random
import statistics
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
for rel in (".", "..", "../../Python/source", "../../source"):
    sys.path.insert(0, os.path.normpath(os.path.join(HERE, rel)))

import a4_solution as A  # noqa: E402


def oracle(text, pattern):
    n, m = len(text), len(pattern)
    if m == 0:
        return list(range(n + 1))
    return [i for i in range(n - m + 1) if text[i:i + m] == pattern]


def make_cases(rng):
    sizes = [(500, 25), (1500, 75), (3000, 150)]  # increasing n and m
    cases = []
    for n, m in sizes:
        text = "".join(rng.choice("abcd") for _ in range(n))
        # pattern is a real substring so that at least one match exists
        start = rng.randrange(n - m + 1)
        cases.append(("random", n, m, text, text[start:start + m]))
    for n, m in sizes:
        cases.append(("repetitive a^n / a^(m-1)b", n, m, "a" * n, "a" * (m - 1) + "b"))
    for n, m in sizes:
        cases.append(("repetitive-match a^n / a^m", n, m, "a" * n, "a" * m))
    for n, m in sizes:
        # 31*ord('b') + ord('B') == 31*ord('a') + ord('a')  (mod 101)  -> same hash as a^m
        cases.append(("collision-heavy a^n / a^(m-2)bB", n, m, "a" * n, "a" * (m - 2) + "bB"))
    return cases


def time_once(fn, text, pattern):
    t0 = time.perf_counter_ns()
    fn(text, pattern)
    return (time.perf_counter_ns() - t0) / 1e6  # ms


def cpu_name():
    try:
        with open("/proc/cpuinfo", encoding="utf-8") as f:
            for line in f:
                if line.lower().startswith("model name"):
                    return line.split(":", 1)[1].strip()
    except OSError:
        pass
    return platform.processor() or platform.machine()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=20261107)
    ap.add_argument("--runs", type=int, default=5, help="measured runs per method (>=3)")
    args = ap.parse_args()
    if args.runs < 3:
        ap.error("--runs must be at least 3")

    rng = random.Random(args.seed)
    methods = [("naive", A.naive), ("kmp", A.kmp), ("rk(mod 101)", A.rk)]

    print("# naive / KMP / RK benchmark")
    print()
    print("- seed: %d, measured runs per method: %d (median reported), warm-up: 1 untimed call"
          % (args.seed, args.runs))
    print("- Python: %s (%s)" % (platform.python_version(), platform.python_implementation()))
    print("- OS: %s; CPU: %s; logical CPUs: %s"
          % (platform.platform(), cpu_name(), os.cpu_count()))
    print("- timer: time.perf_counter_ns around one call of the search function;"
          " compilation/parsing/generation excluded")
    print()
    print("| case | n | m | matches z | naive ms | kmp ms | rk ms | rk candidate windows c |")
    print("|---|---:|---:|---:|---:|---:|---:|---:|")

    for name, n, m, text, pattern in make_cases(rng):
        expected = oracle(text, pattern)
        for label, fn in methods:  # correctness BEFORE timing
            got = fn(text, pattern)
            if got != expected:
                sys.exit("MISMATCH in %s for case %s n=%d m=%d" % (label, name, n, m))
        meds = []
        for label, fn in methods:
            fn(text, pattern)  # warm-up
            runs = [time_once(fn, text, pattern) for _ in range(args.runs)]
            meds.append(statistics.median(runs))
        # number of equal-hash windows (candidates) for the RK row
        base, mod = A.RK_BASE, A.RK_MOD
        high = pow(base, m - 1, mod)
        hp = hw = 0
        for i in range(m):
            hp = (hp * base + ord(pattern[i])) % mod
            hw = (hw * base + ord(text[i])) % mod
        c = 0
        for s in range(n - m + 1):
            if hp == hw:
                c += 1
            if s + m < n:
                hw = ((hw - ord(text[s]) * high) * base + ord(text[s + m])) % mod
        print("| %s | %d | %d | %d | %.3f | %.3f | %.3f | %d |"
              % (name, n, m, len(expected), meds[0], meds[1], meds[2], c))

    print()
    print("All outputs were identical to the oracle before timing. Medians of a few runs on one"
          " machine illustrate behaviour; they do not prove asymptotic complexity.")


if __name__ == "__main__":
    main()
