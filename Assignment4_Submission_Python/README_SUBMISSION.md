# Assignment 4 — Python submission files

Student: **Serik Zhankuat, SE-2520**  
Language: **Python 3.12+** (tested here with Python 3.13.5).

## Important: use the official template repository

This ZIP contains your implementation, tests, benchmark and completed draft analysis. It is **not** a replacement for the official GitHub template. Create your own repository using **Use this template → Create a new repository** from https://github.com/RZhaniya/daa-assignment-4-archive, then copy/merge these files into that repository, preserving the official `tools/`, `tests/public.json`, `.github/workflows/`, `docs/` and launcher files. Replace the template's `Python/source/` with the folder here, replace root `ANALYSIS.md` and `submission.json`, and add `tests/student/`.

## Run from the official repository root

```bash
python tools/run.py --setup
python tools/run.py --check
python -m unittest discover -s tests/student -v
python tests/student/bench_search.py --runs 5 --seed 20261107
```

The 37 own tests passed in the review environment. The official 44-case launcher and GitHub Actions have **not** been run on your repository yet. Do not claim they passed until you run them.

## Final Moodle submission

Push your work to GitHub. In Actions, verify **Public checks** for the exact commit. Copy the commit URL with its full 40-character SHA and selected language `Python` into Moodle Online text, click **Submit assignment**, and verify the final status. Deadline in the assignment brief: 8 November 2026, 23:59.

This package cannot guarantee a 100/100 grade: the practical score depends on the official grader, and the 50-point defence is an individual 15-question Moodle quiz. Prepare for that quiz independently.
