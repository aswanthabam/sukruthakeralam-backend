#!/usr/bin/env python3
"""
Root script runner.

Runs any script inside scripts/ by name, forwarding all remaining
arguments to it untouched.

Usage:
    python run.py <script_name> [args...]

Examples:
    python run.py test_ses_email someone@example.com
    python run.py test_ses_email someone@example.com --template

`<script_name>` can be given with or without the .py extension.
Run with no arguments (or --list) to see available scripts.
"""

import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
SCRIPTS_DIR = PROJECT_ROOT / "scripts"


def list_scripts() -> list[str]:
    if not SCRIPTS_DIR.exists():
        return []
    return sorted(p.stem for p in SCRIPTS_DIR.glob("*.py") if p.name != "__init__.py")


def print_usage(exit_code: int = 0) -> int:
    print(__doc__)
    available = list_scripts()
    if available:
        print("Available scripts:")
        for name in available:
            print(f"  - {name}")
    else:
        print(f"No scripts found in {SCRIPTS_DIR}")
    return exit_code


def main() -> int:
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help", "--list"):
        return print_usage()

    script_name = sys.argv[1]
    script_args = sys.argv[2:]

    # Allow passing with or without .py
    candidate = script_name if script_name.endswith(".py") else f"{script_name}.py"
    script_path = SCRIPTS_DIR / candidate

    if not script_path.is_file():
        print(f"❌ Script not found: {script_path}\n")
        return print_usage(exit_code=1)

    # Run as a subprocess with the same interpreter (respects active venv),
    # and with cwd set to the project root so relative imports/paths
    # inside the script (e.g. `from apps.settings import settings`) work
    # the same way they would if run directly from the root.
    result = subprocess.run(
        [sys.executable, str(script_path), *script_args],
        cwd=PROJECT_ROOT,
    )
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
