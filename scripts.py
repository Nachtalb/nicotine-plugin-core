#!/usr/bin/env python
import os
import subprocess
import webbrowser
from pathlib import Path

BASE_PATH = Path(__file__).resolve().parent


def build_docs() -> None:
    docs_dir = BASE_PATH / "docs"
    os.chdir(docs_dir)
    subprocess.run(["make", "html"])


def open_docs() -> None:
    index_path = os.path.join(os.getcwd(), "docs", "build", "html", "index.html")
    webbrowser.open(f"file://{index_path}")


def check() -> None:
    subprocess.run(["pre-commit", "run", "--all-files"])
