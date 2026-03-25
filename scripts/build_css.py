"""
Compile Tailwind vers static/css/tailwind.css (nécessite Node.js et npm install à la racine).

Usage :
  uv run python scripts/build_css.py
"""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    npm = shutil.which("npm") or shutil.which("npm.cmd")
    if not npm:
        print(
            "npm introuvable : installe Node.js puis exécute `npm install` à la racine du projet.",
            file=sys.stderr,
        )
        return 1
    try:
        subprocess.run([npm, "run", "build:css"], cwd=ROOT, check=True)
    except subprocess.CalledProcessError:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
