# Student tests and benchmark

Run from repository root:

```bash
python -m unittest discover -s tests/student -v
python tests/student/bench_search.py --runs 5 --seed 20261107
```

The unit suite contains 37 tests with brute-force/random oracles, edge cases, collision tests, repeated-request checks and scale cases. The benchmark verifies all methods against an independent oracle before measuring them.
