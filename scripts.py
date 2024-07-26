#!/usr/bin/env python
import os
import subprocess
import sys
import webbrowser
from pathlib import Path

from generate_changelog import main as generate_changelog

BASE_PATH = Path(__file__).resolve().parent


def build_docs() -> None:
    if len(sys.argv) > 1:
        changelog_file = sys.argv[1]
    else:
        changelog_file = str(BASE_PATH / "CHANGELOG.rst")
    generate_changelog(changelog_file)
    docs_dir = BASE_PATH / "docs"
    os.chdir(docs_dir)
    subprocess.run(["make", "html"])


def open_docs() -> None:
    index_path = os.path.join(os.getcwd(), "docs", "build", "html", "index.html")
    webbrowser.open(f"file://{index_path}")


def check() -> None:
    subprocess.run(["pre-commit", "run", "--all-files"])


def build_changelog() -> None:
    generate_changelog()


def change_version() -> None:
    args = sys.argv[1:]
    subprocess.run(["change-version-doc.sh", *args])


def release() -> None:
    args = sys.argv[1:]
    subprocess.run(["./release.sh", *args])
