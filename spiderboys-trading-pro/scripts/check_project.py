from __future__ import annotations

import compileall
import json
import re
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = [
    "app.py",
    "requirements.txt",
    "pyproject.toml",
    "README.md",
    ".streamlit/config.toml",
    "core/engine.py",
    "core/data.py",
    "core/risk.py",
    "core/analytics.py",
    "data/market.csv",
    "data/journal.csv",
]


def main() -> int:
    missing = [path for path in REQUIRED if not (ROOT / path).exists()]
    if missing:
        print("Missing required files:", *missing, sep="\n- ")
        return 1
    if not compileall.compile_dir(ROOT, quiet=1, rx=re.compile(r"/(\.venv|\.git)/")):
        print("Python compilation failed.")
        return 1
    version = json.loads((ROOT / "VERSION.json").read_text())
    print(f"Project check passed: Spiderboys Trading Pro {version['version']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
