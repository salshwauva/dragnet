#!/usr/bin/env python3
"""Convenience: runs `python -m dragnet --smoke-test -v` so users don't have to remember.

Run as: `./scripts/smoke_test.py` (requires .venv activated first).
"""

import os
import sys
from pathlib import Path

repo_root = Path(__file__).parent.parent
os.chdir(repo_root)
os.execvp(sys.executable, [sys.executable, "-m", "dragnet", "--smoke-test", "-v"])
