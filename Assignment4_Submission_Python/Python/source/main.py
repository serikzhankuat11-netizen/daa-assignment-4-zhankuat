"""Official JSON Lines entry point for Assignment 4 (Python)."""
from a4_solution import main

if __name__ == "__main__":
    import sys
    if hasattr(sys.stdin, "reconfigure"):
        sys.stdin.reconfigure(encoding="utf-8")
        sys.stdout.reconfigure(encoding="utf-8")
    main()
