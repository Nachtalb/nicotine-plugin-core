#!/usr/bin/env python
import os
import subprocess
import webbrowser


def build_docs() -> None:
    docs_dir = os.path.join(os.getcwd(), "docs")
    os.chdir(docs_dir)
    subprocess.run(["make", "html"])


def open_docs() -> None:
    index_path = os.path.join(os.getcwd(), "docs", "build", "html", "index.html")
    webbrowser.open(f"file://{index_path}")


def check() -> None:
    subprocess.run(["pre-commit", "run", "--all-files"])
